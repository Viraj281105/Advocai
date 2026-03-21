import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AdvocAI — AI-Powered Insurance Appeal System",
  description: "Turn your denied insurance claim into a medically, legally, and procedurally airtight appeal — fully automated by 5 specialized AI agents.",
  keywords: ["insurance appeal", "AI", "health insurance", "claim denial", "medical appeal"],
  openGraph: {
    title: "AdvocAI — Fight Back Against Insurance Denials",
    description: "5 AI agents. One airtight appeal letter. Free.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
