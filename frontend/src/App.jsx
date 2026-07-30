import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const WELCOME_MESSAGE = "Hello. I am an AI assistant trained on Dr. Khare's CV, publications, and professional background. How can I help you today?";

const LOADING_MESSAGES = [
  "Searching knowledge base...",
  "Retrieving documents...",
  "Analyzing information...",
  "Preparing response..."
];

function LoadingMessage() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="loading-container">
      <span className="loading-text">{LOADING_MESSAGES[index]}</span>
      <span className="dots"><span /><span /><span /></span>
    </div>
  );
}

function App() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: WELCOME_MESSAGE }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(() => localStorage.getItem("session_khare") || "");
  const [remainingQuestions, setRemainingQuestions] = useState(null);
  const [resetInSeconds, setResetInSeconds] = useState(null);
  const messagesEndRef = useRef(null);
  const abortRef = useRef(null);

  const fetchRemaining = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/chat/remaining-questions`);
      if (res.ok) {
        const data = await res.json();
        setRemainingQuestions(data.remaining);
        setResetInSeconds(data.reset_in_seconds);
      }
    } catch (e) {
      console.error("Failed to fetch remaining questions", e);
    }
  }, []);

  useEffect(() => {
    fetchRemaining();
  }, [fetchRemaining]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim() || isLoading) return;

    setInput("");
    setIsLoading(true);

    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
      { role: "assistant", content: "", streaming: true },
    ]);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const currentSession = sessionId || crypto.randomUUID();
      if (!sessionId) {
        setSessionId(currentSession);
        localStorage.setItem("session_khare", currentSession);
      }

      const response = await fetch(`${API_BASE}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, session_id: currentSession, stream: true, mode: "doctor" }),
        signal: controller.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let fullContent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          let event;
          try { event = JSON.parse(line.slice(6)); } catch { continue; }

          if (event.type === "token") {
            fullContent += event.content;
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: fullContent,
                streaming: true,
              };
              return updated;
            });
          } else if (event.type === "done") {
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: fullContent,
                streaming: false,
              };
              return updated;
            });
            if (event.session_id) {
              setSessionId(event.session_id);
              localStorage.setItem("session_khare", event.session_id);
            }
          }
        }
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: "Connection error. Please check that the backend is running and try again.",
            isError: true,
            streaming: false,
          };
          return updated;
        });
      }
    } finally {
      setIsLoading(false);
      abortRef.current = null;
      fetchRemaining();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="shell">
      <header className="header">
        <div className="header-left">
          <div className="logo-circle">SK</div>
          <div className="header-title-container">
            <h1 className="header-title">Ask Dr. Khare</h1>
            <p className="header-subtitle">AI assistant • Trained on CV data</p>
          </div>
        </div>
        <div className="header-right">
          <div className="status-dot" />
          <span>online</span>
        </div>
      </header>

      {remainingQuestions === 0 && resetInSeconds > 0 && (
        <div className="limit-banner">
          You have used all 5 questions. Limit resets in {Math.floor(resetInSeconds / 3600)} hours {Math.floor((resetInSeconds % 3600) / 60)} minutes.
        </div>
      )}

      <div className="chat-window">
        {messages.map((msg, index) => (
          <div key={index} className={`msg-row ${msg.role}`}>
            <div className={`bubble ${msg.isError ? "error" : ""}`}>
              <ReactMarkdown>{msg.content}</ReactMarkdown>
              
              {msg.streaming && msg.content && (
                <span className="cursor">▋</span>
              )}
              {msg.role === "assistant" && msg.streaming && !msg.content && (
                <LoadingMessage />
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form className="input-row" onSubmit={handleSubmit}>
        <div className="input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about Dr. Khare's background..."
            disabled={isLoading}
            autoFocus
          />
          <button
            type="submit"
            className="send-btn"
            disabled={isLoading || !input.trim()}
          >
            Ask
          </button>
        </div>
      </form>
    </div>
  );
}

export default App;
