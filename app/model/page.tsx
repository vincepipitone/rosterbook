import SiteNav from "@/app/components/SiteNav";
import { loadModel, pct } from "@/app/lib/data";

export const metadata = { title: "The model" };

const ABL: Record<string, string> = {
  base: "Roster mechanics, history, this season's line, depth (previous model)", "+war": "+ FanGraphs WAR history (two seasons, this season, wRC+, FIP, change)",
  "+role": "+ starter / reliever share", "+rank": "+ WAR rank within the club's position group", "+injury": "+ IL days this season, 60-day IL",
  "+recency": "+ moves in the last year, Rule 5 pick, days since last move", "+team": "+ club record and run differential", "+all": "All groups together (current model)",
};
const LABEL: Record<string, string> = { none: "Stays put", designated: "Designated", optioned: "Optioned", traded: "Traded", released: "Released / non-tendered" };

export default async function ModelPage() {
  const { meta, report, ablation } = await loadModel();
  const seasons = Object.entries(report.seasons as Record<string, { n: number; logloss: number; logloss_base: number; auc: Record<string, number | null> }>);
  const pooled = report.pooled;
  return (
    <>
      <SiteNav />
      <div className="mt-6 max-w-3xl">
        <h1 className="text-3xl font-bold tracking-tight">The transaction model</h1>
        <p className="prose-narrow mt-2 text-[15px] leading-snug">
          For every player on a 40-man roster, the probability that within the next {meta.horizon_days} days he is designated for
          assignment, optioned, traded, released or non-tendered, or nothing happens. It is a gradient-boosted classifier trained on{" "}
          {meta.n_train.toLocaleString()} player-snapshot rows from {meta.seasons}: every dated 40-man roster (Opening Day, June 1, July 1,
          the day after the deadline, September 1, season&apos;s end, the reserve-list filing, tender day, the Rule 5 draft) and what the
          transaction log says happened next.
        </p>
        <p className="prose-narrow mt-2 text-[15px] leading-snug">
          It sees only what was knowable on the snapshot date: roster status, option years used and option days, times optioned this season,
          service time where published, age and years since debut, how and when the player joined the club (including a trade or claim in
          the last 60 days), his prior DFAs, outrights, claims and trades and how recent they were, IL days this season, the club&apos;s
          40-man and 60-day IL counts and depth at his position, the club&apos;s record, the time of year, FanGraphs WAR for the last two
          seasons and his rank at his position on the club, last season&apos;s stat line, and this season&apos;s line once September arrives.
          It does not see contracts, projected arbitration salaries, or anything a front office knows about health or intent.
        </p>
      </div>

      <section className="mt-8 max-w-3xl">
        <h2 className="text-xl font-semibold">Held-out accuracy, season by season</h2>
        <p className="mt-1 text-sm text-ink-soft">
          Each season is predicted by a model trained on all the others. Log loss is lower-is-better; the base rate is a model that knows only the
          time of year. AUC is one-versus-rest: 0.5 is a coin flip, 1.0 is perfect ordering.
        </p>
        <table className="board mt-3">
          <thead>
            <tr><th>Season</th><th className="num">Rows</th><th className="num">Log loss</th><th className="num">Base rate</th>
              {Object.keys(LABEL).map((k) => <th key={k} className="num">AUC {LABEL[k].split(" ")[0]}</th>)}</tr>
          </thead>
          <tbody>
            {seasons.map(([s, r]) => (
              <tr key={s}><td>{s}</td><td className="num">{r.n.toLocaleString()}</td><td className="num">{r.logloss}</td><td className="num text-ink-soft">{r.logloss_base}</td>
                {Object.keys(LABEL).map((k) => <td key={k} className="num">{r.auc[k] ?? ""}</td>)}</tr>
            ))}
            <tr className="font-semibold"><td>Pooled</td><td className="num">{pooled.n.toLocaleString()}</td><td className="num">{pooled.logloss}</td><td className="num text-ink-soft">{pooled.logloss_base}</td>
              {Object.keys(LABEL).map((k) => <td key={k} className="num">{pooled.auc[k]}</td>)}</tr>
          </tbody>
        </table>
      </section>

      <section className="mt-8 max-w-3xl">
        <h2 className="text-xl font-semibold">Calibration</h2>
        <p className="mt-1 text-sm text-ink-soft">Held-out predictions sorted into ten bins per outcome: what the model said against what happened.</p>
        <div className="mt-3 grid gap-6 sm:grid-cols-2">
          {Object.entries(report.calibration as Record<string, { pred: number; actual: number; n: number }[]>).map(([k, rows]) => (
            <table key={k} className="board">
              <thead><tr><th>{LABEL[k]}</th><th className="num">Predicted</th><th className="num">Actual</th><th className="num">n</th></tr></thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i}><td className="text-ink-soft">bin {i + 1}</td><td className="num">{pct(r.pred)}</td><td className="num">{pct(r.actual)}</td><td className="num">{r.n.toLocaleString()}</td></tr>
                ))}
              </tbody>
            </table>
          ))}
        </div>
      </section>

      {ablation ? (
        <section className="mt-8 max-w-3xl">
          <h2 className="text-xl font-semibold">What was tried</h2>
          <p className="mt-1 text-sm text-ink-soft">
            Feature groups added one at a time to the previous model, each scored leave-one-season-out. &ldquo;Tender window&rdquo; is the
            reserve-list filing and tender-day snapshots only. Lower log loss and higher AUC are better. All groups were adopted.
          </p>
          <table className="board mt-3">
            <thead><tr><th>Configuration</th><th className="num">Log loss</th><th className="num">Log loss, tender window</th><th className="num">AUC designated</th><th className="num">AUC released, tender</th></tr></thead>
            <tbody>
              {Object.entries(ablation as Record<string, Record<string, number>>).map(([k, r]) => (
                <tr key={k}><td>{ABL[k] ?? k}</td><td className="num">{r.logloss}</td><td className="num">{r.logloss_tender}</td><td className="num">{r.auc_designated}</td><td className="num">{r.auc_released_tender}</td></tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      <section className="mt-8 max-w-3xl">
        <h2 className="text-xl font-semibold">What it leans on</h2>
        <p className="mt-1 text-sm text-ink-soft">Total split gain by feature, top 20.</p>
        <table className="board mt-3">
          <tbody>
            {Object.entries(report.importance as Record<string, number>).map(([k, v]) => (
              <tr key={k}><td>{k}</td><td className="num">{Math.round(v).toLocaleString()}</td></tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="prose-narrow mt-8 text-sm text-ink-soft">
        <h2 className="text-base font-semibold text-ink">Base rates and limits</h2>
        <p className="mt-1">
          Over any 90-day window since 2011: {Object.entries(meta.base_rates as Record<string, number>).map(([k, v], i) => `${i ? ", " : ""}${LABEL[k].toLowerCase()} ${pct(v)}`)}.
          Trades are the hardest outcome to anticipate from roster mechanics alone. Historical service time is only available from 2020, so
          earlier seasons lean on years since debut. Retrained nightly as of {meta.asof}.
        </p>
      </section>
    </>
  );
}
