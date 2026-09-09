import { promises as fs } from "fs";
import path from "path";
import type { Deadlines, Meta, PlayerFull, PlayerSummary, Rule, Team, TeamCounts } from "@/app/types";

const DATA = path.join(process.cwd(), "public", "data");

async function readJson<T>(rel: string): Promise<T> {
  return JSON.parse(await fs.readFile(path.join(DATA, rel), "utf8")) as T;
}

export async function loadTeams(): Promise<{ meta: Meta; deadlines: Deadlines; teams: { abbr: string; name: string; id: number; counts: TeamCounts }[] }> {
  return readJson("teams.json");
}

export async function loadTeam(abbr: string): Promise<Team> {
  return readJson(`teams/${abbr}.json`);
}

export async function loadTeamPlayers(abbr: string): Promise<Record<string, PlayerFull>> {
  return readJson(`players/${abbr}.json`);
}

export async function loadRules(): Promise<{ meta: Meta; cba_eras: { id: string; effective_from: string; effective_to: string | null }[]; cba: { title: string; pdf: string; source_url: string }; rules: Rule[] }> {
  return readJson("rules.json");
}

export async function loadOutOfOptions(): Promise<{ meta: Meta; players: PlayerSummary[] }> {
  return readJson("out_of_options.json");
}

export async function loadRule5(): Promise<{ meta: Meta; deadlines: Deadlines; players: { team: string; id: number; name: string; pos: string | null; age: number | null; acquired: string | null; signyear: string | null; prior_outrights: number; rule5: PlayerFull["rule5"] }[] }> {
  return readJson("rule5.json");
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function loadValidation(): Promise<any> {
  return readJson("validation.json");
}

export const TEAM_ORDER = ["CHC", "AZ", "ATL", "BAL", "BOS", "CIN", "CLE", "COL", "CWS", "DET", "HOU", "KC", "LAA", "LAD", "MIA", "MIL", "MIN", "NYM", "NYY", "ATH", "PHI", "PIT", "SD", "SEA", "SF", "STL", "TB", "TEX", "TOR", "WSH"];

export function fmtDate(s: string | null | undefined): string {
  if (!s) return "";
  const d = new Date(s + (s.length === 10 ? "T12:00:00Z" : ""));
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
}
