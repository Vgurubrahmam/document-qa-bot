/**
 * API Client Module
 * ==================
 * Centralized fetch wrapper for all backend API calls.
 *
 * All API communication goes through this module so:
 *  - The backend URL is defined in one place
 *  - Error handling is consistent
 *  - Types are enforced on every call
 */

import type {
  QueryResponse,
  StatusResponse,
  MessageResponse,
} from "@/types";

// Backend API base URL
const API_BASE = import.meta.env.VITE_API_BASE_URL || "https://document-qa-bot-fh3j.onrender.com";

/**
 * Upload files to the backend data/ directory.
 */
export async function uploadDocuments(
  files: FileList
): Promise<MessageResponse> {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  const response = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Upload failed");
  }

  return response.json();
}

/**
 * Trigger document ingestion (extract → chunk → embed → store).
 */
export async function ingestDocuments(): Promise<MessageResponse> {
  const response = await fetch(`${API_BASE}/api/ingest`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Ingestion failed");
  }

  return response.json();
}

/**
 * Ask a question about the ingested documents.
 */
export async function queryDocuments(
  question: string
): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Query failed");
  }

  return response.json();
}

/**
 * Get the current status of the vector database.
 */
export async function getStatus(): Promise<StatusResponse> {
  const response = await fetch(`${API_BASE}/api/status`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Status check failed");
  }

  return response.json();
}

/**
 * Reset the database and remove all uploaded files.
 */
export async function resetDatabase(): Promise<MessageResponse> {
  const response = await fetch(`${API_BASE}/api/reset`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Reset failed");
  }

  return response.json();
}
