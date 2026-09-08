import Link from "next/link";
import SiteNav from "@/app/components/SiteNav";
import Stamps from "@/app/components/Stamp";
import { fmtDate, loadOutOfOptions } from "@/app/lib/data";

export const metadata = { title: "Out of options" };

export default async function OutOfOptionsPage() {
  const { meta, players } = await loadOutOfOptions();
  const byTeam = new Map<string, typeof players>();
  for (const p of players) byTeam.set(p.team, [...(byTeam.get(p.team) ?? []), p]);
  return (
    <>
      <SiteNav />
      <div className="mt-6 max-w-3xl">
        <h1 className="text-3xl font-bold tracking-tight">Out of options</h1>
        <p className="prose-narrow mt-2 text-[15px] leading-snug">
          {players.length} players on 40-man rosters with under five years of service and no option years left. Each has to be carried
          on the 26-man next spring or pass through outright waivers, which is why this list predicts March DFAs better than any
          depth chart. Players with five years of service are omitted: they can refuse an assignment anyway.
        </p>
      </div>
      <div className="mt-6 overflow-x-auto">
        <table className="board w-full max-w-5xl">
          <thead>
            <tr>
              <th>Team</th><th>Player</th><th className="num">Age</th><th className="num">Service thru {meta.season - 1}</th>
              <th>Status</th><th>Contract ({meta.season + 1})</th><th>Rights</th>
            </tr>
          </thead>
          <tbody>
            {[...byTeam.entries()].map(([team, ps]) =>
              ps.map((p, i) => (
                <tr key={p.id}>
                  <td>{i === 0 ? <Link href={`/team/${team}`} className="font-medium hover:underline">{team}</Link> : ""}</td>
                  <td className="whitespace-nowrap"><Link href={`/player/${p.id}`} className="hover:underline">{p.name}</Link> <span className="text-ink-soft">{p.pos}</span></td>
                  <td className="num">{p.age ?? ""}</td>
                  <td className="num">{p.mls_prior ?? "n/a"}</td>
                  <td className="whitespace-nowrap">{p.roster_status}</td>
                  <td>{p.contract_status}</td>
                  <td><Stamps flags={p.flags.filter((f) => f.rule !== "opt.out")} /></td>
                </tr>
              )),
            )}
          </tbody>
        </table>
      </div>
      <p className="mt-6 text-sm text-ink-soft">Data as of {fmtDate(meta.fg_snapshot)}.</p>
    </>
  );
}
