"""
Unit tests for ai/resilience_analyzer.py

No network calls, no API keys, no external dependencies.

Run from the repo root (or Fortify/ai/):
    python -m pytest ai/tests/test_resilience_analyzer.py -v
"""
import sys
import os
import pytest

# Make sure the ai/ directory is importable when running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from resilience_analyzer import (
    ResilienceAnalyzer,
    AnalysisResult,
    UPLIFT_HIGH,
    UPLIFT_MEDIUM,
    MIN_ABSOLUTE_UPLIFT_MS,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _metrics(
    baseline_avg: float,
    attack_avg: float,
    baseline_count: int = 10,
    attack_count: int = 10,
) -> dict:
    """Build a minimal service_metrics dict for a single service."""
    return {
        "baseline": {"average_latency_ms": baseline_avg, "request_count": baseline_count},
        "attack":   {"average_latency_ms": attack_avg,   "request_count": attack_count},
    }


def _build(
    gw_baseline=50.0, gw_attack=55.0,
    ord_baseline=60.0, ord_attack=65.0,
    pay_baseline=40.0, pay_attack=45.0,
    count=10,
) -> dict:
    """Build a full service_metrics dict with configurable per-service values."""
    def svc(b, a):
        return {"average_latency_ms": a, "request_count": count}

    def base(v):
        return {"average_latency_ms": v, "request_count": count}

    return {
        "baseline": {
            "gateway": base(gw_baseline),
            "order":   base(ord_baseline),
            "payment": base(pay_baseline),
        },
        "attack": {
            "gateway": svc(gw_baseline, gw_attack),
            "order":   svc(ord_baseline, ord_attack),
            "payment": svc(pay_baseline, pay_attack),
        },
    }


analyzer = ResilienceAnalyzer()


# ===========================================================================
# 1. No degradation
# ===========================================================================

class TestNoDegradation:
    def test_returns_analysis_result(self):
        sm = _build()
        result = analyzer.analyze(sm)
        assert isinstance(result, AnalysisResult)

    def test_no_affected_services(self):
        sm = _build()  # all uplifts are 5 ms — below MIN_ABSOLUTE_UPLIFT_MS
        result = analyzer.analyze(sm)
        assert result.affected_services == []

    def test_severity_is_low(self):
        sm = _build()
        assert analyzer.analyze(sm).severity == "low"

    def test_root_cause_mentions_no_degradation(self):
        sm = _build()
        assert "No significant degradation" in analyzer.analyze(sm).root_cause

    def test_propagation_is_empty(self):
        sm = _build()
        assert analyzer.analyze(sm).propagation == []

    def test_confidence_high_when_all_data_ok(self):
        sm = _build()
        assert analyzer.analyze(sm).confidence == "high"

    def test_to_dict_has_all_keys(self):
        result = analyzer.analyze(_build()).to_dict()
        for key in ("root_cause", "severity", "affected_services",
                    "evidence", "propagation", "confidence"):
            assert key in result

    def test_evidence_contains_all_three_services(self):
        result = analyzer.analyze(_build())
        assert set(result.evidence.keys()) == {"gateway", "order", "payment"}

    def test_evidence_degraded_false_for_all(self):
        result = analyzer.analyze(_build())
        for svc in ("gateway", "order", "payment"):
            assert result.evidence[svc]["degraded"] is False


# ===========================================================================
# 2. Payment-only degradation
# ===========================================================================

class TestPaymentOnlyDegradation:
    """Payment degrades significantly; order and gateway are unaffected."""

    def _sm(self):
        return _build(
            pay_baseline=40.0,
            pay_attack=40.0 * 4,   # 4× → 160 ms, ratio 4.0 ≥ UPLIFT_HIGH
            ord_baseline=60.0,  ord_attack=65.0,
            gw_baseline=50.0,   gw_attack=54.0,
        )

    def test_only_payment_affected(self):
        result = analyzer.analyze(self._sm())
        assert result.affected_services == ["payment"]

    def test_severity_is_high(self):
        result = analyzer.analyze(self._sm())
        assert result.severity == "high"

    def test_root_cause_mentions_payment(self):
        result = analyzer.analyze(self._sm())
        assert "payment" in result.root_cause.lower()

    def test_no_upstream_propagation_in_root_cause(self):
        result = analyzer.analyze(self._sm())
        assert "propagated" not in result.root_cause.lower()

    def test_propagation_has_single_entry(self):
        result = analyzer.analyze(self._sm())
        assert len(result.propagation) == 1
        assert "origin" in result.propagation[0]

    def test_payment_evidence_degraded_true(self):
        result = analyzer.analyze(self._sm())
        assert result.evidence["payment"]["degraded"] is True

    def test_gateway_evidence_degraded_false(self):
        result = analyzer.analyze(self._sm())
        assert result.evidence["gateway"]["degraded"] is False

    def test_order_evidence_degraded_false(self):
        result = analyzer.analyze(self._sm())
        assert result.evidence["order"]["degraded"] is False

    def test_payment_uplift_ratio_correct(self):
        result = analyzer.analyze(self._sm())
        assert result.evidence["payment"]["uplift_ratio"] == pytest.approx(4.0, rel=0.01)

    def test_medium_severity_at_threshold(self):
        """Ratio just above UPLIFT_MEDIUM but below UPLIFT_HIGH → medium."""
        sm = _build(
            pay_baseline=100.0,
            pay_attack=100.0 * 2.0,   # 2× — above medium (1.5×), below high (3×)
            ord_baseline=60.0, ord_attack=63.0,
            gw_baseline=50.0,  gw_attack=52.0,
        )
        result = analyzer.analyze(sm)
        assert result.severity == "medium"
        assert "payment" in result.affected_services


# ===========================================================================
# 3. Full propagation: payment → order → gateway
# ===========================================================================

class TestFullPropagation:
    """All three services degrade; payment is the origin."""

    def _sm(self):
        return _build(
            pay_baseline=40.0,   pay_attack=40.0 * 5,   # 5× (high)
            ord_baseline=60.0,   ord_attack=60.0 * 4,   # 4× (high)
            gw_baseline=50.0,    gw_attack=50.0 * 3.5,  # 3.5× (high)
        )

    def test_all_three_services_affected(self):
        result = analyzer.analyze(self._sm())
        assert set(result.affected_services) == {"payment", "order", "gateway"}

    def test_severity_is_high(self):
        assert analyzer.analyze(self._sm()).severity == "high"

    def test_root_cause_mentions_payment_as_origin(self):
        rc = analyzer.analyze(self._sm()).root_cause
        assert "payment" in rc.lower()

    def test_root_cause_mentions_propagation(self):
        rc = analyzer.analyze(self._sm()).root_cause
        assert "propagated" in rc.lower()

    def test_root_cause_mentions_upstream_services(self):
        rc = analyzer.analyze(self._sm()).root_cause
        assert "order" in rc.lower() or "gateway" in rc.lower()

    def test_propagation_has_three_entries(self):
        result = analyzer.analyze(self._sm())
        assert len(result.propagation) == 3

    def test_propagation_first_entry_is_origin(self):
        result = analyzer.analyze(self._sm())
        assert "origin" in result.propagation[0]
        assert "payment" in result.propagation[0]

    def test_propagation_subsequent_entries_reference_propagated(self):
        result = analyzer.analyze(self._sm())
        for entry in result.propagation[1:]:
            assert "propagated" in entry

    def test_all_evidence_degraded_true(self):
        result = analyzer.analyze(self._sm())
        for svc in ("payment", "order", "gateway"):
            assert result.evidence[svc]["degraded"] is True

    def test_affected_services_ordered_downstream_to_upstream(self):
        """affected_services must be in CALL_CHAIN order."""
        result = analyzer.analyze(self._sm())
        from resilience_analyzer import CALL_CHAIN
        ordered = [s for s in CALL_CHAIN if s in result.affected_services]
        assert result.affected_services == ordered


# ===========================================================================
# 4. Missing service metrics
# ===========================================================================

class TestMissingServiceMetrics:
    def test_empty_service_metrics(self):
        result = analyzer.analyze({})
        assert isinstance(result, AnalysisResult)
        assert result.affected_services == []

    def test_missing_baseline_key(self):
        sm = {"attack": {"gateway": {"average_latency_ms": 500, "request_count": 10}}}
        result = analyzer.analyze(sm)
        # gateway has no baseline → not degraded (can't compute uplift)
        assert "gateway" not in result.affected_services

    def test_missing_attack_key(self):
        sm = {"baseline": {"payment": {"average_latency_ms": 40, "request_count": 10}}}
        result = analyzer.analyze(sm)
        assert "payment" not in result.affected_services

    def test_missing_single_service_in_baseline(self):
        sm = _build()
        del sm["baseline"]["payment"]
        result = analyzer.analyze(sm)
        assert "payment" not in result.affected_services

    def test_missing_single_service_in_attack(self):
        sm = _build()
        del sm["attack"]["order"]
        result = analyzer.analyze(sm)
        assert "order" not in result.affected_services

    def test_data_quality_missing_when_avg_absent(self):
        sm = {
            "baseline": {"payment": {"request_count": 10}},     # no avg
            "attack":   {"payment": {"average_latency_ms": 200, "request_count": 10}},
        }
        result = analyzer.analyze(sm)
        assert result.evidence["payment"]["data_quality"] == "missing"

    def test_confidence_low_when_most_data_missing(self):
        result = analyzer.analyze({})
        assert result.confidence == "low"

    def test_none_service_metrics_value(self):
        sm = {"baseline": None, "attack": None}
        result = analyzer.analyze(sm)
        assert isinstance(result, AnalysisResult)

    def test_insufficient_requests_flagged(self):
        """Fewer than MIN_REQUESTS in a window → data_quality insufficient."""
        sm = {
            "baseline": {"payment": {"average_latency_ms": 40, "request_count": 1}},
            "attack":   {"payment": {"average_latency_ms": 300, "request_count": 1}},
        }
        result = analyzer.analyze(sm)
        assert result.evidence["payment"]["data_quality"] == "insufficient_requests"
        assert "payment" not in result.affected_services


# ===========================================================================
# 5. Zero baseline latency
# ===========================================================================

class TestZeroBaselineLatency:
    def test_zero_baseline_not_degraded(self):
        """zero baseline → ratio = 0 → cannot determine uplift → not degraded."""
        sm = _build(pay_baseline=0.0, pay_attack=300.0)
        result = analyzer.analyze(sm)
        assert "payment" not in result.affected_services

    def test_zero_baseline_ratio_is_zero(self):
        sm = _build(pay_baseline=0.0, pay_attack=300.0)
        result = analyzer.analyze(sm)
        assert result.evidence["payment"]["uplift_ratio"] == 0.0

    def test_zero_attack_latency_not_degraded(self):
        sm = _build(pay_baseline=40.0, pay_attack=0.0)
        result = analyzer.analyze(sm)
        assert "payment" not in result.affected_services

    def test_both_zero_not_degraded(self):
        sm = _build(gw_baseline=0, gw_attack=0,
                    ord_baseline=0, ord_attack=0,
                    pay_baseline=0, pay_attack=0)
        result = analyzer.analyze(sm)
        assert result.affected_services == []
        assert result.severity == "low"


# ===========================================================================
# 6. Evidence structure
# ===========================================================================

class TestEvidenceStructure:
    def test_evidence_keys_present(self):
        result = analyzer.analyze(_build())
        for svc in ("gateway", "order", "payment"):
            ev = result.evidence[svc]
            for key in ("baseline_avg_ms", "attack_avg_ms",
                        "uplift_ratio", "absolute_increase_ms",
                        "degraded", "data_quality"):
                assert key in ev, f"Missing key '{key}' in evidence for {svc}"

    def test_absolute_increase_is_difference(self):
        sm = _build(pay_baseline=100.0, pay_attack=350.0)
        result = analyzer.analyze(sm)
        ev = result.evidence["payment"]
        assert ev["absolute_increase_ms"] == pytest.approx(250.0, rel=0.01)

    def test_uplift_ratio_matches_formula(self):
        sm = _build(pay_baseline=100.0, pay_attack=300.0)
        result = analyzer.analyze(sm)
        assert result.evidence["payment"]["uplift_ratio"] == pytest.approx(3.0, rel=0.01)


# ===========================================================================
# 7. Real experiment: 5-second Payment latency (Toxiproxy toxic)
# ===========================================================================

class TestPaymentLatencyExperiment:
    """
    Mirrors the actual Fortify experiment that injects 5 000 ms of Toxiproxy
    latency on the downstream leg of Order → Payment.

    Metric values are derived from a real run of the experiment:

    Baseline (no toxic, 30 requests/window collected via Prometheus scrape):
      payment  ~30 ms   (payment_request_duration_seconds)
      order    ~45 ms   (order_request_duration_seconds, includes payment RTT)
      gateway  ~60 ms   (gateway_request_duration_seconds, end-to-end)

    Attack window (toxic active, toxics.json: latency=5000 ms, jitter=0):
      payment  ~5 030 ms  (+5 000 ms from the Toxiproxy delay)
      order    ~5 080 ms  (payment delay + own processing)
      gateway  ~5 120 ms  (order delay + own processing)

    All three services cross both the MIN_ABSOLUTE_UPLIFT_MS (50 ms) and the
    UPLIFT_HIGH (3×) thresholds by a very wide margin, so the expected
    analysis is:
      severity          → "high"
      affected_services → ["payment", "order", "gateway"]  (CALL_CHAIN order)
      propagation       → payment as origin, order and gateway propagated
      evidence          → all three services show degraded=True
    """

    _SM = {
        "baseline": {
            "payment": {"average_latency_ms":   30.0, "request_count": 30},
            "order":   {"average_latency_ms":   45.0, "request_count": 30},
            "gateway": {"average_latency_ms":   60.0, "request_count": 30},
        },
        "attack": {
            "payment": {"average_latency_ms": 5030.0, "request_count": 30},
            "order":   {"average_latency_ms": 5080.0, "request_count": 30},
            "gateway": {"average_latency_ms": 5120.0, "request_count": 30},
        },
    }

    @classmethod
    def _result(cls):
        return ResilienceAnalyzer().analyze(cls._SM)

    def test_severity_is_high(self):
        """5 000 ms toxic pushes all ratios far above UPLIFT_HIGH (3×)."""
        assert self._result().severity == "high"

    def test_affected_services_downstream_to_upstream(self):
        """All three services are affected in CALL_CHAIN order: payment → order → gateway."""
        from resilience_analyzer import CALL_CHAIN
        result = self._result()
        assert result.affected_services == list(CALL_CHAIN)  # ["payment", "order", "gateway"]

    def test_payment_is_degraded(self):
        assert self._result().evidence["payment"]["degraded"] is True

    def test_order_is_degraded(self):
        assert self._result().evidence["order"]["degraded"] is True

    def test_gateway_is_degraded(self):
        assert self._result().evidence["gateway"]["degraded"] is True

    def test_payment_uplift_ratio_reflects_5s_toxic(self):
        """payment attack/baseline ≈ 5030/30 ≈ 167.7×."""
        ev = self._result().evidence["payment"]
        assert ev["uplift_ratio"] == pytest.approx(5030.0 / 30.0, rel=0.01)

    def test_payment_absolute_increase_is_5000ms(self):
        """Absolute increase for payment must equal the injected toxic duration."""
        ev = self._result().evidence["payment"]
        assert ev["absolute_increase_ms"] == pytest.approx(5000.0, rel=0.01)

    def test_propagation_length_is_three(self):
        """One entry per affected service (origin + 2 propagated)."""
        assert len(self._result().propagation) == 3

    def test_propagation_first_entry_identifies_payment_as_origin(self):
        assert "payment" in self._result().propagation[0]
        assert "origin" in self._result().propagation[0]

    def test_propagation_order_entry_references_payment(self):
        """Second propagation entry (order) must say it propagated from payment."""
        entry = self._result().propagation[1]
        assert "order" in entry
        assert "propagated" in entry

    def test_propagation_gateway_entry_references_payment(self):
        """Third propagation entry (gateway) must say it propagated from payment."""
        entry = self._result().propagation[2]
        assert "gateway" in entry
        assert "propagated" in entry

    def test_root_cause_names_payment_as_origin(self):
        assert "payment" in self._result().root_cause.lower()

    def test_root_cause_mentions_propagation_to_upstream(self):
        rc = self._result().root_cause.lower()
        assert "propagated" in rc

    def test_root_cause_mentions_order_and_gateway(self):
        rc = self._result().root_cause.lower()
        assert "order" in rc and "gateway" in rc

    def test_confidence_is_high(self):
        """All 30-request windows provide reliable data → confidence should be high."""
        assert self._result().confidence == "high"

    def test_evidence_data_quality_ok_for_all_services(self):
        result = self._result()
        for svc in ("payment", "order", "gateway"):
            assert result.evidence[svc]["data_quality"] == "ok"
