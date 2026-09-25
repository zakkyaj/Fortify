"""
ResilienceAnalyzer
==================
Deterministic, keyless analysis of multi-service Prometheus metrics collected
during a Fortify experiment.

Accepts the ``service_metrics`` dict produced by the experiment orchestrator:

    {
        "baseline": {
            "gateway": {"average_latency_ms": ..., "request_count": ..., ...},
            "order":   {...},
            "payment": {...},
        },
        "attack": {
            "gateway": {...},
            "order":   {...},
            "payment": {...},
        },
    }

Returns a structured result with:
    root_cause        – human-readable description of the primary failure origin
    severity          – "low" | "medium" | "high"
    affected_services – list of service names that show significant degradation
    evidence          – per-service dict of latency uplift facts
    propagation       – ordered list describing how degradation travelled
    confidence        – "high" | "medium" | "low" (based on data quality)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------

# Minimum absolute latency increase (ms) to consider a service degraded.
MIN_ABSOLUTE_UPLIFT_MS: float = 50.0

# Relative uplift thresholds (ratio of attack/baseline average latency).
# A ratio of 2.0 means attack latency is at least 2× baseline.
UPLIFT_HIGH: float = 3.0    # ratio ≥ 3× → high severity
UPLIFT_MEDIUM: float = 1.5  # ratio ≥ 1.5× → medium severity

# Minimum request count for a window to be considered reliable data.
MIN_REQUESTS: int = 2

# Services in call-chain order (downstream → upstream).
CALL_CHAIN: tuple[str, ...] = ("payment", "order", "gateway")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _avg(metrics: dict[str, Any]) -> float | None:
    """Return average_latency_ms from a service metric dict, or None."""
    v = metrics.get("average_latency_ms")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _count(metrics: dict[str, Any]) -> int:
    """Return request_count from a service metric dict, or 0."""
    try:
        return int(metrics.get("request_count", 0))
    except (TypeError, ValueError):
        return 0


def _uplift_ratio(baseline_ms: float, attack_ms: float) -> float:
    """Return attack/baseline ratio; 0 when baseline is zero or negative."""
    if baseline_ms <= 0:
        return 0.0
    return attack_ms / baseline_ms


def _is_degraded(
    baseline_ms: float | None,
    attack_ms: float | None,
    baseline_count: int,
    attack_count: int,
) -> tuple[bool, float, float]:
    """
    Determine whether a service is degraded.

    Returns (degraded, ratio, absolute_increase_ms).
    """
    if baseline_ms is None or attack_ms is None:
        return False, 0.0, 0.0
    if baseline_count < MIN_REQUESTS or attack_count < MIN_REQUESTS:
        return False, 0.0, 0.0

    absolute = attack_ms - baseline_ms
    ratio = _uplift_ratio(baseline_ms, attack_ms)

    degraded = absolute >= MIN_ABSOLUTE_UPLIFT_MS and ratio >= UPLIFT_MEDIUM
    return degraded, ratio, absolute


# ---------------------------------------------------------------------------
# Public result dataclass
# ---------------------------------------------------------------------------

@dataclass
class AnalysisResult:
    root_cause: str
    severity: str                          # "low" | "medium" | "high"
    affected_services: list[str]
    evidence: dict[str, dict]              # service -> latency facts
    propagation: list[str]                 # ordered description of spread
    confidence: str                        # "high" | "medium" | "low"

    def to_dict(self) -> dict:
        return {
            "root_cause": self.root_cause,
            "severity": self.severity,
            "affected_services": self.affected_services,
            "evidence": self.evidence,
            "propagation": self.propagation,
            "confidence": self.confidence,
        }


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class ResilienceAnalyzer:
    """
    Deterministic resilience analyzer.  No network calls, no API keys.

    Usage::

        analyzer = ResilienceAnalyzer()
        result = analyzer.analyze(service_metrics)
        print(result.to_dict())
    """

    def analyze(self, service_metrics: dict[str, dict]) -> AnalysisResult:
        """
        Analyse ``service_metrics`` and return a structured :class:`AnalysisResult`.

        Parameters
        ----------
        service_metrics:
            Dict with keys ``"baseline"`` and ``"attack"``, each mapping
            service name → metric dict (as produced by the experiment
            orchestrator).
        """
        baseline = service_metrics.get("baseline") or {}
        attack   = service_metrics.get("attack")   or {}

        # ── 1. Per-service uplift ────────────────────────────────────────────
        degraded: list[str] = []
        evidence: dict[str, dict] = {}

        for svc in CALL_CHAIN:
            b_metrics = baseline.get(svc) or {}
            a_metrics = attack.get(svc)   or {}

            b_avg = _avg(b_metrics)
            a_avg = _avg(a_metrics)
            b_cnt = _count(b_metrics)
            a_cnt = _count(a_metrics)

            is_deg, ratio, absolute = _is_degraded(b_avg, a_avg, b_cnt, a_cnt)

            svc_evidence: dict[str, Any] = {
                "baseline_avg_ms": round(b_avg, 1) if b_avg is not None else None,
                "attack_avg_ms":   round(a_avg, 1) if a_avg is not None else None,
                "uplift_ratio":    round(ratio, 2),
                "absolute_increase_ms": round(absolute, 1),
                "degraded":        is_deg,
            }

            # Flag when we have too little data to be reliable
            if b_avg is None or a_avg is None:
                svc_evidence["data_quality"] = "missing"
            elif b_cnt < MIN_REQUESTS or a_cnt < MIN_REQUESTS:
                svc_evidence["data_quality"] = "insufficient_requests"
            else:
                svc_evidence["data_quality"] = "ok"

            evidence[svc] = svc_evidence
            if is_deg:
                degraded.append(svc)

        # ── 2. Root cause & propagation ──────────────────────────────────────
        root_cause, propagation = self._root_cause_and_propagation(degraded, evidence)

        # ── 3. Severity ──────────────────────────────────────────────────────
        severity = self._severity(degraded, evidence)

        # ── 4. Confidence ────────────────────────────────────────────────────
        confidence = self._confidence(evidence)

        return AnalysisResult(
            root_cause=root_cause,
            severity=severity,
            affected_services=degraded,
            evidence=evidence,
            propagation=propagation,
            confidence=confidence,
        )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _root_cause_and_propagation(
        self,
        degraded: list[str],
        evidence: dict[str, dict],
    ) -> tuple[str, list[str]]:
        if not degraded:
            return "No significant degradation detected across services.", []

        # Identify the most downstream degraded service — that is the origin.
        origin = None
        for svc in CALL_CHAIN:            # payment → order → gateway
            if svc in degraded:
                origin = svc
                break

        if origin is None:
            return "Degradation detected but origin undetermined.", []

        propagation: list[str] = []
        ratio = evidence[origin]["uplift_ratio"]
        abs_ms = evidence[origin]["absolute_increase_ms"]
        propagation.append(
            f"{origin}: latency increased {abs_ms:.0f} ms "
            f"({ratio:.1f}× baseline) — identified as origin"
        )

        # Walk upstream from origin and describe spread
        found_origin = False
        for svc in CALL_CHAIN:
            if svc == origin:
                found_origin = True
                continue
            if found_origin and svc in degraded:
                r = evidence[svc]["uplift_ratio"]
                a = evidence[svc]["absolute_increase_ms"]
                propagation.append(
                    f"{svc}: latency increased {a:.0f} ms ({r:.1f}×) — "
                    f"propagated from {origin}"
                )

        root_cause = (
            f"Latency degradation originated at {origin} "
            f"({abs_ms:.0f} ms increase, {ratio:.1f}× baseline)."
        )
        if len(degraded) > 1:
            upstream = [s for s in degraded if s != origin]
            root_cause += (
                f" Degradation propagated upstream to: {', '.join(upstream)}."
            )

        return root_cause, propagation

    def _severity(
        self,
        degraded: list[str],
        evidence: dict[str, dict],
    ) -> str:
        if not degraded:
            return "low"

        # Use the maximum ratio across all degraded services
        max_ratio = max(
            evidence[svc]["uplift_ratio"]
            for svc in degraded
        )

        if max_ratio >= UPLIFT_HIGH:
            return "high"
        if max_ratio >= UPLIFT_MEDIUM:
            return "medium"
        return "low"

    def _confidence(self, evidence: dict[str, dict]) -> str:
        qualities = [v.get("data_quality") for v in evidence.values()]
        missing   = qualities.count("missing")
        insuf     = qualities.count("insufficient_requests")

        if missing == 0 and insuf == 0:
            return "high"
        if missing <= 1 and insuf <= 1:
            return "medium"
        return "low"
