"""Per-player scenarios: post-season eligibility as it stands, and what each roster move would mean.

Post-season eligibility is Major League Rule 40 (the Basic Agreement's Attachment 25 defers to
the Major League Rules). Mechanics follow Arizona Phil's "Post-Season Roster Eligibility":
the eligibility list is fixed at 12:00 PM ET on September 1 (2025 onward); a 60-day IL player
is eligible only after 60 days on the list and reinstatement; a player outrighted after the
cutoff loses automatic eligibility and can only return as an injury replacement if he stays in
the organization continuously; injury replacements must come from players who were in the
organization before the cutoff and need a 40-man spot.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from pipeline import config as C

YEAR = 172
JOIN_TYPES = {"selected", "claimed", "traded", "signed_fa", "rule5_selected", "purchased"}


def _forty_join(tx: pd.DataFrame, team_id: int, season: int) -> tuple[dt.date | None, str | None]:
    """Date and type of the transaction that put the player on this club's 40-man for the current stint."""
    if not len(tx):
        return None, None
    t = tx[(tx["season"] >= season - 1)]
    cand = t[(t["type"].isin(JOIN_TYPES)) & ((t["to_team"] == team_id) | (t["to_team"].isna() & (t["type"] == "selected")))]
    cand = cand[~((cand["type"] == "signed_fa") & cand["description"].str.contains("minor league", case=False))]
    if not len(cand):
        return None, None
    r = cand.sort_values("date").iloc[-1]
    return r["date"], r["type"]


def _il60_start(tx: pd.DataFrame, season: int) -> dt.date | None:
    """Original IL placement date behind the current 60-day stint (a transfer keeps the earlier days)."""
    if not len(tx):
        return None
    t = tx[tx["season"] == season].sort_values("date")
    il60 = t[t["subtype"].isin(["il_60", "il_60_transfer"])]
    if not len(il60):
        return None
    last = il60.iloc[-1]
    if last["subtype"] == "il_60_transfer":
        before = t[(t["date"] <= last["date"]) & (t["subtype"].isin(["il_7", "il_10", "il_15"]))]
        if len(before):
            return before.iloc[-1]["effective_date"] or before.iloc[-1]["date"]
    return last["effective_date"] or last["date"]


def postseason(p: dict, out: dict, ctx: dict) -> dict:
    today: dt.date = ctx["today"]; season = today.year
    cutoff = dt.date(season, 9, 1)
    reg_end = C.d(ctx["seasons"][season]["regularSeasonEndDate"])
    tx = p["tx"]
    status = out["status_code"]
    join_date, join_type = _forty_join(tx, p["team_id"], season)
    res = {"status": None, "label": None, "why": "", "rule": "post.eligibility", "cutoff": cutoff.isoformat()}
    if not p.get("on_forty"):
        res.update(status="replacement_only", label="Injury replacement only",
                   why=f"Not on the 40-man at the {cutoff:%b %-d} cutoff. He can join a post-season roster only as an approved replacement for an injured eligible player, and only if he was in the organization before noon ET {cutoff:%b %-d}; that also requires a 40-man spot.")
        return res
    if status in ("RST", "SU", "DEC"):
        res.update(status="ineligible", label="Not post-season eligible", why="On the restricted, suspended or ineligible list at or after the September 1 cutoff.")
        return res
    if today < cutoff:
        res.update(status="pending", label="Eligible if on the 40-man Sept 1",
                   why=f"The post-season eligibility list is fixed at noon ET on {cutoff:%b %-d}. He qualifies if he is on the 40-man, the 60-day IL or the military list at that moment and stays there through the post-season.")
        return res
    joined_after = join_date is not None and join_date >= cutoff
    if joined_after:
        in_org = join_type == "selected"
        res.update(status="replacement_only", label="Injury replacement only",
                   why=(f"Added to the 40-man on {join_date:%b %-d}, after the {cutoff:%b %-d} noon cutoff, so he is not automatically eligible. "
                        + ("He was in the organization before the cutoff, so he can be approved as a replacement for an injured eligible player." if in_org
                           else "He was not in the organization before the cutoff, so he cannot be added to a post-season roster this year.")))
        return res
    if status == "D60":
        start = _il60_start(tx, season)
        served = (today - start).days if start else None
        need = None if served is None else max(0, 60 - served)
        earliest = (start + dt.timedelta(days=60)) if start else None
        forty_full = p.get("club_forty_count", 40) >= 40
        why = "On the 60-day IL before the cutoff, so he is on the eligibility list. "
        if served is None:
            why += "He becomes eligible to play once he has spent 60 days on the injured list and is reinstated."
        elif need > 0:
            why += f"He has served {served} of the 60 required days (eligible to be activated from {earliest:%b %-d}), then must be reinstated to the 40-man and 26-man."
        else:
            why += f"He has served the 60 days ({served}), so the only step is reinstatement: the club must open a 40-man spot" + (" (the 40-man is full, so someone must be traded, outrighted, released or moved to the 60-day IL)" if forty_full else "") + " and a 26-man spot before the series roster is submitted."
        res.update(status="needs_reinstatement" if (need is None or need > 0 or forty_full) else "eligible_after_activation",
                   label="Eligible once reinstated", why=why, il_start=start.isoformat() if start else None, days_served=served)
        return res
    res.update(status="eligible", label="Post-season eligible",
               why=f"On the 40-man before noon ET {cutoff:%b %-d}. He stays eligible as long as he remains on the 40-man or 60-day IL through the post-season; an outright after the cutoff would end automatic eligibility.")
    return res


def scenarios(p: dict, out: dict, ctx: dict, era: dict) -> list[dict]:
    today: dt.date = ctx["today"]; season = today.year
    s = ctx["seasons"][season]
    od = C.d(s["regularSeasonStartDate"]); reg_end = C.d(s["regularSeasonEndDate"]); ws_end = C.d(s["postSeasonEndDate"])
    dl = C.DEADLINES.get(season, {})
    deadline = C.d(dl.get("trade_deadline")); tender = C.d(dl.get("tender"))
    m0 = out.get("mls_prior_days"); m_now = C.parse_mls(out["mls_now"].replace("+", ".")) if out.get("mls_now") else m0
    five = m_now is not None and m_now >= era["xix_a_years"] * YEAR
    three = m_now is not None and m_now >= era["xx_d_years"] * YEAR
    six_end = out.get("mls_end_proj") and C.parse_mls(out["mls_end_proj"].replace("+", ".")) >= era["xx_b_years"] * YEAR
    posted = any(f["rule"] == "opt.xix_a" and f["status"] == "likely" for f in out["flags"])
    prior_out = out["prior_outrights"]
    status = out["status_code"]; on_il = status in ("D7", "D10", "D15", "D60")
    left = out["options_left"]; avail = out["assignments_available"]
    in_season = od <= today <= reg_end
    after_cutoff = today >= dt.date(season, 9, 1)
    contract = p.get("contract") or {}
    desc = contract.get("description")
    rule5_pick = any(f["rule"] == "r5.selected" for f in out["flags"])
    excluded = any(f["rule"] == "r5.excluded" for f in out["flags"])
    ps = out.get("postseason") or {}
    out_list: list[dict] = []

    # ---------------- option
    if five or posted:
        out_list.append(dict(action="Option him to the minors", possible=False, rules=["opt.xix_a"],
                             text="Not without his consent: with five years of service" + (" (or, for a posted player, a contractual clause)" if posted else "") + " he can refuse the assignment or elect free agency instead. The club's only unilateral moves are to keep him, trade him, or release him."))
    elif on_il:
        out_list.append(dict(action="Option him to the minors", possible=False, rules=["il.no_assignment"],
                             text="Not while he is on the injured list. He must be healthy and reinstated first; a rehab assignment (20 days, 30 for pitchers, with his consent) is the only way to send him down injured."))
    elif rule5_pick or excluded:
        out_list.append(dict(action="Option him to the minors", possible=False, rules=["r5.selected" if rule5_pick else "r5.excluded"],
                             text=("A Rule 5 pick cannot be optioned; he must stay on the 26-man or be offered back." if rule5_pick
                                   else f"Draft-Excluded status blocks any option until 20 days before Opening Day {season + 1}.")))
    elif left == 0:
        out_list.append(dict(action="Option him to the minors", possible=False, rules=["opt.out"],
                             text="Out of options: the only route to the minors is outright waivers, where any club can claim him for $50,000."))
    else:
        parts = [f"Yes, {left} option year{'s' if left != 1 else ''} left."]
        if avail is not None:
            parts.append(f"{avail} of the five optional assignments for {season} remain." if avail > 0 else f"But all five optional assignments for {season} are used, so a sixth trip would need outright waivers.")
        days = out["option_days_this_season"]
        if in_season and not out["burning_this_season"]:
            parts.append(f"He has {days} option days this season; at 20 a {season} option year is used and those days stop counting as service.")
        elif out["burning_this_season"]:
            parts.append(f"A {season} option year is already used ({days} days), so further trips this season cost nothing extra.")
        pos_pitcher = (out.get("pos") or "").upper() in ("SP", "RP", "P", "LHP", "RHP")
        parts.append(f"Once down he must stay {'15' if pos_pitcher else '10'} days unless he replaces an injured or traded player.")
        if three or prior_out:
            parts.append("An option does not trigger his Article XX-D right; only an outright would.")
        out_list.append(dict(action="Option him to the minors", possible=True, rules=["opt.years", "opt.cap", "opt.recall_min"], text=" ".join(parts)))

    # ---------------- DFA / outright
    parts = ["The club has 7 days to trade him, pass him through outright waivers, or release him; he is paid at the major-league rate and keeps accruing service in the meantime.",
             "On outright waivers any club can claim him for $50,000, worst record first, and the claiming club takes his contract" + (f" ({desc})" if desc else "") + "."]
    if five or posted:
        parts.append("If he clears, he cannot be outrighted without his consent: he can refuse and force a release with his contract intact, or elect free agency (forfeiting termination pay).")
    elif three or prior_out:
        parts.append(("Three-plus years of service" if three else f"He was outrighted before ({prior_out}x)") + " give him the Article XX-D choice: elect free agency immediately (giving up the rest of his salary) or accept the assignment, keep getting paid, and elect free agency after the season unless he is added back to a 40-man first.")
    else:
        parts.append("If he clears, the club can outright him to the minors and he has no say; he stays under club control on a minor-league deal. He would then be Rule 5-eligible and would hold XX-D rights against any future outright.")
    if in_season and after_cutoff:
        if ps.get("status") in ("eligible", "needs_reinstatement", "eligible_after_activation"):
            parts.append("Post-season: an outright after the September 1 cutoff ends his automatic eligibility. He could only return as an approved injury replacement, and only if he accepts the outright and stays on a minor-league reserve list in the organization without interruption; a release makes him ineligible for anyone this October.")
    if on_il:
        parts.append("Because he is on the injured list he cannot be outrighted until he is healthy and reinstated, so a DFA now would have to end in a trade or a release.")
    if desc and contract.get("aav") and contract.get("aav", 0) >= 3_000_000:
        parts.append("With real money left on the contract a claim is unlikely; the usual outcome is clearing waivers, then release, with the club paying the balance less what a new club pays him.")
    out_list.append(dict(action="Designate him for assignment (or put him on outright waivers)", possible=True,
                         rules=["dfa.clock", "waiv.outright", "waiv.xix_a_outright" if five else "waiv.xx_d"], text=" ".join(parts)))

    # ---------------- release
    if in_season:
        pay = "the full unpaid balance of this season's salary"
    elif today > reg_end and (tender is None or today <= tender):
        pay = f"nothing if he is simply not tendered a contract by {tender:%b %-d}" if tender else "nothing if he is non-tendered"
    else:
        pay = "30 days' pay (45 days if released within 15 days of Opening Day)"
    parts = [f"Release waivers cost a claiming club $1 but the claimant assumes the whole contract, so expensive players clear. The club owes {pay}, offset by whatever another club pays him this year."]
    if "SIGNED THRU" in (out.get("contract_status") or ""):
        parts.append("The guaranteed years remain owed in full.")
    if in_season and after_cutoff:
        parts.append("A released player is not post-season eligible for any club this year.")
    out_list.append(dict(action="Release him", possible=True, rules=["waiv.release", "waiv.split_rate"], text=" ".join(parts)))

    # ---------------- trade
    parts = []
    if deadline and today > deadline and today <= ws_end:
        parts.append(f"Not now: players on major-league contracts cannot be traded after the {deadline:%b %-d} deadline until the day after the World Series.")
        possible = False
    else:
        possible = True
        if any(f["rule"] == "mls.ten_five" for f in out["flags"]):
            parts.append("Only with his written consent: he holds 10-and-5 rights.")
        if contract.get("no_trade"):
            parts.append(f"Contract: {contract['no_trade']}.")
        june15 = any(f["rule"] == "trade.june15" for f in out["flags"])
        if june15:
            parts.append("As a free-agent signee he cannot be dealt before June 16 without consent.")
        if out.get("on_option"):
            parts.append("An optioned player can be traded; the acquiring club may option him again within 24 hours without using an assignment.")
        if on_il:
            parts.append("Injured players can be traded; his IL days carry over to the new club.")
        if not parts:
            parts.append("Yes, no restrictions on the books.")
    out_list.append(dict(action="Trade him", possible=possible, rules=["trade.deadline", "mls.ten_five", "trade.june15"], text=" ".join(parts)))

    # ---------------- offseason / tender
    if out.get("contract_status"):
        cs = out["contract_status"]
        if cs.startswith("FREE AGENT") or six_end and "SIGNED" not in cs and "OPTION" not in cs:
            parts = [f"He becomes an Article XX-B free agent at 9 AM ET the day after the World Series; only the club can talk to him for five days after that."]
            parts.append("A qualifying offer is possible only if he has been with the club since Opening Day and never received one before." if not any(f["rule"] == "money.qo" for f in out["flags"]) else "")
            out_list.append(dict(action="Let the season end", possible=True, rules=["mls.xx_b", "money.qo"], text=" ".join(x for x in parts if x)))
        elif cs.startswith("SALARY ARBITRATION"):
            out_list.append(dict(action="Non-tender him", possible=True, rules=["money.tender", "mls.arb", "money.max_cut"],
                                 text=f"At the tender deadline ({tender.strftime('%b %-d') if tender else 'the Friday before Thanksgiving'}) the club can decline to offer a contract: no waivers, no termination pay, and he can be re-signed the same night. Tendering means arbitration, where he cannot be cut more than 20% from this year's salary."))
        elif cs.startswith("PRE-ARB"):
            out_list.append(dict(action="Renew him for next year", possible=True, rules=["money.min_salary", "money.tender"],
                                 text=f"Pre-arbitration: the club sets his {season + 1} salary near the minimum (${era['min_salary'].get(season + 1, era['min_salary'][season]):,} floor{' likely higher after a Super Two ruling' if any(f['rule'] == 'mls.super_two' for f in out['flags']) else ''}) and he has no leverage beyond a non-tender."))
        elif cs.startswith(f"{season + 1} ") and "OPTION" in cs:
            out_list.append(dict(action="Decide his contract option", possible=True, rules=["mls.xx_b"],
                                 text=f"{cs.title()}: the decision must be made inside the five-day quiet period after the World Series. If declined and he has six years of service, he is a free agent immediately."))
        elif cs.startswith("SIGNED THRU"):
            out_list.append(dict(action="Let the season end", possible=True, rules=["waiv.release"],
                                 text=f"Under contract ({desc or cs.title()}): nothing to decide this winter. Moving him later means trading the contract or releasing him and paying the guaranteed years in full."))
    return out_list
