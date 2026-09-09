import SiteNav from "@/app/components/SiteNav";
import { loadRules } from "@/app/lib/data";

export const metadata = { title: "The rules" };

export default async function RulesPage() {
  const { rules, cba_eras, cba } = await loadRules();
  const cats = [...new Set(rules.map((r) => r.cat))];
  const current = cba_eras[cba_eras.length - 1];
  return (
    <>
      <SiteNav />
      <div className="mt-6 max-w-3xl">
        <h1 className="text-3xl font-bold tracking-tight">The rules behind the board</h1>
        <p className="prose-narrow mt-2 text-[15px] leading-snug">
          Every flag on a player page points at one of these. Each is cited to the article and printed page of the{" "}
          <a href={cba.pdf} className="underline" rel="noopener" target="_blank">{cba.title}</a> between MLB and the Players
          Association, and the link opens the PDF at that page. A few mechanics, such as Rule 5 eligibility, the waiver claim order and
          the option-year count, sit in the Major League Rules, which the agreement incorporates by reference; those entries name the rule
          that holds the number. The wording here is ours.
        </p>
        <p className="prose-narrow mt-2 text-[15px] leading-snug">
          The current agreement ({current.id}) expires {current.effective_to}. Whatever replaces it gets its own tag, and the old numbers
          stay attached to old seasons.
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
                  <a href={r.cite.url} className="underline" rel="noopener" target="_blank">
                    {r.cite.article}, p. {r.cite.page}
                  </a>
                  {r.cite.mlr ? <span> (number in {r.cite.mlr})</span> : null}
                </dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
      <p className="prose-narrow mt-10 text-sm text-ink-soft">
        Source document: the {cba.title} as published by the Players Association (
        <a href={cba.source_url} className="underline" rel="noopener" target="_blank">original PDF</a>), mirrored here so page links stay
        stable. Arizona Phil&apos;s roster-rules guide at The Cub Reporter remains the best plain-English companion and was the map that
        pointed us to the right articles.
      </p>
    </>
  );
}
