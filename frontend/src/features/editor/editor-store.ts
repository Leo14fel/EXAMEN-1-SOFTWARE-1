import { defineStore } from 'pinia'
import { applyDocumentChanges, type SyncEvent, type SyncStatus } from './editor-sync'
import {
  addCollaborator,
  createProject as createPersistedProject,
  EditorApiError,
  executeProjectCommand,
  getProject,
  listProjects,
  listCollaborators,
  redoProject,
  removeCollaborator,
  undoProject,
  updateCollaborator,
} from './editor-api'
import type {
  ProjectCollaborator,
  ProjectDocument,
  ProjectEditorState,
  ProjectRole,
  ProjectSummary,
  UmlCommand,
} from './types'

function messageFromError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error inesperado del editor'
}

export const useEditorStore = defineStore('editor', {
  state: () => ({
    projectId: null as string | null,
    projects: [] as ProjectSummary[],
    collaborators: [] as ProjectCollaborator[],
    effectiveRole: null as ProjectRole | null,
    syncStatus: 'connecting' as SyncStatus,
    document: null as ProjectDocument | null,
    canUndo: false,
    canRedo: false,
    loading: false,
    error: null as string | null,
  }),
  actions: {
    applySyncEvent(event: SyncEvent): boolean {
      const current = this.document
      if (!current) return false
      if (event.type === 'snapshot') {
        if (event.document.id !== current.id) return false
        if (event.document.revision < current.revision) return true
        this.applyProjectState(event)
      } else {
        if (event.projectId !== current.id) return false
        if (event.revision < current.revision) return true
        if (event.revision !== current.revision) {
          if (event.baseRevision !== current.revision) return false
          try {
            const next = applyDocumentChanges(current, event.changes)
            if (next.id !== current.id || next.revision !== event.revision) return false
            this.document = next
          } catch {
            return false
          }
        }
        this.canUndo = event.canUndo
        this.canRedo = event.canRedo
      }
      this.effectiveRole = event.effectiveRole
      return true
    },
    applyProjectState(state: ProjectEditorState) {
      if (this.document?.id === state.document.id && this.document.revision > state.document.revision) return
      this.projectId = state.document.id
      this.document = structuredClone(state.document)
      this.canUndo = state.canUndo
      this.canRedo = state.canRedo
      this.error = null
    },
    applyProjectDocument(document: ProjectDocument) {
      this.projectId = document.id
      this.document = structuredClone(document)
      this.canUndo = false
      this.canRedo = false
      this.error = null
    },
    requireDocument(): ProjectDocument {
      if (!this.document || !this.projectId) throw new Error('No hay un proyecto abierto')
      return this.document
    },
    async loadProjects() {
      this.loading = true
      this.error = null
      try {
        this.projects = structuredClone(await listProjects())
      } catch (error) {
        this.error = messageFromError(error)
        throw error
      } finally {
        this.loading = false
      }
    },
    async createProject(name: string) {
      this.loading = true
      this.error = null
      try {
        this.applyProjectDocument(await createPersistedProject({ name }))
        this.effectiveRole = 'EDITOR'
        await this.loadProjects()
      } catch (error) {
        this.error = messageFromError(error)
        throw error
      } finally {
        this.loading = false
      }
    },
    async openProject(projectId: string) {
      this.loading = true
      this.error = null
      try {
        this.applyProjectDocument(await getProject(projectId))
        this.effectiveRole = this.projects.find((project) => project.id === projectId)?.effectiveRole ?? null
      } catch (error) {
        this.error = messageFromError(error)
        throw error
      } finally {
        this.loading = false
      }
    },
    async refreshProjectAfterConflict() {
      const document = this.requireDocument()
      const refreshed = await getProject(document.id)
      if (this.projectId === document.id && (this.document?.revision ?? -1) <= refreshed.revision) {
        this.applyProjectDocument(refreshed)
      }
    },
    async loadCollaborators() {
      const document = this.requireDocument()
      this.collaborators = structuredClone(await listCollaborators(document.id))
    },
    async addCollaborator(email: string, role: ProjectRole) {
      const document = this.requireDocument()
      const collaborator = await addCollaborator(document.id, email, role)
      this.collaborators.push(collaborator)
    },
    async updateCollaborator(collaboratorId: string, role: ProjectRole) {
      const document = this.requireDocument()
      const collaborator = await updateCollaborator(document.id, collaboratorId, role)
      const index = this.collaborators.findIndex((item) => item.userId === collaboratorId)
      if (index >= 0) this.collaborators.splice(index, 1, collaborator)
    },
    async removeCollaborator(collaboratorId: string) {
      const document = this.requireDocument()
      await removeCollaborator(document.id, collaboratorId)
      this.collaborators = this.collaborators.filter((item) => item.userId !== collaboratorId)
    },
    async execute(command: UmlCommand) {
      this.loading = true
      this.error = null
      try {
        const document = this.requireDocument()
        const state = await executeProjectCommand(document.id, document.revision, command)
        if (this.projectId === document.id) this.applyProjectState(state)
      } catch (error) {
        if (error instanceof EditorApiError && error.code === 'PROJECT_REVISION_CONFLICT') {
          await this.refreshProjectAfterConflict()
          this.error = 'El proyecto cambió en otra instancia y se recargó la versión actual.'
        } else {
          this.error = messageFromError(error)
        }
        throw error
      } finally {
        this.loading = false
      }
    },
    async undo() {
      this.loading = true
      this.error = null
      try {
        const document = this.requireDocument()
        const state = await undoProject(document.id, document.revision)
        if (this.projectId === document.id) this.applyProjectState(state)
      } catch (error) {
        if (error instanceof EditorApiError && error.code === 'PROJECT_REVISION_CONFLICT') {
          await this.refreshProjectAfterConflict()
          this.error = 'El proyecto cambió en otra instancia y se recargó la versión actual.'
        } else {
          this.error = messageFromError(error)
        }
        throw error
      } finally {
        this.loading = false
      }
    },
    async redo() {
      this.loading = true
      this.error = null
      try {
        const document = this.requireDocument()
        const state = await redoProject(document.id, document.revision)
        if (this.projectId === document.id) this.applyProjectState(state)
      } catch (error) {
        if (error instanceof EditorApiError && error.code === 'PROJECT_REVISION_CONFLICT') {
          await this.refreshProjectAfterConflict()
          this.error = 'El proyecto cambió en otra instancia y se recargó la versión actual.'
        } else {
          this.error = messageFromError(error)
        }
        throw error
      } finally {
        this.loading = false
      }
    },
  },
})
