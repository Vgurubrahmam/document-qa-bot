/**
 * TypeScript interfaces for the Document Q&A Bot API.
 *
 * These types mirror the backend's Pydantic models (api.py)
 * and ensure type safety across the frontend.
 */

// --- API Response Types ---

/** Response from POST /api/query */
export interface QueryResponse {
  answer: string;
  sources: Source[];
  question: string;
}

/** A single cited source in the answer */
export interface Source {
  source_number: number;
  file: string;
  chunk_index: number;
}

/** Response from GET /api/status */
export interface StatusResponse {
  document_count: number;
  files: string[];
}

/** Generic message response from upload/ingest/reset */
export interface MessageResponse {
  message: string;
}

// --- Chat UI Types ---

/** A single message in the chat conversation */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  timestamp: Date;
  isLoading?: boolean;
}

/** Possible states for the app */
export type AppStatus = "idle" | "uploading" | "ingesting" | "querying";
