/**
 * ExperimentPage — Steps 2–8 of the Fortify workflow.
 *
 * Scrollable single page that sequentially reveals:
 *   Step 2  Configure Attack
 *   Step 3  Run Experiment
 *   Step 4  Metrics
 *   Step 5  Diagnosis
 *   Step 6  Recommendations
 *   Step 7  Retest
 *   Step 8  Before/After Comparison
 *
 * Each section beyond "Configure Attack" is revealed only when the
 * previous step's data is available — no stub data.
 */
import { useRef } from 'react'
import { useExperiment } from '../store/experimentStore'
import AttackForm from '../components/AttackForm'
import ExperimentRunner from '../components/ExperimentRunner'
import MetricsPanel from '../components/MetricsPanel'
import DiagnosisPanel from '../components/DiagnosisPanel'
import RecommendationsPanel from '../components/RecommendationsPanel'
import RetestPanel from '../components/RetestPanel'
import ComparisonPanel from '../components/ComparisonPanel'
import styles from './ExperimentPage.module.css'

export default function ExperimentPage() {
  const { architectureId, experimentResult, retestResult } = useExperiment()
  const runnerRef       = useRef(null)
  const resultsRef      = useRef(null)
  const retestRef       = useRef(null)
  const comparisonRef   = useRef(null)

  function scrollTo(ref) {
    setTimeout(() => ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 80)
  }

  function handleFormReady() {
    scrollTo(runnerRef)
  }

  function handleRunComplete() {
    scrollTo(resultsRef)
  }

  function handleProceedToRetest() {
    scrollTo(retestRef)
  }

  return (
    <div className={styles.page}>
      {/* ── Page Header ── */}
      <header className={styles.pageHeader}>
        <div className={styles.pageHeaderLeft}>
          <span className={styles.stepBadge}>Steps 2–8</span>
          <div>
            <h1 className={styles.pageTitle}>Attack & Experiment</h1>
            <p className={styles.pageSubtitle}>
              Configure an attack, run the resilience experiment, and analyse the results.
            </p>
          </div>
        </div>

        {architectureId && (
          <div className={styles.archIdBadge}>
            <span className={styles.archIdLabel}>Architecture</span>
            <code className={styles.archIdValue}>{architectureId}</code>
          </div>
        )}
      </header>

      <div className={styles.content}>
        {/* ── Step 2: Configure Attack ── */}
        <section className={styles.section}>
          <AttackForm onReady={handleFormReady} />
        </section>

        {/* ── Step 3: Run Experiment ── */}
        <section className={styles.section} ref={runnerRef}>
          <ExperimentRunner onComplete={handleRunComplete} />
        </section>

        {/* ── Steps 4–6: Results (visible after experiment completes) ── */}
        {experimentResult && (
          <section className={`${styles.section} ${styles.resultsSection} fade-in`} ref={resultsRef}>
            <div className={styles.resultsBanner}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--status-healthy)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <span>Experiment completed — <code className={styles.expId}>{experimentResult.experiment_id}</code></span>
            </div>

            {/* Step 4: Metrics */}
            <MetricsPanel />

            {/* Step 5: Diagnosis */}
            <DiagnosisPanel />

            {/* Step 6: Recommendations */}
            <RecommendationsPanel onProceedToRetest={handleProceedToRetest} />
          </section>
        )}

        {/* ── Step 7: Retest (always shown after experiment, scroll-targeted) ── */}
        {experimentResult && (
          <section className={`${styles.section} fade-in`} ref={retestRef}>
            <RetestPanel />
          </section>
        )}

        {/* ── Step 8: Comparison ── */}
        {retestResult && (
          <section className={`${styles.section} fade-in`} ref={comparisonRef}>
            <ComparisonPanel />
          </section>
        )}

        {/* Empty state when no architecture registered */}
        {!architectureId && (
          <div className={`${styles.emptyState} card`}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <p className={styles.emptyTitle}>No architecture registered</p>
            <p className={styles.emptyDesc}>
              Go to <strong>Architecture</strong> (Step 1), register your architecture, then come back here to configure an attack.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
