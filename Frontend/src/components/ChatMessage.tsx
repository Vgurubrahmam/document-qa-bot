import type { Source } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Bot, User, FileText, Loader2, ChevronDown } from "lucide-react";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  isLoading?: boolean;
}

/**
 * Parses markdown into structured H2 sections for custom rendering.
 */
function parseMarkdownSections(content: string) {
  const sections: { title: string; body: string }[] = [];
  const regex = /^##\s+(.+)$/gm;

  let match;
  const headers: { title: string; index: number }[] = [];
  while ((match = regex.exec(content)) !== null) {
    headers.push({
      title: match[1].trim(),
      index: match.index,
    });
  }

  if (headers.length === 0) {
    return [{ title: "Answer", body: content }];
  }

  for (let i = 0; i < headers.length; i++) {
    const nextNewline = content.indexOf("\n", headers[i].index);
    const start = nextNewline !== -1 ? nextNewline + 1 : headers[i].index;
    const end = i + 1 < headers.length ? headers[i + 1].index : content.length;
    sections.push({
      title: headers[i].title,
      body: content.substring(start, end).trim(),
    });
  }

  return sections;
}

/**
 * Parses bold text (**text**) and inline code (`code`) in strings.
 */
function renderInlineMarkdown(text: string) {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={idx} className="font-semibold text-foreground">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={idx}
          className="bg-muted-foreground/10 px-1.5 py-0.5 rounded text-[11px] font-mono border border-border/30 text-foreground"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

/**
 * Renders paragraphs, lists, and tables.
 */
function FormattedBody({ body }: { body: string }) {
  const blocks = body.split(/\n\n+/);

  return (
    <div className="space-y-3">
      {blocks.map((block, idx) => {
        const trimmed = block.trim();
        if (!trimmed) return null;

        // Bulleted lists
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          const items = trimmed
            .split("\n")
            .map((line) => line.replace(/^[-*]\s+/, "").trim());
          return (
            <ul
              key={idx}
              className="list-disc pl-5 space-y-1.5 text-muted-foreground my-2"
            >
              {items.map((item, itemIdx) => (
                <li key={itemIdx}>{renderInlineMarkdown(item)}</li>
              ))}
            </ul>
          );
        }

        // Tables
        if (trimmed.startsWith("|")) {
          const lines = trimmed
            .split("\n")
            .map((l) => l.trim())
            .filter((l) => l.length > 0);
          if (lines.length >= 2) {
            const isTable = lines[1].includes("-");
            if (isTable) {
              const parseRow = (row: string) => {
                return row
                  .split("|")
                  .map((cell) => cell.trim())
                  .filter(
                    (_, colIdx, arr) => colIdx > 0 && colIdx < arr.length - 1
                  );
              };
              const headers = parseRow(lines[0]);
              const rows = lines.slice(2).map(parseRow);
              return (
                <div
                  key={idx}
                  className="overflow-x-auto my-3 rounded-lg border border-border/60"
                >
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-muted border-b border-border/60">
                        {headers.map((h, hIdx) => (
                          <th
                            key={hIdx}
                            className="px-3 py-2 font-semibold text-foreground"
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/40">
                      {rows.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-muted/30">
                          {row.map((cell, cIdx) => (
                            <td
                              key={cIdx}
                              className="px-3 py-1.8 text-muted-foreground"
                            >
                              {renderInlineMarkdown(cell)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              );
            }
          }
        }

        // Paragraphs
        return (
          <p key={idx} className="text-muted-foreground leading-relaxed">
            {renderInlineMarkdown(block)}
          </p>
        );
      })}
    </div>
  );
}

/**
 * Handles custom formatting for RAG response segments.
 */
function AssistantMessageContent({ content }: { content: string }) {
  const sections = parseMarkdownSections(content);

  return (
    <div className="space-y-4">
      {sections.map((section, index) => {
        const titleLower = section.title.toLowerCase();

        // Check if this section should be collapsible
        const isCollapsible =
          titleLower.includes("details") ||
          titleLower.includes("source") ||
          titleLower.includes("learn");

        if (isCollapsible) {
          return (
            <details
              key={index}
              className="group border border-border/50 rounded-xl px-3 py-2 bg-background/20 hover:bg-background/40 transition-colors my-2"
            >
              <summary className="flex items-center justify-between cursor-pointer font-medium text-foreground list-none select-none">
                <span className="text-[11px] tracking-wide uppercase font-semibold text-foreground/80">
                  {section.title}
                </span>
                <ChevronDown className="h-4 w-4 text-muted-foreground transition-transform group-open:rotate-180" />
              </summary>
              <div className="mt-2 pt-2 border-t border-border/30 text-xs">
                <FormattedBody body={section.body} />
              </div>
            </details>
          );
        }

        return (
          <div key={index} className="space-y-1.5">
            {titleLower !== "answer" && (
              <h4 className="text-[11px] tracking-wide uppercase font-semibold text-foreground/80">
                {section.title}
              </h4>
            )}
            <FormattedBody body={section.body} />
          </div>
        );
      })}
    </div>
  );
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
          ) : isUser ? (
            <p className="whitespace-pre-wrap">{content}</p>
          ) : (
            <AssistantMessageContent content={content} />
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
