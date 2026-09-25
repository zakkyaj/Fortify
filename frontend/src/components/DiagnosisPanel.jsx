/**
 * DiagnosisPanel — Step 5: AI Diagnosis
 * Displays backend diagnosis data: problem, severity, evidence, root cause.
 * Source of truth is experimentResult.diagnosis — nothing is invented.
 */
import { useExperiment } from '../store/experimentStore'
import styles from './DiagnosisPanel.module.css'

const SEVERITY_META = {
  high:    { cls: styles.severityHigh,    label: 'High',    icon: '⬆' },
  medium:  { cls: styles.severityMedium,  label: 'Medium',  icon: '→' },
  low:     { cls: styles.severityLow,     label: 'Low',     icon: '⬇' },
  unknown: { cls: styles.severityUnknown, label: 'Unknown', icon: '?' },
}

export default function DiagnosisPanel() {
  const { experimentResult } = useExperiment()
  if (!experimentResult) return null

  const diag = experimentResult.diagnosis
  if (!diag) {
    return (
      <div className={`${styles.wrapper} card`}>
        <div className={styles.head}>
          <span className={styles.stepNum}>5</span>
          <h3 className={styles.title}>Diagnosis</h3>
        </div>
        <div className={styles.empty}>No diagnosis data returned by the backend.</div>
      </div>
    )
  }

  const severity = diag.severity ?? 'unknown'
  const meta = SEVERITY_META[severity] ?? SEVERITY_META.unknown
  const evidence = diag.evidence ?? {}
  const affectedServices = diag.affected_services ?? []

  return (
    <div className={`${styles.wrapper} card`}>
      <div className={styles.head}>
        <span className={styles.stepNum}>5</span>
        <h3 className={styles.title}>AI Diagnosis</h3>
        <span className={`${styles.severityBadge} ${meta.cls}`}>
          {meta.icon} {meta.label} Severity
        </span>
      </div>

      {/* Problem */}
      <div className={styles.section}>
        <span className={styles.sectionLabel}>Problem</span>
        <p className={styles.problemText}>{diag.problem ?? '—'}</p>
      </div>

      {/* Root cause */}
      {diag.root_cause && (
        <div className={styles.section}>
          <span className={styles.sectionLabel}>Root Cause</span>
          <p className={styles.rootCauseText}>{diag.root_cause}</p>
        </div>
      )}

      {/* Affected services */}
      {affectedServices.length > 0 && (
        <div className={styles.section}>
          <span className={styles.sectionLabel}>Affected Services</span>
          <div className={styles.serviceChain}>
            {affectedServices.map((svc, i) => (
              <span key={svc} className={styles.serviceChainItem}>
                <span className={styles.svcBadge}>{svc}</span>
                {i < affectedServices.length - 1 && (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
                  </svg>
                )}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Evidence */}
      {Object.keys(evidence).length > 0 && (
        <div className={styles.section}>
          <span className={styles.sectionLabel}>Evidence</span>
          <div className={styles.evidenceGrid}>
            {Object.entries(evidence).map(([key, val]) => (
              <div key={key} className={styles.evidenceItem}>
                <span className={styles.evidenceKey}>{key.replace(/_/g, ' ')}</span>
                <span className={styles.evidenceVal}>{String(val)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Backend recommendation text */}
      {diag.recommendation && (
        <div className={styles.recBox}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          <p className={styles.recText}>{diag.recommendation}</p>
        </div>
      )}
    </div>
  )
}
