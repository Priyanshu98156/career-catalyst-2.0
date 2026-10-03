/**
 * Centralized TypeScript type definitions mapped from OpenAPI generated schemas (DRY-7).
 */
import type { components, paths } from './api.generated';

export type { components, paths };

// Component Schema Shortcuts
export type ApiSchemas = components['schemas'];

// Domain Entity Shortcuts
export type UserResponse = ApiSchemas['UserResponse'];
export type TokenResponse = ApiSchemas['Token'];
export type ParsedProfileSchema = ApiSchemas['ParsedProfile'];
export type ProfileResponseSchema = ApiSchemas['ProfileResponse'];
export type ProfileCreateSchema = ApiSchemas['ProfileCreate'];
export type JDAnalysisSchema = ApiSchemas['JDAnalysis'];
export type JDAnalysisRequestSchema = ApiSchemas['JDAnalysisRequest'];
export type TailorRequestSchema = ApiSchemas['TailorRequest'];
export type TailoredResumeResponseSchema = ApiSchemas['TailoredResumeResponse'];
export type TailoredResumeModelResponseSchema = ApiSchemas['TailoredResumeModelResponse'];
export type MasterBulletResponseSchema = ApiSchemas['MasterBulletResponse'];
export type MasterBulletCreateSchema = ApiSchemas['MasterBulletCreate'];
