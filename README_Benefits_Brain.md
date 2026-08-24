# NFL Legends Benefits Brain

A lightweight, rule-based **"brain"** for simple benefit eligibility awards and coordination, built from the **NFL Legends Community Resource Guide (2026 / 2020 CBA)**.

## What it does

- **Knowledge base** of 21+ key benefits across Financial, Medical/Disability, Wellness, Career, Education, and Perks.
- **Simple eligibility evaluation** (“award” check) using a `PlayerProfile` (credited seasons, vested status, age, years since last active, etc.).
- **Coordination packages**: step-by-step how-to-access, contacts, links, deadlines, and cautions.
- **Recommendations**: list benefits that pass eligibility for a given player profile.
- **Search** by keyword.

This is an **educational / reference tool only**.  
Always verify eligibility, amounts, and procedures with official sources:
- [NFLPlayerBenefits.com](https://www.nflplayerbenefits.com)
- Plan Summary Plan Descriptions (SPDs)
- Current Collective Bargaining Agreement

Rules and benefits can change with future CBAs or plan amendments.

## Quick start

```bash
cd /home/workdir/artifacts
python3 nfl_legends_benefits_brain.py
```

Interactive commands:
- `list` – list all benefits
- `search <keyword>`
- `check <benefit_id>` – eligibility for sample player
- `coord <benefit_id>` – full coordination package
- `recommend` – benefits that pass for sample player
- `profile` – view sample PlayerProfile
- `quit`

## Programmatic use

```python
from nfl_legends_benefits_brain import BenefitsBrain, PlayerProfile

brain = BenefitsBrain()

player = PlayerProfile(
    name="Jane Legend",
    credited_seasons=6,
    is_vested=True,
    years_since_last_active=4,
    age=41,
    retired_before_july_2013=False,
    has_applied_for_pension=False
)

# Eligibility award check
print(brain.evaluate_eligibility("pension", player))

# Coordination (steps + contacts)
print(brain.coordinate("tuition", player))

# Recommendations
for rec in brain.recommend(player):
    print(rec["name"])
```

## Extending the brain

1. Add new `Benefit` objects inside `_load_knowledge()`.
2. Write clear `EligibilityRule` callables that take a `PlayerProfile`.
3. Keep `how_to_access` and `contacts` up to date from official sources.
4. For production use, replace simple rules with real plan data lookups and add authentication / audit logging.

## Key contacts (from the Guide)

| Resource                        | Contact                              |
|---------------------------------|--------------------------------------|
| NFL Player Benefits / Severance | 800.635.4625 (prompt 1)             |
| Main Benefits line              | 800.638.3186                        |
| HRA                             | 800.501.7633                        |
| CV Insurance (Cigna)            | 800.635.9671 / myCigna.com          |
| Total Wellness                  | TotalWellness@nfl.com               |
| NFL Life Line                   | 800.506.0078 / nflifeline.org       |
| Players Community               | players.nfl.com                     |
| Legends email                   | NFLLegends@NFL.com                  |
| Tracy Perlman (SVP)             | Tracy.Perlman@nfl.com               |

## Multi-Agent Coordination

A full multi-agent pipeline is available in `multi_agent_benefits_coordinator.py`.

**Agents:**

| Agent | Role |
|-------|------|
| **IntakeAgent** | Validates player profile, normalizes request, sets default exploratory set |
| **EligibilityAgent** | Runs deterministic rule-based award checks |
| **CoordinationAgent** | Builds concrete how-to-access steps + contacts |
| **CautionAgent** | Surfaces timing risks, IRS penalties, benefit dependencies (e.g. T&P before Pension) |
| **RecommendationAgent** | Prioritizes actions by urgency / value |
| **OrchestratorAgent** | Sequences the pipeline and synthesizes the final Case Package |

**Usage:**
```python
from multi_agent_benefits_coordinator import MultiAgentBenefitsCoordinator
from nfl_legends_benefits_brain import PlayerProfile

coord = MultiAgentBenefitsCoordinator()
player = PlayerProfile(name="Legend", credited_seasons=5, is_vested=True, age=40)
package = coord.coordinate(player, intent="explore")
coord.pretty_print(package)
```

Or run the demo:
```bash
python3 multi_agent_benefits_coordinator.py
```

## LLM Integration for Explanations

Natural-language explanations are provided by an optional **ExplanationAgent**.

### How it works
1. The deterministic multi-agent pipeline produces a structured Case Package.
2. `ExplanationAgent` sends a compact JSON summary to an LLM (or Mock).
3. The resulting plain-language explanation is attached as `natural_language_explanation`.

### Providers (auto-detected)
| Priority | Env Vars | Provider |
|----------|----------|----------|
| 1 | `XAI_API_KEY` or `GROK_API_KEY` | xAI Grok (`https://api.x.ai/v1`) |
| 2 | `OPENAI_API_KEY` (+ optional `OPENAI_BASE_URL`, `OPENAI_MODEL`) | OpenAI or compatible |
| 3 | (none) | **MockLLMClient** (deterministic, offline) |

Optional controls:
- `LLM_PROVIDER=mock|xai|openai` to force a provider
- `XAI_MODEL` / `OPENAI_MODEL` to choose the model

### Usage
```python
from multi_agent_benefits_coordinator import MultiAgentBenefitsCoordinator
from nfl_legends_benefits_brain import PlayerProfile

# Explanations on (default) — uses Mock if no key, real LLM if key present
coord = MultiAgentBenefitsCoordinator(enable_explanations=True)

# Or force mock / disable
coord = MultiAgentBenefitsCoordinator(enable_explanations=False)
```

### Files added
- `llm_client.py` — thin LLM abstraction (Mock + OpenAI-compatible / xAI)
- ExplanationAgent integrated into the Orchestrator pipeline

The core eligibility and coordination logic remains fully deterministic and does not require an LLM.

## Streamlit Web App

A full interactive UI is available:

```bash
cd /home/workdir/artifacts
./run_app.sh
# or
streamlit run app.py
```

Then open the local URL (usually http://localhost:8501).

**Features**
- Sidebar player profile (credited seasons, vested, age, pension status, etc.)
- Multi-select benefits or automatic exploratory set
- One-click multi-agent coordination
- Priority actions, color-coded cautions, eligible benefits
- Optional plain-language explanation (Mock or live LLM)
- Browsable knowledge base of all 21 benefits
- Agent log and raw JSON package

**Files**
- `app.py` — Streamlit application
- `run_app.sh` — convenience launcher

## Files

- `nfl_legends_benefits_brain.py` — core knowledge base + single-agent checks
- `multi_agent_benefits_coordinator.py` — multi-agent coordination logic
- `benefits_knowledge.json` — exported knowledge
- `sample_coordination_package.json` — example output
- `legends_guide.txt` — full text extract of the source PDF
- This README

Built for simple, transparent benefit awareness and multi-agent coordination for NFL Legends.
