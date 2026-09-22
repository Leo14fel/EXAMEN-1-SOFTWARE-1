<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  createRelationshipElement,
  parseMultiplicity,
  type RelationshipKind,
} from './editor-elements'
import type { UmlClass, UmlRelationship } from './types'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    classes: UmlClass[]
    busy?: boolean
  }>(),
  {
    busy: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  create: [relationship: UmlRelationship]
}>()

const kind = ref<RelationshipKind>('association')
const sourceId = ref('')
const targetId = ref('')
const sourceLower = ref('1')
const sourceUpper = ref('1')
const targetLower = ref('0')
const targetUpper = ref('*')

const kindItems = [
  { title: 'Asociación', value: 'association' },
  { title: 'Agregación', value: 'aggregation' },
  { title: 'Composición', value: 'composition' },
  { title: 'Generalización / herencia', value: 'generalization' },
]

const isGeneralization = computed(() => kind.value === 'generalization')
const targetClasses = computed(() =>
  isGeneralization.value
    ? props.classes.filter((umlClass) => umlClass.id !== sourceId.value)
    : props.classes,
)
const sourceMultiplicity = computed(() =>
  parseMultiplicity(sourceLower.value, sourceUpper.value),
)
const targetMultiplicity = computed(() =>
  parseMultiplicity(targetLower.value, targetUpper.value),
)

const valid = computed(() => {
  if (!sourceId.value || !targetId.value) return false
  if (isGeneralization.value) return sourceId.value !== targetId.value
  return sourceMultiplicity.value !== null && targetMultiplicity.value !== null
})

const relationHint = computed(() => {
  if (kind.value === 'generalization') return 'Origen = clase hija; destino = clase padre.'
  if (kind.value === 'aggregation' || kind.value === 'composition') {
    return 'Origen = todo/contenedor; destino = parte/contenido.'
  }
  return 'Asociación neutral entre las clases seleccionadas.'
})

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    sourceId.value = props.classes[0]?.id ?? ''
    targetId.value = props.classes[1]?.id ?? props.classes[0]?.id ?? ''
    kind.value = 'association'
    sourceLower.value = '1'
    sourceUpper.value = '1'
    targetLower.value = '0'
    targetUpper.value = '*'
  },
)

function close(): void {
  emit('update:modelValue', false)
}

function submit(): void {
  if (props.busy || !valid.value) return

  const relationship = createRelationshipElement({
    kind: kind.value,
    sourceId: sourceId.value,
    targetId: targetId.value,
    sourceMultiplicity: sourceMultiplicity.value ?? undefined,
    targetMultiplicity: targetMultiplicity.value ?? undefined,
  })

  emit('create', relationship)
  close()
}
</script>

<template>
  <v-dialog
    :model-value="modelValue"
    :persistent="busy"
    max-width="680"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card title="Nueva relación UML">
      <v-card-text>
        <v-select
          v-model="kind"
          :items="kindItems"
          item-title="title"
          item-value="value"
          label="Tipo de relación"
          density="comfortable"
          :disabled="busy"
        />

        <div class="relationship-grid">
          <v-select
            v-model="sourceId"
            :items="classes"
            item-title="name"
            item-value="id"
            label="Clase origen"
            density="comfortable"
            :disabled="busy"
          />
          <v-select
            v-model="targetId"
            :items="targetClasses"
            item-title="name"
            item-value="id"
            label="Clase destino"
            density="comfortable"
            :disabled="busy"
          />
        </div>

        <v-alert type="info" variant="tonal" density="compact" class="mb-4">
          {{ relationHint }}
        </v-alert>

        <div v-if="!isGeneralization" class="relationship-grid">
          <v-text-field
            v-model="sourceLower"
            label="Origen mínimo"
            density="comfortable"
            :disabled="busy"
          />
          <v-text-field
            v-model="sourceUpper"
            label="Origen máximo"
            hint="Número o *"
            density="comfortable"
            :disabled="busy"
          />
          <v-text-field
            v-model="targetLower"
            label="Destino mínimo"
            density="comfortable"
            :disabled="busy"
          />
          <v-text-field
            v-model="targetUpper"
            label="Destino máximo"
            hint="Número o *"
            density="comfortable"
            :disabled="busy"
          />
        </div>

        <v-alert v-if="!valid" type="warning" variant="tonal" density="compact">
          Selecciona clases distintas para herencia y usa multiplicidades válidas cuando correspondan.
        </v-alert>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" :disabled="busy" @click="close">Cancelar</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :disabled="busy || !valid"
          :loading="busy"
          @click="submit"
        >
          Crear relación
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.relationship-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 600px) {
  .relationship-grid {
    grid-template-columns: 1fr;
  }
}
</style>
