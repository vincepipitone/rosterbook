export type Flag = {
  rule: string;
  title: string;
  status: "yes" | "no" | "info" | "watch" | "likely" | "possible" | "after_season" | "signed";
  value: string | number | null;
  why: string;
  since?: string | null;
  cite?: Cite;
  cba_era?: string;
};

export type ModelReason = { feature: string; label: string; value: number | string | null; contrib: number };
export type ModelOut = {
  p_none: number; p_designated: number; p_optioned: number; p_traded: number; p_released: number; p_cut: number;
  reasons_designated: ModelReason[]; reasons_optioned: ModelReason[];
} | null;

export type PlayerSummary = {
  id: number;
  model: ModelOut;
  proj: { zips?: { war: number | null; pa: number | null; ip: number | null }; steamer?: { war: number | null; pa: number | null; ip: number | null } } | null;
  war_now: number | null;
  context: { group: string; same_group_on_forty: number; same_group_leaving: string[] } | null;
  name: string;
  team: string;
  pos: string | null;
  bats: string | null;
  throws: string | null;
  age: number | null;
  on_forty: boolean;
  roster_status: string;
  status_code: string;
  on_option: boolean;
  il: string | null;
  injury: string | null;
  mls_prior: string | null;
  mls_prior_days: number | null;
  mls_now: string | null;
  mls_this_season_days: number;
  mls_end_proj: string | null;
  options_left: number;
  options_left_source: string;
  fangraphs_options: string | null;
  burning_this_season: boolean;
  option_days_this_season: number;
  assignments_used: number;
  assignments_available: number | null;
  prior_outrights: number;
  prior_dfa: number;
  acquired: string | null;
  acquired_code: string | null;
  contract_status: string;
  contract_status_source: string;
  contract: string | null;
  fourth_option: { eligible: boolean; source: string | null; full_seasons_approx: number | null };
  flags: Flag[];
};

export type Rule5Info = {
  eligible_this_winter: boolean | null;
  first_eligible_year: number | null;
  age_june5: number | null;
  clock: number | null;
  reason: string;
  sign_date?: string | null;
  sign_source?: string;
  always_eligible_outright?: boolean;
};

export type PlayerFull = PlayerSummary & {
  birth: string | null;
  original_team: string | null;
  signyear: string | null;
  rule5: Rule5Info;
  option_history: Record<string, { days: number; burned: boolean; assignments: number; intervals: { start: string; end: string | null; close: string | null; days: number; source: string; exempt: string | null }[] }>;
  contract: { description: string | null; contract_type: string | null; end_all: number | null; aav: number | null; no_trade: string | null } | null;
  transactions: { date: string; type: string; subtype: string; desc: string }[];
  postseason: { status: string; label: string; why: string; cutoff: string; il_start?: string | null; days_served?: number | null } | null;
  scenarios: { action: string; possible: boolean; rules: string[]; text: string }[];
};

export type TeamCounts = { forty: number; il60: number; optioned: number; out_of_options: number; xxb_fa: number; arb: number; rule5_exposed: number; pool: number };

export type Team = {
  abbr: string;
  name: string;
  id: number;
  counts: TeamCounts;
  players: PlayerSummary[];
  rule5_pool: { id: number; name: string; pos: string | null; age: number | null; acquired: string | null; signyear: string | null; rule5: Rule5Info; prior_outrights: number }[];
};

export type Meta = { generated_at: string; fg_snapshot: string; contracts_snapshot: string; statsapi_snapshot: string; season: number; cba_era: string; n_players: number; n_forty: number };
export type Deadlines = Record<string, string | null>;

export type Cite = { source: string; article: string; page: number; pdf_page: number; url: string; mlr: string | null };
export type Rule = { id: string; cat: string; cba_era: string; title: string; summary: string; detail: string; cite: Cite };
