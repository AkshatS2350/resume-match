"use client";

import React, { useEffect, useState } from "react";

import { ConfirmProfileDialog } from "../../components/ConfirmProfileDialog";
import { ProfileSectionEditor, profileSections, type ProfileSection, type ReviewItem } from "../../components/ProfileSectionEditor";

const reviewStorageKey = "resumematch.profile.review";

type ReviewDraft = Record<ProfileSection, ReviewItem[]>;

function emptyDraft(): ReviewDraft {
  return {
    skills: [],
    experience: [],
    education: [],
    projects: [],
    certifications: [],
    achievements: [],
    unclassified: []
  };
}

function ProfileReviewPage() {
  const [draft, setDraft] = useState<ReviewDraft>(emptyDraft);
  const [confirmed, setConfirmed] = useState(false);

  useEffect(() => {
    const saved = window.sessionStorage.getItem(reviewStorageKey);
    if (saved === null) {
      return;
    }
    const parsed: unknown = JSON.parse(saved);
    if (typeof parsed === "object" && parsed !== null) {
      setDraft(parsed as ReviewDraft);
    }
  }, []);

  useEffect(() => {
    window.sessionStorage.setItem(reviewStorageKey, JSON.stringify(draft));
  }, [draft]);

  return (
    <main>
      <h1>Review your profile</h1>
      <p>Corrections are held in session-scoped browser storage.</p>
      {profileSections.map((section) => (
        <ProfileSectionEditor
          key={section}
          section={section}
          items={draft[section]}
          onChange={(items) => setDraft((current) => ({ ...current, [section]: items }))}
        />
      ))}
      <ConfirmProfileDialog
        experience={draft.experience}
        onConfirm={() => setConfirmed(true)}
        skills={draft.skills}
      />
      {confirmed ? <p role="status">Profile confirmation is ready to continue.</p> : null}
    </main>
  );
}

export default ProfileReviewPage;
