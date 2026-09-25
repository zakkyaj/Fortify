/**
 * MetricsPanel — Step 4: Metrics
 * Shows baseline vs attack metrics returned by POST /api/experiment/run.
 * Never invents a value — shows "—" when a metric is absent.
 */
import { useExperiment } from '../store/experimentStore'
import styles from './MetricsPanel.module.css'

function fmt(val, unit = '') {
  if (val == null || val === undefined) return '—'
  const n = typeof val === 'number' ? val : Number(val)
  if (isNaN(n)) return '—'
  return unit ? `${n.toLocaleString()} ${unit}` : n.toLocaleString()
}

function MetricCard({ label, baseline, attack, unit = '', highlight = false }) {
  const bNum = baseline != null ? Number(baseline) : null
  const aNum = attack   != null ? Number(attack)   : null

  let delta = null
  let direction = null
  if (bNum != null && aNum != null && bNum > 0) {
    delta = ((aNum - bNum) / bNum) * 100
    direction = delta > 5 ? 'worse' : delta < -5 ? 'better' : 'neutral'
  }

  return (
    <div className={`${styles.card} ${highlight ? styles.cardHighlight : ''}`}>
      <span className={styles.cardLabel}>{label}</span>
      <div className={styles.cardValues}>
        <div className={styles.cardValue}>
          <span className={styles.valueLabel}>Baseline</span>
          <span className={styles.valueNum}>{fmt(baseline, unit)}</span>
        </div>
        <div className={styles.cardArrow}>→</div>
        <div className={styles.cardValue}>
          <span className={styles.valueLabel}>Under Attack</span>
          <span className={`${styles.valueNum} ${styles[`val_${direction}`] ?? ''}`}>
            {fmt(attack, unit)}
          </span>
        </div>
      </div>
      {delta != null && (
        <div className={`${styles.delta} ${styles[`delta_${direction}`]}`}>
          {delta > 0 ? '+' : ''}{delta.toFixed(1)}%
          {direction === 'worse'   ? ' degraded'  : ''}
          {direction === 'better'  ? ' improved'  : ''}
          {direction === 'neutral' ? ' unchanged' : ''}
        </div>
      )}
    </div>
  )
}

function TrafficRow({ label, value }) {
  return (
    <div className={styles.trafficRow}>
      <span className={styles.trafficKey}>{label}</span>
      <span className={styles.trafficVal}>{value ?? '—'}</span>
    </div>
  )
}

export default function MetricsPanel() {
  const { experimentResult } = useExperiment()

  if (!experimentResult) return null

  const b = experimentResult.baseline_metrics ?? {}
  const a = experimentResult.attack_metrics   ?? {}
  const t = experimentResult.traffic          ?? {}

  const hasBaseline = Object.keys(b).length > 0
  const hasAttack   = Object.keys(a).length > 0

  return (
    <div className={`${styles.wrapper} card`}>
      <div className={styles.head}>
        <span className={styles.stepNum}>4</span>
        <h3 className={styles.title}>Metrics</h3>
        <span className={styles.subLabel}>Baseline vs Attack</span>
      </div>

      {(!hasBaseline && !hasAttack) && (
        <div className={styles.empty}>
          No metric data returned. Prometheus may not have scraped data yet.
        </div>
      )}

      {(hasBaseline || hasAttack) && (
        <div className={styles.grid}>
          <MetricCard
            label="Avg Latency"
            baseline={b.average_latency_ms}
            attack={a.average_latency_ms}
            unit="ms"
            highlight
          />
          <MetricCard
            label="P95 Latency"
            baseline={b.p95_latency_ms}
            attack={a.p95_latency_ms}
            unit="ms"
          />
          <MetricCard
            label="Error Rate"
            baseline={b.error_rate_percent}
            attack={a.error_rate_percent}
            unit="%"
          />
          <MetricCard
            label="Request Count"
            baseline={b.request_count}
            attack={a.request_count}
          />
        </div>
      )}

      {/* Traffic summary */}
      {Object.keys(t).length > 0 && (
        <div className={styles.trafficSection}>
          <span className={styles.trafficTitle}>Traffic Summary</span>
          <div className={styles.trafficGrid}>
            <TrafficRow label="Rate"            value={t.requested_rate != null ? `${t.requested_rate} req/s` : null} />
            <TrafficRow label="Duration"        value={t.duration_seconds != null ? `${t.duration_seconds} s` : null} />
            <TrafficRow label="Total Requests"  value={t.total_requests} />
            <TrafficRow label="Successful"      value={t.success_count} />
            <TrafficRow label="Errors"          value={t.error_count} />
          </div>
        </div>
      )}

      {/* Experiment IDs */}
      <div className={styles.ids}>
        {experimentResult.experiment_id && (
          <div className={styles.idRow}>
            <span className={styles.idKey}>experiment_id</span>
            <code className={styles.idVal}>{experimentResult.experiment_id}</code>
          </div>
        )}
        {experimentResult.attack_id && (
          <div className={styles.idRow}>
            <span className={styles.idKey}>attack_id</span>
            <code className={styles.idVal}>{experimentResult.attack_id}</code>
          </div>
        )}
      </div>
    </div>
  )
}
