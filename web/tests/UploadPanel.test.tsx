import "@testing-library/jest-dom/vitest";
import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { UploadPanel } from "../src/components/UploadPanel";

describe("UploadPanel", () => {
  afterEach(cleanup);
  it("discloses both formats and the size limit before selection", () => {
    render(<UploadPanel />);
    expect(screen.getByText(/PDF or DOCX/i)).toBeInTheDocument();
    expect(screen.getByText(/10 MB/i)).toBeInTheDocument();
  });

  it.each(["SCANNED_PDF_UNSUPPORTED", "SCANNED_PDF_PARTIAL"])(
    "shows safe scan guidance for %s",
    (errorCode) => {
      render(<UploadPanel errorCode={errorCode} />);
      expect(screen.getByText(/scan.*OCR.*text-based/i)).toBeInTheDocument();
    }
  );
});
