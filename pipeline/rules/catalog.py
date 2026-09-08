"""The rule catalog: every rule the engine evaluates, in our own words, with a citation.

Prose is paraphrased from the CBA/Major League Rules as explained in Arizona Phil's "MLB Roster
Rules" (thecubreporter.com, CC BY-ND 3.0) and MLB.com's transactions glossary. `cba_era` marks the
agreement a threshold belongs to; the 2022-2026 Basic Agreement expires 2026-12-01.
"""
from __future__ import annotations

TCR = "https://www.thecubreporter.com/book/export/html/"
GLOSS = "https://www.mlb.com/glossary/transactions/"

RULES: list[dict] = [
    # ---------------------------------------------------------------- roster limits
    dict(id="roster.active", cat="Roster limits", cba_era="2022-2026", title="26-man Active List",
         summary="26 players Opening Day through Aug 31, 28 from Sep 1; max 13 pitchers (14 in September).",
         detail="Only players on the 40-man reserve list can be on the Active List. The pitcher cap is enforced "
                "by a position/pitcher/two-way designation locked before Opening Day.",
         cite=TCR + "3508"),
    dict(id="roster.forty", cat="Roster limits", cba_era="2022-2026", title="40-man Reserve List",
         summary="Max 40 players under major-league contract. Players on the 60-day IL do not count.",
         detail="Every optioned player, every 7/10/15-day IL player and every DFA'd player (until resolved) "
                "occupies a spot. The 60-day IL is the only way to park a contract off the 40.",
         cite=TCR + "3507"),
    dict(id="il.sixty", cat="Injured list", cba_era="2022-2026", title="60-day IL and the November crunch",
         summary="60-day IL players are off the 40-man, but must be reinstated by 5 PM ET on the 5th day after the World Series.",
         detail="A club needs a full 40-man to place someone on the 60-day IL. Reinstatement after the Series "
                "is mandatory even if the player is still hurt, which is why November 40-man math is tight "
                "before the reserve-list filing deadline and Rule 5 draft.",
         cite=TCR + "3538"),
    # ---------------------------------------------------------------- options
    dict(id="opt.years", cat="Options", cba_era="2022-2026", title="Three option years",
         summary="A player gets three option years. One is used when he spends 20+ days on optional assignment in a season.",
         detail="19 or fewer days in a season does not use an option and those days count as MLB service. "
                "Spring-training and postseason days never count toward the 20.",
         cite=TCR + "3521"),
    dict(id="opt.fourth", cat="Options", cba_era="2022-2026", title="Fourth option",
         summary="A player who has used three options but has fewer than five full seasons gets a fourth.",
         detail="A full season is 90+ days on an active list (any level), or 30+ active days plus IL time totaling 90. "
                "Minor-league IL days are not public, so this tool approximates full seasons and shows its source.",
         cite=TCR + "3522"),
    dict(id="opt.cap", cat="Options", cba_era="2022-2026", title="Five optional assignments per season",
         summary="A player can be optioned at most five times in a season (2022 CBA); a sixth trip requires outright waivers.",
         detail="Spring-training options, a return after serving as the 27th man for a doubleheader, and an option "
                "within 24 hours of arriving by trade do not count. Option years left and assignments left are "
                "different numbers.",
         cite=TCR + "3523"),
    dict(id="opt.recall_min", cat="Options", cba_era="2022-2026", title="Minimum stay on option",
         summary="An optioned position player must stay down 10 days, a pitcher 15, unless replacing an injured or traded player.",
         detail="Exceptions: trade, waiver claim, doubleheader 27th man, or recall to replace a player placed on the IL, "
                "bereavement, paternity or restricted lists.",
         cite=TCR + "3523"),
    dict(id="opt.out", cat="Options", cba_era="2022-2026", title="Out of options",
         summary="With no option years left, the only way to the minors is through irrevocable outright waivers.",
         detail="This is the single biggest driver of spring DFAs: a club must carry him on the 26-man or risk losing him.",
         cite=TCR + "3521"),
    dict(id="opt.xix_a", cat="Options", cba_era="2022-2026", title="Article XIX-A: five years, no forced option",
         summary="A player with 5+ years of MLB service can refuse an optional assignment, or elect free agency instead.",
         detail="Posted NPB/KBO players usually negotiate the same right. If he refuses, the club must keep him on the "
                "Active List, trade him, or release him.",
         cite=TCR + "3523"),
    # ---------------------------------------------------------------- waivers / DFA
    dict(id="dfa.clock", cat="Waivers & DFA", cba_era="2022-2026", title="Designated for assignment",
         summary="DFA removes a player from the 40-man; the club then has 7 days to trade, waive, outright or release him.",
         detail="He is paid at the major-league rate during the DFA period and accrues MLB service in-season. "
                "Christmas week is excluded from the 7 days.",
         cite=TCR + "3535"),
    dict(id="waiv.outright", cat="Waivers & DFA", cba_era="2022-2026", title="Outright waivers",
         summary="Irrevocable, $50,000 claim price; claim priority goes to the worst record, either league.",
         detail="Prior-season standings are used through day 30 of the season, current standings after. Optional and "
                "trade waivers no longer exist (2017 and 2019).",
         cite=TCR + "3530"),
    dict(id="waiv.xx_d", cat="Waivers & DFA", cba_era="2022-2026", title="Article XX-D: the right to walk",
         summary="A player with 3+ years of service, or one who has been outrighted before, may elect free agency instead of accepting an outright.",
         detail="He can leave immediately (forfeiting the rest of his salary) or accept the assignment and defer the choice "
                "to the end of the season, keeping his pay. A Super Two-only qualifier must decide immediately.",
         cite=TCR + "3531"),
    dict(id="waiv.xix_a_outright", cat="Waivers & DFA", cba_era="2022-2026", title="Article XIX-A: five years, no forced outright",
         summary="A player with 5+ years of service can refuse an outright assignment altogether.",
         detail="The club must then keep him on the 40-man, trade him, or release him with his contract intact.",
         cite=TCR + "3531"),
    dict(id="waiv.release", cat="Waivers & DFA", cba_era="2022-2026", title="Release waivers",
         summary="$1 claim price but the claiming club owes the full remaining salary, so expensive players clear.",
         detail="Once released, the former club pays the balance and any new club pays only the prorated minimum.",
         cite=TCR + "3534"),
    # ---------------------------------------------------------------- rule 5
    dict(id="r5.eligible", cat="Rule 5", cba_era="2022-2026", title="Rule 5 eligibility",
         summary="Signed at 18 or younger: eligible at the 5th Rule 5 draft after signing. 19 or older: the 4th.",
         detail="Age is measured on the June 5 before the first contract. A player previously outrighted is always eligible. "
                "A player on the 40-man at the filing deadline is protected.",
         cite=TCR + "3517"),
    dict(id="r5.selected", cat="Rule 5", cba_era="2022-2026", title="Rule 5 selected player",
         summary="$100,000 pick who must stay on the 26-man (90 active days, carrying into a second season) or be offered back for $50,000.",
         detail="He can be traded any time but cannot be optioned. IL days do not count toward the 90. "
                "Triple-A phase picks ($24,000) need no 40-man spot and carry no offer-back.",
         cite=TCR + "3520"),
    dict(id="r5.excluded", cat="Rule 5", cba_era="2022-2026", title="Draft-Excluded Player",
         summary="A Rule 5-eligible player with under 3 years of service added to the 40-man after Aug 15 cannot be optioned until 20 days before Opening Day.",
         detail="It stops clubs from protecting a player in September and quietly stashing him in March. He can still be "
                "traded, non-tendered or released.",
         cite=TCR + "3520"),
    dict(id="r5.filing", cat="Rule 5", cba_era="2022-2026", title="Reserve-list filing deadline",
         summary="Clubs must set their 40-man about a week before the tender deadline (the Friday before Thanksgiving).",
         detail="Between filing and the draft, eligible minor leaguers cannot be added, traded or released, and no player "
                "may be outrighted from three days before the draft.",
         cite=TCR + "3517"),
    # ---------------------------------------------------------------- service time
    dict(id="mls.year", cat="Service time", cba_era="2022-2026", title="172 days = one year",
         summary="A season is 182-187 days but service caps at 172. Active, IL, paternity and bereavement days all count.",
         detail="Days on optional assignment count only in a season with 19 or fewer of them.",
         cite=TCR + "4043"),
    dict(id="mls.super_two", cat="Service time", cba_era="2022-2026", title="Super Two",
         summary="The top 22% by service among players with 2-3 years (and 86+ days in the prior season) reach arbitration a year early.",
         detail="The cutoff is announced each fall; recent cutoffs 2+118 to 2+140. Super Twos go through arbitration four times.",
         cite=TCR + "3515"),
    dict(id="mls.arb", cat="Service time", cba_era="2022-2026", title="Arbitration",
         summary="3 to 6 years of service: salary set by negotiation or a hearing, not by the club alone.",
         detail="Figures are exchanged in mid-January. Non-tendering before the tender deadline is the waiver-free exit.",
         cite=TCR + "3515"),
    dict(id="mls.xx_b", cat="Service time", cba_era="2022-2026", title="Article XX-B free agency",
         summary="6+ years of service with an expiring contract: free agent the day after the World Series.",
         detail="An XX-B free agent who signs a major-league deal after the 5th day post-Series cannot be traded before June 15 "
                "without consent. A previously received qualifying offer cannot be repeated.",
         cite=TCR + "5361"),
    dict(id="mls.ten_five", cat="Service time", cba_era="2022-2026", title="10-and-5 rights",
         summary="10 years of service, the last 5 with the same club: full no-trade protection.",
         detail="Waivable by the player; often the reason a veteran 'approves' a deadline deal.",
         cite=TCR + "3524"),
    dict(id="mls.roy", cat="Service time", cba_era="2022-2026", title="Rookie of the Year service credit",
         summary="A top-2 Rookie of the Year finisher receives a full year of service regardless of call-up date (2022 CBA).",
         detail="Pairs with the Prospect Promotion Incentive draft pick for clubs that carry top prospects on Opening Day.",
         cite=TCR + "6112"),
    # ---------------------------------------------------------------- minor-league free agency
    dict(id="milb.rule9", cat="Minor-league free agency", cba_era="2022-2026", title="Rule 9 minor-league free agency",
         summary="A player not on a 40-man who has spent parts of seven seasons on minor-league rosters becomes a free agent five days after the World Series.",
         detail="Players first signed at 19+ from June 2023 onward reach it after six seasons. A second contract after a release resets the clock.",
         cite=TCR + "4400"),
    dict(id="milb.xx_b_optout", cat="Minor-league free agency", cba_era="2022-2026", title="XX-B veteran opt-outs",
         summary="A 6-year veteran on a minor-league deal signed 10+ days before Opening Day can opt out 4 days before Opening Day, May 1 and June 1.",
         detail="The $100,000 retention bonus was eliminated in 2023.",
         cite=TCR + "5361"),
    # ---------------------------------------------------------------- money
    dict(id="money.tender", cat="Contracts", cba_era="2022-2026", title="Tender deadline",
         summary="The Friday before Thanksgiving, 8 PM ET: unsigned players not tendered a contract become free agents.",
         detail="No waivers, no termination pay. It is the one day a club can drop anyone, healthy or hurt, without waiver "
                "risk, and re-sign him the same night.",
         cite=TCR + "3513"),
    dict(id="money.qo", cat="Contracts", cba_era="2022-2026", title="Qualifying offer",
         summary="One-year offer at the average of the top 125 salaries ($22.025M for 2026), only to a player who spent the whole season with the club and never received one before.",
         detail="Declining it attaches draft-pick compensation to the player, which lowers his market.",
         cite=TCR + "3512"),
    dict(id="trade.june15", cat="Trades", cba_era="2022-2026", title="June 15 no-trade for XX-B signees",
         summary="A 6-year free agent who signs a major-league contract has an automatic no-trade through June 15 of the next season.",
         detail="Applies even when he re-signs with his own club. Not for players who signed minor-league deals.",
         cite=TCR + "3524"),
    dict(id="trade.deadline", cat="Trades", cba_era="2022-2026", title="Trade deadline",
         summary="No trades of players on major-league contracts from the deadline (late July / early August) until the day after the World Series.",
         detail="Waiver trades ended in 2019; a player claimed in August cannot be flipped for value.",
         cite=TCR + "3524"),
]

BY_ID = {r["id"]: r for r in RULES}
