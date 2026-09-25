/**
 * ExperimentRunner — Step 3: Run Experiment
 * Calls POST /api/experiment/run, shows animated stage progress,
 * stores the result in global context.
 */
import { useState } from 'react'
import { useExperiment } from '../store/experimentStore'
import { runExperiment } from '../api/experiment'
import styles from './ExperimentRunner.module.css'

const STAGES = [
  { key: 'baseline',      label: 'Baseline collection',   desc: 'Measuring normal behaviour' },
  { key: 'inject',        label: 'Failure injection',      desc: 'Applying Toxiproxy toxic' },
  { key: 'traffic',       label: 'Traffic generation',     desc: 'Sending requests under attack' },
  { key: 'metrics',       label: 'Metrics collection',     desc: 'Reading Prometheus data' },
  { key: 'diagnosis',     label: 'Diagnosis',              desc: 'Analysing failure propagation' },
  { key: 'recommendations', label: 'Recommendations',      desc: 'Generating resilience advice' },
]

export default function ExperimentRunner({ onComplete }) {
  const {
    architectureId, attackConfig, trafficConfig,
    running, setRunning,
    runError, setRunError,
    setExperimentResult,
    resetResults,
  } = useExperiment()

  const [activeStageIdx, setActiveStageIdx] = useState(-1)
  const [completedStages, setCompletedStages] = useState(new Set())

  async function handleRun() {
    if (running) return
    resetResults()
    setRunning(true)
    setRunError(null)
    setActiveStageIdx(-1)
    setCompletedStages(new Set())

    // Animate stages while the single long-running request is in-flight.
    // Duration is estimated from traffic config: baseline(~5s) + inject + traffic + metrics + diagnose
    const totalMs = (trafficConfig.duration_seconds + 20) * 1000
    const perStage = Math.floor(totalMs / STAGES.length)
    let stageTimer
    let idx = 0

    function advanceStage() {
      setActiveStageIdx(idx)
      setCompletedStages(prev => {
        const next = new Set(prev)
        if (idx > 0) next.add(STAGES[idx - 1].key)
        return next
      })
      idx++
      if (idx < STAGES.length) {
        stageTimer = setTimeout(advanceStage, perStage)
      }
    }
    advanceStage()

    try {
      const result = await runExperiment({
        architecture_id: architectureId,
        attack: {
          target: attackConfig.target,
          type: attackConfig.type,
          value: Number(attackConfig.value),
        },
        traffic: {
          rate: Number(trafficConfig.rate),
          duration_seconds: Number(trafficConfig.duration_seconds),
        },
      })
      clearTimeout(stageTimer)
      setCompletedStages(new Set(STAGES.map(s => s.key)))
      setActiveStageIdx(STAGES.length)
      setExperimentResult(result)
      onComplete?.()
    } catch (err) {
      clearTimeout(stageTimer)
      setActiveStageIdx(-1)
      const detail =
        err?.response?.data?.detail ??
        err?.response?.data?.error?.message ??
        err?.message ??
        'Unknown error'
      setRunError(`Experiment failed: ${detail}`)
    } finally {
      setRunning(false)
    }
  }

  const allDone = completedStages.size === STAGES.length && !running

  return (
    <div className={`${styles.wrapper} card`}>
      <div className={styles.head}>
        <div className={styles.headLeft}>
          <span className={styles.stepNum}>3</span>
          <h3 className={styles.title}>Run Experiment</h3>
        </div>
        {running && (
          <span className={styles.runningBadge}>
            <span className={`${styles.runningDot} pulse`} />
            Running
          </span>
        )}
        {allDone && (
          <span className={styles.doneBadge}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Complete
          </span>
        )}
      </div>

      {/* Stage progress */}
      <div className={styles.stages}>
        {STAGES.map((stage, i) => {
          const done = completedStages.has(stage.key)
          const active = i === activeStageIdx && running
          return (
            <div
              key={stage.key}
              className={[
                styles.stage,
                done    ? styles.stageDone   : '',
                active  ? styles.stageActive : '',
              ].join(' ')}
            >
              <div className={styles.stageIcon}>
                {done ? (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                ) : active ? (
                  <span className={styles.spinner} />
                ) : (
                  <span className={styles.stageCircle}>{i + 1}</span>
                )}
              </div>
              <div className={styles.stageText}>
                <span className={styles.stageLabel}>{stage.label}</span>
                {active && <span className={styles.stageDesc}>{stage.desc}</span>}
              </div>
            </div>
          )
        })}
      </div>

      {/* Error */}
      {runError && (
        <div className={styles.error}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          {runError}
        </div>
      )}

      <button
        className={`btn btn-primary ${styles.btn}`}
        onClick={handleRun}
        disabled={running || !architectureId}
      >
        {running ? (
          <>
            <span className={styles.spinner} />
            Running…
          </>
        ) : allDone ? (
          <>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.95"/>
            </svg>
            Run Again
          </>
        ) : (
          <>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            Run Resilience Test
          </>
        )}
      </button>
    </div>
  )
}
