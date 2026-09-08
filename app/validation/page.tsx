import SiteNav from "@/app/components/SiteNav";
import { loadValidation } from "@/app/lib/data";

export const metadata = { title: "Accuracy" };

const COLS: [string, string][] = [["mls", "Service time"], ["options", "Option years left"], ["assignments", "Assignments left"], ["status", "Roster status"], ["contract", "Contract status"]];

export default async function ValidationPage() {
  const v = await loadValidation();
  const az = v.azphil;
  const fg = v.fangraphs;
  const bad = az.rows.filter((r: { matched: boolean }) => r.matched).filter((r: Record<string, { agree: boolean }>) => COLS.some(([k]) => !r[k].agree));
  return (
    <>
      <SiteNav />
      <div className="mt-6 max-w-3xl">
        <h1 className="text-3xl font-bold tracking-tight">How accurate is this?</h1>
        <p className="prose-narrow mt-2 text-[15px] leading-snug">
          Everything on the board is derived, so it is checked against the two best human-maintained sources every night. Arizona
          Phil&apos;s Cubs 40-man page is the gold standard for one team; FanGraphs RosterResource carries option counts for every team.
          Disagreements are listed rather than hidden.
        </p>
      </div>

      <section className="mt-8 max-w-3xl">
        <h2 className="text-xl font-semibold">Against Arizona Phil&apos;s Cubs page</h2>
        <p className="mt-1 text-sm text-ink-soft">Page dated {az.page_updated}; {az.n_matched} of {az.n_rows} players matched by name.</p>
        <table className="board mt-3">
          <thead><tr><th>Column</th><th className="num">Agree</th><th className="num">Share</th></tr></thead>
          <tbody>
            {COLS.map(([k, label]) => (
              <tr key={k}><td>{label}</td><td className="num">{az.agreement[k].n} / {az.n_matched}</td><td className="num">{az.agreement[k].pct}%</td></tr>
            ))}
          </tbody>
        </table>
        {bad.length ? (
          <>
            <h3 className="mt-4 font-medium">Where we differ</h3>
            <table className="board mt-2">
              <thead><tr><th>Player</th><th>Column</th><th>Arizona Phil</th><th>Rosterbook</th></tr></thead>
              <tbody>
                {bad.flatMap((r: Record<string, { agree: boolean; azphil: string; ours: string }> & { name: string }) =>
                  COLS.filter(([k]) => !r[k].agree).map(([k, label]) => (
                    <tr key={r.name + k}><td>{r.name}</td><td>{label}</td><td>{r[k].azphil}</td><td>{r[k].ours}</td></tr>
                  )),
                )}
              </tbody>
            </table>
          </>
        ) : null}
      </section>

      <section className="mt-8 max-w-3xl">
        <h2 className="text-xl font-semibold">Option years against FanGraphs, all 30 teams</h2>
        <p className="mt-1 text-[15px]">
          {fg.exact} of {fg.n} players with a FanGraphs option count match exactly ({fg.pct}%). The rest are shown on each player&apos;s
          page next to our number.
        </p>
        <table className="board mt-3">
          <thead><tr><th>FanGraphs → ours</th><th className="num">Players</th></tr></thead>
          <tbody>
            {Object.entries(fg.confusion as Record<string, number>).sort((a, b) => b[1] - a[1]).map(([k, n]) => (
              <tr key={k}><td>{k}</td><td className="num">{n}</td></tr>
            ))}
          </tbody>
        </table>
        <details className="mt-3">
          <summary className="cursor-pointer text-sm text-ink-soft">List the disagreements</summary>
          <table className="board mt-2">
            <tbody>
              {fg.disagreements.map((d: { name: string; team: string; fangraphs: number; ours: number }) => (
                <tr key={d.name + d.team}><td>{d.team}</td><td>{d.name}</td><td className="num">FG {d.fangraphs}</td><td className="num">ours {d.ours}</td></tr>
              ))}
            </tbody>
          </table>
        </details>
      </section>

      <section className="mt-8 max-w-3xl">
        <h2 className="text-xl font-semibold">Transaction volume by season</h2>
        <p className="mt-1 text-sm text-ink-soft">Each type is compared with the mean of the three prior seasons (the current season pro-rated). Outside 50% fails the build.</p>
        <table className="board mt-3">
          <thead>
            <tr><th>Season</th>{Object.keys(v.transactions.years[Object.keys(v.transactions.years)[0]]).map((t) => <th key={t} className="num">{t}</th>)}</tr>
          </thead>
          <tbody>
            {Object.entries(v.transactions.years as Record<string, Record<string, { n: number; ok: boolean }>>).map(([y, row]) => (
              <tr key={y}><td>{y}</td>{Object.values(row).map((c, i) => <td key={i} className={`num ${c.ok ? "" : "text-red"}`}>{c.n}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="prose-narrow mt-8 text-sm text-ink-soft">
        <h2 className="text-base font-semibold text-ink">Known limits</h2>
        <p className="mt-1">{v.service_time_note}</p>
        <p className="mt-2">
          Fourth options follow FanGraphs where it shows a count, because minor-league injured-list days are not public. Doubleheader
          27th-man returns are counted as optional assignments. Arizona Phil&apos;s page can lag a move by a few days, which shows up as
          status disagreements.
        </p>
      </section>
    </>
  );
}
