import Link from "next/link";
import SiteNav from "@/app/components/SiteNav";
import { fmtDate, loadTeams } from "@/app/lib/data";

export const metadata = { title: "40-man crunch" };

export default async function CrunchPage() {
  const { meta, deadlines, teams } = await loadTeams();
  const rows = teams
    .map((t) => ({ ...t, pressure: t.counts.forty + t.counts.il60 - t.counts.xxb_fa }))
    .sort((a, b) => b.pressure - a.pressure || b.counts.rule5_exposed - a.counts.rule5_exposed);
  return (
    <>
      <SiteNav />
      <div className="mt-6 max-w-3xl">
        <h1 className="text-3xl font-bold tracking-tight">The November 40-man crunch</h1>
        <p className="prose-narrow mt-2 text-[15px] leading-snug">
          Five days after the World Series ({fmtDate(deadlines.il60_reinstate_by)}) every 60-day IL player comes back onto the 40-man.
          Six-year free agents leave the same week. What is left is the roster a club must fit Rule 5 protections into by{" "}
          {fmtDate(deadlines.reserve_list_filing)} and then tender contracts to by {fmtDate(deadlines.tender)}. The projected count below
          is 40-man plus 60-day IL minus departing free agents; anything near 40 means outrights, non-tenders or trades before the deadline.
        </p>
      </div>
      <div className="mt-6 overflow-x-auto">
        <table className="board w-full max-w-4xl">
          <thead>
            <tr>
              <th>Team</th>
              <th className="num">On the 40</th>
              <th className="num">60-day IL returning</th>
              <th className="num">Free agents leaving</th>
              <th className="num">Projected count</th>
              <th className="num">Out of options</th>
              <th className="num">Arbitration-eligible</th>
              <th className="num">Rule 5 exposed</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.abbr}>
                <td><Link href={`/team/${t.abbr}`} className="font-medium hover:underline">{t.name}</Link></td>
                <td className="num">{t.counts.forty}</td>
                <td className="num">{t.counts.il60}</td>
                <td className="num">{t.counts.xxb_fa}</td>
                <td className={`num font-semibold ${t.pressure >= 40 ? "text-red" : t.pressure >= 37 ? "text-amber" : ""}`}>{t.pressure}</td>
                <td className="num">{t.counts.out_of_options}</td>
                <td className="num">{t.counts.arb}</td>
                <td className="num">{t.counts.rule5_exposed}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="prose-narrow mt-6 text-sm text-ink-soft">
        Free agents leaving counts players projected to six years of service with no {meta.season + 1} contract; club, mutual and player
        options are treated as staying. Data as of {fmtDate(meta.fg_snapshot)}.
      </p>
    </>
  );
}
