#!/usr/bin/env python3
"""
NFL Legends Benefits Brain
A simple rule-based knowledge system for benefit eligibility checks ("awards")
and coordination of next steps for former NFL players (Legends).

Based on the NFL Legends Community Resource Guide (2026 / 2020 CBA).
This is an educational/reference tool only — always verify with official sources
(NFLPlayerBenefits.com, plan SPDs, and current CBA). Rules can change.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from enum import Enum
import json
from datetime import datetime


class BenefitCategory(Enum):
    FINANCIAL = "Financial Benefits & Resources"
    MEDICAL = "Medical & Disability Benefits"
    WELLNESS = "NFL Total Wellness"
    CAREER = "Career Development"
    PERKS = "Perks & Engagement"
    EDUCATION = "Educational Assistance"


@dataclass
class EligibilityRule:
    """Simple condition for eligibility."""
    description: str
    check: Callable[["PlayerProfile"], bool]
    notes: str = ""


@dataclass
class Benefit:
    id: str
    name: str
    category: BenefitCategory
    summary: str
    eligibility_rules: List[EligibilityRule]
    how_to_access: List[str]
    contacts: List[str]
    amount_or_value: Optional[str] = None
    deadlines: Optional[str] = None
    official_links: List[str] = field(default_factory=list)
    cautions: List[str] = field(default_factory=list)


@dataclass
class PlayerProfile:
    """Minimal player data needed for simple eligibility checks."""
    name: str = "Legend"
    credited_seasons: int = 0
    last_credited_season_year: Optional[int] = None
    is_vested: bool = False  # Usually 3+ credited seasons under Pension Plan rules
    years_since_last_active: Optional[int] = None
    age: Optional[int] = None
    retired_before_july_2013: bool = False
    has_applied_for_pension: bool = False
    notes: str = ""


class BenefitsBrain:
    """
    The 'brain': holds knowledge of benefits, evaluates simple eligibility,
    and coordinates next steps / contacts.
    """

    def __init__(self):
        self.benefits: Dict[str, Benefit] = {}
        self._load_knowledge()

    def _load_knowledge(self):
        """Populate the knowledge base from the Resource Guide."""

        # --- FINANCIAL ---
        self.benefits["severance"] = Benefit(
            id="severance",
            name="Severance Plan",
            category=BenefitCategory.FINANCIAL,
            summary="Lump-sum payment for Legends with at least 2 Credited Seasons. Automatically issued ~12 months after last contract.",
            amount_or_value="$30,000–$50,000 per year for 2020–2030 (depends on seasons earned)",
            eligibility_rules=[
                EligibilityRule(
                    "At least 2 Credited Seasons",
                    lambda p: p.credited_seasons >= 2
                )
            ],
            how_to_access=[
                "Payment is automatic if eligible.",
                "Verify/update permanent home address with the Plan so the check reaches you.",
                "Call NFL Customer Service Center or visit NFLPlayerBenefits.com."
            ],
            contacts=["800.635.4625 (prompt 1)", "NFLPlayerBenefits.com"],
            official_links=["https://www.nflplayerbenefits.com"],
            cautions=["Address must be current; otherwise payment may be delayed or lost."]
        )

        self.benefits["capital_accumulation"] = Benefit(
            id="capital_accumulation",
            name="Capital Accumulation Plan",
            category=BenefitCategory.FINANCIAL,
            summary="Club-funded retirement investment account. You direct the investments.",
            eligibility_rules=[
                EligibilityRule(
                    "Account exists from Club contributions during playing years",
                    lambda p: True  # Assume if they played; actual balance check needed
                )
            ],
            how_to_access=[
                "Access as early as age 40 or 5 years after last Credited Season (whichever later).",
                "Log into NFLPlayerBenefits.com or call to manage investments/withdrawals."
            ],
            contacts=["800.638.3186", "NFLPlayerBenefits.com"],
            cautions=["Withdrawals before age 59½ may incur 10% IRS early withdrawal penalty."]
        )

        self.benefits["annuity"] = Benefit(
            id="annuity",
            name="Annuity Program",
            category=BenefitCategory.FINANCIAL,
            summary="Club-funded retirement benefit with Tax-Qualified and/or Nonqualified accounts.",
            eligibility_rules=[
                EligibilityRule("Club contributions were made during active years", lambda p: True)
            ],
            how_to_access=[
                "Portion may be available as early as 5 years after last Credited Season.",
                "Contact the plan administrator via NFLPlayerBenefits.com."
            ],
            contacts=["800.638.3186", "NFLPlayerBenefits.com"],
            cautions=["Tax-Qualified withdrawals before 59½ may have 10% penalty."]
        )

        self.benefits["401k"] = Benefit(
            id="401k",
            name="401(k) Savings Plan",
            category=BenefitCategory.FINANCIAL,
            summary="Salary deferrals + Club contributions during playing years. You direct investments.",
            eligibility_rules=[
                EligibilityRule("Account exists from contributions", lambda p: True)
            ],
            how_to_access=[
                "Access as early as age 45.",
                "Manage via NFLPlayerBenefits.com or phone."
            ],
            contacts=["800.638.3186 (prompt 2)", "NFLPlayerBenefits.com"],
            cautions=["Early withdrawals before 59½ may incur 10% penalty."]
        )

        self.benefits["pension"] = Benefit(
            id="pension",
            name="Pension Plan",
            category=BenefitCategory.FINANCIAL,
            summary="Monthly retirement benefit based on total Credited Seasons and years earned. Payable as early as age 55 (defer to 65 for higher amount).",
            amount_or_value="Increased to $600 per Credited Season for seasons prior to 2012 (eff. Apr 1, 2025); post-2011 seasons +10% under 2020 CBA. Pre-1993 players with 3+ seasons now eligible.",
            eligibility_rules=[
                EligibilityRule(
                    "Typically vested with sufficient Credited Seasons (often 3+); Pre-1993 with 3+ now covered",
                    lambda p: p.credited_seasons >= 3 or p.is_vested
                )
            ],
            how_to_access=[
                "Apply via NFLPlayerBenefits.com or call.",
                "Elect start date (55–65).",
                "Must apply before electing certain other benefits in some cases."
            ],
            contacts=["800.638.3186 (prompt 3)", "NFLPlayerBenefits.com"],
            cautions=["Application timing matters relative to other disability benefits."]
        )

        self.benefits["tuition"] = Benefit(
            id="tuition",
            name="NFL Player Tuition Assistance Plan",
            category=BenefitCategory.EDUCATION,
            summary="Reimbursement for tuition, fees, and books (100% up to lifetime max). Also covers approved trade/business management programs.",
            amount_or_value="Lifetime max: $25k (2 seasons), $45k (3), $65k (4), $85k (5+)",
            eligibility_rules=[
                EligibilityRule(
                    "Expenses incurred within 72 months of the first day of the Plan Year following last regular/postseason game",
                    lambda p: p.years_since_last_active is None or p.years_since_last_active <= 6
                )
            ],
            how_to_access=[
                "1. Verify eligibility and qualifying institution before enrolling (call or email).",
                "2. Submit reimbursement request + docs within 6 months of class completion (or grade post / 30 days after finals).",
                "3. Receive check if rules met."
            ],
            contacts=["800.NFL.GOAL (800.635.4625) prompt 1", "NFLTuitionAssist@Alight.com"],
            deadlines="Expenses within ~6 years of last game; claim within 6 months of completion."
        )

        # --- MEDICAL & DISABILITY ---
        self.benefits["cv_coverage"] = Benefit(
            id="cv_coverage",
            name="NFL Player Insurance Plan — Continuing Veteran (CV)",
            category=BenefitCategory.MEDICAL,
            summary="5 years of free extended medical, behavioral health, dental, vision, and Rx coverage after final active season for you and eligible dependents.",
            eligibility_rules=[
                EligibilityRule("Completed final season as Active Player", lambda p: True)
            ],
            how_to_access=[
                "Coverage is automatic for eligible players.",
                "Manage via myCigna.com or call."
            ],
            contacts=["800.635.9671", "myCigna.com"]
        )

        self.benefits["dedicated_hospital"] = Benefit(
            id="dedicated_hospital",
            name="NFL Dedicated Hospital Network Program",
            category=BenefitCategory.MEDICAL,
            summary="After CV coverage ends: limited benefit access to high-quality network for preventive, primary, and mental health services (Annual Maximums apply). Available until age 65.",
            eligibility_rules=[
                EligibilityRule("CV coverage has ended", lambda p: True),
                EligibilityRule("Under age 65", lambda p: p.age is None or p.age < 65)
            ],
            how_to_access=[
                "Must contact Dedicated Concierge Team PRIOR to each visit.",
                "Dependents not eligible."
            ],
            contacts=["800.635.4625 (prompt 3)", "NFLPlayerBenefits.com"],
            cautions=["Contact concierge first; Annual Maximums renew Sept 1."]
        )

        self.benefits["disability_lod"] = Benefit(
            id="disability_lod",
            name="Line of Duty Disability",
            category=BenefitCategory.MEDICAL,
            summary="For partial disability due to NFL-football activities.",
            eligibility_rules=[
                EligibilityRule(
                    "If ≤4 Credited Seasons: apply within 4 years of last Active Player date. If 5+: deadline = number of Credited Seasons.",
                    lambda p: True  # Time-sensitive; needs specific calculation
                )
            ],
            how_to_access=["Apply via NFL Disability Benefits process.", "Call for guidance."],
            contacts=["800.638.3186"],
            deadlines="Strict application windows based on Credited Seasons."
        )

        self.benefits["disability_neuro"] = Benefit(
            id="disability_neuro",
            name="Neurocognitive Disability",
            category=BenefitCategory.MEDICAL,
            summary="For mild to moderate brain impairment.",
            eligibility_rules=[
                EligibilityRule(
                    "Must be Vested Inactive under Pension Plan, OR if not vested apply within 7 years of last Active date.",
                    lambda p: p.is_vested or (p.years_since_last_active is not None and p.years_since_last_active <= 7)
                )
            ],
            how_to_access=["Apply through Disability Plan process."],
            contacts=["800.638.3186"]
        )

        self.benefits["disability_tp"] = Benefit(
            id="disability_tp",
            name="Total and Permanent Disability",
            category=BenefitCategory.MEDICAL,
            summary="Unable to work due to disability.",
            eligibility_rules=[
                EligibilityRule(
                    "Must be Vested Inactive Player; application before electing Pension. Non-vested limited cases possible.",
                    lambda p: p.is_vested and not p.has_applied_for_pension
                )
            ],
            how_to_access=["Apply prior to Pension election."],
            contacts=["800.638.3186"],
            cautions=["Timing relative to Pension election is critical."]
        )

        self.benefits["hra"] = Benefit(
            id="hra",
            name="Health Reimbursement Account (HRA) Plan",
            category=BenefitCategory.MEDICAL,
            summary="Club-funded account to help pay health expenses after CV coverage ends. Covers you, spouse, eligible dependents.",
            eligibility_rules=[
                EligibilityRule("Eligible Vested Legend with HRA balance from Club contributions", lambda p: p.is_vested)
            ],
            how_to_access=["Use for qualified health expenses.", "Manage via plan portal."],
            contacts=["800.501.7633", "NFLPlayerBenefits.com"]
        )

        self.benefits["fplip"] = Benefit(
            id="fplip",
            name="Former Player Life-Improvement Plan (FPLIP)",
            category=BenefitCategory.MEDICAL,
            summary="Bundle including discount Rx card, Vested Inactive Life Insurance ($40k + $2k/extra season up to $50k), Joint Replacement reimbursement (up to $5,250), Assisted Living access, Enhanced Assessment/Counseling (2 visits/year), Medicare subsidy (up to $200/mo at 65+).",
            eligibility_rules=[
                EligibilityRule("Vested Inactive for many components", lambda p: p.is_vested)
            ],
            how_to_access=[
                "Discount Rx: available at participating pharmacies.",
                "Life Insurance: designate beneficiary via form on NFLPlayerBenefits.com.",
                "Joint Replacement: submit for reimbursement (one per joint).",
                "Medicare: through Alight Retiree Health Solutions at 65+."
            ],
            contacts=["800.635.4625 (prompt 1)", "NFLPlayerBenefits.com"],
            cautions=["Life insurance ends at age 55 or pension start."]
        )

        self.benefits["pfrpa_dental"] = Benefit(
            id="pfrpa_dental",
            name="PFRPA Dental Plan",
            category=BenefitCategory.MEDICAL,
            summary="Delta Dental coverage for Legends who retired by July 2013 (and spouse option). Not collectively bargained.",
            amount_or_value="Preventive 100%, Basic 70%, Major 50%; $25 deductible; $3,000 calendar max",
            eligibility_rules=[
                EligibilityRule("Retired from NFL by July 2013", lambda p: p.retired_before_july_2013)
            ],
            how_to_access=["Contact PFRPA / Delta Dental."],
            contacts=["855.497.6675", "PFRPA.com"]
        )

        self.benefits["pfrpa_vision"] = Benefit(
            id="pfrpa_vision",
            name="PFRPA Vision Plan",
            category=BenefitCategory.MEDICAL,
            summary="VSP Vision Care for Legends who effectively retired by July 2013 (spouse option). Not collectively bargained.",
            eligibility_rules=[
                EligibilityRule("Retired by July 2013", lambda p: p.retired_before_july_2013)
            ],
            how_to_access=["Contact PFRPA / VSP."],
            contacts=["855.497.6675", "PFRPA.com"]
        )

        # --- WELLNESS ---
        self.benefits["total_wellness"] = Benefit(
            id="total_wellness",
            name="NFL Total Wellness",
            category=BenefitCategory.WELLNESS,
            summary="Holistic support: mental health literacy trainings, Headspace app (shareable with 5 family), monthly webinars, Wellness Retreat, Coordination of Care, Transition Coaches, NFL Life Line.",
            eligibility_rules=[
                EligibilityRule("Available to NFL Legends and family", lambda p: True)
            ],
            how_to_access=[
                "Email TotalWellness@nfl.com for training registration, Headspace, retreats, coaches.",
                "NFL Life Line: 800.506.0078 or nflifeline.org (24/7 urgent support)."
            ],
            contacts=["TotalWellness@nfl.com", "800.506.0078 (Life Line)"]
        )

        self.benefits["transition_coaches"] = Benefit(
            id="transition_coaches",
            name="NFL Transition Coaches",
            category=BenefitCategory.WELLNESS,
            summary="Peer Legends with 70+ hours training providing one-on-one support for wellness, resource access, care coordination, and crisis management.",
            eligibility_rules=[EligibilityRule("Available to Legends", lambda p: True)],
            how_to_access=["Email totalwellness@nfl.com or complete Transition Coach Referral form."],
            contacts=["totalwellness@nfl.com"]
        )

        # --- CAREER ---
        self.benefits["player_engagement"] = Benefit(
            id="player_engagement",
            name="NFL Player Engagement",
            category=BenefitCategory.CAREER,
            summary="Programs under four pillars: Continuing Education, Financial Empowerment, Professional Development, Personal Development.",
            eligibility_rules=[EligibilityRule("Available to Legends", lambda p: True)],
            how_to_access=["Visit players.nfl.com or contact Player Engagement."],
            contacts=["players.nfl.com"]
        )

        self.benefits["legends_networks"] = Benefit(
            id="legends_networks",
            name="Legends Business / Coaches / Media Networks",
            category=BenefitCategory.CAREER,
            summary="Exclusive networks for business owners/aspirants, coaches, and media professionals with education, mentorship, resources, and NFL partner opportunities.",
            eligibility_rules=[EligibilityRule("Registered Legend", lambda p: True)],
            how_to_access=["Register via Players Community portal at players.nfl.com."],
            contacts=["players.nfl.com"]
        )

        # --- ENGAGEMENT / PERKS ---
        self.benefits["legends_grant"] = Benefit(
            id="legends_grant",
            name="Legends Community Grant",
            category=BenefitCategory.PERKS,
            summary="$5,000 quarterly grant from funds raised on NFL Auction Legends page. For community give-back.",
            amount_or_value="$5,000",
            eligibility_rules=[EligibilityRule("Sign up / apply as Legend", lambda p: True)],
            how_to_access=["Visit players.nfl.com or email NFLLegends@NFL.com."],
            contacts=["NFLLegends@NFL.com", "players.nfl.com"]
        )

        self.benefits["portal"] = Benefit(
            id="portal",
            name="Players Community Portal & App + NFL Player Benefits App",
            category=BenefitCategory.PERKS,
            summary="Central digital hubs for resources, benefits, events, RSVPs, trusted users, perks, and account management.",
            eligibility_rules=[EligibilityRule("Any Legend", lambda p: True)],
            how_to_access=[
                "players.nfl.com — create account or sign in.",
                "Download Players Community App and NFL Player Benefits App (App Store / Google Play)."
            ],
            contacts=["players.community@nfl.com", "NFLPlayerBenefits.com"]
        )

    def list_all_benefits(self) -> List[str]:
        return [f"{b.id}: {b.name} [{b.category.value}]" for b in self.benefits.values()]

    def evaluate_eligibility(self, benefit_id: str, player: PlayerProfile) -> Dict:
        """Simple award check: returns eligibility status + reasons."""
        if benefit_id not in self.benefits:
            return {"error": f"Unknown benefit_id: {benefit_id}"}

        benefit = self.benefits[benefit_id]
        results = []
        all_pass = True

        for rule in benefit.eligibility_rules:
            try:
                passed = rule.check(player)
            except Exception as e:
                passed = False
                results.append({"rule": rule.description, "passed": False, "error": str(e)})
                all_pass = False
                continue
            results.append({"rule": rule.description, "passed": passed, "notes": rule.notes})
            if not passed:
                all_pass = False

        return {
            "benefit_id": benefit_id,
            "benefit_name": benefit.name,
            "eligible": all_pass,
            "rule_results": results,
            "summary": benefit.summary,
            "amount_or_value": benefit.amount_or_value,
            "cautions": benefit.cautions,
            "player": player.name
        }

    def coordinate(self, benefit_id: str, player: PlayerProfile = None) -> Dict:
        """Return coordination package: how to access + contacts + next steps."""
        if benefit_id not in self.benefits:
            return {"error": f"Unknown benefit_id: {benefit_id}"}

        benefit = self.benefits[benefit_id]
        eligibility = None
        if player:
            eligibility = self.evaluate_eligibility(benefit_id, player)

        return {
            "benefit_id": benefit_id,
            "benefit_name": benefit.name,
            "category": benefit.category.value,
            "summary": benefit.summary,
            "amount_or_value": benefit.amount_or_value,
            "deadlines": benefit.deadlines,
            "how_to_access": benefit.how_to_access,
            "contacts": benefit.contacts,
            "official_links": benefit.official_links,
            "cautions": benefit.cautions,
            "eligibility_check": eligibility,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }

    def recommend(self, player: PlayerProfile) -> List[Dict]:
        """Simple recommendation engine: evaluate all benefits and return those that pass."""
        recommendations = []
        for bid in self.benefits:
            result = self.evaluate_eligibility(bid, player)
            if result.get("eligible"):
                recommendations.append({
                    "benefit_id": bid,
                    "name": result["benefit_name"],
                    "summary": result["summary"],
                    "amount_or_value": result.get("amount_or_value"),
                    "priority_note": "Review contacts and how_to_access via coordinate()"
                })
        return recommendations

    def search(self, query: str) -> List[str]:
        """Simple keyword search across names and summaries."""
        q = query.lower()
        hits = []
        for b in self.benefits.values():
            if q in b.name.lower() or q in b.summary.lower() or q in b.id:
                hits.append(f"{b.id}: {b.name}")
        return hits


def interactive_demo():
    """Simple CLI for demonstration."""
    brain = BenefitsBrain()
    print("=" * 60)
    print("NFL LEGENDS BENEFITS BRAIN")
    print("Simple eligibility awards + coordination")
    print("=" * 60)
    print("\nAvailable commands:")
    print("  list                  - list all benefits")
    print("  search <keyword>      - search benefits")
    print("  check <id>            - eligibility check (uses sample player)")
    print("  coord <id>            - full coordination package")
    print("  recommend             - recommend for sample player")
    print("  profile               - show/edit sample player profile")
    print("  quit")
    print()

    # Sample player (editable)
    player = PlayerProfile(
        name="Sample Legend",
        credited_seasons=5,
        last_credited_season_year=2018,
        is_vested=True,
        years_since_last_active=8,
        age=42,
        retired_before_july_2013=False,
        has_applied_for_pension=False
    )

    while True:
        try:
            cmd = input("\nbrain> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not cmd:
            continue
        parts = cmd.split(maxsplit=1)
        action = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if action in ("quit", "exit", "q"):
            break
        elif action == "list":
            for line in brain.list_all_benefits():
                print(" ", line)
        elif action == "search":
            hits = brain.search(arg)
            if hits:
                for h in hits:
                    print(" ", h)
            else:
                print("  No matches.")
        elif action == "check":
            if not arg:
                print("  Usage: check <benefit_id>")
                continue
            result = brain.evaluate_eligibility(arg, player)
            print(json.dumps(result, indent=2))
        elif action == "coord":
            if not arg:
                print("  Usage: coord <benefit_id>")
                continue
            result = brain.coordinate(arg, player)
            print(json.dumps(result, indent=2))
        elif action == "recommend":
            recs = brain.recommend(player)
            print(f"\nRecommendations for {player.name} ({player.credited_seasons} CS, vested={player.is_vested}):")
            for r in recs:
                print(f"  • {r['name']} ({r['benefit_id']})")
                if r.get("amount_or_value"):
                    print(f"      Value: {r['amount_or_value']}")
        elif action == "profile":
            print(json.dumps(player.__dict__, indent=2))
            print("\n(To change, edit the PlayerProfile in code or extend this CLI.)")
        else:
            print("  Unknown command. Try list, search, check, coord, recommend, profile, quit.")


if __name__ == "__main__":
    interactive_demo()
