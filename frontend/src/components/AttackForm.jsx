/**
 * AttackForm — Step 2: Configure Attack
 * Lets the user select target, attack type, value and traffic config.
 * Shows a pre-execution summary before handing off to ExperimentRunner.
 */
import { useState } from 'react'
import { useExperiment } from '../store/experimentStore'
import styles from './AttackForm.module.css'

const ATTACK_TYPES = [
  { value: 'latency', label: 'Latency Injection', unit: 'ms', min: 100, max: 30000, step: 100, default: 5000 },
]

const TARGET_OPTIONS = [
  { value: 'payment', label: 'Payment Service', note: 'Via Toxiproxy' },
]

export default function AttackForm({ onReady }) {
  const { attackConfig, setAttackConfig, trafficConfig, setTrafficConfig, architectureId } = useExperiment()

  const [validationError, setValidationError] = useState(null)

  const attackMeta = ATTACK_TYPES.find(t => t.value === attackConfig.type) ?? ATTACK_TYPES[0]

  function handleAttackChange(field, raw) {
    setValidationError(null)
    setAttackConfig(prev => ({ ...prev, [field]: field === 'value' ? Number(raw) : raw }))
  }

  function handleTrafficChange(field, raw) {
    setValidationError(null)
    setTrafficConfig(prev => ({ ...prev, [field]: Number(raw) }))
  }

  function validate() {
    if (!architectureId) return 'Register an architecture first (Step 1).'
    if (!attackConfig.target) return 'Select a target service.'
    if (!attackConfig.type) return 'Select an attack type.'
    const v = Number(attackConfig.value)
    if (isNaN(v) || v < 1) return 'Attack value must be a positive number.'
    const r = Number(trafficConfig.rate)
    if (isNaN(r) || r < 1 || r > 20) return 'Traffic rate must be between 1 and 20 req/s.'
    const d = Number(trafficConfig.duration_seconds)
    if (isNaN(d) || d < 5 || d > 120) return 'Duration must be between 5 and 120 seconds.'
    return null
  }

  function handleRunClick() {
    const err = validate()
    if (err) { setValidationError(err); return }
    onReady?.()
  }

  const targetLabel = TARGET_OPTIONS.find(t => t.value === attackConfig.target)?.label ?? attackConfig.target
  const totalRequests = trafficConfig.rate * trafficConfig.duration_seconds

  return (
    <div className={styles.wrapper}>
      <div className={styles.formGrid}>

        {/* ── Attack configuration ── */}
        <div className={`${styles.section} card`}>
          <div className={styles.sectionHead}>
            <span className={styles.sectionNum}>2</span>
            <h3 className={styles.sectionTitle}>Configure Attack</h3>
          </div>

          {!architectureId && (
            <div className={styles.notice}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              Register an architecture in Step 1 to enable attack configuration.
            </div>
          )}

          <div className={styles.fieldGroup}>
            <label className={styles.label}>Target Service</label>
            <select
              className={styles.select}
              value={attackConfig.target}
              onChange={e => handleAttackChange('target', e.target.value)}
              disabled={!architectureId}
            >
              {TARGET_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label} — {o.note}</option>
              ))}
            </select>
          </div>

          <div className={styles.fieldGroup}>
            <label className={styles.label}>Attack Type</label>
            <select
              className={styles.select}
              value={attackConfig.type}
              onChange={e => handleAttackChange('type', e.target.value)}
              disabled={!architectureId}
            >
              {ATTACK_TYPES.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          <div className={styles.fieldGroup}>
            <label className={styles.label}>
              Latency Value
              <span className={styles.labelUnit}>milliseconds</span>
            </label>
            <div className={styles.sliderRow}>
              <input
                type="range"
                className={styles.slider}
                min={attackMeta.min}
                max={attackMeta.max}
                step={attackMeta.step}
                value={attackConfig.value}
                onChange={e => handleAttackChange('value', e.target.value)}
                disabled={!architectureId}
              />
              <input
                type="number"
                className={styles.numberInput}
                min={attackMeta.min}
                max={attackMeta.max}
                step={attackMeta.step}
                value={attackConfig.value}
                onChange={e => handleAttackChange('value', e.target.value)}
                disabled={!architectureId}
              />
            </div>
            <div className={styles.sliderTicks}>
              <span>100 ms</span>
              <span>{(attackMeta.max / 2).toLocaleString()} ms</span>
              <span>{attackMeta.max.toLocaleString()} ms</span>
            </div>
          </div>
        </div>

        {/* ── Traffic configuration ── */}
        <div className={`${styles.section} card`}>
          <div className={styles.sectionHead}>
            <span className={styles.sectionNum}>2b</span>
            <h3 className={styles.sectionTitle}>Traffic Configuration</h3>
          </div>

          <div className={styles.fieldGroup}>
            <label className={styles.label}>
              Requests per second
              <span className={styles.labelUnit}>max 20</span>
            </label>
            <div className={styles.sliderRow}>
              <input
                type="range"
                className={styles.slider}
                min={1} max={20} step={1}
                value={trafficConfig.rate}
                onChange={e => handleTrafficChange('rate', e.target.value)}
                disabled={!architectureId}
              />
              <input
                type="number"
                className={styles.numberInput}
                min={1} max={20} step={1}
                value={trafficConfig.rate}
                onChange={e => handleTrafficChange('rate', e.target.value)}
                disabled={!architectureId}
              />
            </div>
          </div>

          <div className={styles.fieldGroup}>
            <label className={styles.label}>
              Duration
              <span className={styles.labelUnit}>seconds (5–120)</span>
            </label>
            <div className={styles.sliderRow}>
              <input
                type="range"
                className={styles.slider}
                min={5} max={120} step={5}
                value={trafficConfig.duration_seconds}
                onChange={e => handleTrafficChange('duration_seconds', e.target.value)}
                disabled={!architectureId}
              />
              <input
                type="number"
                className={styles.numberInput}
                min={5} max={120} step={5}
                value={trafficConfig.duration_seconds}
                onChange={e => handleTrafficChange('duration_seconds', e.target.value)}
                disabled={!architectureId}
              />
            </div>
          </div>

          <div className={styles.trafficEstimate}>
            <span className={styles.estimateLabel}>Estimated requests</span>
            <span className={styles.estimateValue}>{totalRequests.toLocaleString()}</span>
          </div>
        </div>

      </div>

      {/* ── Experiment Summary ── */}
      <div className={`${styles.summary} card`}>
        <div className={styles.summaryHead}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          <span className={styles.summaryTitle}>Experiment Summary</span>
        </div>
        <div className={styles.summaryGrid}>
          <div className={styles.summaryItem}>
            <span className={styles.summaryKey}>Architecture</span>
            <code className={styles.summaryVal}>{architectureId ?? '—'}</code>
          </div>
          <div className={styles.summaryItem}>
            <span className={styles.summaryKey}>Target</span>
            <span className={styles.summaryVal}>{targetLabel}</span>
          </div>
          <div className={styles.summaryItem}>
            <span className={styles.summaryKey}>Attack</span>
            <span className={styles.summaryVal}>Latency</span>
          </div>
          <div className={styles.summaryItem}>
            <span className={styles.summaryKey}>Value</span>
            <span className={`${styles.summaryVal} ${styles.summaryHighlight}`}>
              {Number(attackConfig.value).toLocaleString()} ms
            </span>
          </div>
          <div className={styles.summaryItem}>
            <span className={styles.summaryKey}>Traffic</span>
            <span className={styles.summaryVal}>{trafficConfig.rate} req/s</span>
          </div>
          <div className={styles.summaryItem}>
            <span className={styles.summaryKey}>Duration</span>
            <span className={styles.summaryVal}>{trafficConfig.duration_seconds} seconds</span>
          </div>
        </div>

        {validationError && (
          <div className={styles.validationError}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            {validationError}
          </div>
        )}

        <button
          className={`btn btn-primary ${styles.runBtn}`}
          onClick={handleRunClick}
          disabled={!architectureId}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          Run Resilience Test
        </button>
      </div>
    </div>
  )
}
