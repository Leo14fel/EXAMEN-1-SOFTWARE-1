import { defineStore } from 'pinia'
import {
  createEditorSession,
  executeEditorCommand,
  getEditorSession,
  redoEditorSession,
  undoEditorSession,
} from './editor-api'
import type { EditorSessionState, ProjectDocument, UmlCommand } from './types'

function messageFromError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error inesperado del editor'
}

export const useEditorStore = defineStore('editor', {
  state: () => ({
    sessionId: null as string | null,
    document: null as ProjectDocument | null,
    canUndo: false,
    canRedo: false,
    loading: false,
    error: null as string | null,
  }),
  actions: {
    applySessionState(state: EditorSessionState) {
      this.sessionId = state.sessionId
      this.document = structuredClone(state.document)
      this.canUndo = state.canUndo
      this.canRedo = state.canRedo
      this.error = null
    },
    requireSessionId(): string {
      if (!this.sessionId) throw new Error('No hay una sesión de editor activa')
      return this.sessionId
    },
    async startSession() {
      this.loading = true
      this.error = null
      try {
        this.applySessionState(await createEditorSession())
      } catch (error) {
        this.error = messageFromError(error)
        throw error
      } finally {
        this.loading = false
      }
    },
    async refreshSession() {
      this.loading = true
      this.error = null
      try {
        this.applySessionState(await getEditorSession(this.requireSessionId()))
      } catch (error) {
        this.error = messageFromError(error)
        throw error
      } finally {
        this.loading = false
      }
    },
    async execute(command: UmlCommand) {
      this.loading = true
      this.error = null
      try {
        this.applySessionState(await executeEditorCommand(this.requireSessionId(), command))
      } catch (error) {
        this.error = messageFromError(error)
        throw error
      } finally {
        this.loading = false
      }
    },
    async undo() {
      this.loading = true
      this.error = null
      try {
        this.applySessionState(await undoEditorSession(this.requireSessionId()))
      } catch (error) {
        this.error = messageFromError(error)
        throw error
      } finally {
        this.loading = false
      }
    },
    async redo() {
      this.loading = true
      this.error = null
      try {
        this.applySessionState(await redoEditorSession(this.requireSessionId()))
      } catch (error) {
        this.error = messageFromError(error)
        throw error
      } finally {
        this.loading = false
      }
    },
  },
})