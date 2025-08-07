"use client";
import { useState, useRef, useEffect } from "react";

export default function Page() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const chatEndRef = useRef(null);

  const handleSend = async () => {
    if (!question.trim()) return;

    const newUserMsg = { role: "user", content: question };
    setMessages((prev) => [...prev, newUserMsg]);
    setLoading(true);
    setQuestion("");

    const res = await fetch("https://rag-chatbot-itut.onrender.com/query", { // import hereeeeeee http://localhost:8000/query
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
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    const newFile = { name: file.name, status: "Uploading..." };
    setUploadedFiles((prev) => [...prev, newFile]);
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("https://rag-chatbot-itut.onrender.com/upload", { // important heree http://localhost:8000/upload
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.name === file.name ? { ...f, status: "✅ Uploaded" } : f
          )
        );
      } else {
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.name === file.name ? { ...f, status: "❌ Failed" } : f
          )
        );
      }
    } catch (err) {
      setUploadedFiles((prev) =>
        prev.map((f) =>
          f.name === file.name ? { ...f, status: "❌ Error" } : f
        )
      );
    }

    setUploading(false);
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center px-4 py-6">
      <div className="w-full max-w-3xl bg-white rounded-lg shadow-xl p-6 flex flex-col">
        <h1 className="text-2xl font-bold text-center mb-6 text-black">💬 RAG AI Assistant</h1>

        {/* Upload Section */}
        <div className="mb-6">
          <label
            htmlFor="file-upload"
            className="flex flex-col items-center justify-center w-full border-2 border-dashed border-gray-300 rounded-lg p-6 cursor-pointer hover:bg-gray-100 transition"
          >
            <svg
              className="w-10 h-10 mb-2 text-gray-400"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1M12 12v9m0 0l-3-3m3 3l3-3M12 3v9" />
            </svg>
            <p className="text-gray-500 text-sm">Click to upload or drag a PDF file here</p>
            <input
              id="file-upload"
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>

          {/* Uploaded Files List */}
          {uploadedFiles.length > 0 && (
            <div className="mt-4 space-y-1">
              <h3 className="text-sm font-medium text-gray-700">Uploaded Files:</h3>
              {uploadedFiles.map((file, idx) => (
                <div
                  key={idx}
                  className="flex justify-between items-center text-sm bg-gray-100 p-2 rounded"
                >
                  <span className="text-gray-800 truncate">{file.name}</span>
                  <span className="text-xs">{file.status}</span>
                </div>
              ))}
            </div>
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
