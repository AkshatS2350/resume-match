import "@testing-library/jest-dom/vitest";
import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import PrivacyInspectorPage from "../src/app/privacy/page";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const pendingResponse = {
  request_id: "request-1",
  operation: "bounded_extract",
  fields: [{ path: "/unclassified/0/text", value: "approved sanitized value" }],
  payload_hash: "sha256:abc",
  provider_identity: "configured-provider",
  provider_locality: "cloud",
  admitted_at: "2026-01-01T00:00:00+00:00",
  omissions: [{ path: "/summary", reason: "not_required_by_operation" }]
};

const sanitizationResponse = {
  artifact_label: "session_sanitization_result",
  sanitization_result: {
    resume: { summary: "raw resume text must not be displayed" }
  },
  removed_categories: ["email"],
  fail_safe_redaction_count: 2
};

function response(body: object, ok = true): Response {
  return { ok, json: async () => body } as Response;
}

describe("PrivacyInspectorPage", () => {
  it("keeps the pending transmission and sanitization-result views separate", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/llm-requests/pending")) {
        return Promise.resolve(response(pendingResponse));
      }
      if (url.endsWith("/sanitized-resume")) {
        return Promise.resolve(response(sanitizationResponse));
      }
      return Promise.resolve(response({}, false));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<PrivacyInspectorPage />);

    expect(await screen.findByRole("heading", { name: "Privacy Inspector" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "What will be sent" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Sanitization result held in this session" })
    ).toBeInTheDocument();
    expect(screen.getByText("Provider: configured-provider")).toBeInTheDocument();
    expect(screen.getByText("Locality: cloud")).toBeInTheDocument();
    expect(screen.getByText("/summary: not_required_by_operation")).toBeInTheDocument();
    expect(screen.getByText("email")).toBeInTheDocument();
    expect(screen.getByText("Fail-safe redaction count: 2")).toBeInTheDocument();
    expect(screen.queryByText("raw resume text must not be displayed")).toBeNull();
    expect(screen.queryByText("approved sanitized value")).toBeNull();

    const disclosure = screen.getByRole("button", { name: "Show complete projected payload" });
    expect(disclosure).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(disclosure);
    expect(screen.getByRole("button", { name: "Hide complete projected payload" })).toHaveAttribute(
      "aria-expanded",
      "true"
    );
    expect(screen.getByText(/approved sanitized value/)).toBeInTheDocument();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith("/api/v1/sessions/llm-requests/pending");
      expect(fetchMock).toHaveBeenCalledWith("/api/v1/sessions/sanitized-resume");
    });
  });

  it("renders safe unavailable states instead of backend error details", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(response({ detail: "private failure" }, false))));

    render(<PrivacyInspectorPage />);

    expect(await screen.findByText("No pending cloud request is available for this session.")).toBeInTheDocument();
    expect(screen.getByText("No sanitization result is available for this session.")).toBeInTheDocument();
    expect(screen.queryByText("private failure")).toBeNull();
  });
});
