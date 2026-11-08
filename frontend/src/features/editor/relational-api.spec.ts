import { afterEach, expect, it, vi } from 'vitest'
import { getRelationalPreview } from './relational-api'
import { setAccessToken } from '../../services/api'
afterEach(()=>{ vi.unstubAllGlobals();setAccessToken(null) })
it('consulta el esquema por GET autenticado sin enviar mutaciones',async()=>{
  setAccessToken('test-token')
  const result={projectId:'p',sourceRevision:4,model:null,diagnostics:[]}
  const fetchMock=vi.fn().mockResolvedValue(new Response(JSON.stringify(result)))
  vi.stubGlobal('fetch',fetchMock)
  await expect(getRelationalPreview('p')).resolves.toEqual(result)
  const [url,init]=fetchMock.mock.calls[0]!
  expect(url).toBe('http://localhost:8000/projects/p/relational-model')
  expect(init.body).toBeUndefined();expect(init.headers.get('Authorization')).toBe('Bearer test-token')
})
it('no devuelve un esquema ficticio si falla el backend',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response('{}',{status:503})))
  await expect(getRelationalPreview('p')).rejects.toThrow('No se pudo consultar')
})
