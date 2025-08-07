"use client";
import { useState, useRef, useEffect } from "react";

export default function Page() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const chatEndRef = useRef(null);

  const handleSend = async () => {
    if (!question.trim()) return;

    const newUserMsg = { role: "user", content: question };
    setMessages((prev) => [...prev, newUserMsg]);
    setLoading(true);
    setQuestion("");

    const res = await fetch("http://localhost:8000/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    const data = await res.json();
    const botReply = { role: "assistant", content: data.answer };
    setMessages((prev) => [...prev, botReply]);
    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus("Uploading...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        setUploadStatus("✅ File uploaded & indexed!");
      } else {
        setUploadStatus("❌ Upload failed.");
      }
    } catch (err) {
      setUploadStatus("❌ Upload error.");
    }

    setUploading(false);
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center px-4 py-6">
      <div className="w-full max-w-2xl bg-white rounded-lg shadow-xl p-6 flex flex-col">
        <h1 className="text-2xl font-bold text-center mb-4 text-black">💬 RAG AI Assistant</h1>

        {/* Upload Section */}
        <div className="mb-4 flex items-center gap-4">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="text-sm"
          />
          {uploading ? (
            <span className="text-blue-600 text-sm">Uploading...</span>
          ) : (
            uploadStatus && <span className="text-green-600 text-sm">{uploadStatus}</span>
          )}
        </div>

        {/* Chat Display */}
        <div className="flex-1 overflow-y-auto mb-4 max-h-[60vh] space-y-4 pr-2">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`rounded-lg px-4 py-2 max-w-[75%] text-sm ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-br-none"
                    : "bg-gray-200 text-gray-800 rounded-bl-none"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>

        {/* Message Input */}
        <div className="flex gap-2">
          <textarea
            rows={1}
            className="flex-1 p-3 border border-gray-300 rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm text-black"
            placeholder="Ask something..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
          />

          <button
            onClick={handleSend}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded"
          >
            {loading ? "..." : "Send"}
          </button>
        </div>
      </div>
    </main>
  );
}
