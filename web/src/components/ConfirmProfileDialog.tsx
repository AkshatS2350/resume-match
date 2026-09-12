"use client";

import React, { useState } from "react";

import type { ReviewItem } from "./ProfileSectionEditor";

type ConfirmProfileDialogProps = {
  skills: readonly ReviewItem[];
  experience: readonly ReviewItem[];
  onConfirm: () => void;
};

function hasMeaningfulItem(items: readonly ReviewItem[]): boolean {
  return items.some((item) => Boolean(item.text.trim() || item.title?.trim()));
}

export function ConfirmProfileDialog({ skills, experience, onConfirm }: ConfirmProfileDialogProps) {
  const [warningOpen, setWarningOpen] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);
  const isEmptyProfile = !hasMeaningfulItem(skills) && !hasMeaningfulItem(experience);

  function startConfirmation() {
    if (!isEmptyProfile) {
      onConfirm();
      return;
    }
    setWarningOpen(true);
  }

  function confirmEmptyProfile() {
    if (!acknowledged) {
      return;
    }
    setWarningOpen(false);
    onConfirm();
  }

  return (
    <section aria-label="Profile confirmation">
      <button type="button" onClick={startConfirmation}>
        Confirm profile
      </button>
      {warningOpen ? (
        <div aria-labelledby="empty-profile-warning" aria-modal="true" role="dialog">
          <h2 id="empty-profile-warning">Empty profile warning</h2>
          <p>
            Your profile has no skills or experience. Readiness scoring will produce a near-zero
            readiness result.
          </p>
          <label>
            <input
              checked={acknowledged}
              onChange={(event) => setAcknowledged(event.target.checked)}
              type="checkbox"
            />
            I understand and want to confirm this empty profile.
          </label>
          <button disabled={!acknowledged} onClick={confirmEmptyProfile} type="button">
            Confirm empty profile
          </button>
        </div>
      ) : null}
    </section>
  );
}
