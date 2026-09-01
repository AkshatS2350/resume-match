// Generated from docs/schemas/openapi.json. Do not edit.

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
