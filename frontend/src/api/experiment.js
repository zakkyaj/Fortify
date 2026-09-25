/**
 * Experiment API — wraps all experiment-related backend endpoints.
 *
 * POST /api/experiment/run
 * POST /api/retest
 * GET  /api/comparisons/{attack_id}
 * GET  /api/metrics/{service_id}
 * POST /api/diagnosis
 * POST /api/recommendations
 */
import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

const client = axios.create({
  baseURL: BASE,
  headers: { 'Content-Type': 'application/json' },
  // Experiment runs generate real traffic and collect metrics — allow up to 3 min
  timeout: 180_000,
})

/**
 * Run a full experiment.
 *
 * @param {{
 *   architecture_id: string,
 *   attack: { target: string, type: string, value: number },
 *   traffic: { rate: number, duration_seconds: number }
 * }} payload
 */
export async function runExperiment(payload) {
  const response = await client.post('/experiment/run', payload)
  return response.data
}

/**
 * Re-run an experiment with an optional resilience strategy.
 *
 * @param {{
 *   architecture_id: string,
 *   previous_attack_id: string,
 *   recommendation_id?: string,
 *   resilience?: { strategy: string, timeout_ms?: number, circuit_breaker_threshold_ms?: number },
 *   traffic: { rate: number, duration_seconds: number }
 * }} payload
 */
export async function runRetest(payload) {
  const response = await client.post('/retest', payload)
  return response.data
}

/**
 * Fetch the before/after comparison for the given original attack ID.
 *
 * @param {string} attackId
 */
export async function getComparison(attackId) {
  const response = await client.get(`/comparisons/${attackId}`)
  return response.data
}

/**
 * Fetch live metrics for a specific service.
 *
 * @param {string} serviceId — 'gateway' | 'order' | 'payment'
 */
export async function getServiceMetrics(serviceId) {
  const response = await client.get(`/metrics/${serviceId}`)
  return response.data
}
