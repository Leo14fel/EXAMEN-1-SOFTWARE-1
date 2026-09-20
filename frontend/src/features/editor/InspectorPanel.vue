<script setup lang="ts">
import { computed, ref, toRaw, watch } from 'vue'
import {
  createAttribute,
  createOperation,
  createParameter,
  parseMultiplicity,
  visibilityOptions,
} from './editor-elements'
import type {
  ProjectDocument,
  UmlClass,
  UmlCommand,
  UmlRelationship,
  UmlVisibility,
} from './types'

const props = defineProps<{
  document: ProjectDocument
  selectedElementId: string | null
  busy: boolean
}>()

const emit = defineEmits<{
  execute: [command: UmlCommand]
  clearSelection: []
}>()

interface RelationshipForm {
  id: string
  kind: UmlRelationship['kind']
  sourceId: string
  targetId: string
  sourceLower: string
  sourceUpper: string
  targetLower: string
  targetUpper: string
}

const classDraft = ref<UmlClass | null>(null)
const relationshipForm = ref<RelationshipForm | null>(null)
const classDraftBaseline = ref<string | null>(null)
const relationshipDraftBaseline = ref<string | null>(null)

const classes = computed(() =>
  props.document.umlModel.elements.filter(
    (element): element is UmlClass => element.kind === 'class',
  ),
)

const selectedElement = computed(() =>
  props.document.umlModel.elements.find((element) => element.id === props.selectedElementId),
)

const classHasRelationships = computed(() => {
  if (!classDraft.value) return false
  return props.document.umlModel.elements.some(
    (element) =>
      element.kind !== 'class' &&
      (element.sourceId === classDraft.value?.id || element.targetId === classDraft.value?.id),
  )
})

const validClass = computed(() => {
  const draft = classDraft.value
  if (!draft || !draft.name.trim()) return false

  if (draft.attributes.some((item) => !item.name.trim() || !item.type.trim())) return false
  if (draft.operations.some((item) => !item.name.trim())) return false
  if (
    draft.operations.some((operation) =>
      operation.parameters.some((parameter) => !parameter.name.trim() || !parameter.type.trim()),
    )
  ) {
    return false
  }
  return true
})

const relationshipSourceMultiplicity = computed(() => {
  const form = relationshipForm.value
  if (!form || form.kind === 'generalization') return null
  return parseMultiplicity(form.sourceLower, form.sourceUpper)
})

const relationshipTargetMultiplicity = computed(() => {
  const form = relationshipForm.value
  if (!form || form.kind === 'generalization') return null
  return parseMultiplicity(form.targetLower, form.targetUpper)
})

const validRelationship = computed(() => {
  const form = relationshipForm.value
  if (!form || !form.sourceId || !form.targetId) return false
  if (form.kind === 'generalization') return true
  return relationshipSourceMultiplicity.value !== null && relationshipTargetMultiplicity.value !== null
})

function visibilityLabel(value: UmlVisibility): string {
  return visibilityOptions.find((item) => item.value === value)?.title ?? value
}

function serializeDraft(value: unknown): string {
  return JSON.stringify(value)
}

function syncDraft(): void {
  const element = selectedElement.value
  classDraft.value = null
  relationshipForm.value = null
  classDraftBaseline.value = null
  relationshipDraftBaseline.value = null

  if (!element) return

  if (element.kind === 'class') {
    const draft = structuredClone(toRaw(element))
    classDraft.value = draft
    classDraftBaseline.value = serializeDraft(draft)
    return
  }

  const form: RelationshipForm = {
    id: element.id,
    kind: element.kind,
    sourceId: element.sourceId,
    targetId: element.targetId,
    sourceLower: element.kind === 'generalization' ? '1' : String(element.sourceMultiplicity.lower),
    sourceUpper:
      element.kind === 'generalization' ? '1' : String(element.sourceMultiplicity.upper),
    targetLower: element.kind === 'generalization' ? '1' : String(element.targetMultiplicity.lower),
    targetUpper:
      element.kind === 'generalization' ? '1' : String(element.targetMultiplicity.upper),
  }

  relationshipForm.value = form
  relationshipDraftBaseline.value = serializeDraft(form)
}



function addAttribute(): void {
  classDraft.value?.attributes.push(createAttribute())
}

function addOperation(): void {
  classDraft.value?.operations.push(createOperation())
}

function addParameter(operationIndex: number): void {
  classDraft.value?.operations[operationIndex]?.parameters.push(createParameter())
}

function removeAttribute(index: number): void {
  classDraft.value?.attributes.splice(index, 1)
}

function removeOperation(index: number): void {
  classDraft.value?.operations.splice(index, 1)
}

function removeParameter(operationIndex: number, parameterIndex: number): void {
  classDraft.value?.operations[operationIndex]?.parameters.splice(parameterIndex, 1)
}

function saveClass(): void {
  if (!classDraft.value || !validClass.value) return

  const element = structuredClone(toRaw(classDraft.value))
  element.name = element.name.trim()
  for (const attribute of element.attributes) {
    attribute.name = attribute.name.trim()
    attribute.type = attribute.type.trim()
  }
  for (const operation of element.operations) {
    operation.name = operation.name.trim()
    operation.returnType = operation.returnType?.trim() || null
    for (const parameter of operation.parameters) {
      parameter.name = parameter.name.trim()
      parameter.type = parameter.type.trim()
    }
  }

  classDraft.value = structuredClone(element)

  emit('execute', {
    commandType: 'updateElement',
    elementId: element.id,
    element,
  })
}

function relationshipElement(): UmlRelationship | null {
  const form = relationshipForm.value
  if (!form || !validRelationship.value) return null

  if (form.kind === 'generalization') {
    return {
      id: form.id,
      kind: 'generalization',
      sourceId: form.sourceId,
      targetId: form.targetId,
    }
  }

  const sourceMultiplicity = relationshipSourceMultiplicity.value
  const targetMultiplicity = relationshipTargetMultiplicity.value
  if (!sourceMultiplicity || !targetMultiplicity) return null

  return {
    id: form.id,
    kind: form.kind,
    sourceId: form.sourceId,
    targetId: form.targetId,
    sourceMultiplicity,
    targetMultiplicity,
  }
}

const hasUnsavedChanges = computed(() => {
  if (classDraft.value) {
    return (
      classDraftBaseline.value !== null &&
      serializeDraft(classDraft.value) !== classDraftBaseline.value
    )
  }

  if (relationshipForm.value) {
    return (
      relationshipDraftBaseline.value !== null &&
      serializeDraft(relationshipForm.value) !== relationshipDraftBaseline.value
    )
  }

  return false
})

function draftMatchesSelectedElement(): boolean {
  const element = selectedElement.value
  if (!element) return false

  if (element.kind === 'class') {
    return (
      classDraft.value !== null &&
      serializeDraft(toRaw(classDraft.value)) === serializeDraft(toRaw(element))
    )
  }

  const draft = relationshipElement()
  return draft !== null && serializeDraft(draft) === serializeDraft(toRaw(element))
}

watch(
  () => props.selectedElementId,
  syncDraft,
  { immediate: true },
)

watch(
  () => props.document.revision,
  () => {
    if (!hasUnsavedChanges.value || draftMatchesSelectedElement()) {
      syncDraft()
    }
  },
)

function saveRelationship(): void {
  const element = relationshipElement()
  if (!element) return

  emit('execute', {
    commandType: 'updateElement',
    elementId: element.id,
    element,
  })
}

function removeSelected(): void {
  if (!props.selectedElementId) return
  emit('execute', {
    commandType: 'removeElement',
    elementId: props.selectedElementId,
  })
}

function relationshipTitle(kind: UmlRelationship['kind']): string {
  return {
    association: 'Asociación',
    aggregation: 'Agregación',
    composition: 'Composición',
    generalization: 'Generalización',
  }[kind]
}
</script>

<template>
  <aside class="inspector-panel">
    <div class="inspector-heading">
      <div>
        <div class="text-overline text-secondary">Inspector</div>
        <div class="text-subtitle-1 font-weight-bold">
          {{ selectedElement ? 'Elemento UML' : 'Sin selección' }}
        </div>
      </div>
      <v-btn
        v-if="selectedElement"
        icon="mdi-close"
        size="x-small"
        variant="text"
        title="Cerrar inspector"
        @click="emit('clearSelection')"
      />
    </div>

    <div v-if="!selectedElement" class="inspector-empty">
      <v-icon icon="mdi-cursor-default-click-outline" size="36" />
      <p>Selecciona una clase o relación del canvas para editarla.</p>
    </div>

    <div v-else-if="classDraft" class="inspector-scroll">
      <v-chip size="x-small" color="primary" variant="tonal" class="mb-4">
        Clase UML
      </v-chip>

      <v-alert
        v-if="hasUnsavedChanges"
        type="warning"
        variant="tonal"
        density="compact"
        class="mb-4"
      >
        Hay cambios sin guardar. Una actualización externa del canvas no reemplazará este borrador.
      </v-alert>

      <v-text-field v-model="classDraft.name" label="Nombre" density="compact" />
      <v-select
        v-model="classDraft.visibility"
        :items="visibilityOptions"
        item-title="title"
        item-value="value"
        label="Visibilidad"
        density="compact"
      />

      <div class="inspector-section-title">
        <span>Atributos</span>
        <v-btn size="x-small" variant="tonal" prepend-icon="mdi-plus" @click="addAttribute">
          Agregar
        </v-btn>
      </div>

      <v-card
        v-for="(attribute, index) in classDraft.attributes"
        :key="attribute.id"
        variant="tonal"
        class="member-card"
      >
        <v-card-text class="pa-3">
          <div class="member-grid">
            <v-text-field v-model="attribute.name" label="Nombre" density="compact" hide-details />
            <v-text-field v-model="attribute.type" label="Tipo" density="compact" hide-details />
          </div>
          <div class="d-flex align-center ga-2 mt-2">
            <v-select
              v-model="attribute.visibility"
              :items="visibilityOptions"
              item-title="title"
              item-value="value"
              label="Visibilidad"
              density="compact"
              hide-details
              class="flex-grow-1"
            />
            <v-btn
              icon="mdi-delete-outline"
              size="small"
              variant="text"
              color="error"
              @click="removeAttribute(index)"
            />
          </div>
        </v-card-text>
      </v-card>

      <div class="inspector-section-title mt-5">
        <span>Operaciones</span>
        <v-btn size="x-small" variant="tonal" prepend-icon="mdi-plus" @click="addOperation">
          Agregar
        </v-btn>
      </div>

      <v-card
        v-for="(operation, operationIndex) in classDraft.operations"
        :key="operation.id"
        variant="tonal"
        class="member-card"
      >
        <v-card-text class="pa-3">
          <div class="member-grid">
            <v-text-field v-model="operation.name" label="Nombre" density="compact" hide-details />
            <v-text-field
              v-model="operation.returnType"
              label="Retorno"
              placeholder="Sin retorno"
              density="compact"
              hide-details
            />
          </div>

          <div class="d-flex align-center ga-2 mt-2">
            <v-select
              v-model="operation.visibility"
              :items="visibilityOptions"
              item-title="title"
              item-value="value"
              label="Visibilidad"
              density="compact"
              hide-details
              class="flex-grow-1"
            />
            <v-btn
              icon="mdi-delete-outline"
              size="small"
              variant="text"
              color="error"
              @click="removeOperation(operationIndex)"
            />
          </div>

          <div class="inspector-subtitle mt-3">
            <span>Parámetros</span>
            <v-btn
              size="x-small"
              variant="text"
              prepend-icon="mdi-plus"
              @click="addParameter(operationIndex)"
            >
              Agregar
            </v-btn>
          </div>

          <div
            v-for="(parameter, parameterIndex) in operation.parameters"
            :key="parameter.id"
            class="parameter-row"
          >
            <v-text-field v-model="parameter.name" label="Nombre" density="compact" hide-details />
            <v-text-field v-model="parameter.type" label="Tipo" density="compact" hide-details />
            <v-btn
              icon="mdi-close"
              size="x-small"
              variant="text"
              color="error"
              @click="removeParameter(operationIndex, parameterIndex)"
            />
          </div>
        </v-card-text>
      </v-card>

      <v-alert v-if="!validClass" type="warning" variant="tonal" density="compact" class="mt-4">
        Nombre, tipos y miembros no pueden quedar vacíos.
      </v-alert>

      <v-alert
        v-if="classHasRelationships"
        type="info"
        variant="tonal"
        density="compact"
        class="mt-4"
      >
        Para eliminar esta clase, elimina primero sus relaciones.
      </v-alert>

      <div class="inspector-actions">
        <v-btn
          color="primary"
          variant="flat"
          :disabled="busy || !validClass"
          @click="saveClass"
        >
          Guardar clase
        </v-btn>
        <v-btn
          color="error"
          variant="text"
          :disabled="busy || classHasRelationships"
          @click="removeSelected"
        >
          Eliminar
        </v-btn>
      </div>
    </div>

    <div v-else-if="relationshipForm" class="inspector-scroll">
      <v-chip size="x-small" color="secondary" variant="tonal" class="mb-4">
        {{ relationshipTitle(relationshipForm.kind) }}
      </v-chip>

      <v-alert
        v-if="hasUnsavedChanges"
        type="warning"
        variant="tonal"
        density="compact"
        class="mb-4"
      >
        Hay cambios sin guardar. Una actualización externa del canvas no reemplazará este borrador.
      </v-alert>

      <v-alert type="info" variant="tonal" density="compact" class="mb-4">
        El tipo de una relación no se cambia en sitio porque CU-05 exige conservar su
        <code>kind</code>. Para cambiar de tipo, elimínala y crea otra.
      </v-alert>

      <v-select
        v-model="relationshipForm.sourceId"
        :items="classes"
        item-title="name"
        item-value="id"
        label="Clase origen"
        density="compact"
      />
      <v-select
        v-model="relationshipForm.targetId"
        :items="classes"
        item-title="name"
        item-value="id"
        label="Clase destino"
        density="compact"
      />

      <div v-if="relationshipForm.kind !== 'generalization'" class="member-grid">
        <v-text-field
          v-model="relationshipForm.sourceLower"
          label="Origen mínimo"
          density="compact"
        />
        <v-text-field
          v-model="relationshipForm.sourceUpper"
          label="Origen máximo"
          density="compact"
        />
        <v-text-field
          v-model="relationshipForm.targetLower"
          label="Destino mínimo"
          density="compact"
        />
        <v-text-field
          v-model="relationshipForm.targetUpper"
          label="Destino máximo"
          density="compact"
        />
      </div>

      <v-alert
        v-if="!validRelationship"
        type="warning"
        variant="tonal"
        density="compact"
        class="mt-2"
      >
        Revisa clases y multiplicidades.
      </v-alert>

      <div class="inspector-actions">
        <v-btn
          color="primary"
          variant="flat"
          :disabled="busy || !validRelationship"
          @click="saveRelationship"
        >
          Guardar relación
        </v-btn>
        <v-btn color="error" variant="text" :disabled="busy" @click="removeSelected">
          Eliminar
        </v-btn>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.inspector-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 16px;
  background: #111c26;
}

.inspector-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}

.inspector-empty {
  display: grid;
  place-items: center;
  align-content: center;
  flex: 1;
  padding: 24px;
  color: #8194a7;
  text-align: center;
}

.inspector-empty p {
  max-width: 250px;
}

.inspector-scroll {
  overflow-y: auto;
  padding: 16px;
}

.inspector-section-title,
.inspector-subtitle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 12px;
  font-weight: 700;
}

.member-card {
  margin-bottom: 10px;
}

.member-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.parameter-row {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.inspector-actions {
  display: flex;
  gap: 8px;
  justify-content: space-between;
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

code {
  color: #7dd3fc;
}

@media (max-width: 900px) {
  .member-grid {
    grid-template-columns: 1fr;
  }
}
</style>