# NFL Legends Benefits Brain 🏈

Multi-agent system for **eligibility checks**, **benefit coordination**, and **plain-language guidance** for former NFL players (Legends).

Built from the **NFL Legends Community Resource Guide (2026 / 2020 CBA)**.

> **Educational / reference tool only.** Always verify eligibility, amounts, and procedures with official sources ([NFLPlayerBenefits.com](https://www.nflplayerbenefits.com), plan SPDs, and the current CBA).

## Features

| Component | Description |
|-----------|-------------|
| **Knowledge Base** | 21+ benefits across Financial, Medical/Disability, Wellness, Career, Education, Perks |
| **Eligibility Engine** | Deterministic rule-based “award” checks using a simple PlayerProfile |
| **Multi-Agent Pipeline** | Intake → Eligibility → Coordination → Caution → Recommendation → Explanation |
| **Caution Agent** | Surfaces timing risks (e.g. Total & Permanent Disability **before** Pension election), IRS early-withdrawal warnings |
| **LLM Explanations** | Optional plain-language summaries (Mock offline, or live xAI Grok / OpenAI) |
| **Streamlit UI** | Interactive web app for profile entry, one-click coordination, and knowledge browsing |

## Quick Start

```bash
# Clone
git clone https://github.com/emaillp77/nfl-legends-benefits-brain.git
cd nfl-legends-benefits-brain

# Install
pip install -r requirements.txt

# Run CLI demo
python multi_agent_benefits_coordinator.py

# Run web app
streamlit run app.py
# or
./run_app.sh
```

## Multi-Agent Architecture

```
PlayerProfile + request
        |
        v
+-----------------+
|  IntakeAgent    |  normalize profile, expand exploratory set
+--------+--------+
         v
+-----------------+
| EligibilityAgent|  rule-based award checks
+--------+--------+
         v
+-----------------+
|CoordinationAgent|  how-to-access steps + contacts
+--------+--------+
         v
+-----------------+
|  CautionAgent   |  timing risks, dependencies, penalties
+--------+--------+
         v
+-----------------+
|RecommendationAg.|  prioritize next actions
+--------+--------+
         v
+-----------------+
|ExplanationAgent |  plain-language summary (Mock / Grok / OpenAI)
+--------+--------+
         v
   Case Package (JSON)
```

## LLM Explanations (optional)

| Priority | Env Var | Provider |
|----------|---------|----------|
| 1 | `XAI_API_KEY` or `GROK_API_KEY` | xAI Grok |
| 2 | `OPENAI_API_KEY` (+ optional `OPENAI_BASE_URL`, `OPENAI_MODEL`) | OpenAI-compatible |
| 3 | (none) | **MockLLMClient** (offline, deterministic) |

```bash
export XAI_API_KEY="your-key"
python multi_agent_benefits_coordinator.py
```

## Project Structure

```
├── nfl_legends_benefits_brain.py       # Core knowledge base + eligibility rules
├── multi_agent_benefits_coordinator.py # Multi-agent pipeline + Orchestrator
├── llm_client.py                       # Mock / xAI / OpenAI client
├── app.py                              # Streamlit web UI
├── run_app.sh                          # Convenience launcher
├── benefits_knowledge.json             # Exported knowledge
├── sample_coordination_package.json    # Example output
├── requirements.txt
└── README.md
```

## Example (Python)

```python
from multi_agent_benefits_coordinator import MultiAgentBenefitsCoordinator
from nfl_legends_benefits_brain import PlayerProfile

coord = MultiAgentBenefitsCoordinator(enable_explanations=True)

player = PlayerProfile(
    name="Marcus Reynolds",
    credited_seasons=7,
    is_vested=True,
    age=39,
    years_since_last_active=7,
)

package = coord.coordinate(player, intent="explore")
coord.pretty_print(package)
```

## Disclaimer

This project is an **educational tool**. It is not affiliated with or endorsed by the NFL, NFLPA, or any plan administrator. Benefit rules change. Always confirm with official plan documents and administrators before taking action.

## License

MIT (or as specified by the repository owner).
