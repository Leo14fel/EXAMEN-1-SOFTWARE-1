import { afterEach, expect, it, vi } from 'vitest'
import { authenticatedFetch } from '../../services/api'
import { AiApiError, evaluateAi, getAiResult, getAiStatus } from './ai-api'

vi.mock('../../services/api', () => ({ authenticatedFetch: vi.fn() }))
afterEach(() => vi.clearAllMocks())

it('consulta disponibilidad y resultado; solo POST evalúa una solicitud con revisión e ID', async () => {
  vi.mocked(authenticatedFetch).mockImplementation(async () => new Response('{}'))
  await getAiStatus('project'); await getAiResult('project', 'request')
  const body = { id: 'request', baseRevision: 3, text: 'Crea Producto' }
  await evaluateAi('project', body)
  expect(authenticatedFetch).toHaveBeenNthCalledWith(1, '/projects/project/ai/status', undefined)
  expect(authenticatedFetch).toHaveBeenNthCalledWith(2, '/projects/project/ai/requests/request', undefined)
  expect(authenticatedFetch).toHaveBeenNthCalledWith(3, '/projects/project/ai/requests', expect.objectContaining({ method: 'POST', body: JSON.stringify(body) }))
})

it('muestra un error controlado sin exponer el cuerpo del servidor', async () => {
  vi.mocked(authenticatedFetch).mockResolvedValue(new Response(JSON.stringify({ detail: { code: 'AI_NOT_CONFIGURED', message: 'PRIVATE_INTERNAL' } }), { status: 503 }))
  await expect(getAiStatus('project')).rejects.toBeInstanceOf(AiApiError)
  vi.mocked(authenticatedFetch).mockResolvedValue(new Response('PRIVATE_INTERNAL', { status: 502 }))
  await expect(getAiStatus('project')).rejects.not.toThrow('PRIVATE_INTERNAL')
})
