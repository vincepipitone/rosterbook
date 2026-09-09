import Link from "next/link";
import { notFound } from "next/navigation";
import SiteNav from "@/app/components/SiteNav";
import { stampClass, stampLabel } from "@/app/components/Stamp";
import { fmtDate, loadRules, loadTeamPlayers, loadTeams, TEAM_ORDER } from "@/app/lib/data";
import type { PlayerFull } from "@/app/types";

export const dynamicParams = false;

let cache: Promise<Map<string, PlayerFull>> | null = null;
function allPlayers(): Promise<Map<string, PlayerFull>> {
  return (cache ||= buildIndex());
}

async function buildIndex(): Promise<Map<string, PlayerFull>> {
  const m = new Map<string, PlayerFull>();
  for (const abbr of TEAM_ORDER) {
    const ps = await loadTeamPlayers(abbr);
    for (const [id, p] of Object.entries(ps)) m.set(id, p);
  }
  return m;
}

export async function generateStaticParams() {
  const m = await allPlayers();
  return [...m.keys()].map((id) => ({ id }));
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const p = (await allPlayers()).get(id);
  return { title: p ? `${p.name} roster status` : "Player" };
}

const TYPE_LABEL: Record<string, string> = {
  optioned: "Optioned", recalled: "Recalled", selected: "Contract selected", designated: "Designated for assignment",
  outrighted: "Outrighted", claimed: "Claimed off waivers", released: "Released", traded: "Traded", rule5_selected: "Rule 5 pick",
  rule5_returned: "Returned (Rule 5)", declared_fa: "Declared free agent", signed_fa: "Signed as free agent", signed: "Signed",
  assigned: "Assigned", status_change: "Status change", purchased: "Purchased", retired: "Retired",
};

export default async function PlayerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const p = (await allPlayers()).get(id);
  if (!p) notFound();
  const [{ meta, deadlines }, { rules }] = await Promise.all([loadTeams(), loadRules()]);
  const ruleById = Object.fromEntries(rules.map((r) => [r.id, r]));
  const season = meta.season;
  const stamps = p.flags.map((f) => ({ f, label: stampLabel(f) })).filter((x) => x.label);
  const history = Object.entries(p.option_history || {}).sort((a, b) => Number(b[0]) - Number(a[0]));
  const notable = p.transactions.filter((t) => !["assigned", "number"].includes(t.type) && !(t.type === "status_change" && ["sc_status", "sc_other"].includes(t.subtype)));
  return (
    <>
      <SiteNav team={p.team} />
      <div className="mt-6 flex flex-wrap items-baseline gap-x-4 gap-y-1">
        <h1 className="text-3xl font-bold tracking-tight">{p.name}</h1>
        <span className="text-ink-soft">
          {p.pos} · {p.bats}/{p.throws} · age {p.age} · <Link href={`/team/${p.team}`} className="underline">{p.team}</Link>
        </span>
      </div>
      <p className="mt-1">
        {stamps.map(({ f, label }) => (
          <span key={f.rule + f.status} className={stampClass(f)}>{label}</span>
        ))}
      </p>

      <div className="board mt-6 grid max-w-3xl grid-cols-2 gap-x-8 gap-y-1 sm:grid-cols-3">
        <div><span className="text-ink-soft">Roster status</span><br />{p.roster_status}{p.injury ? ` (${p.injury})` : ""}</div>
        <div><span className="text-ink-soft">Service thru {season - 1}</span><br />{p.mls_prior ?? "n/a"}</div>
        <div><span className="text-ink-soft">Service now / projected</span><br />{p.mls_now ?? "n/a"} / {p.mls_end_proj ?? "n/a"}</div>
        <div><span className="text-ink-soft">Option years left ({season})</span><br />{p.options_left}{p.burning_this_season ? ` (using one in ${season})` : ""}</div>
        <div><span className="text-ink-soft">Assignments left this season</span><br />{p.assignments_available ?? "n/a"} of 5</div>
        <div><span className="text-ink-soft">Contract ({season + 1})</span><br />{p.contract_status}</div>
        <div><span className="text-ink-soft">Acquired</span><br />{p.acquired ?? ""}</div>
        <div><span className="text-ink-soft">Outrighted / DFA&apos;d before</span><br />{p.prior_outrights} / {p.prior_dfa}</div>
        <div><span className="text-ink-soft">Contract</span><br />{p.contract?.description ?? "none listed"}{p.contract?.no_trade ? `; ${p.contract.no_trade}` : ""}</div>
      </div>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">What the rules say about him</h2>
        <ul className="prose-narrow mt-3 space-y-3">
          {p.flags.map((f) => {
            const r = ruleById[f.rule];
            return (
              <li key={f.rule + f.status} className="border-l-2 border-rule pl-3">
                <div className="font-medium">{f.title}</div>
                <div className="text-[15px] leading-snug">{f.why}</div>
                {r ? (
                  <div className="mt-0.5 text-sm text-ink-soft">
                    {r.summary}{" "}
                    <a href={r.cite.url} className="underline" rel="noopener" target="_blank">{r.cite.source}, {r.cite.article}, p. {r.cite.page}</a>
                    {r.cite.mlr ? ` (the number itself is in ${r.cite.mlr})` : ""}
                  </div>
                ) : null}
              </li>
            );
          })}
          {p.rule5?.reason ? (
            <li className="border-l-2 border-rule pl-3">
              <div className="font-medium">Rule 5 clock</div>
              <div className="text-[15px] leading-snug">{p.rule5.reason.charAt(0).toUpperCase() + p.rule5.reason.slice(1)}.</div>
            </li>
          ) : null}
        </ul>
      </section>

      {history.length ? (
        <section className="mt-8">
          <h2 className="text-xl font-semibold">Option years, season by season</h2>
          <table className="board mt-3 max-w-3xl">
            <thead>
              <tr><th>Season</th><th className="num">Days on option</th><th>Option year used</th><th>Stints</th></tr>
            </thead>
            <tbody>
              {history.map(([s, h]) => (
                <tr key={s}>
                  <td>{s}</td>
                  <td className="num">{h.days}</td>
                  <td>{h.burned ? "yes" : "no (under 20)"}</td>
                  <td className="text-ink-soft">
                    {h.intervals.map((iv, i) => (
                      <span key={i} className="mr-3 inline-block">
                        {fmtDate(iv.start)} to {iv.end ? fmtDate(iv.end) : "now"} ({iv.days}d{iv.exempt ? `, ${iv.exempt}` : ""}{iv.source === "implied" ? ", implied" : ""})
                      </span>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      <section className="mt-8">
        <h2 className="text-xl font-semibold">Transaction log</h2>
        <table className="board mt-3 max-w-4xl">
          <tbody>
            {notable.slice(0, 40).map((t, i) => (
              <tr key={i}>
                <td className="whitespace-nowrap text-ink-soft">{fmtDate(t.date)}</td>
                <td className="whitespace-nowrap">{TYPE_LABEL[t.type] ?? t.type}</td>
                <td className="text-ink-soft">{t.desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <p className="prose-narrow mt-8 text-sm text-ink-soft">
        Service through {season - 1} per FanGraphs RosterResource; options and this-season service reconstructed from the MLB transaction log
        ({p.options_left_source}{p.fangraphs_options ? `; FanGraphs shows ${p.fangraphs_options}` : ""}). Rule 5 exposure deadline {fmtDate(deadlines.reserve_list_filing)}.
      </p>
    </>
  );
}
