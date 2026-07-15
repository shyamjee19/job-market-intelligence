import { AlertTriangle, Send, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { sendChatMessage } from "../api/client";
import { PageTransition } from "../components/PageTransition";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import type { ChatSource } from "../types";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
}

const SUGGESTED_PROMPTS = [
  "What skills are trending in these job postings?",
  "Which companies are hiring backend engineers?",
  "Tell me about remote Python jobs.",
  "What's a typical salary range for data roles here?",
];

export function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(text: string) {
    const message = text.trim();
    if (!message || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage(message, conversationId);
      setConversationId(response.conversation_id);
      setMessages((prev) => [...prev, { role: "assistant", content: response.answer, sources: response.sources }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get a response");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageTransition>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 flex flex-col" style={{ minHeight: "calc(100vh - 60px)" }}>
        <div className="mb-6">
          <h1 className="text-2xl font-semibold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
            <Sparkles size={22} style={{ color: "var(--series-violet)" }} />
            AI Assistant
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
            Ask about jobs, skills, companies, or salaries — answers are grounded in the postings in this database,
            with sources cited below each answer.
          </p>
        </div>

        <div className="flex-1 flex flex-col gap-4 mb-4">
          {messages.length === 0 && (
            <Card className="p-5">
              <p className="text-sm mb-3" style={{ color: "var(--text-secondary)" }}>
                Try asking:
              </p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => send(prompt)}
                    className="text-left text-sm rounded-lg px-3 py-2 transition-colors duration-150"
                    style={{ background: "var(--surface-2)", color: "var(--text-primary)" }}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </Card>
          )}

          {messages.map((message, index) => (
            <div key={index} className={message.role === "user" ? "flex justify-end" : "flex justify-start"}>
              <div
                className="rounded-xl px-4 py-2.5 max-w-[85%] text-sm leading-relaxed"
                style={
                  message.role === "user"
                    ? { background: "var(--series-blue)", color: "#fff" }
                    : { background: "var(--surface-1)", border: "1px solid var(--border)", color: "var(--text-primary)" }
                }
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-2.5 pt-2.5 flex flex-wrap gap-1.5" style={{ borderTop: "1px solid var(--border)" }}>
                    {message.sources.map((source) => (
                      <span
                        key={source.job_id}
                        className="text-xs rounded-full px-2 py-0.5"
                        style={{ background: "var(--surface-2)", color: "var(--text-secondary)" }}
                        title={`Similarity: ${(source.score * 100).toFixed(0)}%`}
                      >
                        {source.position ?? "Untitled"} · {source.company ?? "Unknown"}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div
                className="rounded-xl px-4 py-2.5 text-sm"
                style={{ background: "var(--surface-1)", border: "1px solid var(--border)", color: "var(--text-muted)" }}
              >
                Thinking…
              </div>
            </div>
          )}

          {error && (
            <Card className="flex items-center gap-2 p-3">
              <AlertTriangle size={16} style={{ color: "var(--status-critical)" }} />
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {error}
              </p>
            </Card>
          )}

          <div ref={scrollRef} />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="flex gap-2 sticky bottom-4"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about jobs, skills, companies, salaries…"
            className="flex-1 rounded-lg text-sm px-3.5 py-2.5 outline-none"
            style={{ background: "var(--surface-1)", border: "1px solid var(--border)", color: "var(--text-primary)" }}
          />
          <Button type="submit" variant="primary" disabled={loading || !input.trim()}>
            <Send size={15} />
          </Button>
        </form>
      </div>
    </PageTransition>
  );
}
