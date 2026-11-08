import { afterEach, expect, it, vi } from 'vitest'
import { acceptInvitation, createInvitation } from './invitations-api'
import { setAccessToken } from '../../services/api'
afterEach(() => { vi.unstubAllGlobals(); setAccessToken(null) })
it('envía el código por POST autenticado y nunca en URL', async () => {
  setAccessToken('test-jwt')
  const fetchMock=vi.fn().mockResolvedValue(new Response(JSON.stringify({projectId:'shared',effectiveRole:'VIEWER'})))
  vi.stubGlobal('fetch',fetchMock)
  await acceptInvitation('private-invite')
  const [url,init]=fetchMock.mock.calls[0]!
  expect(url).toBe('http://localhost:8000/project-invitations/accept')
  expect(init.body).toBe(JSON.stringify({token:'private-invite'}))
  expect(init.headers.get('Authorization')).toBe('Bearer test-jwt')
})
it('envía vigencia/rol del código y presenta vencimiento sin revelar el token', async () => {
  const fetchMock=vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({id:'invite',token:'new-code'}),{status:201})).mockResolvedValueOnce(new Response('{}',{status:410}))
  vi.stubGlobal('fetch',fetchMock)
  await createInvitation('project','peer@example.com','EDITOR',48)
  expect(JSON.parse(fetchMock.mock.calls[0]![1].body)).toEqual({email:'peer@example.com',role:'EDITOR',expiresHours:48})
  await expect(acceptInvitation('secret')).rejects.toThrow('La invitación venció')
})
