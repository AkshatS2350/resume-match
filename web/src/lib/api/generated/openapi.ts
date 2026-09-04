// Generated from docs/schemas/openapi.json. Do not edit.

export interface Body_upload_resume_api_v1_sessions_resume_post {
  file: string;
}

export interface ExtractionResponse {
  extraction_ok: boolean;
  page_count: number;
  warnings?: unknown;
}

export interface HTTPValidationError {
  detail?: unknown;
}

export interface SessionCreated {
  expires_at: string;
  session_start_date: string;
  token: string;
}

export interface SessionDeleted {
  discarded: boolean;
}

export interface ValidationError {
  loc: unknown;
  msg: string;
  type: string;
}
