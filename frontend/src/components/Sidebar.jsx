/**
 * Sidebar navigation component.
 * Displays the Fortify brand and navigation items.
 * Only Architecture is active in Step 1.
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
    active: true,
    available: true,
  },
  {
    id: 'attack',
    label: 'Attack',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
      </svg>
    ),
    active: false,
    available: false,
  },
  {
    id: 'observe',
    label: 'Observe',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
    active: false,
    available: false,
  },
  {
    id: 'diagnose',
    label: 'Diagnose',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
        <line x1="11" y1="8" x2="11" y2="14" />
        <line x1="8" y1="11" x2="14" y2="11" />
      </svg>
    ),
    active: false,
    available: false,
  },
  {
    id: 'improve',
    label: 'Improve',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
        <polyline points="17 6 23 6 23 12" />
      </svg>
    ),
    active: false,
    available: false,
  },
  {
    id: 'retest',
    label: 'Re-test',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="1 4 1 10 7 10" />
        <path d="M3.51 15a9 9 0 1 0 .49-4.95" />
      </svg>
    ),
    active: false,
    available: false,
  },
]

export default function Sidebar({ activePage, onNavigate }) {
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
          const isDisabled = !item.available
          return (
            <button
              key={item.id}
              className={[
                styles.navItem,
                isActive ? styles.navItemActive : '',
                isDisabled ? styles.navItemDisabled : '',
              ].join(' ')}
              onClick={() => item.available && onNavigate && onNavigate(item.id)}
              disabled={isDisabled}
              title={isDisabled ? 'Coming in a later step' : item.label}
            >
              <span className={styles.navStep}>{index + 1}</span>
              <span className={styles.navIcon}>{item.icon}</span>
              <span className={styles.navText}>{item.label}</span>
              {isActive && <span className={styles.navActiveIndicator} />}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className={styles.footer}>
        <span className={styles.footerVersion}>v0.1 · MVP</span>
      </div>
    </aside>
  )
}
