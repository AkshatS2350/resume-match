"use client";

import React, { useEffect, useState } from "react";

type ProjectedField = {
  path: string;
  value: unknown;
};

type Omission = {
  path: string;
  reason: "not_required_by_operation" | "omitted_for_budget";
};

type PendingRequest = {
  request_id: string;
  operation: string;
  fields: ProjectedField[];
  payload_hash: string;
  provider_identity: string;
  provider_locality: string;
  admitted_at: string;
  omissions: Omission[];
};

const pendingRequestEndpoint = "/api/v1/sessions/llm-requests/pending";

export function PendingRequestView() {
  const [pending, setPending] = useState<PendingRequest | null>(null);
  const [showPayload, setShowPayload] = useState(false);

  useEffect(() => {
    void fetch(pendingRequestEndpoint)
      .then(async (response) => (response.ok ? (response.json() as Promise<PendingRequest>) : null))
      .then(setPending)
      .catch(() => setPending(null));
  }, []);

  return (
    <section aria-labelledby="pending-request-heading">
      <h2 id="pending-request-heading">What will be sent</h2>
      {pending === null ? (
        <p role="status">No pending cloud request is available for this session.</p>
      ) : (
        <>
          <p>This is the pending cloud request payload. It is not the complete session profile.</p>
          <p>Provider: {pending.provider_identity}</p>
          <p>Locality: {pending.provider_locality}</p>
          <h3>Included field paths</h3>
          <ul>
            {pending.fields.map((field) => (
              <li key={field.path}>{field.path}</li>
            ))}
          </ul>
          <h3>Omitted field paths</h3>
          <ul>
            {pending.omissions.map((omission) => (
              <li key={omission.path}>{omission.path}: {omission.reason}</li>
            ))}
          </ul>
          <button
            type="button"
            aria-expanded={showPayload}
            onClick={() => setShowPayload((visible) => !visible)}
          >
            {showPayload ? "Hide complete projected payload" : "Show complete projected payload"}
          </button>
          {showPayload ? <pre aria-label="Complete projected payload">{JSON.stringify(pending.fields)}</pre> : null}
        </>
      )}
    </section>
  );
}
