"use client";

import React from "react";

type UploadPanelProps = { errorCode?: string };

export function UploadPanel({ errorCode }: UploadPanelProps) {
  const isScan = errorCode === "SCANNED_PDF_UNSUPPORTED" || errorCode === "SCANNED_PDF_PARTIAL";
  return (
    <section aria-label="Resume upload">
      <p>Upload a PDF or DOCX file. Maximum size: 10 MB.</p>
      <input aria-label="Resume file" type="file" accept="application/pdf,.docx" />
      {isScan ? (
        <p role="alert">
          Your file appears to be a scan or image. OCR is not supported; upload a text-based PDF or
          DOCX.
        </p>
      ) : null}
    </section>
  );
}
