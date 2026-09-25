/**
 * ServiceNode — custom ReactFlow node for Fortify services.
 *
 * Props (from ReactFlow data object):
 *   label      {string}  — display name
 *   nodeType   {string}  — 'gateway' | 'service' | 'database'
 *   status     {string}  — 'healthy' | 'degraded' | 'failure' | 'unknown'
 *   description {string} — optional subtitle
 */
import { memo } from 'react'
import { Handle, Position } from 'reactflow'
import styles from './ServiceNode.module.css'

const TYPE_META = {
  gateway: {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <line x1="8" y1="21" x2="16" y2="21" />
        <line x1="12" y1="17" x2="12" y2="21" />
      </svg>
    ),
    label: 'Gateway',
  },
  service: {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="2" width="20" height="8" rx="2" />
        <rect x="2" y="14" width="20" height="8" rx="2" />
        <line x1="6" y1="6" x2="6.01" y2="6" />
        <line x1="6" y1="18" x2="6.01" y2="18" />
      </svg>
    ),
    label: 'Service',
  },
  database: {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3" />
        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
      </svg>
    ),
    label: 'Database',
  },
}

const STATUS_CLASSES = {
  healthy:  styles.statusHealthy,
  degraded: styles.statusDegraded,
  failure:  styles.statusFailure,
  unknown:  styles.statusUnknown,
}

const STATUS_LABELS = {
  healthy:  'Healthy',
  degraded: 'Degraded',
  failure:  'Failure Injected',
  unknown:  'Unknown',
}

function ServiceNode({ data }) {
  const { label, nodeType = 'service', status = 'healthy', description } = data
  const meta = TYPE_META[nodeType] ?? TYPE_META.service
  const statusClass = STATUS_CLASSES[status] ?? STATUS_CLASSES.unknown
  const statusLabel = STATUS_LABELS[status] ?? 'Unknown'

  return (
    <div className={`${styles.node} ${statusClass}`}>
      {/* Top handle — receives connections */}
      <Handle
        type="target"
        position={Position.Top}
        className={styles.handle}
      />

      {/* Node body */}
      <div className={styles.header}>
        <span className={styles.typeIcon}>{meta.icon}</span>
        <span className={styles.typeLabel}>{meta.label}</span>
      </div>

      <div className={styles.body}>
        <span className={styles.nodeName}>{label}</span>
        {description && (
          <span className={styles.nodeDesc}>{description}</span>
        )}
      </div>

      <div className={styles.footer}>
        <span className={`${styles.statusDot} ${styles[`dot_${status}`]}`} />
        <span className={styles.statusText}>{statusLabel}</span>
      </div>

      {/* Bottom handle — emits connections */}
      <Handle
        type="source"
        position={Position.Bottom}
        className={styles.handle}
      />
    </div>
  )
}

export default memo(ServiceNode)
