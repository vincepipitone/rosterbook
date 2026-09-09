import Link from "next/link";
import SiteNav from "@/app/components/SiteNav";
import Stamps from "@/app/components/Stamp";
import { fmtDate, loadNonTender, pct } from "@/app/lib/data";

export const metadata = { title: "Non-tender watch" };

function money(x: number | null): string {
  if (!x) return "";
  return x >= 1e6 ? `$${(x / 1e6).toFixed(2)}M` : `$${Math.round(x / 1000)}K`;
}

export default async function NonTenderPage() {
  const { meta, deadlines, players } = await loadNonTender();
  const season = meta.season;
  const hot = players.filter((p) => (p.model?.p_cut ?? 0) >= 0.3);
  return (
    <>
      <SiteNav />
      <div className="mt-6 max-w-3xl">
        <h1 className="text-3xl font-bold tracking-tight">Non-tender watch, {season} offseason</h1>
        <p className="prose-narrow mt-2 text-[15px] leading-snug">
          {players.length} players on 40-man rosters are arbitration-eligible for {season + 1}. Each must be tendered a contract by{" "}
          {fmtDate(deadlines.tender)}, 8 PM ET, or become a free agent that night, with no waivers and no termination pay. A tendered player
          cannot be cut more than 20% from this year&apos;s salary, so the tender is a real decision: {hot.length} of them carry a cut risk of 30%
          or more by the model, whose 90-day window from today runs through {fmtDate(deadlines.rule5_draft)} and was trained on past
          non-tenders and November outrights alike.
        </p>
        <p className="prose-narrow mt-2 text-sm text-ink-soft">
          Cut risk = designated or released within 90 days. Arbitration salary projections are added when FanGraphs and MLB Trade Rumors
          publish them in October; until then the table shows this year&apos;s salary where a contract is on file.
        </p>
      </div>
      <div className="mt-6 overflow-x-auto">
        <table className="board w-full max-w-6xl">
          <thead>
            <tr>
              <th>Team</th><th>Player</th><th className="num">Age</th><th className="num">Service thru {season - 1}</th>
              <th className="num">Arb year</th><th className="num">{season} salary</th><th className="num">Cut risk</th><th className="num">Optioned</th>
              <th>Status</th><th>Rights</th>
            </tr>
          </thead>
          <tbody>
            {players.map((p) => (
              <tr key={p.id}>
                <td><Link href={`/team/${p.team}`} className="hover:underline">{p.team}</Link></td>
                <td className="whitespace-nowrap"><Link href={`/player/${p.id}`} className="font-medium hover:underline">{p.name}</Link> <span className="text-ink-soft">{p.pos}</span></td>
                <td className="num">{p.age ?? ""}</td>
                <td className="num">{p.mls_prior ?? "n/a"}{p.super_two ? <span className="stamp stamp-amber ml-2">S2</span> : null}</td>
                <td className="num">{p.arb_year ?? ""}</td>
                <td className="num">{money(p.salary_2026)}</td>
                <td className={`num ${(p.model?.p_cut ?? 0) >= 0.3 ? "font-semibold text-red" : (p.model?.p_cut ?? 0) >= 0.15 ? "text-amber" : ""}`}>{p.model ? pct(p.model.p_cut) : ""}</td>
                <td className="num text-ink-soft">{p.model ? pct(p.model.p_optioned) : ""}</td>
                <td className="whitespace-nowrap">{p.roster_status}</td>
                <td><Stamps flags={p.flags} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-6 text-sm text-ink-soft">Data as of {fmtDate(meta.fg_snapshot)}.</p>
    </>
  );
}
