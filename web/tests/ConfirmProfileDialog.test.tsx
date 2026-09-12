import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConfirmProfileDialog } from "../src/components/ConfirmProfileDialog";
import type { ReviewItem } from "../src/components/ProfileSectionEditor";

afterEach(cleanup);

const meaningfulSkill: ReviewItem = {
  id: "skill-1",
  text: "Python",
  sourceText: "Private source resume text",
  extractionConfidence: 1
};

describe("ConfirmProfileDialog", () => {
  it("blocks empty-profile confirmation until the warning is explicitly acknowledged", () => {
    const onConfirm = vi.fn();
    render(<ConfirmProfileDialog skills={[]} experience={[]} onConfirm={onConfirm} />);

    fireEvent.click(screen.getByRole("button", { name: "Confirm profile" }));

    expect(screen.getByRole("dialog", { name: "Empty profile warning" })).toBeTruthy();
    expect(screen.getByText(/near-zero readiness result/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Confirm empty profile" }).hasAttribute("disabled")).toBe(true);
    expect(onConfirm).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("checkbox", { name: /understand/i }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm empty profile" }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("does not warn when meaningful skills or experience exists", () => {
    const onConfirm = vi.fn();
    render(<ConfirmProfileDialog skills={[meaningfulSkill]} experience={[]} onConfirm={onConfirm} />);

    fireEvent.click(screen.getByRole("button", { name: "Confirm profile" }));

    expect(screen.queryByRole("dialog", { name: "Empty profile warning" })).toBeNull();
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(screen.queryByText("Private source resume text")).toBeNull();
  });
});
