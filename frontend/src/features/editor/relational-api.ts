import { authenticatedFetch } from '../../services/api'
import type { UmlMultiplicity } from './types'

export interface RelationalColumn {
  name: string; sqlType: string; nullable: boolean; sourceAttributeId: string | null
  generated: 'uuid' | null; enumName: string | null; allowedValues: string[] | null
}
export interface RelationalTable {
  name: string; sourceClassId: string | null; sourceRelationshipId: string | null
  columns: RelationalColumn[]; primaryKey: string[]; uniqueConstraints: string[][]
  foreignKeys: { name: string; columns: string[]; targetTable: string; targetColumns: string[]; onDelete: string; sourceId: string }[]
  indexes: { name: string; columns: string[] }[]
}
export interface RelationalPreview {
  projectId: string; sourceRevision: number
  model: {
    version: 1; dialect: 'postgresql'; inheritanceStrategy: 'joined'; quotedIdentifiers: true
    tables: RelationalTable[]
    relations: { sourceId: string; kind: string; sourceTable: string; targetTable: string;
      cardinality: string; storageTable: string; columns: string[]; sourceMultiplicity: UmlMultiplicity | null;
      targetMultiplicity: UmlMultiplicity | null; requiresRuntimeValidation: boolean }[]
  } | null
  diagnostics: { severity: 'warning' | 'error'; code: string; message: string; sourceId: string | null }[]
}

export async function getRelationalPreview(projectId: string): Promise<RelationalPreview> {
  const response = await authenticatedFetch(`/projects/${projectId}/relational-model`)
  if (!response.ok) throw new Error('No se pudo consultar la estructura relacional del proyecto.')
  return response.json() as Promise<RelationalPreview>
}
