import "./globals.css";

export const metadata = {
  title: "RAG AI Assistant",
  description: "Chat with your documents using RAG + GPT",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-gray-100 text-gray-800 font-sans">{children}</body>
    </html>
  );
}
