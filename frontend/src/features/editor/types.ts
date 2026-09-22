export type UUID = string
export type ProjectRole = 'EDITOR' | 'VIEWER'
export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue }
export type UmlVisibility = 'public' | 'private' | 'protected' | 'package'

export interface UmlParameter {
  id: UUID
  name: string
  type: string
}

export interface UmlAttribute {
  id: UUID
  kind: 'attribute'
  name: string
  type: string
  visibility: UmlVisibility
}

export interface UmlOperation {
  id: UUID
  kind: 'operation'
  name: string
  visibility: UmlVisibility
  parameters: UmlParameter[]
  returnType: string | null
}

export interface UmlClass {
  id: UUID
  kind: 'class'
  name: string
  visibility: UmlVisibility
  attributes: UmlAttribute[]
  operations: UmlOperation[]
}

export interface UmlMultiplicity {
  lower: number
  upper: number | '*'
}

export interface UmlRelationshipBase {
  id: UUID
  sourceId: UUID
  targetId: UUID
}

export interface UmlAssociation extends UmlRelationshipBase {
  kind: 'association'
  sourceMultiplicity: UmlMultiplicity
  targetMultiplicity: UmlMultiplicity
}

export interface UmlAggregation extends UmlRelationshipBase {
  kind: 'aggregation'
  sourceMultiplicity: UmlMultiplicity
  targetMultiplicity: UmlMultiplicity
}

export interface UmlComposition extends UmlRelationshipBase {
  kind: 'composition'
  sourceMultiplicity: UmlMultiplicity
  targetMultiplicity: UmlMultiplicity
}

export interface UmlGeneralization extends UmlRelationshipBase {
  kind: 'generalization'
}

export type UmlRelationship =
  | UmlAssociation
  | UmlAggregation
  | UmlComposition
  | UmlGeneralization

export type CanonicalUmlElement = UmlClass | UmlRelationship

export interface CanonicalUmlModel {
  elements: CanonicalUmlElement[]
}

export interface DiagramNodeLayout {
  x: number
  y: number
  width: number
  height: number
}

export interface DiagramLayout {
  nodes: Record<UUID, DiagramNodeLayout>
}

export interface ProjectDocument {
  id: UUID
  metadata: Record<string, JsonValue>
  ownerId: UUID
  revision: number
  createdAt: string
  updatedAt: string
  umlModel: CanonicalUmlModel
  diagramLayout: DiagramLayout
}

export interface ProjectEditorState {
  document: ProjectDocument
  canUndo: boolean
  canRedo: boolean
}

export interface ProjectSummary {
  id: UUID
  ownerId: UUID
  metadata: Record<string, JsonValue>
  revision: number
  createdAt: string
  updatedAt: string
  effectiveRole: ProjectRole
}

export interface ProjectCollaborator {
  userId: UUID
  email: string
  role: ProjectRole
}

export interface AddUmlElementCommand {
  commandType: 'addElement'
  element: CanonicalUmlElement
}

export interface UpdateUmlElementCommand {
  commandType: 'updateElement'
  elementId: UUID
  element: CanonicalUmlElement
}

export interface RemoveUmlElementCommand {
  commandType: 'removeElement'
  elementId: UUID
}

export interface SetNodeLayoutCommand {
  commandType: 'setNodeLayout'
  elementId: UUID
  layout: DiagramNodeLayout
}

export interface RemoveNodeLayoutCommand {
  commandType: 'removeNodeLayout'
  elementId: UUID
}

export type UmlCommand =
  | AddUmlElementCommand
  | UpdateUmlElementCommand
  | RemoveUmlElementCommand
  | SetNodeLayoutCommand
  | RemoveNodeLayoutCommand
