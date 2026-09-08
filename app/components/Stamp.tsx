import type { Flag } from "@/app/types";

// Short labels for the board. Color = what the flag means for the club:
// red = expendable/exposed, green = the player holds a consent right, amber = watch.
const LABEL: Record<string, string> = {
  "opt.out": "OUT OF OPTIONS",
  "opt.xix_a": "XIX-A",
  "waiv.xix_a_outright": "",
  "waiv.xx_d": "XX-D",
  "opt.fourth": "4TH OPTION",
  "r5.eligible": "RULE 5",
  "r5.excluded": "DRAFT-EXCLUDED",
  "r5.selected": "RULE 5 PICK",
  "il.sixty": "60-DAY IL",
  "mls.super_two": "SUPER TWO",
  "mls.xx_b": "XX-B FA",
  "mls.ten_five": "10-AND-5",
};

export function stampClass(f: Flag): string {
  if (f.rule === "opt.out" || (f.rule === "r5.eligible" && f.status === "yes")) return "stamp stamp-red";
  if (f.rule === "opt.xix_a" || f.rule === "waiv.xx_d" || f.rule === "mls.ten_five") return "stamp stamp-green";
  if (f.rule === "mls.xx_b") return f.status === "yes" ? "stamp stamp-red" : "stamp stamp-ink";
  if (f.status === "watch" || f.status === "likely" || f.status === "possible" || f.status === "after_season") return "stamp stamp-amber";
  return "stamp stamp-ink";
}

export function stampLabel(f: Flag): string | null {
  const l = LABEL[f.rule];
  if (l === undefined || l === "") return null;
  if (f.rule === "opt.xix_a" && f.status === "after_season") return "XIX-A NEXT YEAR";
  if (f.rule === "opt.xix_a" && f.status === "likely") return "XIX-A (POSTED)";
  if (f.rule === "mls.super_two" && f.status === "possible") return "SUPER TWO?";
  if (f.rule === "mls.xx_b" && f.status === "signed") return null;
  if (f.rule === "r5.eligible" && f.status === "no") return null;
  return l;
}

export default function Stamps({ flags }: { flags: Flag[] }) {
  const items = flags.map((f) => ({ f, label: stampLabel(f) })).filter((x) => x.label);
  if (!items.length) return null;
  return (
    <span>
      {items.map(({ f, label }) => (
        <span key={f.rule + f.status} className={stampClass(f)} title={f.why}>
          {label}
        </span>
      ))}
    </span>
  );
}
