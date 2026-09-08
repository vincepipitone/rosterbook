import Link from "next/link";
import { notFound } from "next/navigation";
import SiteNav from "@/app/components/SiteNav";
import Stamps from "@/app/components/Stamp";
import { fmtDate, loadTeam, loadTeams, TEAM_ORDER } from "@/app/lib/data";
import type { PlayerSummary } from "@/app/types";

export const dynamicParams = false;
export async function generateStaticParams() {
  return TEAM_ORDER.map((abbr) => ({ abbr }));
}

export async function generateMetadata({ params }: { params: Promise<{ abbr: string }> }) {
  const { abbr } = await params;
  return { title: `${abbr} 40-man` };
}

function group(p: PlayerSummary): string {
  const pos = (p.pos || "").toUpperCase();
  if (["SP", "RP", "P", "LHP", "RHP", "CL"].includes(pos)) return "Pitchers";
  if (pos === "C") return "Catchers";
  if (["1B", "2B", "3B", "SS", "IF", "UT"].includes(pos)) return "Infielders";
  return "Outfielders and DH";
}

function Row({ p }: { p: PlayerSummary }) {
  const veteran = (p.mls_prior_days ?? 0) >= 860;
  return (
    <tr>
      <td className="whitespace-nowrap">
        <Link href={`/player/${p.id}`} className="font-medium hover:underline">
          {p.name}
        </Link>
        <span className="ml-2 text-ink-soft">{p.pos}</span>
      </td>
      <td className="num">{p.age ?? ""}</td>
      <td className="num">{p.mls_prior ?? "n/a"}</td>
      <td className="num text-ink-soft">{p.mls_now ?? ""}</td>
      <td className="num">
        {veteran ? <span className="text-ink-soft">{p.options_left}*</span> : p.options_left}
        {p.burning_this_season && !veteran ? <span className="text-amber" title={`${p.option_days_this_season} option days this season: one option year used`}> ▾</span> : null}
      </td>
      <td className="num">{p.assignments_available === null ? <span className="text-ink-soft">n/a</span> : p.assignments_available}</td>
      <td className="whitespace-nowrap">
        {p.roster_status}
        {p.injury ? <span className="block text-[12px] text-ink-soft">{p.injury}</span> : null}
      </td>
      <td>{p.contract_status}</td>
      <td>
        <Stamps flags={p.flags} />
      </td>
    </tr>
  );
}

export default async function TeamPage({ params }: { params: Promise<{ abbr: string }> }) {
  const { abbr } = await params;
  if (!TEAM_ORDER.includes(abbr)) notFound();
  const [team, all] = await Promise.all([loadTeam(abbr), loadTeams()]);
  const { meta, deadlines } = all;
  const c = team.counts;
  const groups = ["Pitchers", "Catchers", "Infielders", "Outfielders and DH"];
  const byGroup: Record<string, PlayerSummary[]> = {};
  for (const p of team.players) (byGroup[group(p)] ||= []).push(p);
  const season = meta.season;
  return (
    <>
      <SiteNav team={abbr} />
      <div className="mt-6">
        <h1 className="text-3xl font-bold tracking-tight">{team.name}</h1>
        <p className="prose-narrow mt-2 text-[15px] leading-snug">
          {c.forty} on the 40-man reserve list and {c.il60} parked on the 60-day IL who must be back on it by{" "}
          {fmtDate(deadlines.il60_reinstate_by)}. {c.optioned} currently optioned, {c.out_of_options} out of options,{" "}
          {c.xxb_fa} headed to free agency after the season, {c.arb} arbitration-eligible for {season + 1}, and{" "}
          <Link href="/rule5" className="underline">{c.rule5_exposed} farmhands exposed</Link> to the Rule 5 draft unless protected by{" "}
          {fmtDate(deadlines.reserve_list_filing)}.
        </p>
      </div>

      <div className="mt-6 overflow-x-auto">
        <table className="board w-full">
          <thead>
            <tr>
              <th>Player</th>
              <th className="num">Age</th>
              <th className="num">Service thru {season - 1}</th>
              <th className="num">Service now</th>
              <th className="num">Options left ({season})</th>
              <th className="num">Assignments left</th>
              <th>Roster status</th>
              <th>Contract ({season + 1})</th>
              <th>Rights and exposure</th>
            </tr>
          </thead>
          <tbody>
            {groups.map((g) =>
              byGroup[g]?.length ? (
                <>
                  <tr className="group" key={g}>
                    <td colSpan={9}>
                      {g} ({byGroup[g].filter((p) => p.status_code !== "D60").length}
                      {byGroup[g].some((p) => p.status_code === "D60") ? ` + ${byGroup[g].filter((p) => p.status_code === "D60").length} on the 60-day IL` : ""})
                    </td>
                  </tr>
                  {byGroup[g].map((p) => (
                    <Row key={p.id} p={p} />
                  ))}
                </>
              ) : null,
            )}
          </tbody>
        </table>
      </div>

      <div className="prose-narrow mt-8 space-y-2 text-sm text-ink-soft">
        <p>
          Service time is years+days (172 days is a year), through last season per FanGraphs RosterResource; the &ldquo;now&rdquo; column adds
          this season&apos;s days from the transaction log. Options left is reconstructed from every option and recall since 2010, with the
          20-day rule and spring-training exclusion applied; ▾ marks a player who has already used a {season} option year. Assignments left
          counts against the five-per-season cap. * = five or more years of service, so he can refuse an assignment regardless.
        </p>
        <p>
          <span className="stamp stamp-red">RED</span> means the club is exposed (out of options, Rule 5, free agency);{" "}
          <span className="stamp stamp-green">GREEN</span> means the player holds a consent right; <span className="stamp stamp-amber">AMBER</span> is
          something about to change. Hover a stamp for the reason, or open the player for the full explanation and history. Data as of{" "}
          {fmtDate(meta.fg_snapshot)}.
        </p>
      </div>
    </>
  );
}
