/**
 * Sidebar navigation component.
 * All 7 workflow steps are navigable.
 * Accepts `unlockedSteps` set to disable steps that require prior data.
 */
import styles from './Sidebar.module.css'

const NAV_ITEMS = [
  {
    id: 'architecture',
    label: 'Architecture',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="8" height="6" rx="1.5" />
        <rect x="14" y="3" width="8" height="6" rx="1.5" />
        <rect x="7" y="15" width="10" height="6" rx="1.5" />
        <line x1="6" y1="9" x2="6" y2="12" />
        <line x1="18" y1="9" x2="18" y2="12" />
        <line x1="6" y1="12" x2="18" y2="12" />
        <line x1="12" y1="12" x2="12" y2="15" />
      </svg>
    ),
  },
  {
    id: 'experiment',
    label: 'Attack & Run',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
      </svg>
    ),
  },
]

export default function Sidebar({ activePage, onNavigate, unlockedSteps }) {
  const unlocked = unlockedSteps ?? new Set(['architecture'])
  return (
    <aside className={styles.sidebar}>
      {/* Brand */}
      <div className={styles.brand}>
        <div className={styles.brandIcon}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z"
              fill="var(--accent)"
              opacity="0.9"
            />
            <path
              d="M9 12l2 2 4-4"
              stroke="#000"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <div>
          <span className={styles.brandName}>FORTIFY</span>
          <span className={styles.brandSub}>Resilience Platform</span>
        </div>
      </div>

      <div className={styles.divider} />

      {/* Navigation */}
      <nav className={styles.nav}>
        <span className={styles.navLabel}>Workflow</span>
        {NAV_ITEMS.map((item, index) => {
          const isActive = activePage === item.id
          const isDisabled = !unlocked.has(item.id)
          return (
            <button
              key={item.id}
              className={[
                styles.navItem,
                isActive ? styles.navItemActive : '',
                isDisabled ? styles.navItemDisabled : '',
              ].join(' ')}
              onClick={() => !isDisabled && onNavigate && onNavigate(item.id)}
              disabled={isDisabled}
              title={isDisabled ? 'Register an architecture first' : item.label}
            >
              <span className={styles.navStep}>{index + 1}</span>
              <span className={styles.navIcon}>{item.icon}</span>
              <span className={styles.navText}>{item.label}</span>
              {isActive && <span className={styles.navActiveIndicator} />}
            </button>
          )
        })}
      </nav>

      {/* Workflow stage legend */}
      <div className={styles.stageLegend}>
        <span className={styles.navLabel}>Stages</span>
        {[
          'Configure Attack',
          'Run Experiment',
          'Metrics',
          'Diagnosis',
          'Recommendations',
          'Retest',
          'Comparison',
        ].map((s, i) => (
          <div key={s} className={styles.stageItem}>
            <span className={styles.stageNum}>{i + 1}</span>
            <span className={styles.stageLabel}>{s}</span>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className={styles.footer}>
        <span className={styles.footerVersion}>v0.1 · MVP</span>
      </div>
    </aside>
  )
}
