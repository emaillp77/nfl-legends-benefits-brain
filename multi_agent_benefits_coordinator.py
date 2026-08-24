#!/usr/bin/env python3
"""
Multi-Agent Coordination Logic for NFL Legends Benefits Brain

Agents:
  - IntakeAgent          : validates / normalizes PlayerProfile + request
  - EligibilityAgent     : runs rule-based award checks
  - CoordinationAgent    : builds step-by-step access plans + contacts
  - CautionAgent         : surfaces timing risks, penalties, dependencies
  - RecommendationAgent  : prioritizes and ranks suitable benefits
  - OrchestratorAgent    : routes, sequences, synthesizes final Case Package

Pure Python, no external LLM required for core logic (rules are deterministic).
Optional LLM hooks can be added later for natural-language explanations.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime, timezone
import json
import copy

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# Optional LLM support
try:
    from llm_client import get_llm_client, BENEFITS_EXPLANATION_SYSTEM, LLMClient
    _LLM_AVAILABLE = True
except ImportError:
    _LLM_AVAILABLE = False
    LLMClient = None  # type: ignore

# Import the base brain
from nfl_legends_benefits_brain import (
    BenefitsBrain,
    PlayerProfile,
    Benefit,
    BenefitCategory,
)


# ---------------------------------------------------------------------------
# Shared Case State
# ---------------------------------------------------------------------------

@dataclass
class CaseState:
    """Shared memory for a coordination session."""
    case_id: str
    player: PlayerProfile
    requested_benefit_ids: List[str] = field(default_factory=list)
    intent: str = "general"  # "check", "apply", "explore", "urgent"
    eligibility_results: Dict[str, Dict] = field(default_factory=dict)
    coordination_plans: Dict[str, Dict] = field(default_factory=dict)
    cautions: List[Dict] = field(default_factory=list)
    recommendations: List[Dict] = field(default_factory=list)
    prioritized_actions: List[Dict] = field(default_factory=list)
    final_package: Optional[Dict] = None
    agent_log: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utc_now_iso)
    status: str = "open"  # open | in_progress | completed | needs_human


# ---------------------------------------------------------------------------
# Base Agent
# ---------------------------------------------------------------------------

class BaseAgent:
    name: str = "BaseAgent"

    def __init__(self, brain: BenefitsBrain):
        self.brain = brain

    def log(self, state: CaseState, message: str):
        entry = f"[{self.name}] {message}"
        state.agent_log.append(entry)
        return entry

    def run(self, state: CaseState) -> CaseState:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Specialized Agents
# ---------------------------------------------------------------------------

class IntakeAgent(BaseAgent):
    """Normalizes player data and request scope."""
    name = "IntakeAgent"

    def run(self, state: CaseState) -> CaseState:
        self.log(state, f"Intake for {state.player.name}")

        # Basic validation / defaults
        p = state.player
        if p.credited_seasons < 0:
            p.credited_seasons = 0
        if p.credited_seasons >= 3:
            p.is_vested = True  # common heuristic; real vesting can be more nuanced

        # If no specific benefits requested, expand to exploratory set
        if not state.requested_benefit_ids:
            state.intent = "explore"
            # Core high-value set for most Legends
            state.requested_benefit_ids = [
                "severance", "pension", "cv_coverage", "hra",
                "fplip", "tuition", "total_wellness", "portal"
            ]
            self.log(state, "No specific benefits requested \u2192 default exploratory set loaded")
        else:
            # Filter unknown IDs
            known = set(self.brain.benefits.keys())
            valid = [bid for bid in state.requested_benefit_ids if bid in known]
            unknown = set(state.requested_benefit_ids) - known
            if unknown:
                self.log(state, f"Dropped unknown benefit IDs: {unknown}")
            state.requested_benefit_ids = valid

        state.status = "in_progress"
        self.log(state, f"Ready. Intent={state.intent}, benefits={state.requested_benefit_ids}")
        return state


class EligibilityAgent(BaseAgent):
    """Runs deterministic award/eligibility checks."""
    name = "EligibilityAgent"

    def run(self, state: CaseState) -> CaseState:
        self.log(state, "Running eligibility checks...")
        for bid in state.requested_benefit_ids:
            result = self.brain.evaluate_eligibility(bid, state.player)
            state.eligibility_results[bid] = result
            status = "ELIGIBLE" if result.get("eligible") else "NOT ELIGIBLE"
            self.log(state, f"  {bid}: {status}")
        return state


class CoordinationAgent(BaseAgent):
    """Builds concrete next-step plans and contact lists."""
    name = "CoordinationAgent"

    def run(self, state: CaseState) -> CaseState:
        self.log(state, "Building coordination plans...")
        for bid in state.requested_benefit_ids:
            # Only fully coordinate those that passed (or all if explore)
            elig = state.eligibility_results.get(bid, {})
            if elig.get("eligible") or state.intent == "explore":
                plan = self.brain.coordinate(bid, state.player)
                state.coordination_plans[bid] = plan
                self.log(state, f"  Plan ready for {bid}")
            else:
                self.log(state, f"  Skipped full plan for ineligible {bid}")
        return state


class CautionAgent(BaseAgent):
    """Surfaces timing risks, dependencies, penalties, and sequencing issues."""
    name = "CautionAgent"

    def run(self, state: CaseState) -> CaseState:
        self.log(state, "Analyzing cautions and dependencies...")
        p = state.player
        cautions = []

        # Cross-benefit dependency examples from the Guide
        if "disability_tp" in state.eligibility_results or "pension" in state.eligibility_results:
            if p.has_applied_for_pension:
                cautions.append({
                    "severity": "high",
                    "benefit_id": "disability_tp",
                    "message": "Total & Permanent Disability generally requires application BEFORE electing Pension. Current profile indicates pension already applied/elected \u2014 T&P window may be closed. Review immediately with plan administrator."
                })
            elif "disability_tp" in state.requested_benefit_ids:
                cautions.append({
                    "severity": "high",
                    "benefit_id": "disability_tp",
                    "message": "If considering Total & Permanent Disability, apply BEFORE electing Pension. Sequencing is critical."
                })

        if "pension" in state.eligibility_results and p.age and p.age < 55:
            cautions.append({
                "severity": "info",
                "benefit_id": "pension",
                "message": f"Player age {p.age}. Pension payable as early as 55; deferring to 65 increases monthly amount."
            })

        if "tuition" in state.eligibility_results:
            tu = state.eligibility_results["tuition"]
            if not tu.get("eligible") and p.years_since_last_active and p.years_since_last_active > 6:
                cautions.append({
                    "severity": "medium",
                    "benefit_id": "tuition",
                    "message": "Tuition Assistance window is typically within ~72 months of last game. Confirm exact Plan Year rules."
                })

        # Collect per-benefit cautions
        for bid, plan in state.coordination_plans.items():
            for c in plan.get("cautions", []):
                cautions.append({
                    "severity": "medium",
                    "benefit_id": bid,
                    "message": c
                })

        # Early withdrawal warnings
        for bid in ["capital_accumulation", "annuity", "401k"]:
            if bid in state.coordination_plans:
                cautions.append({
                    "severity": "medium",
                    "benefit_id": bid,
                    "message": "Withdrawals before age 59\u00bd may incur 10% IRS early-withdrawal penalty (Tax-Qualified accounts)."
                })

        state.cautions = cautions
        self.log(state, f"Identified {len(cautions)} caution(s)")
        return state


class RecommendationAgent(BaseAgent):
    """Prioritizes actions and ranks benefits."""
    name = "RecommendationAgent"

    PRIORITY_ORDER = [
        # High-urgency / time-sensitive first
        "disability_lod", "disability_neuro", "disability_tp",
        "severance", "cv_coverage", "tuition",
        "pension", "hra", "fplip",
        "total_wellness", "transition_coaches",
        "portal", "player_engagement", "legends_networks", "legends_grant"
    ]

    def run(self, state: CaseState) -> CaseState:
        self.log(state, "Generating prioritized recommendations...")
        ranked = []

        for bid in self.PRIORITY_ORDER:
            if bid not in state.eligibility_results:
                continue
            elig = state.eligibility_results[bid]
            if not elig.get("eligible"):
                continue
            plan = state.coordination_plans.get(bid, {})
            ranked.append({
                "benefit_id": bid,
                "name": elig.get("benefit_name"),
                "priority": self.PRIORITY_ORDER.index(bid) if bid in self.PRIORITY_ORDER else 99,
                "summary": elig.get("summary"),
                "amount_or_value": elig.get("amount_or_value"),
                "next_action": (plan.get("how_to_access") or ["Contact plan administrator"])[0],
                "contacts": plan.get("contacts", [])
            })

        # Also include any eligible that weren't in the priority list
        for bid, elig in state.eligibility_results.items():
            if elig.get("eligible") and bid not in [r["benefit_id"] for r in ranked]:
                plan = state.coordination_plans.get(bid, {})
                ranked.append({
                    "benefit_id": bid,
                    "name": elig.get("benefit_name"),
                    "priority": 50,
                    "summary": elig.get("summary"),
                    "amount_or_value": elig.get("amount_or_value"),
                    "next_action": (plan.get("how_to_access") or ["Contact plan administrator"])[0],
                    "contacts": plan.get("contacts", [])
                })

        ranked.sort(key=lambda x: x["priority"])
        state.recommendations = ranked

        # Build simple prioritized action list
        actions = []
        for i, r in enumerate(ranked[:8], 1):  # top 8
            actions.append({
                "step": i,
                "benefit": r["name"],
                "action": r["next_action"],
                "contacts": r["contacts"][:2]
            })
        state.prioritized_actions = actions

        self.log(state, f"Ranked {len(ranked)} eligible benefits; {len(actions)} priority actions")
        return state


class ExplanationAgent(BaseAgent):
    """
    Optional LLM-powered agent that turns the structured Case Package
    into a warm, plain-language explanation for the Legend.
    Falls back to a deterministic template when no LLM is configured.
    """
    name = "ExplanationAgent"

    def __init__(self, brain: BenefitsBrain, llm: Optional[Any] = None, enabled: bool = True):
        super().__init__(brain)
        self.enabled = enabled and _LLM_AVAILABLE
        self.llm = llm
        if self.enabled and self.llm is None:
            self.llm = get_llm_client()

    def run(self, state: CaseState) -> CaseState:
        if not self.enabled or state.final_package is None:
            self.log(state, "Explanation skipped (disabled or no package yet)")
            return state

        self.log(state, f"Generating natural-language explanation via {getattr(self.llm, 'name', 'LLM')}...")

        # Compact payload for the LLM (avoid huge agent logs)
        payload = {
            "player": state.final_package.get("player"),
            "intent": state.final_package.get("intent"),
            "eligible_count": state.final_package.get("summary", {}).get("eligible_count"),
            "priority_actions": state.final_package.get("priority_actions", [])[:6],
            "eligible_benefits": [
                {"name": b["name"], "value": b.get("value")}
                for b in state.final_package.get("eligible_benefits", [])[:8]
            ],
            "cautions": state.final_package.get("cautions", [])[:6],
        }

        user_msg = (
            "Please write a clear, helpful explanation of this benefits coordination result "
            "for the former NFL player (Legend). Focus on what they should do next and any risks.\n\n"
            f"```json\n{json.dumps(payload, indent=2)}\n```"
        )

        try:
            explanation = self.llm.complete(
                system=BENEFITS_EXPLANATION_SYSTEM,
                user=user_msg,
                temperature=0.35,
                max_tokens=700,
            )
            state.final_package["natural_language_explanation"] = explanation
            state.final_package["explanation_provider"] = getattr(self.llm, "name", "unknown")
            self.log(state, "Explanation generated successfully")
        except Exception as e:
            fallback = (
                f"(Explanation generation failed: {e}. "
                "Please review the structured priority_actions and cautions above.)"
            )
            state.final_package["natural_language_explanation"] = fallback
            state.final_package["explanation_provider"] = "error-fallback"
            self.log(state, f"Explanation failed: {e}")

        return state


class OrchestratorAgent(BaseAgent):
    """Routes the case through the agent pipeline and synthesizes the final package."""
    name = "OrchestratorAgent"

    def __init__(self, brain: BenefitsBrain, llm: Optional[Any] = None, enable_explanations: bool = True):
        super().__init__(brain)
        self.intake = IntakeAgent(brain)
        self.eligibility = EligibilityAgent(brain)
        self.coordination = CoordinationAgent(brain)
        self.caution = CautionAgent(brain)
        self.recommendation = RecommendationAgent(brain)
        self.explanation = ExplanationAgent(brain, llm=llm, enabled=enable_explanations)

    def run(self, state: CaseState) -> CaseState:
        self.log(state, "=== Orchestrator starting multi-agent pipeline ===")

        # Sequential pipeline (can be made parallel or conditional later)
        state = self.intake.run(state)
        state = self.eligibility.run(state)
        state = self.coordination.run(state)
        state = self.caution.run(state)
        state = self.recommendation.run(state)

        # Synthesize final package
        state.final_package = {
            "case_id": state.case_id,
            "player": {
                "name": state.player.name,
                "credited_seasons": state.player.credited_seasons,
                "is_vested": state.player.is_vested,
                "age": state.player.age,
                "years_since_last_active": state.player.years_since_last_active,
            },
            "intent": state.intent,
            "status": "completed",
            "summary": {
                "benefits_reviewed": len(state.requested_benefit_ids),
                "eligible_count": sum(1 for r in state.eligibility_results.values() if r.get("eligible")),
                "cautions_count": len(state.cautions),
                "priority_actions": len(state.prioritized_actions),
            },
            "priority_actions": state.prioritized_actions,
            "eligible_benefits": [
                {
                    "id": r["benefit_id"],
                    "name": r["name"],
                    "value": r.get("amount_or_value"),
                    "next_action": r["next_action"],
                    "contacts": r["contacts"],
                }
                for r in state.recommendations
            ],
            "cautions": state.cautions,
            "full_coordination_plans": {
                bid: {
                    "how_to_access": plan.get("how_to_access"),
                    "contacts": plan.get("contacts"),
                    "deadlines": plan.get("deadlines"),
                    "cautions": plan.get("cautions"),
                }
                for bid, plan in state.coordination_plans.items()
            },
            "agent_log": state.agent_log,
            "generated_at": _utc_now_iso(),
            "disclaimer": (
                "Educational tool only. Verify all eligibility, amounts, and procedures "
                "with official NFL Player Benefits sources, plan SPDs, and the current CBA."
            ),
        }

        # Optional natural-language explanation (LLM or mock)
        state = self.explanation.run(state)

        state.status = "completed"
        self.log(state, "=== Pipeline complete. Final package ready. ===")
        return state


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class MultiAgentBenefitsCoordinator:
    """
    High-level fa\u00e7ade for multi-agent benefit coordination.
    """

    def __init__(self, enable_explanations: bool = True, llm: Optional[Any] = None):
        self.brain = BenefitsBrain()
        self.orchestrator = OrchestratorAgent(
            self.brain, llm=llm, enable_explanations=enable_explanations
        )
        self.enable_explanations = enable_explanations

    def create_case(
        self,
        player: PlayerProfile,
        benefit_ids: Optional[List[str]] = None,
        intent: str = "general",
        case_id: Optional[str] = None,
    ) -> CaseState:
        cid = case_id or f"case-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        return CaseState(
            case_id=cid,
            player=copy.deepcopy(player),
            requested_benefit_ids=benefit_ids or [],
            intent=intent,
        )

    def coordinate(
        self,
        player: PlayerProfile,
        benefit_ids: Optional[List[str]] = None,
        intent: str = "general",
    ) -> Dict[str, Any]:
        """
        Run the full multi-agent pipeline (including optional LLM explanation)
        and return the final package.
        """
        state = self.create_case(player, benefit_ids, intent)
        state = self.orchestrator.run(state)
        return state.final_package

    def pretty_print(self, package: Dict[str, Any]):
        """Human-readable summary of a coordination package."""
        print("=" * 70)
        print(f"CASE: {package['case_id']}  |  Status: {package['status']}")
        print(f"Player: {package['player']['name']}  "
              f"(CS={package['player']['credited_seasons']}, "
              f"vested={package['player']['is_vested']}, "
              f"age={package['player']['age']})")
        print("-" * 70)
        print(f"Reviewed: {package['summary']['benefits_reviewed']}  |  "
              f"Eligible: {package['summary']['eligible_count']}  |  "
              f"Cautions: {package['summary']['cautions_count']}")
        print()

        print("PRIORITY ACTIONS")
        for a in package["priority_actions"]:
            print(f"  {a['step']}. {a['benefit']}")
            print(f"      \u2192 {a['action']}")
            if a["contacts"]:
                print(f"      Contacts: {', '.join(a['contacts'])}")
        print()

        if package["cautions"]:
            print("CAUTIONS")
            for c in package["cautions"]:
                print(f"  [{c['severity'].upper()}] {c['benefit_id']}: {c['message']}")
            print()

        print("ALL ELIGIBLE BENEFITS")
        for b in package["eligible_benefits"]:
            val = f"  ({b['value']})" if b.get("value") else ""
            print(f"  \u2022 {b['name']}{val}")
        print()

        # Natural-language explanation (LLM or mock)
        if package.get("natural_language_explanation"):
            provider = package.get("explanation_provider", "unknown")
            print(f"NATURAL-LANGUAGE EXPLANATION  (via {provider})")
            print("-" * 40)
            print(package["natural_language_explanation"])
            print()

        print(package["disclaimer"])
        print("=" * 70)


# ---------------------------------------------------------------------------
# Demo / CLI
# ---------------------------------------------------------------------------

def demo():
    # enable_explanations=True \u2192 uses MockLLM by default (or real LLM if API key present)
    coordinator = MultiAgentBenefitsCoordinator(enable_explanations=True)

    print(f"[LLM] Explanations enabled. Provider will be selected automatically "
          f"(Mock if no XAI_API_KEY / OPENAI_API_KEY).\n")

    # Example player
    player = PlayerProfile(
        name="Marcus 'Tank' Reynolds",
        credited_seasons=7,
        last_credited_season_year=2019,
        is_vested=True,
        years_since_last_active=7,
        age=39,
        retired_before_july_2013=False,
        has_applied_for_pension=False,
        notes="Interested in pension timing, tuition for MBA, and wellness resources."
    )

    print("\n>>> Running multi-agent coordination for exploratory review...\n")
    package = coordinator.coordinate(player, intent="explore")
    coordinator.pretty_print(package)

    print("\n>>> Running focused check on disability + pension (timing risk)...\n")
    player2 = PlayerProfile(
        name="Legacy Player",
        credited_seasons=4,
        is_vested=True,
        years_since_last_active=3,
        age=48,
        has_applied_for_pension=True,  # triggers caution
    )
    package2 = coordinator.coordinate(
        player2,
        benefit_ids=["disability_tp", "pension", "fplip", "hra"],
        intent="check"
    )
    coordinator.pretty_print(package2)

    # Save last package (includes natural_language_explanation)
    with open("/home/workdir/artifacts/sample_coordination_package.json", "w") as f:
        json.dump(package, f, indent=2)
    print("\nSample package written to sample_coordination_package.json")


if __name__ == "__main__":
    demo()
