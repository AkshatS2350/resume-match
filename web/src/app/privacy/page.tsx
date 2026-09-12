import React from "react";

import { PendingRequestView } from "../../components/PendingRequestView";
import { SanitizationResultView } from "../../components/SanitizationResultView";

export default function PrivacyInspectorPage() {
  return (
    <main>
      <h1>Privacy Inspector</h1>
      <PendingRequestView />
      <SanitizationResultView />
    </main>
  );
}
