import { mount } from '@vue/test-utils'
import { beforeEach, afterEach, expect, it, vi } from 'vitest'
import RelationalPreviewPanel from './RelationalPreview.vue'
import { getRelationalPreview, type RelationalPreview } from './relational-api'
vi.mock('./relational-api',()=>({ getRelationalPreview:vi.fn() }))
const report:RelationalPreview={projectId:'project',sourceRevision:3,diagnostics:[],model:{
  version:1,dialect:'postgresql',inheritanceStrategy:'joined',quotedIdentifiers:true,relations:[],tables:[{
    name:'clientes',sourceClassId:'class',sourceRelationshipId:null,primaryKey:['id'],foreignKeys:[],uniqueConstraints:[['correo']],indexes:[],columns:[
      {name:'id',sqlType:'uuid',nullable:false,generated:'uuid',sourceAttributeId:null,enumName:null,allowedValues:null},
      {name:'correo',sqlType:'text',nullable:true,generated:null,sourceAttributeId:'attribute',enumName:null,allowedValues:null},
    ],
  }],
}}
beforeEach(()=>{ vi.clearAllMocks();vi.mocked(getRelationalPreview).mockResolvedValue(structuredClone(report)) })
afterEach(()=>vi.unstubAllGlobals())

it('muestra tablas, columnas, PK, nulabilidad y unicidad desde la proyección recibida',async()=>{
  const wrapper=mount(RelationalPreviewPanel,{props:{projectId:'project',revision:3}})
  await vi.waitFor(()=>expect(wrapper.text()).toContain('clientes'))
  expect(wrapper.text()).toContain('PK');expect(wrapper.text()).toContain('UUID generado')
  expect(wrapper.text()).toContain('Única: correo');expect(wrapper.findAll('tbody tr')).toHaveLength(2)
  expect(getRelationalPreview).toHaveBeenCalledWith('project');wrapper.unmount()
})

it('detecta una revisión atrasada y deja actualizar sin cambiar el diagrama',async()=>{
  const wrapper=mount(RelationalPreviewPanel,{props:{projectId:'project',revision:3}})
  await vi.waitFor(()=>expect(wrapper.text()).toContain('clientes'))
  await wrapper.setProps({revision:4})
  expect(wrapper.text()).toContain('El diagrama cambió')
  vi.mocked(getRelationalPreview).mockResolvedValue({...report,sourceRevision:4})
  await wrapper.findAll('button').find(b=>b.text().includes('Actualizar vista'))!.trigger('click')
  await vi.waitFor(()=>expect(wrapper.text()).not.toContain('El diagrama cambió'))
  expect(wrapper.text()).toContain('Revisión 4');wrapper.unmount()
})

it('diagnostica un modelo inválido sin mostrar tablas parciales ni HTML ejecutable',async()=>{
  vi.mocked(getRelationalPreview).mockResolvedValue({...report,model:null,diagnostics:[{
    severity:'error',code:'TYPE_UNSUPPORTED',sourceId:'attribute',message:'Tipo inválido <script>alert(1)</script>',
  }]})
  const wrapper=mount(RelationalPreviewPanel,{props:{projectId:'project',revision:3}})
  await vi.waitFor(()=>expect(wrapper.text()).toContain('Tipo inválido'))
  expect(wrapper.find('script').exists()).toBe(false);expect(wrapper.find('table').exists()).toBe(false)
  wrapper.unmount()
})

it('avisa límites de validación de cardinalidad y reporta errores de conexión',async()=>{
  vi.mocked(getRelationalPreview).mockResolvedValue({...report,diagnostics:[{
    severity:'warning',code:'RELATION_RUNTIME_VALIDATION',sourceId:'rel',message:'Requiere validaciones entre objetos',
  }]})
  const wrapper=mount(RelationalPreviewPanel,{props:{projectId:'project',revision:3}})
  await vi.waitFor(()=>expect(wrapper.text()).toContain('Requiere validaciones'))
  vi.mocked(getRelationalPreview).mockRejectedValue(new Error('Sin conexión'))
  await wrapper.findAll('button').find(b=>b.text().includes('Actualizar vista'))!.trigger('click')
  await vi.waitFor(()=>expect(wrapper.text()).toContain('Sin conexión'));wrapper.unmount()
})
