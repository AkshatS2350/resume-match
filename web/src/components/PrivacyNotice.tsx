import React from "react";

import { privacyCopy } from "../content/privacy-copy";

export function PrivacyNotice() {
  return (
    <aside aria-label="Privacy notice">
      <p>{privacyCopy.guarantee}</p>
      <p>{privacyCopy.riskReduction}</p>
      <p>{privacyCopy.retention}</p>
    </aside>
  );
}
