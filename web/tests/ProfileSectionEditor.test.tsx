import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ProfileReviewPage from "../src/app/review/page";
import { ProfileSectionEditor, type ReviewItem } from "../src/components/ProfileSectionEditor";

const experience: ReviewItem = {
  id: "experience-1",
  text: "Engineer",
  sourceText: "Engineer, Jan 2024 - Apr 2024",
  extractionConfidence: 0.59,
  startDate: "2024-01",
  endDate: "2024-04"
};

describe("ProfileSectionEditor", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(cleanup);

  it("provides add, edit, and remove controls for every section including unclassified", () => {
    const sections = ["skills", "experience", "education", "projects", "certifications", "achievements", "unclassified"] as const;

    render(
      <>
        {sections.map((section) => (
          <ProfileSectionEditor key={section} section={section} items={[]} onChange={() => undefined} />
        ))}
      </>
    );

    for (const section of sections) {
      expect(screen.getByRole("button", { name: `Add ${section} item` })).toBeTruthy();
    }
  });

  it("shows needs-review source text below the confidence threshold", () => {
    render(<ProfileSectionEditor section="experience" items={[experience]} onChange={() => undefined} />);

    expect(screen.getByText("Needs review")).toBeTruthy();
    expect(screen.getByText(experience.sourceText, { exact: false, selector: "p" })).toBeTruthy();
  });

  it("recomputes the displayed experience duration without a server round trip", () => {
    render(<ProfileSectionEditor section="experience" items={[experience]} onChange={() => undefined} />);

    expect(screen.getByText("Duration: 3 months")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("experience end date 1"), { target: { value: "2024-06" } });

    expect(screen.getByText("Duration: 5 months")).toBeTruthy();
  });

  it("writes review state only to session-scoped browser storage", () => {
    const localStorageSetItem = vi.spyOn(window.localStorage, "setItem");
    render(<ProfileReviewPage />);

    fireEvent.click(screen.getByRole("button", { name: "Add skills item" }));

    expect(window.sessionStorage.getItem("resumematch.profile.review")).not.toBeNull();
    expect(localStorageSetItem).not.toHaveBeenCalled();
    expect(screen.getByText("Corrections are held in session-scoped browser storage.")).toBeTruthy();
  });
});
