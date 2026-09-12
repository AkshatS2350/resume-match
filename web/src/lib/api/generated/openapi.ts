// Generated from docs/schemas/openapi.json. Do not edit.

export interface AchievementItem_Input {
  confidence_inputs: unknown;
  extraction_confidence: unknown;
  item_id: string;
  origin: string;
  provenance: unknown;
  source_text: string;
  text: string;
}

export interface AchievementItem_Output {
  confidence_inputs: unknown;
  extraction_confidence: string;
  item_id: string;
  origin: string;
  provenance: unknown;
  source_text: string;
  text: string;
}

export interface Body_upload_resume_api_v1_sessions_resume_post {
  file: string;
}

export interface CandidateProfile {
  confirmed: boolean;
  profile_revision: number;
  resume: unknown;
  schema_version: string;
  session_start_date: string;
  target: unknown;
}

export interface CertificationItem_Input {
  canonical_certification_id?: unknown;
  confidence_inputs: unknown;
  extraction_confidence: unknown;
  issued: unknown;
  issuer: unknown;
  item_id: string;
  name: unknown;
  origin: string;
  provenance: unknown;
  source_text: string;
}

export interface CertificationItem_Output {
  canonical_certification_id?: unknown;
  confidence_inputs: unknown;
  extraction_confidence: string;
  issued: unknown;
  issuer: unknown;
  item_id: string;
  name: unknown;
  origin: string;
  provenance: unknown;
  source_text: string;
}

export interface ConsentResult {
  decided_at: string;
  decision: string;
  request_id: string;
}

export interface ConsentSubmission {
  approved: boolean;
}

export interface DegreeLevel {
}

export interface EducationItem_Input {
  confidence_inputs: unknown;
  coursework: unknown;
  degree_level: unknown;
  end_date: unknown;
  extraction_confidence: unknown;
  field_of_study: unknown;
  institution: unknown;
  item_id: string;
  origin: string;
  provenance: unknown;
  source_text: string;
  start_date: unknown;
}

export interface EducationItem_Output {
  confidence_inputs: unknown;
  coursework: unknown;
  degree_level: unknown;
  end_date: unknown;
  extraction_confidence: string;
  field_of_study: unknown;
  institution: unknown;
  item_id: string;
  origin: string;
  provenance: unknown;
  source_text: string;
  start_date: unknown;
}

export interface ExperienceItem_Input {
  confidence_inputs: unknown;
  date_conflict: boolean;
  description: unknown;
  duration_months: unknown;
  employer: unknown;
  end_date: unknown;
  extraction_confidence: unknown;
  is_present: boolean;
  item_id: string;
  origin: string;
  provenance: unknown;
  source_text: string;
  start_date: unknown;
  title: unknown;
}

export interface ExperienceItem_Output {
  confidence_inputs: unknown;
  date_conflict: boolean;
  description: unknown;
  duration_months: unknown;
  employer: unknown;
  end_date: unknown;
  extraction_confidence: string;
  is_present: boolean;
  item_id: string;
  origin: string;
  provenance: unknown;
  source_text: string;
  start_date: unknown;
  title: unknown;
}

export interface ExtractionResponse {
  extraction_ok: boolean;
  page_count: number;
  warnings?: unknown;
}

export interface HTTPValidationError {
  detail?: unknown;
}

export interface JsonValue {
}

export interface ManifestEntry {
  field_paths: unknown;
  manifest_version: string;
  omissions: unknown;
  omitted_paths: unknown;
  operation: string;
  payload_hash: string;
  transmitted_at: string;
}

export interface OmissionRecord {
  path: string;
  reason: string;
}

export interface PendingRequestProjection {
  admitted_at: string;
  fields: unknown;
  omissions: unknown;
  operation: string;
  payload_hash: string;
  provider_identity: string;
  provider_locality: string;
  request_id: string;
}

export interface ProfileUpdate {
  resume: unknown;
}

export interface ProjectItem_Input {
  confidence_inputs: unknown;
  description: unknown;
  extraction_confidence: unknown;
  item_id: string;
  name: unknown;
  origin: string;
  provenance: unknown;
  source_text: string;
}

export interface ProjectItem_Output {
  confidence_inputs: unknown;
  description: unknown;
  extraction_confidence: string;
  item_id: string;
  name: unknown;
  origin: string;
  provenance: unknown;
  source_text: string;
}

export interface ProjectedField {
  path: string;
  value: unknown;
}

export interface Provenance {
  block_ids: unknown;
  end_offset: number;
  section_id: string;
  start_offset: number;
}

export interface RequestManifest {
  entries: unknown;
}

export interface SanitizationSummary {
  content_hash: string;
  detector_versions: unknown;
  fail_safe_redaction_count: number;
  pii_policy_version: string;
  placeholder_set_version: string;
  produced_at: string;
  profile_revision: number;
  removed_categories: unknown;
}

export interface SanitizedResume {
  removed_span_counts: unknown;
  resume: unknown;
  schema_version: string;
  source_profile_revision: number;
  target: unknown;
}

export interface SanitizedResumeResult {
  artifact_label: string;
  fail_safe_redaction_count: number;
  removed_categories: unknown;
  sanitization_result: unknown;
}

export interface SeniorityId {
}

export interface SessionCreated {
  expires_at: string;
  session_start_date: string;
  token: string;
}

export interface SessionDeleted {
  discarded: boolean;
}

export interface SkillItem_Input {
  canonical_skill_id: string;
  confidence_inputs: unknown;
  extraction_confidence: unknown;
  item_id: string;
  origin: string;
  provenance: unknown;
  source_text: string;
  surface: string;
}

export interface SkillItem_Output {
  canonical_skill_id: string;
  confidence_inputs: unknown;
  extraction_confidence: string;
  item_id: string;
  origin: string;
  provenance: unknown;
  source_text: string;
  surface: string;
}

export interface StructuredResume_Input {
  achievements: unknown;
  certifications: unknown;
  education: unknown;
  experience: unknown;
  projects: unknown;
  schema_version: string;
  skills: unknown;
  summary: unknown;
  unclassified: unknown;
}

export interface StructuredResume_Output {
  achievements: unknown;
  certifications: unknown;
  education: unknown;
  experience: unknown;
  projects: unknown;
  schema_version: string;
  skills: unknown;
  summary: unknown;
  unclassified: unknown;
}

export interface TargetConstraints {
  domain_id: string;
  locations: unknown;
  role_id: string;
  seniority_id: unknown;
  work_modes: unknown;
}

export interface UnclassifiedItem_Input {
  confidence_inputs: unknown;
  extraction_confidence: unknown;
  item_id: string;
  origin: string;
  provenance: unknown;
  source_text: string;
  text: string;
}

export interface UnclassifiedItem_Output {
  confidence_inputs: unknown;
  extraction_confidence: string;
  item_id: string;
  origin: string;
  provenance: unknown;
  source_text: string;
  text: string;
}

export interface ValidationError {
  loc: unknown;
  msg: string;
  type: string;
}

export interface WorkMode {
}

export interface YearMonth {
  month: number;
  year: number;
}
