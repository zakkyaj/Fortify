/**
 * ComparisonPanel — Step 8: Before / After Comparison
 * Reads comparison data from retestResult.comparison or
 * fetches GET /api/comparisons/{attack_id} if available.
 * Never calculates or invents metrics.
 */
import { useExperiment } from '../store/experimentStore'
import styles from './ComparisonPanel.module.css'

function pct(val) {
  if (val == null) return null
  const n = Number(val)
  if (isNaN(n)) return null
  return n
}

function fmt(val, unit = '') {
  if (val == null) return '—'
  const n = Number(val)
  if (isNaN(n)) return '—'
  return unit ? `${n.toLocaleString()} ${unit}` : n.toLocaleString()
}

function DeltaChip({ value, invertDirection = false }) {
  const n = pct(value)
  if (n == null) return <span className={styles.deltaNeutral}>—</span>
  // Positive delta in latency = degraded; negative = improved (unless inverted)
  const improved = invertDirection ? n > 0 : n < 0
  const cls = improved ? styles.deltaGood : n === 0 ? styles.deltaNeutral : styles.deltaBad
  return (
    <span className={`${styles.delta} ${cls}`}>
      {n > 0 ? '+' : ''}{n.toFixed(1)}%
    </span>
  )
}

function CompRow({ label, before, after, unit, changePct, invertDirection = false }) {
  return (
    <tr className={styles.row}>
      <td className={styles.rowLabel}>{label}</td>
      <td className={styles.rowBefore}>{fmt(before, unit)}</td>
      <td className={styles.rowAfter}>{fmt(after, unit)}</td>
      <td className={styles.rowDelta}>
        <DeltaChip value={changePct} invertDirection={invertDirection} />
      </td>
    </tr>
  )
}

export default function ComparisonPanel() {
  const { retestResult, experimentResult } = useExperiment()

  if (!retestResult) return null

  // Prefer the comparison object embedded in the retest response
  const comp = retestResult.comparison ?? {}
  const before = comp.before ?? experimentResult?.baseline_metrics ?? {}
  const after  = comp.after  ?? retestResult.attack_metrics ?? {}
  const improvement = comp.improvement ?? {}

  const hasData = Object.keys(before).length > 0 || Object.keys(after).length > 0

  return (
    <div className={`${styles.wrapper} card`}>
      <div className={styles.head}>
        <span className={styles.stepNum}>8</span>
        <h3 className={styles.title}>Before / After Comparison</h3>
        {comp.simulation_mode && (
          <span className={styles.simBadge}>Simulation</span>
        )}
        {comp.applied_strategy && (
          <span className={styles.stratBadge}>{comp.applied_strategy.replace('_', ' ')}</span>
        )}
      </div>

      {!hasData && (
        <div className={styles.empty}>No comparison data available yet.</div>
      )}

      {hasData && (
        <>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th className={styles.th}>Metric</th>
                  <th className={styles.th}>Before (Baseline)</th>
                  <th className={styles.th}>After (Retest)</th>
                  <th className={styles.th}>Change</th>
                </tr>
              </thead>
              <tbody>
                <CompRow
                  label="Avg Latency"
                  before={before.average_latency_ms ?? improvement.before_avg_latency_ms}
                  after={after.average_latency_ms  ?? improvement.after_avg_latency_ms}
                  unit="ms"
                  changePct={improvement.latency_change_percent}
                />
                <CompRow
                  label="P95 Latency"
                  before={before.p95_latency_ms ?? improvement.before_p95_ms}
                  after={after.p95_latency_ms  ?? improvement.after_p95_ms}
                  unit="ms"
                  changePct={improvement.p95_change_percent}
                />
                <CompRow
                  label="Error Rate"
                  before={before.error_rate_percent}
                  after={after.error_rate_percent}
                  unit="%"
                  changePct={improvement.error_rate_change_percent}
                />
                <CompRow
                  label="Request Count"
                  before={before.request_count}
                  after={after.request_count}
                />
              </tbody>
            </table>
          </div>

          {/* Direction verdict */}
          {improvement.latency_direction && (
            <div className={`${styles.verdict} ${improvement.latency_direction === 'improved' ? styles.verdictGood : styles.verdictBad}`}>
              {improvement.latency_direction === 'improved' ? (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  Latency <strong>improved</strong> after applying {comp.applied_strategy?.replace('_', ' ') ?? 'resilience strategy'}.
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                  Latency <strong>degraded</strong> — strategy may need tuning.
                </>
              )}
            </div>
          )}

          {/* IDs */}
          <div className={styles.ids}>
            {comp.attack_id && (
              <div className={styles.idRow}>
                <span className={styles.idKey}>original attack</span>
                <code className={styles.idVal}>{comp.attack_id}</code>
              </div>
            )}
            {retestResult.retest_id && (
              <div className={styles.idRow}>
                <span className={styles.idKey}>retest experiment</span>
                <code className={styles.idVal}>{retestResult.retest_id}</code>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
