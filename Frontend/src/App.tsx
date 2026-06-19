import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/Header";
import { DocumentUpload } from "@/components/DocumentUpload";
import { ChatInterface } from "@/components/ChatInterface";
import { getStatus } from "@/lib/api";
import type { AppStatus } from "@/types";

/**
 * Main application component.
 *
 * Layout: Single-page with header, upload section, and chat interface.
 * Responsive: Stacked layout on mobile, centered max-width on desktop.
 */
function App() {
  const [documentCount, setDocumentCount] = useState(0);
  const [fileCount, setFileCount] = useState(0);
  const [appStatus, setAppStatus] = useState<AppStatus>("idle");

  // Fetch status from backend
  const fetchStatus = useCallback(async () => {
    try {
      const status = await getStatus();
      setDocumentCount(status.document_count);
      setFileCount(status.files.length);
    } catch {
      // Backend might not be running yet — silently handle
      console.warn("Could not connect to backend API");
    }
  }, []);

  // Fetch status on mount
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return (
    <div className="min-h-screen bg-background">
      <Header documentCount={documentCount} fileCount={fileCount} />

      <main className="mx-auto max-w-4xl px-4 py-6 space-y-6">
        {/* Document upload section */}
        <DocumentUpload
          onStatusChange={fetchStatus}
          status={appStatus === "uploading" ? "uploading" : appStatus === "ingesting" ? "ingesting" : "idle"}
          onStatusUpdate={(s) => setAppStatus(s)}
        />

        {/* Chat interface */}
        <ChatInterface documentCount={documentCount} />
      </main>
    </div>
  );
}

export default App;
