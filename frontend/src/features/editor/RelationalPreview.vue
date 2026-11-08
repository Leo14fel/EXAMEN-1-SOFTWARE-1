<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { getRelationalPreview, type RelationalPreview } from './relational-api'
const props = defineProps<{ projectId: string; revision: number }>()
const report = ref<RelationalPreview | null>(null)
const loading = ref(false), error = ref('')
const stale = computed(() => report.value && report.value.sourceRevision !== props.revision)
async function load() {
  const id = props.projectId
  loading.value = true; error.value = ''
  try {
    const result = await getRelationalPreview(id)
    if (id === props.projectId) report.value = result
  } catch (reason) { error.value = reason instanceof Error ? reason.message : 'No se pudo consultar.' }
  finally { loading.value = false }
}
watch(() => props.projectId, () => { report.value = null; void load() }, { immediate: true })
function download() {
  if (!report.value?.model) return
  const url = URL.createObjectURL(new Blob([JSON.stringify(report.value, null, 2)], { type: 'application/json' }))
  const link = document.createElement('a')
  link.href = url; link.download = `modelo-relacional-${props.projectId}.json`; link.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <section aria-label="Vista previa del modelo relacional">
    <div class="d-flex align-center flex-wrap ga-2 mb-3">
      <p class="text-body-2 flex-grow-1 ma-0">Estructura que se usará al generar la aplicación.</p>
      <v-btn size="small" variant="tonal" :loading="loading" @click="load">Actualizar vista</v-btn>
      <v-btn size="small" variant="text" :disabled="!report?.model || !!stale" @click="download">Descargar JSON</v-btn>
    </div>
    <v-alert v-if="error" type="error" density="compact" class="mb-3">{{ error }}</v-alert>
    <v-alert v-if="stale" type="warning" density="compact" class="mb-3">El diagrama cambió. Actualiza la vista para revisar su estructura actual.</v-alert>
    <div v-if="report" class="text-caption text-medium-emphasis mb-3">Revisión {{ report.sourceRevision }} · PostgreSQL · Herencia JOINED</div>
    <v-alert v-for="(diagnostic, index) in report?.diagnostics ?? []" :key="`${diagnostic.sourceId}-${index}`"
      :type="diagnostic.severity === 'error' ? 'error' : 'warning'" density="compact" class="mb-2">{{ diagnostic.message }}</v-alert>
    <p v-if="report?.model && report.model.tables.length === 0" class="text-body-2">Agrega clases al diagrama para obtener tablas.</p>
    <article v-for="table in report?.model?.tables ?? []" :key="table.name" class="relational-table mb-4">
      <h3 class="text-subtitle-2 mb-2"><code>{{ table.name }}</code></h3>
      <div class="table-scroll">
        <table>
          <thead><tr><th>Columna</th><th>Tipo</th><th>Permite nulos</th><th>Clave y valores</th></tr></thead>
          <tbody><tr v-for="column in table.columns" :key="column.name">
            <td><code>{{ column.name }}</code></td><td>{{ column.sqlType }}</td><td>{{ column.nullable ? 'Sí' : 'No' }}</td>
            <td>
              <strong v-if="table.primaryKey.includes(column.name)" class="text-primary">PK </strong>
              <strong v-if="table.foreignKeys.some(key => key.columns.includes(column.name))" class="text-secondary">FK </strong>
              <span v-if="column.generated === 'uuid'">UUID generado</span>
              <span v-if="column.allowedValues">{{ column.enumName }}: {{ column.allowedValues.join(', ') }}</span>
            </td>
          </tr></tbody>
        </table>
      </div>
      <p v-for="key in table.foreignKeys" :key="key.name" class="text-caption mt-2 mb-0">
        {{ key.columns.join(', ') }} → {{ key.targetTable }} ({{ key.targetColumns.join(', ') }}) · al eliminar: {{ key.onDelete }}
      </p>
      <p v-for="(unique, index) in table.uniqueConstraints" :key="`unique-${index}`" class="text-caption mt-2 mb-0">Única: {{ unique.join(', ') }}</p>
      <p v-for="index in table.indexes" :key="index.name" class="text-caption mt-2 mb-0">Índice: {{ index.columns.join(', ') }}</p>
    </article>
  </section>
</template>

<style scoped>
.relational-table { padding: 14px; border: 1px solid rgba(53, 208, 186, .2); background: #13212c; border-radius: 12px; overflow-wrap: anywhere; }
.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 9px; border-bottom: 1px solid rgba(148, 163, 184, .15); text-align: left; }
th { color: #35d0ba; }
</style>
