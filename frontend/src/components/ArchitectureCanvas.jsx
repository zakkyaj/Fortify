/**
 * ArchitectureCanvas — ReactFlow canvas that visualises the Fortify
 * service architecture (Gateway → Order → Payment).
 *
 * Accepts:
 *   serviceStatuses {object} — map of serviceId → 'healthy'|'degraded'|'failure'|'unknown'
 */
import { useCallback } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow'
import 'reactflow/dist/style.css'

import ServiceNode from './ServiceNode'
import styles from './ArchitectureCanvas.module.css'

// Register custom node types
const nodeTypes = { serviceNode: ServiceNode }

// ── Default architecture (Gateway → Order → Payment) ──────────────────────

function buildNodes(serviceStatuses = {}) {
  return [
    {
      id: 'gateway',
      type: 'serviceNode',
      position: { x: 160, y: 30 },
      data: {
        label: 'Gateway',
        nodeType: 'gateway',
        status: serviceStatuses.gateway ?? 'healthy',
        description: 'Port 8080 · Entry point',
      },
      draggable: true,
    },
    {
      id: 'order',
      type: 'serviceNode',
      position: { x: 160, y: 175 },
      data: {
        label: 'Order Service',
        nodeType: 'service',
        status: serviceStatuses.order ?? 'healthy',
        description: 'Port 5001 · Processes orders',
      },
      draggable: true,
    },
    {
      id: 'payment',
      type: 'serviceNode',
      position: { x: 160, y: 320 },
      data: {
        label: 'Payment Service',
        nodeType: 'service',
        status: serviceStatuses.payment ?? 'healthy',
        description: 'Port 5002 · Via Toxiproxy',
      },
      draggable: true,
    },
    {
      id: 'database',
      type: 'serviceNode',
      position: { x: 160, y: 465 },
      data: {
        label: 'SQLite Database',
        nodeType: 'database',
        status: serviceStatuses.database ?? 'healthy',
        description: '/data/payments.db',
      },
      draggable: true,
    },
  ]
}

const DEFAULT_EDGES = [
  {
    id: 'e-gateway-order',
    source: 'gateway',
    target: 'order',
    type: 'smoothstep',
    animated: false,
    style: { stroke: '#252a40', strokeWidth: 2 },
    labelStyle: { fill: '#8b95b8', fontSize: 10 },
    label: 'HTTP',
  },
  {
    id: 'e-order-payment',
    source: 'order',
    target: 'payment',
    type: 'smoothstep',
    animated: false,
    style: { stroke: '#252a40', strokeWidth: 2 },
    labelStyle: { fill: '#8b95b8', fontSize: 10 },
    label: 'via Toxiproxy',
  },
  {
    id: 'e-payment-db',
    source: 'payment',
    target: 'database',
    type: 'smoothstep',
    animated: false,
    style: { stroke: '#252a40', strokeWidth: 2 },
    labelStyle: { fill: '#8b95b8', fontSize: 10 },
    label: 'SQLite',
  },
]

// ── Component ──────────────────────────────────────────────────────────────

export default function ArchitectureCanvas({ serviceStatuses = {} }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(buildNodes(serviceStatuses))
  const [edges, , onEdgesChange] = useEdgesState(DEFAULT_EDGES)

  // Rebuild nodes when serviceStatuses changes
  const refreshNodes = useCallback(() => {
    setNodes(buildNodes(serviceStatuses))
  }, [serviceStatuses, setNodes])

  // Update nodes when statuses change externally
  const updatedNodes = nodes.map((node) => ({
    ...node,
    data: {
      ...node.data,
      status: serviceStatuses[node.id] ?? node.data.status,
    },
  }))

  return (
    <div className={styles.canvasWrapper}>
      <ReactFlow
        nodes={updatedNodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        minZoom={0.4}
        maxZoom={2}
        attributionPosition="bottom-right"
        proOptions={{ hideAttribution: false }}
      >
        <Background
          color="#1c2035"
          gap={20}
          size={1}
          variant="dots"
        />
        <Controls
          className={styles.controls}
          showInteractive={false}
        />
        <MiniMap
          className={styles.minimap}
          nodeColor={(node) => {
            const s = serviceStatuses[node.id] ?? 'healthy'
            const MAP = {
              healthy:  '#10d98e',
              degraded: '#f59e0b',
              failure:  '#ef4444',
              unknown:  '#6b7280',
            }
            return MAP[s] ?? MAP.healthy
          }}
          maskColor="rgba(11,13,20,0.7)"
        />
      </ReactFlow>
    </div>
  )
}
