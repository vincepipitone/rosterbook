import Link from "next/link";
import SiteNav from "@/app/components/SiteNav";
import { fmtDate, loadRule5, TEAM_ORDER } from "@/app/lib/data";

export const metadata = { title: "Rule 5 exposure" };

export default async function Rule5Page() {
  const { meta, deadlines, players } = await loadRule5();
  const byTeam = new Map<string, typeof players>();
  for (const p of players) byTeam.set(p.team, [...(byTeam.get(p.team) ?? []), p]);
  const firstTimers = players.filter((p) => p.rule5.first_eligible_year === meta.season && !p.prior_outrights);
  return (
    <>
      <SiteNav />
      <div className="mt-6 max-w-3xl">
        <h1 className="text-3xl font-bold tracking-tight">Rule 5 exposure, {meta.season}</h1>
        <p className="prose-narrow mt-2 text-[15px] leading-snug">
          {players.length} minor leaguers across the 30 organizations are eligible for the {meta.season} Rule 5 draft on{" "}
          {fmtDate(deadlines.rule5_draft)} unless their club adds them to the 40-man by {fmtDate(deadlines.reserve_list_filing)}.{" "}
          {firstTimers.length} are exposed for the first time. Eligibility is computed from signing year and age on the June 5 before the
          first contract (five drafts for 18-and-under signees, four for 19-and-older); anyone outrighted before is eligible every year.
          Most of these players will not be taken; the major-league phase averages 13 to 15 picks and about half stick.
        </p>
      </div>
      {TEAM_ORDER.filter((t) => byTeam.has(t)).map((team) => {
        const ps = byTeam.get(team)!;
        const first = ps.filter((p) => p.rule5.first_eligible_year === meta.season && !p.prior_outrights);
        const rest = ps.filter((p) => !first.includes(p));
        return (
          <details key={team} className="mt-4 max-w-4xl border-b border-rule-soft pb-3" open={team === "CHC"}>
            <summary className="cursor-pointer text-lg font-semibold">
              <Link href={`/team/${team}`} className="hover:underline">{team}</Link>
              <span className="ml-3 text-sm font-normal text-ink-soft">{ps.length} eligible, {first.length} for the first time</span>
            </summary>
            <div className="board mt-2 grid gap-x-8 gap-y-1 sm:grid-cols-2">
              {[...first, ...rest].map((p) => (
                <div key={p.id} className="flex justify-between gap-3">
                  <span>
                    {p.name} <span className="text-ink-soft">{p.pos}</span>
                    {first.includes(p) ? <span className="stamp stamp-red ml-2">FIRST TIME</span> : null}
                    {p.prior_outrights ? <span className="stamp stamp-ink ml-2">OUTRIGHTED</span> : null}
                  </span>
                  <span className="whitespace-nowrap text-ink-soft">age {p.age ?? "?"} · signed {p.rule5.sign_date?.slice(0, 4) ?? "?"}</span>
                </div>
              ))}
            </div>
          </details>
        );
      })}
      <p className="prose-narrow mt-6 text-sm text-ink-soft">
        The pool is every player FanGraphs lists in an organization who is not on the 40-man or a non-roster invitee. Signing dates come
        from the draft record where one exists, otherwise from the FanGraphs signing year (month approximated as July), so a handful of
        players signed around June 5 may sit a year off. Data as of {fmtDate(meta.fg_snapshot)}.
      </p>
    </>
  );
}
