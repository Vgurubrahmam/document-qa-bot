import { Badge } from "@/components/ui/badge";
import { FileText, Database } from "lucide-react";

interface HeaderProps {
  documentCount: number;
  fileCount: number;
}

/**
 * App header with branding and status indicators.
 * Shows the number of document chunks and uploaded files.
 */
export function Header({ documentCount, fileCount }: HeaderProps) {
  return (
    <header className="border-b bg-card">
      <div className="mx-auto max-w-4xl px-4 py-4 flex items-center justify-between">
        {/* Branding */}
        <div className="flex items-center gap-2">
          <FileText className="h-6 w-6 text-primary" />
          <h1 className="text-lg sm:text-xl font-bold">Document Q&A Bot</h1>
        </div>

        {/* Status badges */}
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="hidden sm:flex items-center gap-1">
            <FileText className="h-3 w-3" />
            {fileCount} file{fileCount !== 1 ? "s" : ""}
          </Badge>
          <Badge
            variant={documentCount > 0 ? "default" : "secondary"}
            className="flex items-center gap-1"
          >
            <Database className="h-3 w-3" />
            {documentCount} chunk{documentCount !== 1 ? "s" : ""}
          </Badge>
        </div>
      </div>
    </header>
  );
}
