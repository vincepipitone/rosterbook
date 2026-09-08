import Link from "next/link";
import { TEAM_ORDER } from "@/app/lib/data";

const SECTIONS = [
  { href: "/team/CHC", label: "Board" },
  { href: "/out-of-options", label: "Out of options" },
  { href: "/rule5", label: "Rule 5 exposure" },
  { href: "/crunch", label: "40-man crunch" },
  { href: "/rules", label: "The rules" },
  { href: "/validation", label: "Accuracy" },
];

export default function SiteNav({ team }: { team?: string }) {
  return (
    <header className="border-b-2 border-ink">
      <div className="mx-auto flex max-w-7xl flex-wrap items-baseline gap-x-6 gap-y-1 py-3">
        <Link href="/team/CHC" className="text-xl font-bold tracking-tight no-underline">
          Rosterbook
        </Link>
        <nav className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
          {SECTIONS.map((s) => (
            <Link key={s.href} href={s.href} className="text-ink-soft hover:text-ink hover:underline">
              {s.label}
            </Link>
          ))}
        </nav>
      </div>
      <div className="mx-auto max-w-7xl overflow-x-auto pb-2">
        <div className="board flex gap-1 text-[13px]">
          {TEAM_ORDER.map((t) => (
            <Link
              key={t}
              href={`/team/${t}`}
              className={`rounded-sm px-1.5 py-0.5 no-underline ${t === team ? "bg-ink text-paper" : "text-ink-soft hover:bg-rule-soft hover:text-ink"}`}
            >
              {t}
            </Link>
          ))}
        </div>
      </div>
    </header>
  );
}
