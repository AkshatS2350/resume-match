"use client";

import React, { useEffect, useState } from "react";

export const profileSections = [
  "skills",
  "experience",
  "education",
  "projects",
  "certifications",
  "achievements",
  "unclassified"
] as const;

export type ProfileSection = (typeof profileSections)[number];

export type ReviewItem = {
  id: string;
  text: string;
  sourceText: string;
  extractionConfidence: number;
  title?: string;
  startDate?: string;
  endDate?: string;
};

type ProfileSectionEditorProps = {
  section: ProfileSection;
  items: ReviewItem[];
  onChange: (items: ReviewItem[]) => void;
};

function durationMonths(startDate: string | undefined, endDate: string | undefined): number | null {
  if (!startDate || !endDate) {
    return null;
  }
  const [startYear, startMonth] = startDate.split("-").map(Number);
  const [endYear, endMonth] = endDate.split("-").map(Number);
  if (!startYear || !startMonth || !endYear || !endMonth) {
    return null;
  }
  const duration = (endYear - startYear) * 12 + endMonth - startMonth;
  return duration >= 0 ? duration : null;
}

function emptyItem(section: ProfileSection, position: number): ReviewItem {
  return {
    id: `${section}-${position + 1}`,
    text: "",
    sourceText: "",
    extractionConfidence: 1,
    ...(section === "experience" ? { title: "", startDate: "", endDate: "" } : {})
  };
}

export function ProfileSectionEditor({ section, items, onChange }: ProfileSectionEditorProps) {
  const [draftItems, setDraftItems] = useState(items);

  useEffect(() => {
    setDraftItems(items);
  }, [items]);

  function update(next: ReviewItem[]) {
    setDraftItems(next);
    onChange(next);
  }

  function edit(index: number, field: keyof ReviewItem, value: string) {
    update(draftItems.map((item, itemIndex) => (itemIndex === index ? { ...item, [field]: value } : item)));
  }

  return (
    <section aria-label={`${section} review section`}>
      <h2>{section}</h2>
      {draftItems.map((item, index) => {
        const itemNumber = index + 1;
        const duration = durationMonths(item.startDate, item.endDate);
        return (
          <fieldset key={item.id}>
            <legend>{`${section} item ${itemNumber}`}</legend>
            <label>
              {section === "experience" ? "Title" : "Value"}
              <input
                aria-label={`${section} item ${itemNumber}`}
                value={section === "experience" ? item.title ?? "" : item.text}
                onChange={(event) => edit(index, section === "experience" ? "title" : "text", event.target.value)}
              />
            </label>
            {section === "experience" ? (
              <>
                <label>
                  Start date
                  <input
                    aria-label={`experience start date ${itemNumber}`}
                    type="month"
                    value={item.startDate ?? ""}
                    onChange={(event) => edit(index, "startDate", event.target.value)}
                  />
                </label>
                <label>
                  End date
                  <input
                    aria-label={`experience end date ${itemNumber}`}
                    type="month"
                    value={item.endDate ?? ""}
                    onChange={(event) => edit(index, "endDate", event.target.value)}
                  />
                </label>
                <p>{duration === null ? "Duration: unavailable" : `Duration: ${duration} months`}</p>
              </>
            ) : null}
            {item.extractionConfidence < 0.6 ? (
              <p>
                <strong>Needs review</strong>: {item.sourceText}
              </p>
            ) : null}
            <button type="button" onClick={() => update(draftItems.filter((_, itemIndex) => itemIndex !== index))}>
              {`Remove ${section} item ${itemNumber}`}
            </button>
          </fieldset>
        );
      })}
      <button type="button" onClick={() => update([...draftItems, emptyItem(section, draftItems.length)])}>
        {`Add ${section} item`}
      </button>
    </section>
  );
}
