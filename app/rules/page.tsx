import SiteNav from "@/app/components/SiteNav";
import { loadRules } from "@/app/lib/data";

export const metadata = { title: "The rules" };

export default async function RulesPage() {
  const { rules, cba_eras } = await loadRules();
  const cats = [...new Set(rules.map((r) => r.cat))];
  const current = cba_eras[cba_eras.length - 1];
  return (
    <>
      <SiteNav />
      <div className="mt-6 max-w-3xl">
        <h1 className="text-3xl font-bold tracking-tight">The rules behind the board</h1>
        <p className="prose-narrow mt-2 text-[15px] leading-snug">
          Every flag on a player page points at one of these. The wording is ours; the citations go to Arizona Phil&apos;s roster-rules
          guide at The Cub Reporter, the most careful public explanation of the Major League Rules and the Basic Agreement. Thresholds
          are tagged with the agreement they belong to. The current one ({current.id}) expires {current.effective_to}; whatever replaces
          it gets its own tag and the old numbers stay attached to old seasons.
        </p>
      </div>
      {cats.map((cat) => (
        <section key={cat} className="mt-8 max-w-3xl">
          <h2 className="border-b-2 border-ink pb-1 text-xl font-semibold">{cat}</h2>
          <dl className="mt-3 space-y-5">
            {rules.filter((r) => r.cat === cat).map((r) => (
              <div key={r.id} id={r.id}>
                <dt className="font-medium">
                  {r.title} <span className="ml-2 text-sm font-normal text-ink-soft">{r.cba_era}</span>
                </dt>
                <dd className="mt-0.5 text-[15px] leading-snug">{r.summary}</dd>
                <dd className="mt-0.5 text-sm text-ink-soft">
                  {r.detail}{" "}
                  <a href={r.cite} className="underline" rel="noopener" target="_blank">Source</a>
                </dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
    </>
  );
}
