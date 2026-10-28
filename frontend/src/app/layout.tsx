import "./globals.css";
import React from "react";
import { Navbar } from "@/components/Navbar";
import { Sidebar } from "@/components/Sidebar";
import { DisclaimerBanner } from "@/components/DisclaimerBanner";

export const metadata = {
  title: "Indian Stock Market AI Intelligence | Paper Trading",
  description: "Production-ready AI-powered Indian stock market news intelligence & decision support platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col antialiased">
        <DisclaimerBanner />
        <Navbar />
        <div className="flex flex-1">
          <Sidebar />
          <main className="flex-1 p-6 max-w-7xl mx-auto w-full overflow-y-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
