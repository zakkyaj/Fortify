/**
 * RetestPanel — Step 7: Retest
 * Sends POST /api/retest with a chosen resilience strategy.
 * Stores the result in retestResult context.
 */
import { useState } from 'react'
import { useExperiment } from '../store/experimentStore'
import { runRetest } from '../api/experiment'
import styles from './RetestPanel.module.css'

const STRATEGIES = [
  {
    value: 'timeout',
    label: 'Timeout',
    desc: 'Simulate a request timeout that fails fast instead of waiting the full latency.',
    fields: [
      { key: 'timeout_ms', label: 'Timeout (ms)', min: 100, max: 30000, default: 1000 },
    ],
  },
  {
    value: 'circuit_breaker',
    label: 'Circuit Breaker',
    desc: 'Simulate a circuit breaker that opens and returns 0 ms latency immediately.',
    fields: [],
  },
]

export default function RetestPanel() {
  const {
    architectureId, experimentResult,
    retestResult, setRetestResult,
    retesting, setRetesting,
    retestError, setRetestError,
  } = useExperiment()

  const [strategy, setStrategy] = useState('timeout')
  const [timeoutMs, setTimeoutMs] = useState(1000)

  const canRetest = !!(experimentResult?.attack_id && architectureId && !retesting)

  async function handleRetest() {
    if (!canRetest) return
    setRetesting(true)
    setRetestError(null)

    const resilience = strategy === 'timeout'
      ? { strategy: 'timeout', timeout_ms: Number(timeoutMs) }
      : { strategy: 'circuit_breaker' }

    try {
      const result = await runRetest({
        architecture_id: architectureId,
        previous_attack_id: experimentResult.attack_id,
        resilience,
        traffic: {
          rate: 10,
          duration_seconds: 10,
        },
      })
      setRetestResult(result)
    } catch (err) {
      const detail =
        err?.response?.data?.detail ??
        err?.response?.data?.error?.message ??
        err?.message ?? 'Unknown error'
      setRetestError(`Retest failed: ${detail}`)
    } finally {
      setRetesting(false)
    }
  }

  if (!experimentResult) return null

  const stratMeta = STRATEGIES.find(s => s.value === strategy) ?? STRATEGIES[0]

  return (
    <div className={`${styles.wrapper} card`}>
      <div className={styles.head}>
        <span className={styles.stepNum}>7</span>
        <h3 className={styles.title}>Retest</h3>
        {retestResult && !retesting && (
          <span className={styles.doneBadge}>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Done
          </span>
        )}
      </div>

      {/* Previous attack summary */}
      <div className={styles.prevAttack}>
        <span className={styles.prevLabel}>Original attack</span>
        <div className={styles.prevRow}>
          <span className={styles.prevKey}>attack_id</span>
          <code className={styles.prevVal}>{experimentResult.attack_id}</code>
        </div>
        <div className={styles.prevRow}>
          <span className={styles.prevKey}>target</span>
          <span className={styles.prevVal}>{experimentResult.attack?.target ?? '—'}</span>
        </div>
        <div className={styles.prevRow}>
          <span className={styles.prevKey}>value</span>
          <span className={styles.prevVal}>{experimentResult.attack?.value != null ? `${experimentResult.attack.value} ms` : '—'}</span>
        </div>
      </div>

      {/* Strategy selector */}
      <div className={styles.fieldGroup}>
        <label className={styles.label}>Resilience Strategy</label>
        <div className={styles.strategyCards}>
          {STRATEGIES.map(s => (
            <button
              key={s.value}
              className={`${styles.stratCard} ${strategy === s.value ? styles.stratCardActive : ''}`}
              onClick={() => setStrategy(s.value)}
              disabled={retesting}
              type="button"
            >
              <span className={styles.stratName}>{s.label}</span>
              <span className={styles.stratDesc}>{s.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Strategy-specific fields */}
      {strategy === 'timeout' && (
        <div className={styles.fieldGroup}>
          <label className={styles.label}>
            Timeout Value
            <span className={styles.labelUnit}>milliseconds</span>
          </label>
          <div className={styles.sliderRow}>
            <input
              type="range"
              className={styles.slider}
              min={100} max={10000} step={100}
              value={timeoutMs}
              onChange={e => setTimeoutMs(Number(e.target.value))}
              disabled={retesting}
            />
            <input
              type="number"
              className={styles.numberInput}
              min={100} max={10000} step={100}
              value={timeoutMs}
              onChange={e => setTimeoutMs(Number(e.target.value))}
              disabled={retesting}
            />
          </div>
        </div>
      )}

      {/* Simulation notice */}
      <div className={styles.simNotice}>
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        The retest simulates the strategy by adjusting the Toxiproxy toxic. simulation_mode will be true in the response.
      </div>

      {/* Error */}
      {retestError && (
        <div className={styles.error}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          {retestError}
        </div>
      )}

      <button
        className={`btn btn-secondary ${styles.btn}`}
        onClick={handleRetest}
        disabled={!canRetest}
      >
        {retesting ? (
          <><span className={styles.spinner} />Running Retest…</>
        ) : (
          <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.95"/>
          </svg>Run Retest</>
        )}
      </button>

      {/* Retest result summary */}
      {retestResult && (
        <div className={styles.retestResult}>
          <span className={styles.resultLabel}>Retest Result</span>
          <div className={styles.resultGrid}>
            <div className={styles.resultItem}>
              <span className={styles.resultKey}>Status</span>
              <span className={styles.resultVal}>{retestResult.status ?? '—'}</span>
            </div>
            <div className={styles.resultItem}>
              <span className={styles.resultKey}>Strategy Applied</span>
              <span className={styles.resultVal}>{retestResult.applied_strategy ?? '—'}</span>
            </div>
            <div className={styles.resultItem}>
              <span className={styles.resultKey}>Simulation Mode</span>
              <span className={`${styles.resultVal} ${retestResult.simulation_mode ? styles.simTrue : ''}`}>
                {retestResult.simulation_mode != null ? String(retestResult.simulation_mode) : '—'}
              </span>
            </div>
            <div className={styles.resultItem}>
              <span className={styles.resultKey}>New Attack ID</span>
              <code className={styles.resultCode}>{retestResult.new_attack_id ?? '—'}</code>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
