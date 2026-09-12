"use client";

import React, { useEffect, useState } from "react";

type SanitizationResult = {
  artifact_label: "session_sanitization_result";
  removed_categories: string[];
  fail_safe_redaction_count: number;
};

const sanitizationResultEndpoint = "/api/v1/sessions/sanitized-resume";

export function SanitizationResultView() {
  const [result, setResult] = useState<SanitizationResult | null>(null);

  useEffect(() => {
    void fetch(sanitizationResultEndpoint)
      .then(async (response) => (response.ok ? (response.json() as Promise<SanitizationResult>) : null))
      .then(setResult)
      .catch(() => setResult(null));
  }, []);

  return (
    <section aria-labelledby="sanitization-result-heading">
      <h2 id="sanitization-result-heading">Sanitization result held in this session</h2>
      {result === null ? (
        <p role="status">No sanitization result is available for this session.</p>
      ) : (
        <>
          <p>This is the sanitization result held in session state. It is not the transmitted payload.</p>
          <h3>Removed categories</h3>
          <ul>
            {result.removed_categories.map((category) => (
              <li key={category}>{category}</li>
            ))}
          </ul>
          <p>Fail-safe redaction count: {result.fail_safe_redaction_count}</p>
        </>
      )}
    </section>
  );
}
