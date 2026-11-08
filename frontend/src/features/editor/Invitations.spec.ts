import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, expect, it, vi } from 'vitest'
import InvitationManager from './InvitationManager.vue'
import InvitationRedeem from './InvitationRedeem.vue'
import * as api from './invitations-api'
import { useEditorStore } from './editor-store'
vi.mock('./invitations-api', () => ({ createInvitation:vi.fn(),listInvitations:vi.fn(),cancelInvitation:vi.fn(),acceptInvitation:vi.fn() }))
const invitation = {id:'invite',email:'peer@example.com',role:'VIEWER' as const,createdAt:'2026-11-07T00:00:00Z',expiresAt:'2026-11-08T00:00:00Z'}
beforeEach(() => { setActivePinia(createPinia()); vi.clearAllMocks(); vi.mocked(api.listInvitations).mockResolvedValue([]) })

it('owner crea un código dirigido y lo muestra solo a partir de la respuesta de creación', async () => {
  vi.mocked(api.createInvitation).mockResolvedValue({...invitation,token:'project.invite.secret'})
  const wrapper=mount(InvitationManager,{props:{projectId:'project'}})
  await wrapper.find('input[type="email"]').setValue('peer@example.com')
  await wrapper.find('form').trigger('submit')
  await vi.waitFor(() => expect(wrapper.find('textarea').exists()).toBe(true))
  expect(api.createInvitation).toHaveBeenCalledWith('project','peer@example.com','VIEWER',24)
  expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toBe('project.invite.secret')
  expect(wrapper.text()).toContain('No se envían correos automáticamente')
  wrapper.unmount()
})

it('lista y cancela invitaciones sin recuperar tokens secretos', async () => {
  vi.mocked(api.listInvitations).mockResolvedValue([invitation])
  vi.mocked(api.cancelInvitation).mockResolvedValue(undefined)
  const wrapper=mount(InvitationManager,{props:{projectId:'project'}})
  await vi.waitFor(() => expect(wrapper.text()).toContain('peer@example.com'))
  expect(wrapper.find('textarea').exists()).toBe(false)
  await wrapper.findAll('button').find(button => button.text().includes('Cancelar invitación'))!.trigger('click')
  await vi.waitFor(() => expect(wrapper.text()).toContain('Sin invitaciones pendientes'))
  expect(api.cancelInvitation).toHaveBeenCalledWith('project','invite')
  wrapper.unmount()
})

it('canjea el código y abre el proyecto con los permisos leídos del backend', async () => {
  vi.mocked(api.acceptInvitation).mockResolvedValue({projectId:'shared',effectiveRole:'VIEWER'})
  const store=useEditorStore()
  const load=vi.spyOn(store,'loadProjects').mockResolvedValue(undefined)
  const open=vi.spyOn(store,'openProject').mockResolvedValue(undefined)
  const wrapper=mount(InvitationRedeem)
  await wrapper.find('textarea').setValue('  valid-token  ')
  await wrapper.find('form').trigger('submit')
  await vi.waitFor(() => expect(wrapper.emitted('accepted')).toHaveLength(1))
  expect(api.acceptInvitation).toHaveBeenCalledWith('valid-token')
  expect(load).toHaveBeenCalledOnce(); expect(open).toHaveBeenCalledWith('shared')
  wrapper.unmount()
})

it('un token vencido conserva el código y no abre un proyecto ficticio', async () => {
  vi.mocked(api.acceptInvitation).mockRejectedValue(new Error('La invitación venció'))
  const store=useEditorStore(); const open=vi.spyOn(store,'openProject')
  const wrapper=mount(InvitationRedeem)
  await wrapper.find('textarea').setValue('expired-token')
  await wrapper.find('form').trigger('submit')
  await vi.waitFor(() => expect(wrapper.text()).toContain('La invitación venció'))
  expect(open).not.toHaveBeenCalled()
  expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toBe('expired-token')
  wrapper.unmount()
})

it('si el canje fue aceptado pero el listado falla, informa acceso concedido sin volver a canjear', async () => {
  vi.mocked(api.acceptInvitation).mockResolvedValue({projectId:'shared',effectiveRole:'EDITOR'})
  const store=useEditorStore(); vi.spyOn(store,'loadProjects').mockRejectedValue(new Error('offline'))
  const wrapper=mount(InvitationRedeem)
  await wrapper.find('textarea').setValue('valid-token')
  await wrapper.find('form').trigger('submit')
  await vi.waitFor(() => expect(wrapper.text()).toContain('La invitación se aceptó'))
  expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toBe('')
  expect(api.acceptInvitation).toHaveBeenCalledOnce()
  wrapper.unmount()
})
