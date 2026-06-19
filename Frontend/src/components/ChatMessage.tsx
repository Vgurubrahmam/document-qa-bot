import type { Source } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Bot, User, FileText, Loader2 } from "lucide-react";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  isLoading?: boolean;
}

/**
 * A single chat message bubble.
 * User messages are right-aligned, assistant messages are left-aligned.
 * Assistant messages can include source citations.
 */
export function ChatMessage({
  role,
  content,
  sources,
  isLoading,
}: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
      role="article"
      aria-label={`${isUser ? "Your" : "Assistant"} message`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-muted-foreground"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Message content */}
      <div
        className={`max-w-[85%] sm:max-w-[75%] space-y-2 ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-md"
              : "bg-muted rounded-tl-md"
          }`}
        >
          {isLoading ? (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Thinking...
            </div>
          ) : (
            <p className="whitespace-pre-wrap">{content}</p>
          )}
        </div>

        {/* Source citations */}
        {sources && sources.length > 0 && (
          <div className="flex flex-wrap gap-1.5 px-1">
            {sources.map((source) => (
              <Badge
                key={`${source.file}-${source.chunk_index}`}
                variant="outline"
                className="text-xs flex items-center gap-1"
              >
                <FileText className="h-3 w-3" />
                <span className="hidden sm:inline">{source.file}</span>
                <span className="sm:hidden">
                  Source {source.source_number}
                </span>
                <span className="text-muted-foreground">
                  (chunk {source.chunk_index})
                </span>
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
