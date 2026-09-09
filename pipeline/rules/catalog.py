"""The rule catalog: every rule the engine evaluates, in our own words, cited to the 2022-2026
Basic Agreement (the CBA) by article and printed page, with a deep link into the PDF.

A few mechanics live in the Major League Rules (MLR) rather than the CBA: Rule 5 eligibility,
waiver claim order, option-year counts and the 60-day IL calendar. The CBA incorporates them by
reference (Articles XVIII(B), XIX(E), XIX(F)); those entries cite the incorporating article and say
which Major League Rule holds the number.

`cba_era` marks the agreement a threshold belongs to; this agreement expires 2026-12-01.
"""
from __future__ import annotations

CBA_PDF = "/cba/2022-2026-basic-agreement.pdf"
CBA_SOURCE_URL = "https://2b519a67-e799-4138-9f8d-a79d3fb3d446.filesusr.com/ugd/4d23dc_d6dfc2344d2042de973e37de62484da5.pdf"
CBA_TITLE = "2022-2026 Basic Agreement"


def cba(article: str, page: int, attachment: bool = False, mlr: str | None = None) -> dict:
    """Citation to the printed page of the Basic Agreement. PDF page = printed + 14 (Articles) or
    + 16 (Attachments), verified against the extracted text."""
    pdf_page = page + (16 if attachment else 14)
    return {"source": CBA_TITLE, "article": article, "page": page, "pdf_page": pdf_page,
            "url": f"{CBA_PDF}#page={pdf_page}", "mlr": mlr}


RULES: list[dict] = [
    # ---------------------------------------------------------------- roster limits
    dict(id="roster.active", cat="Roster limits", cba_era="2022-2026", title="26-man Active List (28 in September)",
         summary="26 active players from Opening Day through midnight August 31, minimum 25; 28 from September 1 through the end of the season.",
         detail="A club that drops below 25 has 48 hours plus reporting time to get back. The 13-pitcher cap (14 in September) and the "
                "two-way-player definition sit in Major League Rule 2(b), which this article incorporates.",
         cite=cba("Article XV(E)(1)-(2)", 71, mlr="Major League Rule 2(b)")),
    dict(id="roster.forty", cat="Roster limits", cba_era="2022-2026", title="40-man Reserve List",
         summary="A club may hold title to and reserve up to 40 player contracts.",
         detail="Optioned players, 7/10/15-day IL players and DFA'd players (until resolved) all occupy a spot; only the 60-day IL, the "
                "restricted, suspended, military and voluntarily-retired lists sit outside the 40.",
         cite=cba("Article XX(A)", 100)),
    dict(id="roster.taxi", cat="Roster limits", cba_era="2022-2026", title="No taxi squads",
         summary="A player told to report for a possible recall must be added to the active roster by 8 PM ET (or three hours before the game) the day after he reports, or he cannot stay with the club.",
         detail="He may take one workout without pay or service time. Sending him back without adding him must be justified by a change in "
                "circumstances, which is why 'phantom' call-ups stopped after 2022.",
         cite=cba("Article XV(E)(3)", 72)),
    dict(id="post.eligibility", cat="Roster limits", cba_era="2022-2026", title="Post-season roster eligibility",
         summary="The post-season eligibility list is fixed at noon ET on September 1: everyone on the 40-man, the 60-day IL or the military list at that moment, who then stays there without interruption.",
         detail="Major League Rule 40; the agreement's Attachment 25 defers post-season procedure to the Major League Rules. A 60-day IL player "
                "must have served 60 days and be reinstated before he can play. A player outrighted after the cutoff loses automatic "
                "eligibility and can return only as an approved replacement for an injured player, as can any player who was in the "
                "organization before the cutoff; replacements need a 40-man spot. A drug-program suspension that year makes a player ineligible.",
         cite=cba("Attachment 25", 253, attachment=True, mlr="Major League Rule 40")),
    # ---------------------------------------------------------------- injured list
    dict(id="il.sixty", cat="Injured list", cba_era="2022-2026", title="60-day IL and the November crunch",
         summary="A player on the 60-day IL is off the 40-man, but every 60-day IL player must be reinstated after the World Series, healthy or not.",
         detail="The CBA fixes the IL paperwork (a Standard Form of Diagnosis, recertification every 10 or 15 days except on the 60-day list); "
                "the 60-day minimum, the full-40-man requirement and the fifth-day-after-the-Series reinstatement date are in Major League Rule 2. "
                "That reinstatement is what creates the November squeeze before the reserve-list filing and the Rule 5 draft.",
         cite=cba("Article XIII(C)", 56, mlr="Major League Rule 2")),
    dict(id="il.no_assignment", cat="Injured list", cba_era="2022-2026", title="Injured players cannot be sent down",
         summary="No assignment to a minor-league club while a player is on a Major League injured list, and an injured player who cannot play cannot be optioned or outrighted.",
         detail="Two windows open it up: after the season and before the reserve-list filing if his contract ends this year (a Super Two may "
                "elect free agency instead), and after the filing until 15 days before Opening Day for a player under three years of service "
                "with no service last season, no prior outright, and no Rule 5 selection by that club.",
         cite=cba("Article XIX(C)(1)-(2)", 96)),
    dict(id="il.rehab", cat="Injured list", cba_era="2022-2026", title="Rehab assignments: 20 days, 30 for pitchers",
         summary="A rehab assignment needs the player's written consent and runs at most 20 days (30 for pitchers) per injury; UCL reconstructions may add up to three ten-day extensions.",
         detail="Rehab days count as Major League service at Major League pay, do not use an option, and need no waivers.",
         cite=cba("Article XIX(C)(3)", 97)),
    # ---------------------------------------------------------------- options
    dict(id="opt.years", cat="Options", cba_era="2022-2026", title="Option years and the 20-day rule",
         summary="A season with fewer than 20 days on optional assignment does not count as an option year, and those days count as Major League service.",
         detail="The three-option limit itself is Major League Rule 7(c); the CBA sets the 20-day floor and the counting: the day he is optioned "
                "counts, the day he is recalled does not (unless the game had already started). Spring-training days are never counted.",
         cite=cba("Article XIX(E) and XXI(B)", 98, mlr="Major League Rule 7(c)")),
    dict(id="opt.fourth", cat="Options", cba_era="2022-2026", title="Fourth option",
         summary="A player who has used three option years but has fewer than five full seasons (90+ days on an active list) receives a fourth option.",
         detail="This lives in Major League Rule 7(c), incorporated by Article XIX(E). Minor-league injured-list days are not public, so this "
                "site follows FanGraphs where it shows a count.",
         cite=cba("Article XIX(E)", 98, mlr="Major League Rule 7(c)")),
    dict(id="opt.cap", cat="Options", cba_era="2022-2026", title="Five optional assignments per season",
         summary="A player can be optioned at most five times in a season; a sixth trip requires outright waivers.",
         detail="Major League Rule 7(c), incorporated by Article XIX(E). Spring-training options, a return after serving as the 27th man for a "
                "doubleheader, and an option within 24 hours of arriving by trade do not count. Option years left and assignments left are "
                "different numbers.",
         cite=cba("Article XIX(E)", 98, mlr="Major League Rule 7(c)")),
    dict(id="opt.recall_min", cat="Options", cba_era="2022-2026", title="Minimum stay on option",
         summary="An optioned position player must stay down 10 days, a pitcher 15, unless he replaces an injured or traded player.",
         detail="Major League Rule 7(c). Trades, waiver claims and the doubleheader 27th man are the other exceptions.",
         cite=cba("Article XIX(E)", 98, mlr="Major League Rule 7(c)")),
    dict(id="opt.out", cat="Options", cba_era="2022-2026", title="Out of options",
         summary="With no option years left, the only way to the minors is through irrevocable outright waivers.",
         detail="This is the single biggest driver of spring DFAs: a club must carry him on the 26-man or risk losing him for $50,000.",
         cite=cba("Article XIX(E) and XIX(F)", 98, mlr="Major League Rules 7 and 8")),
    dict(id="opt.counting", cat="Options", cba_era="2022-2026", title="Option days when DFA'd or released",
         summary="If a player is designated or released while on option, the option date is day one and the DFA date is the last day of the option.",
         detail="The forfeiture trap: a player optioned before accruing any service that season, then released or outrighted before 20 days and "
                "never returned to an active list, gets no service for those days at all.",
         cite=cba("Attachment 32 and Article XXI(B)", 265, attachment=True)),
    dict(id="opt.xix_a", cat="Options", cba_era="2022-2026", title="Article XIX-A: five years, no forced assignment",
         summary="A player with five or more years of Major League service cannot be assigned anywhere but another Major League club without his written consent.",
         detail="The club must give written notice 4 days ahead (8 if he is out of options or it is the off-season); he has 2 days (3 in the "
                "off-season) to consent, refuse, or elect free agency, and silence is a refusal. Posted NPB/KBO players usually write the same "
                "right into their contracts.",
         cite=cba("Article XIX(A)(2)", 94)),
    dict(id="opt.advance_consent", cat="Options", cba_era="2022-2026", title="Advance consent to an assignment",
         summary="A five-year player may pre-approve an assignment to a named club, no earlier than 10 days before the season, good for 45 days.",
         detail="A player with 4 years and 127 days can grant it before he reaches five years. Every advance consent must keep the free-agency "
                "election open, and a minor-league contract cannot be used to extract one.",
         cite=cba("Article XIX(A)(3)", 95)),
    # ---------------------------------------------------------------- waivers / DFA
    dict(id="dfa.clock", cat="Waivers & DFA", cba_era="2022-2026", title="Designated for assignment: 7 days",
         summary="A designated player must be released or have his contract assigned within 7 days; he is paid at the Major League rate and credited with Major League service while designated.",
         detail="Christmas Day through New Year's Day do not count toward the 7 days. The club must request waivers early enough to resolve "
                "him inside the window.",
         cite=cba("Article XIX(G)", 99)),
    dict(id="waiv.outright", cat="Waivers & DFA", cba_era="2022-2026", title="Outright waivers",
         summary="Every assignment must clear the waiver rules of Major League Rule 8: outright waivers are irrevocable, cost $50,000 to claim, and go to the worst record first.",
         detail="Prior-season standings are used through day 30 of the season, current standings after that. Optional waivers ended in 2017 "
                "and trade waivers in 2019. Each Friday the Commissioner's Office reports all waiver activity to the union.",
         cite=cba("Article XIX(F)", 99, mlr="Major League Rule 8")),
    dict(id="waiv.xx_d", cat="Waivers & DFA", cba_era="2022-2026", title="Article XX-D: the right to walk",
         summary="A player with three or more years of service (or a Super Two), or any player being outrighted for the second time in his career, may elect free agency instead of accepting the outright.",
         detail="He may also accept and defer the choice to the end of the season, keeping his salary, unless he is returned to a Major "
                "League roster first; a Super Two who accepts a first outright gives up that deferred election. Notice is 4 days (8 if out of "
                "options or off-season) with 2 (or 3) days to answer.",
         cite=cba("Article XX(D)(1)-(2), (4)", 110)),
    dict(id="waiv.xix_a_outright", cat="Waivers & DFA", cba_era="2022-2026", title="Article XIX-A: five years, no forced outright",
         summary="A player with five or more years of service can refuse an outright assignment altogether; the club must then keep him, trade him, or release him.",
         detail="Electing free agency instead forfeits termination pay, so the union must confirm that election in writing.",
         cite=cba("Article XIX(A)(2)", 94)),
    dict(id="waiv.release", cat="Waivers & DFA", cba_era="2022-2026", title="Release waivers and termination pay",
         summary="A player released in-season is owed the unpaid balance of his full salary; released in spring he gets 30 days' pay (45 after the 16th day before the season); released in the off-season, 30 days' pay.",
         detail="Release waivers cost $1 to claim but the claimant assumes the whole salary, which is why expensive players clear. What he "
                "earns from another club that year offsets the bill, and refusing a reasonable Major League offer forfeits that much.",
         cite=cba("Article IX(A)-(C), (F)", 35)),
    dict(id="waiv.split_rate", cat="Waivers & DFA", cba_era="2022-2026", title="Which rate a split contract pays at release",
         summary="On a split contract, termination pay uses the minor-league rate for off-season and early-spring releases and for in-season releases while in the minors; the Major League rate applies late in spring or while in the majors.",
         detail="A contract may not be optioned just to cut termination pay. A player who cannot be assigned without consent, or a Rule 5 pick, always gets the Major League rate unless actually in the minors when released in-season.",
         cite=cba("Article IX(D)", 36)),
    dict(id="waiv.outright_floor", cat="Waivers & DFA", cba_era="2022-2026", title="Salary floor after a late-season outright",
         summary="A player with Major League service outrighted after Labor Day cannot be offered less than 80% of his most recent minor-league monthly rate, or the split minimum, whichever is greater.",
         detail="It caps how cheap a September roster clear-out really is for the club.",
         cite=cba("Attachment 43", 309, attachment=True)),
    # ---------------------------------------------------------------- rule 5
    dict(id="r5.eligible", cat="Rule 5", cba_era="2022-2026", title="Rule 5 eligibility",
         summary="Signed at 18 or younger: eligible at the 5th Rule 5 draft after signing. 19 or older: the 4th. A player previously outrighted is always eligible.",
         detail="Age is measured on the June 5 before the first contract. This is Major League Rule 5, which the CBA incorporates by "
                "reference; a player on the 40-man at the reserve-list filing deadline is protected.",
         cite=cba("Article XVIII(B)", 93, mlr="Major League Rule 5")),
    dict(id="r5.selected", cat="Rule 5", cba_era="2022-2026", title="Rule 5 selected player",
         summary="A $100,000 pick is tendered a Major League contract on draft day and must stay on the 26-man for 90 active days (carrying into a second season) or be offered back for $50,000.",
         detail="He can be traded any time but not optioned. Because he is a tendered Major League player, cutting him in spring costs "
                "Major League-rate termination pay, which is why clubs return or trade him instead. Triple-A phase picks ($24,000) need no "
                "40-man spot and carry no offer-back.",
         cite=cba("Attachment 44 and Article IX(D)", 310, attachment=True, mlr="Major League Rule 5")),
    dict(id="r5.excluded", cat="Rule 5", cba_era="2022-2026", title="Draft-Excluded Player",
         summary="A Rule 5-eligible player with under three years of service added to the 40-man after August 15 cannot be optioned until 20 days before Opening Day.",
         detail="Major League Rule 6. It stops clubs from protecting a player in September and quietly stashing him in March; he can still "
                "be traded, non-tendered or released.",
         cite=cba("Article XVIII(B)", 93, mlr="Major League Rule 6")),
    dict(id="r5.filing", cat="Rule 5", cba_era="2022-2026", title="Reserve-list filing and the tender deadline",
         summary="Clubs file their 40-man reserve lists about a week before the tender deadline, which is the last Friday before Thanksgiving at 8 PM ET.",
         detail="Between filing and the draft, eligible minor leaguers cannot be added, traded or released, and no player may be outrighted "
                "from three days before the draft (Major League Rules 1 and 5). Untendered players become free agents that night with no "
                "waivers and no termination pay.",
         cite=cba("Article XX(A)", 101, mlr="Major League Rule 1(a)")),
    # ---------------------------------------------------------------- service time
    dict(id="mls.year", cat="Service time", cba_era="2022-2026", title="172 days is a year",
         summary="One day of service for each day of the championship season on a Major League active list, injured list or disciplinary suspension; 172 days is a full year and a season caps at 172.",
         detail="Service runs from the first regularly scheduled game to the last, the same for every club regardless of its schedule. "
                "Days on optional assignment count only in a season with fewer than 20 of them.",
         cite=cba("Article XXI(A)-(B)", 114)),
    dict(id="mls.arb", cat="Service time", cba_era="2022-2026", title="Arbitration: 3 to 6 years",
         summary="A player with three or more but fewer than six years of service may take his salary to final and binding arbitration.",
         detail="A club cannot cut a tendered player more than 20% from last year or 30% from two years ago, so the only cheap way out of "
                "an arbitration-eligible player is a non-tender. Figures are exchanged the second Friday of January; a settled arbitration "
                "salary is fully guaranteed against a spring release.",
         cite=cba("Article VI(E)(1)(a), VI(B)", 17)),
    dict(id="mls.super_two", cat="Service time", cba_era="2022-2026", title="Super Two",
         summary="A player with two but fewer than three years of service is arbitration-eligible if he had 86+ days last season and ranks in the top 22% of that group by total service; ties at the line all qualify.",
         detail="The cutoff is a ranking announced each fall (recent lines 2+118 to 2+140), so a club cannot know in September exactly who "
                "qualifies. Super Twos go through arbitration four times.",
         cite=cba("Article VI(E)(1)(b)", 17)),
    dict(id="mls.xx_b", cat="Service time", cba_era="2022-2026", title="Article XX-B free agency",
         summary="Six or more years of service with an expiring contract: free agent at 9 AM ET the day after the last World Series game.",
         detail="For five days only the former club may negotiate (the quiet period). All contract option decisions must fall inside that "
                "window.",
         cite=cba("Article XX(B)(1)-(2)", 102)),
    dict(id="mls.ten_five", cat="Service time", cba_era="2022-2026", title="10-and-5 rights",
         summary="Ten years of service, the last five with the same club: no trade without his written consent.",
         detail="A player can waive it only when signing a multi-year deal before qualifying, and only if that deal carries a no-trade list "
                "of at least 16 clubs.",
         cite=cba("Article XIX(A)(1)", 93)),
    dict(id="mls.roy", cat="Service time", cba_era="2022-2026", title="Rookie of the Year service credit",
         summary="A player who entered the season as an Eligible Prospect and finishes first or second in Rookie of the Year voting is credited with a full 172-day year, whatever he actually accrued.",
         detail="It only applies to players who were top-100 prospects under Major League Rule 4(l), the same test as the Prospect Promotion "
                "Incentive draft pick. Ties break on first-place votes, then Joint WAR; at most two players per league.",
         cite=cba("Attachment 53", 357, attachment=True)),
    dict(id="mls.pre_arb_pool", cat="Service time", cba_era="2022-2026", title="Pre-arbitration bonus pool",
         summary="A $50 million pool paid by the Commissioner's Office each December to players with under three years of service who were not Super Twos: fixed awards for MVP, Cy Young, Rookie of the Year and All-MLB finishes, the rest by Joint WAR among the top 100.",
         detail="Awards range from $2.5 million for an MVP or Cy Young to $500,000 for a Rookie of the Year runner-up, one award per player. "
                "It is central money, so it does not touch the player's own club payroll.",
         cite=cba("Article XV(D)", 68)),
    # ---------------------------------------------------------------- free agency and contracts
    dict(id="money.qo", cat="Contracts", cba_era="2022-2026", title="Qualifying offer",
         summary="A one-year offer at the average of the 125 highest salaries, available only to a free agent who was with the club continuously since Opening Day and has never received one before.",
         detail="It must be made during the five-day quiet period and can be accepted until the reserve-list filing date. Declining it "
                "attaches draft-pick compensation; a player who signs a minor-league deal elsewhere carries none. The amount is set by "
                "Attachment 45 and confirmed within ten days of the season's end.",
         cite=cba("Article XX(B)(3)", 103)),
    dict(id="money.qo_comp", cat="Contracts", cba_era="2022-2026", title="Draft-pick compensation",
         summary="The former club gets a pick after Competitive Balance Round B; after the first round if it is a revenue-sharing payee and the player signed for $50 million or more; after the fourth round if it paid competitive balance tax.",
         detail="The signing club forfeits its second-highest pick and $500,000 of international pool; a tax payor forfeits its second and "
                "fifth picks and $1 million; a revenue-sharing payee forfeits only its third-highest pick.",
         cite=cba("Article XX(B)(4)", 104)),
    dict(id="money.tender", cat="Contracts", cba_era="2022-2026", title="Tender deadline",
         summary="The last Friday before Thanksgiving: the Commissioner's Office sends the union a letter listing every player each club has tendered, and everyone left off becomes a free agent.",
         detail="No waivers, no termination pay. It is the one day a club can drop anyone, healthy or hurt, without waiver risk, and re-sign "
                "him the same night.",
         cite=cba("Article XX(A)", 101)),
    dict(id="money.min_salary", cat="Contracts", cba_era="2022-2026", title="Minimum salaries",
         summary="Major League minimum $700,000 (2022), $720,000 (2023), $740,000 (2024), $760,000 (2025), $780,000 (2026), paid per day on the Major League roster; the minor-league split rate for 40-man players runs $114,100 to $127,100, or $57,200 to $63,600 on a first Major League contract.",
         detail="Optioning a fringe 40-man player saves real money: his pay drops to the split rate for every day he is down.",
         cite=cba("Article VI(A)", 11)),
    dict(id="money.max_cut", cat="Contracts", cba_era="2022-2026", title="Maximum salary cut",
         summary="A tendered or renewed player must be offered at least 80% of last season's salary and 70% of the salary two seasons back; a split rate cannot be cut more than half.",
         detail="This is why a modest arbitration-eligible player is non-tendered rather than kept at a lower number: the club cannot simply "
                "tender him at a steep cut.",
         cite=cba("Article VI(B)(1)", 12)),
    dict(id="money.arb_guarantee", cat="Contracts", cba_era="2022-2026", title="A settled arbitration salary is guaranteed",
         summary="An arbitration-eligible player who agrees to a salary before his hearing is owed the full amount if released before Opening Day.",
         detail="Other spring releases cost 30 or 45 days' pay; this one costs the whole contract, so once an arb-eligible player signs, "
                "releasing him saves nothing.",
         cite=cba("Article VI(E)(2)-(3)", 18)),
    # ---------------------------------------------------------------- trades
    dict(id="trade.june15", cat="Trades", cba_era="2022-2026", title="June 15 no-trade for free-agent signees",
         summary="A six-year free agent who signs after the quiet period cannot be traded before June 16 of the next season without his written consent, and then only for players and cash of $50,000 or less.",
         detail="It applies even when he re-signs with his own club. It does not apply to players who became free agents any other way, or who "
                "signed minor-league contracts.",
         cite=cba("Article XX(B)(6)(a)", 109)),
    dict(id="trade.deadline", cat="Trades", cba_era="2022-2026", title="Trade deadline",
         summary="No trades of players on Major League contracts from the deadline (late July or early August) until the day after the World Series.",
         detail="Major League Rule 9. Waiver trades ended in 2019; a player claimed in August cannot be flipped for value.",
         cite=cba("Article XVIII(B)", 93, mlr="Major League Rule 9")),
    dict(id="trade.foreign", cat="Trades", cba_era="2022-2026", title="No foreign assignments",
         summary="A contract cannot be assigned outside the United States and Canada without the player's written consent.",
         detail="Returning a conditional assignment from abroad is the only exception.",
         cite=cba("Article XIX(D)", 98)),
    # ---------------------------------------------------------------- minor-league free agency
    dict(id="milb.xx_b_optout", cat="Minor-league free agency", cba_era="2022-2026", title="Veteran opt-outs on a minor-league deal",
         summary="A six-year free agent who signs a minor-league contract at least ten days before Opening Day can force his release four days before Opening Day, on May 1, and on June 1 unless the club adds him to the 26-man or the Major League IL.",
         detail="He must ask in writing two days ahead (2 PM ET on the sixth day before the season, April 27, May 28). No other opt-out dates "
                "can be written into that contract. The former $100,000 retention bonus is gone.",
         cite=cba("Article XX(B)(5)", 108)),
    dict(id="milb.rule9", cat="Minor-league free agency", cba_era="2022-2026", title="Minor-league free agency",
         summary="A player not on a 40-man who has spent parts of seven seasons on minor-league rosters becomes a free agent five days after the World Series.",
         detail="Major League Rule 9(b) and the Minor League agreement, not the Basic Agreement. Players first signed at 19 or older from June "
                "2023 reach it after six seasons; a second contract after a release resets the clock.",
         cite=cba("Article XIX(B)", 95, mlr="Major League Rule 9(b)")),
    dict(id="milb.rights_survive", cat="Minor-league free agency", cba_era="2022-2026", title="Rights survive an assignment to the minors",
         summary="A player sent to the minors keeps every right the Basic Agreement gave him, including his free-agency and consent rights, until he signs a minor-league contract after those rights arise.",
         detail="So an outrighted six-year veteran still becomes a free agent after the season on schedule.",
         cite=cba("Article XIX(B)", 95)),
]

BY_ID = {r["id"]: r for r in RULES}
