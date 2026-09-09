import type { Metadata } from "next";
import { Archivo, Archivo_Narrow } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

const archivo = Archivo({ subsets: ["latin"], variable: "--font-archivo", weight: ["400", "500", "600", "700"] });
const narrow = Archivo_Narrow({ subsets: ["latin"], variable: "--font-archivo-narrow", weight: ["400", "500", "600", "700"] });

export const metadata: Metadata = {
  title: { default: "Rosterbook", template: "%s | Rosterbook" },
  description:
    "Every MLB 40-man roster with the rules attached: options left, service time, Rule 5 exposure, " +
    "who can refuse an assignment and why. Built from the public transaction log.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${archivo.variable} ${narrow.variable}`}>
      <body className="min-h-screen bg-paper text-ink antialiased">
        <main className="mx-auto max-w-7xl px-4 pb-16 sm:px-6">{children}</main>
        <footer className="mx-auto max-w-7xl px-4 py-8 text-sm text-ink-soft sm:px-6">
          <p className="prose-narrow">
            Rosterbook is an independent fan project, not affiliated with MLB, the MLBPA or any club. Every rule is cited to the{" "}
            <a href="/cba/2022-2026-basic-agreement.pdf" className="underline">2022-2026 Basic Agreement</a>, which expires December 1, 2026.
            Transactions and rosters come from MLB&apos;s public Stats API; options remaining, service time and contracts from FanGraphs
            RosterResource; the Cubs board is checked nightly against Arizona Phil&apos;s at The Cub Reporter.
          </p>
        </footer>
        <Analytics />
      </body>
    </html>
  );
}
