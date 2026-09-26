import type { Metadata } from "next";
import "./globals.css";
import AppShell from "@/components/AppShell";
import { TooltipProvider } from "@/components/ui/tooltip";

export const metadata: Metadata = {
  title: "AuRAG | Unified Operations",
  description: "Industrial knowledge intelligence for evidence-led operations.",
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
