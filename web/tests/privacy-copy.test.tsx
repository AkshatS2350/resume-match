import "@testing-library/jest-dom/vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PrivacyNotice } from "../src/components/PrivacyNotice";


describe("PrivacyNotice", () => {
  it("renders the required truthful privacy disclosure without prohibited claims", () => {
    render(<PrivacyNotice />);
    const text = screen.getByLabelText("Privacy notice").textContent ?? "";
    expect(text).toContain("Resume files are not persistently stored by ResumeMatch servers.");
    expect(text).toContain("PII removal reduces risk");
    expect(text).toContain("Employer, institution, and certification names are retained");
    expect(text).not.toMatch(/never leaves the device|anonymous|guaranteed de-identification|no data touches disk/i);
  });
});
