import type { Metadata } from "next";
import "./globals.css";
import { DM_Sans, DM_Serif_Display } from "next/font/google";

const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-body" });
const dmSerif = DM_Serif_Display({ 
  subsets: ["latin"], 
  weight: "400", 
  variable: "--font-display" 
});

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
      <body className={`${dmSans.variable} ${dmSerif.variable}`}>{children}</body>
    </html>
  );
}