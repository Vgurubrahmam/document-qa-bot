import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Upload, FileUp, Loader2, Trash2, AlertCircle, CheckCircle2 } from "lucide-react";
import { uploadDocuments, ingestDocuments, resetDatabase } from "@/lib/api";

interface DocumentUploadProps {
  onStatusChange: () => void;
  status: "idle" | "uploading" | "ingesting";
  onStatusUpdate: (status: "idle" | "uploading" | "ingesting") => void;
}

/**
 * Document upload section with drag & drop, file picker,
 * ingest button, and reset functionality.
 */
export function DocumentUpload({
  onStatusChange,
  status,
  onStatusUpdate,
}: DocumentUploadProps) {
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles(e.target.files);
      setMessage(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFiles(e.dataTransfer.files);
      setMessage(null);
    }
  };

  const handleUploadAndIngest = async () => {
    if (!selectedFiles) return;

    try {
      // Upload files
      onStatusUpdate("uploading");
      setMessage(null);
      const uploadResult = await uploadDocuments(selectedFiles);
      setMessage({ type: "success", text: uploadResult.message });

      // Ingest documents
      onStatusUpdate("ingesting");
      const ingestResult = await ingestDocuments();
      setMessage({ type: "success", text: ingestResult.message });

      // Reset state
      setSelectedFiles(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      onStatusChange();
    } catch (error) {
      setMessage({
        type: "error",
        text: error instanceof Error ? error.message : "An error occurred",
      });
    } finally {
      onStatusUpdate("idle");
    }
  };

  const handleReset = async () => {
    try {
      const result = await resetDatabase();
      setMessage({ type: "success", text: result.message });
      setSelectedFiles(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      onStatusChange();
    } catch (error) {
      setMessage({
        type: "error",
        text: error instanceof Error ? error.message : "Reset failed",
      });
    }
  };

  const isProcessing = status === "uploading" || status === "ingesting";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Upload className="h-5 w-5" />
          Upload Documents
        </CardTitle>
        <CardDescription>
          Upload PDF, DOCX, or TXT files to build your knowledge base.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Drop zone */}
        <div
          role="button"
          tabIndex={0}
          aria-label="Drop files here or click to browse"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              fileInputRef.current?.click();
            }
          }}
          className={`border-2 border-dashed rounded-lg p-6 sm:p-8 text-center cursor-pointer transition-colors ${
            isDragOver
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-primary/50"
          }`}
        >
          <FileUp className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            Drag & drop files here, or{" "}
            <span className="text-primary font-medium">click to browse</span>
          </p>
          <div className="flex justify-center gap-2 mt-2">
            <Badge variant="outline">PDF</Badge>
            <Badge variant="outline">DOCX</Badge>
            <Badge variant="outline">TXT</Badge>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx,.txt"
            onChange={handleFileSelect}
            className="hidden"
            aria-label="Select documents to upload"
          />
        </div>

        {/* Selected files list */}
        {selectedFiles && (
          <div className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">
              {selectedFiles.length} file{selectedFiles.length !== 1 ? "s" : ""}{" "}
              selected:
            </span>{" "}
            {Array.from(selectedFiles)
              .map((f) => f.name)
              .join(", ")}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex flex-col sm:flex-row gap-2">
          <Button
            onClick={handleUploadAndIngest}
            disabled={!selectedFiles || isProcessing}
            className="flex-1"
          >
            {isProcessing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                {status === "uploading" ? "Uploading..." : "Ingesting..."}
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" />
                Upload & Ingest
              </>
            )}
          </Button>
          <Button
            variant="outline"
            onClick={handleReset}
            disabled={isProcessing}
            size="default"
          >
            <Trash2 className="h-4 w-4" />
            <span className="sm:inline">Reset</span>
          </Button>
        </div>

        {/* Status messages */}
        {message && (
          <Alert variant={message.type === "error" ? "destructive" : "default"}>
            {message.type === "error" ? (
              <AlertCircle className="h-4 w-4" />
            ) : (
              <CheckCircle2 className="h-4 w-4" />
            )}
            <AlertDescription>{message.text}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
