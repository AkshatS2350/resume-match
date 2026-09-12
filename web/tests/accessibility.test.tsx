import "@testing-library/jest-dom/vitest";
import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { UploadPanel } from "../src/components/UploadPanel";

afterEach(cleanup);

describe("accessibility announcements", () => {
  it("announces upload validation guidance through a live error region", () => {
    render(<UploadPanel errorCode="SCANNED_PDF_UNSUPPORTED" />);

    expect(screen.getByRole("alert")).toHaveTextContent(/OCR is not supported/i);
  });

  it("keeps the upload control labelled without exposing file contents", () => {
    render(<UploadPanel />);

    expect(screen.getByLabelText("Resume file")).toHaveAttribute("type", "file");
  });
});
