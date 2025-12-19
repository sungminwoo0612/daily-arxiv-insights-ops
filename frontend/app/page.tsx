"use client"; // 상태 관리를 위해 클라이언트 컴포넌트로 선언

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

// 백엔드 응답 데이터 타입 정의
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

export default function ChatPage() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    const userMessage: Message = { role: "user", content: query };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setQuery("");

    try {
      // compose.yml에 정의된 환경변수를 사용하여 API 호출
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      
      const res = await fetch(`${apiUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) throw new Error("API 요청 실패");

      const data = await res.json();

      // AI 답변과 출처 정보를 메시지 리스트에 추가
      setMessages((prev) => [
        ...prev,
        { 
          role: "assistant", 
          content: data.answer, 
          sources: data.sources 
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "system", content: "서버와 연결할 수 없습니다. CORS 설정이나 백엔드 실행 상태를 확인하세요." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex items-center justify-center min-h-screen bg-slate-50 p-4">
      <Card className="w-full max-w-3xl h-[85vh] flex flex-col shadow-2xl">
        <CardHeader className="border-b">
          <CardTitle>🎓 ArXiv AI Research Assistant</CardTitle>
        </CardHeader>
        
        <CardContent className="flex-1 flex flex-col gap-4 overflow-hidden pt-6">
          <ScrollArea className="flex-1 pr-4">
            <div className="space-y-6">
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`p-4 rounded-2xl max-w-[85%] shadow-sm ${
                    m.role === "user" ? "bg-primary text-primary-foreground" : "bg-white border text-slate-900"
                  }`}>
                    <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
                    
                    {/* 출처(Sources) 표시 로직 */}
                    {m.sources && m.sources.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-100 text-xs">
                        <p className="font-semibold mb-2 text-slate-500 text-uppercase tracking-wider">References</p>
                        <ul className="space-y-1">
                          {m.sources.map((src, idx) => (
                            <li key={idx}>
                              <a href={src.url} target="_blank" className="text-blue-500 hover:underline">
                                [{idx + 1}] {src.title} ({src.date.split("T")[0]})
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && <div className="text-sm text-muted-foreground animate-pulse ml-2">논문을 분석하고 있습니다...</div>}
            </div>
          </ScrollArea>

          <div className="flex gap-2 pb-2">
            <Input 
              placeholder="궁금한 AI 연구 분야를 입력하세요..." 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="py-6"
            />
            <Button onClick={handleSearch} disabled={loading} className="px-6 py-6">Send</Button>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}