/**
 * RecommendationsPanel — Step 6: Recommendations
 * Displays every recommendation from experimentResult.recommendations.
 * Nothing is invented — if the array is empty we say so.
 */
import { useExperiment } from '../store/experimentStore'
import styles from './RecommendationsPanel.module.css'

const STRATEGY_ICONS = {
  timeout:         '⏱',
  'circuit-breaker': '⚡',
  'async-processing': '⇄',
  retry:           '↺',
  general:         '◈',
}

export default function RecommendationsPanel({ onProceedToRetest }) {
  const { experimentResult } = useExperiment()
  if (!experimentResult) return null

  const recs = experimentResult.recommendations ?? []

  return (
    <div className={`${styles.wrapper} card`}>
      <div className={styles.head}>
        <span className={styles.stepNum}>6</span>
        <h3 className={styles.title}>Recommendations</h3>
        <span className={styles.countBadge}>{recs.length}</span>
      </div>

      {recs.length === 0 ? (
        <div className={styles.empty}>No recommendations returned for this experiment.</div>
      ) : (
        <div className={styles.list}>
          {recs.map((rec, i) => (
            <div key={i} className={styles.recCard}>
              <div className={styles.recHeader}>
                <span className={styles.strategyIcon}>
                  {STRATEGY_ICONS[rec.strategy] ?? '◈'}
                </span>
                <div className={styles.recMeta}>
                  <span className={styles.recTitle}>{rec.title}</span>
                  <span className={styles.recStrategy}>{rec.strategy}</span>
                </div>
                <span className={styles.recNum}>#{i + 1}</span>
              </div>
              {rec.reason && (
                <p className={styles.recReason}>{rec.reason}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Proceed to Retest */}
      <div className={styles.footer}>
        <p className={styles.footerNote}>
          Apply one of these improvements and run a retest to measure the effect.
        </p>
        <button
          className={`btn btn-secondary ${styles.retestBtn}`}
          onClick={onProceedToRetest}
          disabled={recs.length === 0}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.95"/>
          </svg>
          Proceed to Retest →
        </button>
      </div>
    </div>
  )
}
