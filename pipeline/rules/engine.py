"""Evaluate every rule for one player as of a date and emit flags with plain-English reasons.

Input record (dict) assembled by build.build_players; output dict is what the site renders.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from pipeline import config as C
from pipeline.rules import options as O, rule5 as R5, scenarios as SC, service as S
from pipeline.rules.catalog import BY_ID

YEAR = 172


def flag(rule_id: str, status: str, why: str, value=None, **extra) -> dict:
    r = BY_ID[rule_id]
    return {"rule": rule_id, "title": r["title"], "status": status, "value": value, "why": why,
            "cite": r["cite"], "cba_era": r["cba_era"], **extra}


def contract_status_2027(contract: dict | None, mls_end: int | None, super_two: str | None) -> tuple[str, str]:
    """AZ Phil-style 'Contract Status (2027)' label + source."""
    if contract:
        y = next((y for y in contract["years"] if y["season"] == C.CURRENT_SEASON + 1), None)
        t = (y or {}).get("type", "") or ""
        end = contract.get("end_all") or contract.get("end")
        if t == "GUARANTEED":
            label = f"SIGNED THRU {contract.get('end') or end}"
            opts = [yy for yy in contract["years"] if yy["season"] > (contract.get("end") or 0) and "OPTION" in (yy["type"] or "")]
            if opts:
                label += " + " + " / ".join(f"{yy['season']} {yy['type']}" for yy in opts[:2])
            return label, "fangraphs"
        if "OPTION" in t:
            return f"{C.CURRENT_SEASON + 1} {t}", "fangraphs"
        if t.startswith("ARB"):
            return "SALARY ARBITRATION ELIGIBLE" + (' ("SUPER TWO")' if super_two == "likely" else ""), "fangraphs"
        if t.upper().startswith("PRE-ARB"):
            if super_two == "likely":
                return 'SALARY ARBITRATION ELIGIBLE ("SUPER TWO")', "derived"
            if super_two == "possible":
                return 'SALARY ARBITRATION ELIGIBLE ("SUPER TWO") OR PRE-ARBITRATION / AUTO-RENEWAL (TBD)', "derived"
            return "PRE-ARBITRATION / AUTO-RENEWAL", "fangraphs"
        if t.startswith("FREE AGENT"):
            return "FREE AGENT", "fangraphs"
    # derive from service alone
    if mls_end is None:
        return "UNKNOWN", "none"
    if mls_end >= 6 * YEAR:
        return "FREE AGENT (XX-B) UNLESS SIGNED", "derived"
    if mls_end >= 3 * YEAR or super_two == "likely":
        return "SALARY ARBITRATION ELIGIBLE" + (' ("SUPER TWO")' if mls_end < 3 * YEAR else ""), "derived"
    return "PRE-ARBITRATION / AUTO-RENEWAL", "derived"


def _contract_now(c: dict | None, season: int) -> dict:
    if not c:
        return {}
    now = next((y for y in c.get("years", []) if y["season"] == season), {})
    nxt = next((y for y in c.get("years", []) if y["season"] == season + 1), {})
    arb = nxt.get("type") or ""
    return {"salary_now": now.get("salary"), "type_now": now.get("type"), "arb_year": int(arb.split()[-1]) if arb.startswith("ARB") and arb.split()[-1].isdigit() else None,
            "arb_proj": nxt.get("arb_proj")}


def evaluate(p: dict, ctx: dict) -> dict:
    """p: assembled player record; ctx: seasons, era, today, season dates."""
    today: dt.date = ctx["today"]; era = ctx["era"]; seasons = ctx["seasons"]; season = today.year
    od = C.d(seasons[season]["regularSeasonStartDate"]); reg_end = C.d(seasons[season]["regularSeasonEndDate"])
    ws_end = C.d(seasons[season]["postSeasonEndDate"])
    tx: pd.DataFrame = p["tx"]
    flags: list[dict] = []

    # ---------------- options
    ivs = O.option_intervals(tx, seasons, today) if len(tx) else []
    by = O.option_seasons(ivs, seasons, era["option_day_threshold"])
    fg_left = p.get("fg_options")
    fg_left_num = int(fg_left) if fg_left is not None and str(fg_left).isdigit() else None
    full = O.approx_full_seasons(p.get("rosterEntries") or [], seasons, season)
    opt = O.summarize(by, season, era, full_seasons=full, external_left=fg_left_num)
    opt["fangraphs_options"] = fg_left

    # ---------------- service time
    m0 = p.get("mls_prior")               # days through prior season (FanGraphs)
    excl = by[season].days if (season in by and by[season].burned) else 0
    tx_season = tx[tx["season"] == season] if len(tx) else tx
    this = S.season_accrual(tx_season, bool(p.get("on_forty_at_od")), od, today, reg_end, excl) if (len(tx) or p.get("on_forty_at_od")) else 0
    m_now = None if m0 is None else m0 + this
    remaining_days = max(0, (min(reg_end, today) - today).days) if today < reg_end else 0
    # projected end-of-season: assume he keeps his current status
    proj_more = (reg_end - today).days if (today < reg_end and p.get("on_forty") and not (season in by and by[season].burned and p.get("on_option"))) else 0
    m_end = None if m0 is None else min(m0 + min(YEAR, this + proj_more), m0 + YEAR)

    def yrs(d): return C.fmt_mls(d, "+")

    # ---------------- Article XIX-A (5 years)
    posted = any(k in (p.get("acquired") or "") for k in ("(NPB)", "(KBO)", "(CPBL)"))
    if m0 is not None and m0 >= era["xix_a_years"] * YEAR:
        flags.append(flag("opt.xix_a", "yes", f"{yrs(m0)} of MLB service through {season - 1}: can refuse an optional assignment and cannot be outrighted without consent.", value=yrs(m0)))
        flags.append(flag("waiv.xix_a_outright", "yes", f"5+ years of service: an outright assignment requires his consent; otherwise the club must keep, trade or release him."))
    elif m0 is not None and m_now is not None and m_now >= era["xix_a_years"] * YEAR:
        cross = od + dt.timedelta(days=era["xix_a_years"] * YEAR - m0)
        flags.append(flag("opt.xix_a", "yes", f"Crossed 5 years of service on {cross:%b %-d}: can now refuse optional or outright assignment.", value=yrs(m_now), since=cross.isoformat()))
    elif posted:
        flags.append(flag("opt.xix_a", "likely", "Posted from NPB/KBO: posted players almost always negotiate Article XIX-A consent rights into the contract.", value="contractual"))
    elif m_end is not None and m_end >= era["xix_a_years"] * YEAR:
        flags.append(flag("opt.xix_a", "after_season", f"Projects to {yrs(m_end)} by season's end: gains the right to refuse assignments next year."))

    # ---------------- options flags
    left = opt["option_years_left_entering"]
    if m0 is not None and m0 < era["xix_a_years"] * YEAR and not posted:
        if left == 0:
            flags.append(flag("opt.out", "yes", f"Used option years in {', '.join(map(str, opt['option_seasons_burned'][:3]))}: cannot be sent down without clearing outright waivers.", value=0))
        else:
            why = f"{left} option year{'s' if left != 1 else ''} left entering {season}"
            if opt["burning_this_season"]:
                why += f"; {opt['option_days_this_season']} option days this season uses one ({left - 1} after {season})"
            elif opt["option_days_this_season"]:
                why += f"; only {opt['option_days_this_season']} option days this season (under 20, so none used)"
            flags.append(flag("opt.years", "info", why + ".", value=left))
        if opt["fourth_option"]["eligible"]:
            src = opt["fourth_option"]["source"]
            flags.append(flag("opt.fourth", "yes", f"Three options used but fewer than five full seasons ({'per FanGraphs' if src == 'fangraphs' else 'approx. ' + str(opt['fourth_option']['full_seasons_approx']) + ' full seasons'}): a 4th option applies in {season}.", value=src))
        if opt["assignments_available"] is not None:
            used = opt["assignments_used_this_season"]
            flags.append(flag("opt.cap", "info", f"Optioned {used} time{'s' if used != 1 else ''} this season that count toward the cap of {era['optional_assignments_per_season']}: {opt['assignments_available']} left.", value=opt["assignments_available"]))
    prior_outrights = int((tx["type"] == "outrighted").sum()) if len(tx) else 0
    prior_dfa = int((tx["type"] == "designated").sum()) if len(tx) else 0
    prior_claims = int((tx["type"] == "claimed").sum()) if len(tx) else 0

    # ---------------- XX-D
    if m0 is not None and m0 >= era["xx_d_years"] * YEAR and m0 < era["xix_a_years"] * YEAR:
        flags.append(flag("waiv.xx_d", "yes", f"{yrs(m0)} of service (3+): may elect free agency if outrighted, now or deferred to season's end.", value=yrs(m0)))
    elif prior_outrights and (m0 is None or m0 < era["xix_a_years"] * YEAR):
        last = tx.loc[tx["type"] == "outrighted", "date"].max()
        flags.append(flag("waiv.xx_d", "yes", f"Outrighted before ({last:%b %Y}): a second outright lets him elect free agency, so he cannot be stashed in the minors against his will.", value=f"outrighted {prior_outrights}x"))
    elif m0 is not None and m_now is not None and m0 < era["xx_d_years"] * YEAR <= m_now:
        flags.append(flag("waiv.xx_d", "yes", f"Crossed 3 years of service this season: may elect free agency if outrighted.", value=yrs(m_now)))

    # ---------------- Super Two / arbitration / XX-B
    super_two = None
    if m_end is not None and 2 * YEAR <= m_end < 3 * YEAR and this + proj_more >= era["super_two_prior_days"]:
        cutoff = C.parse_mls(C.SUPER_TWO_CUTOFF[max(C.SUPER_TWO_CUTOFF)])
        if m_end >= cutoff:
            super_two = "likely"
            flags.append(flag("mls.super_two", "likely", f"Projects to {yrs(m_end)}: above last year's Super Two cutoff ({C.SUPER_TWO_CUTOFF[max(C.SUPER_TWO_CUTOFF)].replace('.', '+')}), so arbitration-eligible a year early.", value=yrs(m_end)))
        elif m_end >= cutoff - 30:
            super_two = "possible"
            flags.append(flag("mls.super_two", "possible", f"Projects to {yrs(m_end)}: within 30 days of last year's cutoff; Super Two status depends on this fall's line.", value=yrs(m_end)))
    if m_end is not None and m_end >= era["xx_b_years"] * YEAR:
        c = p.get("contract")
        y27 = next((y for y in (c or {}).get("years", []) if y["season"] == season + 1), None)
        if y27 is None or (y27.get("type") or "").startswith("FREE AGENT"):
            flags.append(flag("mls.xx_b", "yes", f"{yrs(m_end)} of service with no contract for {season + 1}: Article XX-B free agent the day after the World Series.", value=yrs(m_end)))
        else:
            flags.append(flag("mls.xx_b", "signed", f"6+ years of service but under contract through {c.get('end_all') or c.get('end')}.", value=yrs(m_end)))
    if m0 is not None and m0 >= 10 * YEAR and p.get("club_since") and (od - p["club_since"]).days >= 5 * 365 - 30:
        flags.append(flag("mls.ten_five", "yes", f"10+ years of service and with the club since {p['club_since']:%Y}: full no-trade rights.", value=yrs(m0)))

    # ---------------- Rule 5
    sign, sign_src = R5.parse_sign_date(p.get("signyear"), p.get("draftyear"), p.get("draft_signing_date"), p.get("first_pro_year"))
    r5 = R5.evaluate(p.get("birth"), sign, season, bool(p.get("on_forty")), prior_outrights, era)
    r5["sign_date"] = sign.isoformat() if sign else None; r5["sign_source"] = sign_src
    if p.get("on_forty"):
        sel = tx[(tx["type"] == "selected") & (tx["date"] >= dt.date(season, 8, 15))]
        if len(sel) and (m0 or 0) < 3 * YEAR and r5.get("first_eligible_year") and r5["first_eligible_year"] <= season:
            flags.append(flag("r5.excluded", "yes", f"Rule 5-eligible and selected to the 40-man on {sel['date'].max():%b %-d}: Draft-Excluded Player, cannot be optioned until 20 days before Opening Day {season + 1}.", value="draft-excluded"))
        r5sel = tx[(tx["type"] == "rule5_selected") & (tx["date"] >= dt.date(season - 1, 12, 1))]
        if len(r5sel):
            flags.append(flag("r5.selected", "yes", f"Rule 5 pick ({r5sel['date'].max():%b %Y}): must stay on the 26-man for 90 active days or be offered back to {p.get('originalteam') or 'his former club'} for $50,000; cannot be optioned.", value="rule 5 selected"))
    elif r5["eligible_this_winter"]:
        flags.append(flag("r5.eligible", "yes", f"Exposed to the {season} Rule 5 draft unless added to the 40-man by the filing deadline: {r5['reason']}.", value=r5["first_eligible_year"]))
    elif r5["eligible_this_winter"] is False and r5.get("first_eligible_year"):
        flags.append(flag("r5.eligible", "no", f"Not yet exposed: {r5['reason']}.", value=r5["first_eligible_year"]))

    # ---------------- IL / roster status
    status = p.get("status_code") or ""
    if status == "D60":
        must = ws_end + dt.timedelta(days=5)
        flags.append(flag("il.sixty", "yes", f"On the 60-day IL: not counting against the 40-man now, but must be reinstated by {must:%b %-d} (5th day after the World Series).", value=must.isoformat()))
    if status in ("D7", "D10", "D15", "D60"):
        flags.append(flag("il.no_assignment", "info", "On the Major League injured list: cannot be optioned or outrighted until he is healthy and reinstated, so an injured fringe player keeps his roster spot by default.", value=status))
    if p.get("on_option") and opt["option_days_this_season"] < era["option_day_threshold"] and left > 0:
        need = era["option_day_threshold"] - opt["option_days_this_season"]
        flags.append(flag("opt.years", "watch", f"Currently optioned with {opt['option_days_this_season']} days this season: {need} more and a {season} option year is used.", value=need))

    # ---------------- contract label
    cs, cs_src = contract_status_2027(p.get("contract"), m_end, super_two)

    out = {
        "id": p["id"], "name": p["name"], "team": p["team_abbr"], "team_id": p["team_id"], "pos": p.get("pos"),
        "bats": p.get("bats"), "throws": p.get("throws"), "birth": p["birth"].isoformat() if p.get("birth") else None,
        "age": (round((today - p["birth"]).days / 365.25, 1) if p.get("birth") else None),
        "on_forty": bool(p.get("on_forty")), "roster_status": p.get("status_label"), "status_code": status,
        "on_option": bool(p.get("on_option")), "il": p.get("il"), "injury": p.get("injury"),
        "mls_prior": None if m0 is None else yrs(m0), "mls_prior_days": m0, "mls_now": None if m_now is None else yrs(m_now),
        "mls_this_season_days": this, "mls_end_proj": None if m_end is None else yrs(m_end),
        "options_left": left, "options_left_source": "reconstruction" + ("+fangraphs(4th)" if opt["fourth_option"]["source"] == "fangraphs" else ""),
        "fangraphs_options": fg_left, "burning_this_season": opt["burning_this_season"],
        "option_days_this_season": opt["option_days_this_season"], "assignments_used": opt["assignments_used_this_season"],
        "assignments_available": opt["assignments_available"], "option_history": opt["seasons"],
        "fourth_option": opt["fourth_option"], "prior_outrights": prior_outrights, "prior_dfa": prior_dfa, "prior_claims": prior_claims,
        "acquired": p.get("acquired"), "acquired_code": p.get("acquired_code"), "original_team": p.get("originalteam"),
        "signyear": p.get("signyear"), "rule5": r5,
        "contract": {k: (p.get("contract") or {}).get(k) for k in ("description", "contract_type", "end_all", "aav", "no_trade")},
        "contract_full": _contract_now(p.get("contract"), season),
        "contract_status": cs, "contract_status_source": cs_src,
        "flags": flags,
        "transactions": [{"date": r.date.isoformat(), "type": r.type, "subtype": r.subtype, "desc": r.description}
                         for r in tx.sort_values("date", ascending=False).head(60).itertuples()] if len(tx) else [],
    }
    if p.get("on_forty"):
        ps = SC.postseason(p, out, ctx)
        out["postseason"] = ps
        if ps.get("status") in ("eligible", "needs_reinstatement", "eligible_after_activation", "replacement_only", "ineligible") and today >= dt.date(season, 9, 1):
            st = {"eligible": "yes", "needs_reinstatement": "watch", "eligible_after_activation": "watch", "replacement_only": "info", "ineligible": "no"}[ps["status"]]
            out["flags"].append(flag("post.eligibility", st, ps["why"], value=ps["label"]))
        out["scenarios"] = SC.scenarios(p, out, ctx, era)
    else:
        out["postseason"] = None
        out["scenarios"] = []
    return out
