import type { Metadata } from "next";
import "./globals.css";
import AppShell from "@/components/AppShell";
import { TooltipProvider } from "@/components/ui/tooltip";

export const metadata: Metadata = {
  title: "AuRAG | Autonomous Machine Money Protocol",
  description: "Industrial machines holding sovereign Bitcoin Lightning wallets (BOLT-11 / Nostr NWC), executing autonomous vendor payments grounded in deterministic GraphRAG evidence. Engineered by Niss.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="min-h-full antialiased">
      <body className="min-h-full">
        <TooltipProvider>
          <AppShell>{children}</AppShell>
        </TooltipProvider>
      </body>
    </html>
  );
}
