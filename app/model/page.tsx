import SiteNav from "@/app/components/SiteNav";
import { loadModel, pct } from "@/app/lib/data";

export const metadata = { title: "The model" };

const LABEL: Record<string, string> = { none: "Stays put", designated: "Designated", optioned: "Optioned", traded: "Traded", released: "Released / non-tendered" };

export default async function ModelPage() {
  const { meta, report } = await loadModel();
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
          service time where published, age and years since debut, how and when the player joined the club, his prior DFAs, outrights, claims
          and trades, the club&apos;s 40-man and 60-day IL counts, the time of year, and last season&apos;s stat line. It does not see this
          season&apos;s performance, injuries beyond the IL status, contracts, or anything a front office knows.
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
