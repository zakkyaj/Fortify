/**
 * Architecture API — wraps POST /api/architecture and GET /api/architecture/:id
 * Uses VITE_API_URL from the environment (falls back to localhost:8000/api).
 */
import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

const client = axios.create({
  baseURL: BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
})

/**
 * Register an architecture with the backend.
 *
 * @param {object} architecture - { name, services, connections }
 * @returns {Promise<{ architecture_id: string, status: string }>}
 */
export async function registerArchitecture(architecture) {
  const response = await client.post('/architecture', architecture)
  return response.data
}

/**
 * Fetch a previously registered architecture by ID.
 *
 * @param {string} architectureId
 * @returns {Promise<{ architecture_id, name, services, connections }>}
 */
export async function getArchitecture(architectureId) {
  const response = await client.get(`/architecture/${architectureId}`)
  return response.data
}

/**
 * Check backend health.
 * @returns {Promise<{ status: string, service: string }>}
 */
export async function healthCheck() {
  const response = await client.get('/health')
  return response.data
}
