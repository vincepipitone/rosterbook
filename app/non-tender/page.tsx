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
          The two risk columns are the model&apos;s: designated or outrighted, and released or non-tendered, within 90 days. Historically
          most arbitration-eligible cuts happen as November outrights rather than at the deadline itself, so read them together. The model
          learns from roster mechanics, history, this season&apos;s line and positional depth; it does not see projections or dollars.
          Those sit alongside as context: ZiPS projected WAR, this year&apos;s WAR, how he was acquired (a club that just traded for a
          player has historically cut him about half as often), and the same-position free agents his club is losing. Arbitration salary
          projections are added when FanGraphs and MLB Trade Rumors publish them in October.
        </p>
      </div>
      <div className="mt-6 overflow-x-auto">
        <table className="board w-full max-w-6xl">
          <thead>
            <tr>
              <th>Team</th><th>Player</th><th className="num">Age</th><th className="num">Service thru {season - 1}</th>
              <th className="num">Arb year</th><th className="num">{season} salary</th>
              <th className="num">DFA / outright</th><th className="num">Non-tender</th>
              <th className="num">ZiPS WAR</th><th className="num">{season} WAR</th><th>Acquired</th><th>Same-position FAs leaving</th>
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
                <td className={`num ${(p.model?.p_designated ?? 0) >= 0.3 ? "font-semibold text-red" : (p.model?.p_designated ?? 0) >= 0.15 ? "text-amber" : ""}`}>{p.model ? pct(p.model.p_designated) : ""}</td>
                <td className={`num ${(p.model?.p_released ?? 0) >= 0.1 ? "font-semibold text-red" : (p.model?.p_released ?? 0) >= 0.05 ? "text-amber" : ""}`}>{p.model ? pct(p.model.p_released) : ""}</td>
                <td className="num">{p.proj?.zips?.war != null ? p.proj.zips.war.toFixed(1) : ""}</td>
                <td className="num">{p.war_now != null ? p.war_now.toFixed(1) : ""}</td>
                <td className="whitespace-nowrap text-ink-soft">{p.acquired ?? ""}</td>
                <td className="text-ink-soft">{p.context?.same_group_leaving?.length ? `${p.context.same_group_leaving.length} of ${p.context.same_group_on_forty} ${p.context.group}: ${p.context.same_group_leaving.join(", ")}` : ""}</td>
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
