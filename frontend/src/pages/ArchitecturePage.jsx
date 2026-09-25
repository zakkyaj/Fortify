/**
 * ArchitecturePage — Step 1 of the Fortify workflow.
 *
 * Features:
 *  - Visualises the fixed Gateway → Order → Payment → Database architecture
 *  - Allows the user to set an architecture name and register it via
 *    POST /api/architecture
 *  - Shows per-service status badges
 *  - Displays the registered architecture_id after a successful save
 *  - Handles backend errors gracefully
 */
import { useState } from 'react'
import ArchitectureCanvas from '../components/ArchitectureCanvas'
import { registerArchitecture } from '../api/architecture'
import { useExperiment } from '../store/experimentStore'
import styles from './ArchitecturePage.module.css'

// ── Fixed architecture definition (matches infrastructure/docker-compose.yml) ──

const FIXED_SERVICES = [
  { id: 'gateway',  name: 'Gateway',          type: 'gateway'  },
  { id: 'order',    name: 'Order Service',     type: 'service'  },
  { id: 'payment',  name: 'Payment Service',   type: 'service'  },
  { id: 'database', name: 'SQLite Database',   type: 'database' },
]

const FIXED_CONNECTIONS = [
  { source: 'gateway',  target: 'order'    },
  { source: 'order',    target: 'payment'  },
  { source: 'payment',  target: 'database' },
]

// ── Status helpers ──────────────────────────────────────────────────────────

const STATUS_OPTIONS = ['healthy', 'degraded', 'failure', 'unknown']

const STATUS_META = {
  healthy:  { label: 'Healthy',          cls: 'badge-healthy'  },
  degraded: { label: 'Degraded',         cls: 'badge-degraded' },
  failure:  { label: 'Failure Injected', cls: 'badge-failure'  },
  unknown:  { label: 'Unknown',          cls: 'badge-unknown'  },
}

// ── Component ───────────────────────────────────────────────────────────────

export default function ArchitecturePage() {
  const { setArchitectureId } = useExperiment()

  // Form state
  const [archName, setArchName] = useState('Order Processing System')

  // Service statuses (visual only in Step 1 — no live polling yet)
  const [serviceStatuses, setServiceStatuses] = useState({
    gateway:  'healthy',
    order:    'healthy',
    payment:  'healthy',
    database: 'healthy',
  })

  // API interaction state
  const [saving, setSaving]           = useState(false)
  const [savedId, setSavedId]         = useState(null)
  const [error, setError]             = useState(null)
  const [successMsg, setSuccessMsg]   = useState(null)

  // ── Handlers ───────────────────────────────────────────────────────────────

  function handleStatusChange(serviceId, newStatus) {
    setServiceStatuses((prev) => ({ ...prev, [serviceId]: newStatus }))
  }

  async function handleRegister() {
    setError(null)
    setSuccessMsg(null)
    setSaving(true)

    const payload = {
      name: archName.trim() || 'Fortify Architecture',
      services: FIXED_SERVICES,
      connections: FIXED_CONNECTIONS,
    }

    try {
      const result = await registerArchitecture(payload)
      setSavedId(result.architecture_id)
      setArchitectureId(result.architecture_id)
      setSuccessMsg(`Architecture registered successfully.`)
    } catch (err) {
      const detail =
        err?.response?.data?.detail ??
        err?.response?.data?.error?.message ??
        err?.message ??
        'Unknown error'
      setError(`Failed to register architecture: ${detail}`)
    } finally {
      setSaving(false)
    }
  }

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <div className={styles.page}>
      {/* ── Page Header ── */}
      <header className={styles.pageHeader}>
        <div className={styles.pageHeaderLeft}>
          <span className={styles.stepBadge}>Step 1</span>
          <div>
            <h1 className={styles.pageTitle}>Architecture</h1>
            <p className={styles.pageSubtitle}>
              Define and visualise your distributed system before running experiments.
            </p>
          </div>
        </div>

        {savedId && (
          <div className={styles.archIdBadge}>
            <span className={styles.archIdLabel}>Architecture ID</span>
            <code className={styles.archIdValue}>{savedId}</code>
          </div>
        )}
      </header>

      {/* ── Main layout: canvas + sidebar panel ── */}
      <div className={styles.content}>

        {/* ── Canvas ── */}
        <div className={styles.canvasArea}>
          <div className={styles.canvasCard}>
            <div className={styles.canvasHeader}>
              <span className={styles.canvasTitle}>Service Graph</span>
              <span className={styles.canvasHint}>Scroll to zoom · Drag nodes to rearrange</span>
            </div>
            <div className={styles.canvasBody}>
              <ArchitectureCanvas serviceStatuses={serviceStatuses} />
            </div>
          </div>
        </div>

        {/* ── Right panel ── */}
        <aside className={styles.panel}>

          {/* Register form */}
          <section className={`${styles.panelSection} card`}>
            <h3 className={styles.sectionTitle}>Register Architecture</h3>
            <p className={styles.sectionDesc}>
              Save this architecture to the backend to enable experiments.
            </p>

            <label className={styles.fieldLabel} htmlFor="arch-name">
              Architecture name
            </label>
            <input
              id="arch-name"
              className={styles.input}
              type="text"
              value={archName}
              onChange={(e) => setArchName(e.target.value)}
              placeholder="e.g. Order Processing System"
              maxLength={80}
            />

            <button
              className={`btn btn-primary ${styles.registerBtn}`}
              onClick={handleRegister}
              disabled={saving}
            >
              {saving ? (
                <>
                  <span className={styles.spinner} />
                  Registering…
                </>
              ) : (
                <>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                    <polyline points="17 21 17 13 7 13 7 21" />
                    <polyline points="7 3 7 8 15 8" />
                  </svg>
                  Register Architecture
                </>
              )}
            </button>

            {/* Feedback */}
            {successMsg && (
              <div className={`${styles.feedback} ${styles.feedbackSuccess}`}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                {successMsg}
              </div>
            )}
            {error && (
              <div className={`${styles.feedback} ${styles.feedbackError}`}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                {error}
              </div>
            )}
          </section>

          {/* Services list */}
          <section className={`${styles.panelSection} card`}>
            <h3 className={styles.sectionTitle}>Services</h3>
            <p className={styles.sectionDesc}>
              Set display status for each service node on the canvas.
            </p>

            <div className={styles.serviceList}>
              {FIXED_SERVICES.map((svc) => {
                const currentStatus = serviceStatuses[svc.id] ?? 'healthy'
                const meta = STATUS_META[currentStatus]
                return (
                  <div key={svc.id} className={styles.serviceRow}>
                    <div className={styles.serviceInfo}>
                      <span className={`dot dot-${currentStatus} ${styles.serviceDot}`} />
                      <div className={styles.serviceNameGroup}>
                        <span className={styles.serviceName}>{svc.name}</span>
                        <span className={styles.serviceType}>{svc.type}</span>
                      </div>
                    </div>
                    <select
                      className={styles.statusSelect}
                      value={currentStatus}
                      onChange={(e) => handleStatusChange(svc.id, e.target.value)}
                      aria-label={`Status for ${svc.name}`}
                    >
                      {STATUS_OPTIONS.map((s) => (
                        <option key={s} value={s}>
                          {STATUS_META[s].label}
                        </option>
                      ))}
                    </select>
                  </div>
                )
              })}
            </div>
          </section>

          {/* Connections summary */}
          <section className={`${styles.panelSection} card`}>
            <h3 className={styles.sectionTitle}>Connections</h3>
            <div className={styles.connectionList}>
              {FIXED_CONNECTIONS.map((conn) => {
                const srcSvc = FIXED_SERVICES.find((s) => s.id === conn.source)
                const tgtSvc = FIXED_SERVICES.find((s) => s.id === conn.target)
                return (
                  <div key={`${conn.source}-${conn.target}`} className={styles.connectionRow}>
                    <span className={styles.connNode}>{srcSvc?.name ?? conn.source}</span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="5" y1="12" x2="19" y2="12" />
                      <polyline points="12 5 19 12 12 19" />
                    </svg>
                    <span className={styles.connNode}>{tgtSvc?.name ?? conn.target}</span>
                  </div>
                )
              })}
            </div>
          </section>

          {/* API endpoint reference */}
          <section className={`${styles.panelSection} card`}>
            <h3 className={styles.sectionTitle}>API</h3>
            <div className={styles.apiRef}>
              <div className={styles.apiRow}>
                <span className={styles.apiMethod}>POST</span>
                <code className={styles.apiPath}>/api/architecture</code>
              </div>
              <div className={styles.apiRow}>
                <span className={styles.apiMethod}>GET</span>
                <code className={styles.apiPath}>/api/architecture/:id</code>
              </div>
            </div>
            {savedId && (
              <div className={styles.apiRow} style={{ marginTop: '8px' }}>
                <span className={styles.apiKey}>arch_id</span>
                <code className={styles.apiPath}>{savedId}</code>
              </div>
            )}
          </section>

        </aside>
      </div>
    </div>
  )
}
