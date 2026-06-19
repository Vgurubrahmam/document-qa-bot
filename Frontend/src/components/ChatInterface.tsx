import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { ChatMessage } from "@/components/ChatMessage";
import { queryDocuments } from "@/lib/api";
import { Send, Loader2, MessageSquare } from "lucide-react";
import type { ChatMessage as ChatMessageType } from "@/types";

interface ChatInterfaceProps {
  documentCount: number;
}

/**
 * Main chat interface with message list, input area, and send button.
 * Shows an empty state when no documents are ingested.
 * Auto-scrolls to the latest message.
 */
export function ChatInterface({ documentCount }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [input, setInput] = useState("");
  const [isQuerying, setIsQuerying] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const question = input.trim();
    if (!question || isQuerying) return;

    // Add user message
    const userMessage: ChatMessageType = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
      timestamp: new Date(),
    };

    // Add loading placeholder for assistant
    const loadingMessage: ChatMessageType = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages((prev) => [...prev, userMessage, loadingMessage]);
    setInput("");
    setIsQuerying(true);

    try {
      const result = await queryDocuments(question);

      // Replace loading message with actual response
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === loadingMessage.id
            ? {
                ...msg,
                content: result.answer,
                sources: result.sources,
                isLoading: false,
              }
            : msg
        )
      );
    } catch (error) {
      // Replace loading message with error
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === loadingMessage.id
            ? {
                ...msg,
                content: `Error: ${
                  error instanceof Error ? error.message : "Something went wrong"
                }. Please try again.`,
                isLoading: false,
              }
            : msg
        )
      );
    } finally {
      setIsQuerying(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isEmpty = documentCount === 0;

  return (
    <Card className="flex flex-col h-[500px] sm:h-[600px]">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <MessageSquare className="h-5 w-5" />
          Chat
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col min-h-0 gap-3">
        {/* Messages area */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {isEmpty ? (
            /* Empty state */
            <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
              <MessageSquare className="h-12 w-12 mb-3 opacity-30" />
              <p className="font-medium">No documents ingested yet</p>
              <p className="text-sm mt-1">
                Upload and ingest documents above to start asking questions.
              </p>
            </div>
          ) : messages.length === 0 ? (
            /* Ready state */
            <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
              <MessageSquare className="h-12 w-12 mb-3 opacity-30" />
              <p className="font-medium">Ready to answer your questions</p>
              <p className="text-sm mt-1">
                {documentCount} chunk{documentCount !== 1 ? "s" : ""} loaded.
                Ask anything about your documents.
              </p>
            </div>
          ) : (
            /* Messages */
            messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                role={msg.role}
                content={msg.content}
                sources={msg.sources}
                isLoading={msg.isLoading}
              />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="flex gap-2 pt-2 border-t">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isEmpty
                ? "Ingest documents first..."
                : "Ask a question about your documents..."
            }
            disabled={isEmpty || isQuerying}
            className="flex-1 h-10 rounded-md border border-input bg-background px-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Question input"
          />
          <Button
            onClick={handleSend}
            disabled={isEmpty || !input.trim() || isQuerying}
            size="default"
            aria-label="Send question"
          >
            {isQuerying ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
