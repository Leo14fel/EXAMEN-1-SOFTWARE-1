<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useEditorStore } from './editor-store'
import {
  createUmlClass,
  nextClassName,
} from './editor-elements'
import type {
  DiagramNodeLayout,
  UmlClass,
  UmlCommand,
  UmlRelationship,
} from './types'
import { computeAutoLayout } from './canvas/auto-layout'
import UmlCanvas from './canvas/UmlCanvas.vue'
import InspectorPanel from './InspectorPanel.vue'
import RelationshipDialog from './RelationshipDialog.vue'

const editorStore = useEditorStore()
const { document, loading, error, sessionId, canUndo, canRedo } = storeToRefs(editorStore)

const selectedElementId = ref<string | null>(null)
const relationshipDialogOpen = ref(false)
const batchBusy = ref(false)
const canvasRef = ref<{ fitContent: () => void } | null>(null)

const shortSessionId = computed(() => sessionId.value?.slice(0, 8) ?? 'sin sesión')
const revision = computed(() => document.value?.revision ?? 0)
const busy = computed(() => loading.value || batchBusy.value)
const classes = computed(() =>
  document.value?.umlModel.elements.filter(
    (element): element is UmlClass => element.kind === 'class',
  ) ?? [],
)

async function startEditor(): Promise<void> {
  try {
    selectedElementId.value = null
    await editorStore.startSession()
  } catch {
    // El store expone el mensaje en `error`.
  }
}

async function executeCommand(command: UmlCommand): Promise<boolean> {
  try {
    await editorStore.execute(command)
    return true
  } catch {
    return false
  }
}

async function createClass(): Promise<void> {
  if (!document.value || busy.value) return
  const element = createUmlClass(nextClassName(document.value))

  if (
    await executeCommand({
      commandType: 'addElement',
      element,
    })
  ) {
    selectedElementId.value = element.id
  }
}

async function createRelationship(relationship: UmlRelationship): Promise<void> {
  if (!document.value || busy.value) return

  if (
    await executeCommand({
      commandType: 'addElement',
      element: relationship,
    })
  ) {
    selectedElementId.value = relationship.id
  }
}

async function handleMoveNode(payload: {
  elementId: string
  layout: DiagramNodeLayout
}): Promise<void> {
  await executeCommand({
    commandType: 'setNodeLayout',
    elementId: payload.elementId,
    layout: payload.layout,
  })
}

async function handleInspectorCommand(command: UmlCommand): Promise<void> {
  const removedId = command.commandType === 'removeElement' ? command.elementId : null
  const ok = await executeCommand(command)
  if (ok && removedId === selectedElementId.value) {
    selectedElementId.value = null
  }
}

async function undo(): Promise<void> {
  if (!canUndo.value || busy.value) return
  try {
    await editorStore.undo()
    ensureValidSelection()
  } catch {
    // El store ya expone el error.
  }
}

async function redo(): Promise<void> {
  if (!canRedo.value || busy.value) return
  try {
    await editorStore.redo()
    ensureValidSelection()
  } catch {
    // El store ya expone el error.
  }
}

async function autoLayout(): Promise<void> {
  if (!document.value || classes.value.length === 0 || busy.value) return

  batchBusy.value = true
  try {
    const layouts = computeAutoLayout(document.value)

    for (const [elementId, layout] of Object.entries(layouts)) {
      await editorStore.execute({
        commandType: 'setNodeLayout',
        elementId,
        layout,
      })
    }

    await nextTick()
    canvasRef.value?.fitContent()
  } catch {
    // El store ya expone el error si un comando falla.
  } finally {
    batchBusy.value = false
  }
}

function ensureValidSelection(): void {
  if (!selectedElementId.value || !document.value) return
  const stillExists = document.value.umlModel.elements.some(
    (element) => element.id === selectedElementId.value,
  )
  if (!stillExists) selectedElementId.value = null
}

watch(
  () => document.value?.revision,
  ensureValidSelection,
)

onMounted(startEditor)
</script>

<template>
  <v-app>
    <v-main class="editor-main">
      <div class="editor-shell">
        <header class="editor-toolbar">
          <div>
            <div class="text-overline text-primary">EXAMEN SOFTWARE I</div>
            <h1 class="text-h5 font-weight-bold">Editor UML</h1>
          </div>

          <div class="editor-toolbar__status">
            <v-chip size="small" variant="tonal" color="secondary">
              Sesión {{ shortSessionId }}
            </v-chip>
            <v-chip size="small" variant="tonal" color="primary">
              Revisión {{ revision }}
            </v-chip>
          </div>
        </header>

        <v-alert
          v-if="error"
          type="error"
          variant="tonal"
          class="mb-4"
          title="Error del editor"
          closable
          @click:close="editorStore.error = null"
        >
          {{ error }}
        </v-alert>

        <div v-if="loading && !document" class="editor-loading">
          <v-progress-circular indeterminate color="primary" size="48" />
          <span class="text-body-2 text-medium-emphasis">Preparando sesión de editor...</span>
        </div>

        <template v-else-if="document">
          <div class="editor-commandbar">
            <div class="editor-commandbar__group">
              <v-btn
                color="primary"
                variant="flat"
                prepend-icon="mdi-plus-box-outline"
                :disabled="busy"
                @click="createClass"
              >
                Nueva clase
              </v-btn>
              <v-btn
                color="secondary"
                variant="tonal"
                prepend-icon="mdi-vector-line"
                :disabled="busy || classes.length === 0"
                @click="relationshipDialogOpen = true"
              >
                Nueva relación
              </v-btn>
            </div>

            <div class="editor-commandbar__group">
              <v-btn
                variant="text"
                prepend-icon="mdi-undo"
                :disabled="busy || !canUndo"
                @click="undo"
              >
                Deshacer
              </v-btn>
              <v-btn
                variant="text"
                prepend-icon="mdi-redo"
                :disabled="busy || !canRedo"
                @click="redo"
              >
                Rehacer
              </v-btn>
              <v-btn
                variant="tonal"
                prepend-icon="mdi-auto-fix"
                :disabled="busy || classes.length === 0"
                @click="autoLayout"
              >
                Auto-organizar
              </v-btn>
            </div>
          </div>

          <div class="editor-grid">
            <section class="toolbox-panel">
              <div class="text-overline text-primary">Toolbox</div>
              <div class="text-subtitle-2 font-weight-bold mb-3">Modelado manual</div>

              <v-list density="compact" bg-color="transparent">
                <v-list-item
                  prepend-icon="mdi-cube-outline"
                  title="Clase"
                  subtitle="Nueva clase UML"
                  :disabled="busy"
                  @click="createClass"
                />
                <v-list-item
                  prepend-icon="mdi-vector-line"
                  title="Relación"
                  subtitle="Asociación, agregación, composición o herencia"
                  :disabled="busy || classes.length === 0"
                  @click="relationshipDialogOpen = true"
                />
              </v-list>

              <v-divider class="my-4" />

              <div class="text-caption text-medium-emphasis">
                Arrastra clases para guardar su posición. Selecciona un elemento para editarlo en el
                inspector. Las mutaciones pasan por el Command Bus del backend.
              </div>

              <v-progress-linear
                v-if="busy"
                indeterminate
                color="primary"
                class="mt-4"
              />
            </section>

            <UmlCanvas
              ref="canvasRef"
              :document="document"
              :selected-element-id="selectedElementId"
              :busy="busy"
              @select="selectedElementId = $event"
              @move-node="handleMoveNode"
            />

            <InspectorPanel
              :document="document"
              :selected-element-id="selectedElementId"
              :busy="busy"
              @execute="handleInspectorCommand"
              @clear-selection="selectedElementId = null"
            />
          </div>

          <RelationshipDialog
            v-model="relationshipDialogOpen"
            :classes="classes"
            :busy="busy"
            @create="createRelationship"
          />
        </template>

        <div v-else-if="!error" class="editor-loading">
          <span class="text-body-2 text-medium-emphasis">Esperando documento...</span>
        </div>
      </div>
    </v-main>
  </v-app>
</template>

<style scoped>
.editor-main {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(53, 208, 186, 0.08), transparent 32%),
    #0f1720;
}

.editor-shell {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  width: 100%;
  min-height: 100vh;
  padding: 18px;
}

.editor-toolbar,
.editor-commandbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.editor-toolbar {
  margin-bottom: 14px;
}

.editor-toolbar__status,
.editor-commandbar__group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.editor-toolbar__status {
  justify-content: flex-end;
}

.editor-commandbar {
  margin-bottom: 12px;
  padding: 10px 12px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 14px;
  background: rgba(17, 28, 38, 0.86);
}

.editor-grid {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr) 360px;
  gap: 12px;
  min-height: 0;
  flex: 1;
}

.toolbox-panel {
  min-width: 0;
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 16px;
  background: #111c26;
}

.editor-loading {
  flex: 1;
  min-height: 620px;
  display: grid;
  place-content: center;
  justify-items: center;
  gap: 16px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 16px;
  background: #0c141d;
}

@media (max-width: 1180px) {
  .editor-grid {
    grid-template-columns: 180px minmax(0, 1fr) 300px;
  }
}

@media (max-width: 900px) {
  .editor-grid {
    grid-template-columns: 1fr;
  }

  .toolbox-panel {
    display: none;
  }

  .editor-commandbar,
  .editor-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .editor-toolbar__status {
    justify-content: flex-start;
  }
}
</style>