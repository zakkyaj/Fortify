/**
 * experimentStore.js — React Context that carries shared experiment state
 * across all workflow pages (Architecture → Attack → Results).
 *
 * Consumed by App.jsx, ArchitecturePage, ExperimentPage and all sub-panels.
 */
import { createContext, useContext, useState } from 'react'

const ExperimentContext = createContext(null)

export function ExperimentProvider({ children }) {
  // ── Architecture (set in Step 1) ─────────────────────────────────────────
  const [architectureId, setArchitectureId] = useState(null)

  // ── Attack config (set in Step 2) ────────────────────────────────────────
  const [attackConfig, setAttackConfig] = useState({
    target: 'payment',
    type: 'latency',
    value: 5000,
  })
  const [trafficConfig, setTrafficConfig] = useState({
    rate: 10,
    duration_seconds: 10,
  })

  // ── Full experiment result (returned by POST /api/experiment/run) ─────────
  const [experimentResult, setExperimentResult] = useState(null)

  // ── Retest result (returned by POST /api/retest) ──────────────────────────
  const [retestResult, setRetestResult] = useState(null)

  // ── Comparison (returned by GET /api/comparisons/:id) ────────────────────
  const [comparisonResult, setComparisonResult] = useState(null)

  // ── Running / error state ─────────────────────────────────────────────────
  const [running, setRunning] = useState(false)
  const [retesting, setRetesting] = useState(false)
  const [runError, setRunError] = useState(null)
  const [retestError, setRetestError] = useState(null)

  // ── Helper: reset all results (e.g. before a new run) ─────────────────────
  function resetResults() {
    setExperimentResult(null)
    setRetestResult(null)
    setComparisonResult(null)
    setRunError(null)
    setRetestError(null)
  }

  return (
    <ExperimentContext.Provider value={{
      // Architecture
      architectureId, setArchitectureId,
      // Attack
      attackConfig, setAttackConfig,
      trafficConfig, setTrafficConfig,
      // Results
      experimentResult, setExperimentResult,
      retestResult,    setRetestResult,
      comparisonResult, setComparisonResult,
      // Status
      running, setRunning,
      retesting, setRetesting,
      runError, setRunError,
      retestError, setRetestError,
      // Helpers
      resetResults,
    }}>
      {children}
    </ExperimentContext.Provider>
  )
}

export function useExperiment() {
  const ctx = useContext(ExperimentContext)
  if (!ctx) throw new Error('useExperiment must be used inside ExperimentProvider')
  return ctx
}
