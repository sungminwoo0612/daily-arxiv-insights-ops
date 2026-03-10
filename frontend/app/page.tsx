"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Source {
  title: string;
  url: string;
  date: string;
}

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  sources?: Source[];
}

interface DigestEntry {
  paper_id: string;
  title: string;
  source_url: string;
  published_date: string;
  score: number;
  why_it_matters: string;
  relation_to_interests: string;
  read_next: string;
  topics: string[];
}

interface Digest {
  date: string;
  generated_at: string;
  summary: string;
  profile_focus: string[];
  entries: DigestEntry[];
}

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ResearchCopilotPage() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingDigest, setLoadingDigest] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);

  const loadDigest = () => {
    setLoadingDigest(true);
    void (async () => {
      try {
        const response = await fetch(`${apiUrl}/digest/latest`);
        if (!response.ok) {
          throw new Error("digest fetch failed");
        }
        const data = await response.json();
        setDigest(data);
      } catch {
        setDigest(null);
      } finally {
        setLoadingDigest(false);
      }
    })();
  };

  useEffect(() => {
    setLoadingDigest(true);
    void (async () => {
      try {
        const response = await fetch(`${apiUrl}/digest/latest`);
        if (!response.ok) {
          throw new Error("digest fetch failed");
        }
        const data = await response.json();
        setDigest(data);
      } catch {
        setDigest(null);
      } finally {
        setLoadingDigest(false);
      }
    })();
  }, []);

  const refreshResearch = () => {
    setLoadingDigest(true);
    void (async () => {
      try {
        await fetch(`${apiUrl}/research/refresh`, { method: "POST" });
        const response = await fetch(`${apiUrl}/digest/latest`);
        if (!response.ok) {
          throw new Error("digest fetch failed");
        }
        const data = await response.json();
        setDigest(data);
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            role: "system",
            content: "라이브러리 새로고침에 실패했습니다. 백엔드 상태와 API 키를 확인하세요.",
          },
        ]);
      } finally {
        setLoadingDigest(false);
      }
    })();
  };

  const handleAsk = () => {
    if (!query.trim()) {
      return;
    }

    const currentQuery = query;
    setMessages((prev) => [...prev, { role: "user", content: currentQuery }]);
    setQuery("");

    setLoadingChat(true);
    void (async () => {
      try {
        const response = await fetch(`${apiUrl}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: currentQuery }),
        });

        if (!response.ok) {
          throw new Error("chat failed");
        }

        const data = await response.json();
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.answer,
            sources: data.sources,
          },
        ]);
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            role: "system",
            content: "질의응답 호출에 실패했습니다. 먼저 연구 라이브러리를 새로고침해 보세요.",
          },
        ]);
      } finally {
        setLoadingChat(false);
      }
    })();
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(14,116,144,0.14),_transparent_35%),linear-gradient(180deg,_#f7fbfc_0%,_#eef6f8_52%,_#f8fbfd_100%)] px-4 py-8 text-slate-950">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <section className="overflow-hidden rounded-[2rem] border border-slate-200/80 bg-white/85 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur">
          <div className="grid gap-6 px-6 py-8 md:grid-cols-[1.6fr_0.9fr] md:px-8">
            <div className="space-y-4">
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-700">
                Research Copilot
              </p>
              <h1 className="max-w-3xl text-3xl font-semibold tracking-tight text-slate-950 md:text-5xl">
                Daily digest first, grounded Q&A second.
              </h1>
              <p className="max-w-2xl text-sm leading-7 text-slate-600 md:text-base">
                Khoj의 second-brain 검색, OpenPaper의 paper-library UX, autoresearch의 research program
                아이디어를 반영해 개인 연구 메모 중심으로 정렬한 화면입니다.
              </p>
              <div className="flex flex-wrap gap-2">
                {(digest?.profile_focus || ["retrieval augmented generation", "agentic workflows"]).map((focus) => (
                  <span
                    key={focus}
                    className="rounded-full border border-cyan-200 bg-cyan-50 px-3 py-1 text-xs font-medium text-cyan-900"
                  >
                    {focus}
                  </span>
                ))}
              </div>
            </div>

            <Card className="border-slate-200/80 bg-slate-950 text-slate-50 shadow-none">
              <CardHeader>
                <CardTitle className="text-lg">Today&apos;s Loop</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm text-slate-300">
                <p>{digest?.summary || "저장된 다이제스트가 없습니다. 라이브러리를 새로고침해 첫 번째 메모를 생성하세요."}</p>
                <div className="flex flex-col gap-2">
                  <Button
                    onClick={refreshResearch}
                    disabled={loadingDigest}
                    className="bg-cyan-500 text-slate-950 hover:bg-cyan-400"
                  >
                    {loadingDigest ? "Refreshing..." : "Refresh Library"}
                  </Button>
                  <Button variant="outline" onClick={loadDigest} disabled={loadingDigest} className="border-slate-700 bg-transparent text-slate-50 hover:bg-slate-900">
                    Reload Digest
                  </Button>
                </div>
                <p className="text-xs text-slate-400">
                  Digest date: {digest?.date || "N/A"} / generated {digest?.generated_at?.split("T")[0] || "N/A"}
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <Card className="border-slate-200/80 bg-white/85 shadow-[0_20px_70px_rgba(15,23,42,0.06)]">
            <CardHeader className="border-b border-slate-100">
              <CardTitle className="text-xl">Priority Papers</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                {(digest?.entries || []).map((entry) => (
                  <article key={entry.paper_id} className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-slate-950 px-2.5 py-1 text-[11px] font-semibold text-white">
                        Score {entry.score.toFixed(2)}
                      </span>
                      {entry.topics.slice(0, 3).map((topic) => (
                        <span key={topic} className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] text-slate-600">
                          {topic}
                        </span>
                      ))}
                    </div>
                    <h2 className="mt-3 text-lg font-semibold text-slate-950">{entry.title}</h2>
                    <p className="mt-2 text-sm leading-6 text-slate-600">{entry.why_it_matters}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-500">{entry.relation_to_interests}</p>
                    <p className="mt-3 text-sm font-medium text-slate-700">Read next: {entry.read_next}</p>
                    <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
                      <span>{entry.published_date.split("T")[0]}</span>
                      <a
                        href={entry.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-medium text-cyan-700 hover:text-cyan-900"
                      >
                        Open paper
                      </a>
                    </div>
                  </article>
                ))}
                {!digest?.entries?.length && (
                  <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-8 text-sm text-slate-500">
                    아직 정렬된 논문이 없습니다. `Refresh Library`로 수집과 노트 생성을 먼저 실행하세요.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200/80 bg-white/85 shadow-[0_20px_70px_rgba(15,23,42,0.06)]">
            <CardHeader className="border-b border-slate-100">
              <CardTitle className="text-xl">Ask Your Library</CardTitle>
            </CardHeader>
            <CardContent className="flex h-[720px] flex-col gap-4 pt-6">
              <ScrollArea className="flex-1 pr-4">
                <div className="space-y-4">
                  {messages.length === 0 && (
                    <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm leading-6 text-slate-500">
                      예시 질문: &quot;이번 주 RAG 논문에서 retrieval quality를 어떻게 평가하나?&quot;
                    </div>
                  )}
                  {messages.map((message, index) => (
                    <div key={`${message.role}-${index}`} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div
                        className={`max-w-[92%] rounded-3xl p-4 text-sm leading-6 shadow-sm ${
                          message.role === "user"
                            ? "bg-slate-950 text-white"
                            : message.role === "assistant"
                              ? "border border-slate-200 bg-white text-slate-900"
                              : "border border-amber-200 bg-amber-50 text-amber-900"
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{message.content}</p>
                        {message.sources && message.sources.length > 0 && (
                          <div className="mt-4 border-t border-slate-100 pt-3 text-xs text-slate-500">
                            {message.sources.map((source, idx) => (
                              <a
                                key={`${source.url}-${idx}`}
                                href={source.url}
                                target="_blank"
                                rel="noreferrer"
                                className="block py-1 text-cyan-700 hover:text-cyan-900"
                              >
                                [{idx + 1}] {source.title} ({source.date.split("T")[0]})
                              </a>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {loadingChat && <div className="text-sm text-slate-500">Research memory를 조회하고 있습니다...</div>}
                </div>
              </ScrollArea>

              <div className="flex gap-2">
                <Input
                  placeholder="질문을 입력하면 저장된 연구 메모를 먼저 조회합니다."
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  onKeyDown={(event) => event.key === "Enter" && handleAsk()}
                  className="h-12 border-slate-200 bg-white"
                />
                <Button onClick={handleAsk} disabled={loadingChat} className="h-12 px-5">
                  Ask
                </Button>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  );
}
