# Setup

All core modules are now in this repository.

## Quick start

```bash
git clone https://github.com/emaillp77/nfl-legends-benefits-brain.git
cd nfl-legends-benefits-brain
pip install -r requirements.txt

# CLI demo
python multi_agent_benefits_coordinator.py

# Web UI
streamlit run app.py
# or
./run_app.sh
```

## Optional LLM explanations

```bash
export XAI_API_KEY="your-key"   # or OPENAI_API_KEY
python multi_agent_benefits_coordinator.py
```

Without a key, the MockLLMClient provides offline plain-language summaries.

## Project layout

| File | Role |
|------|------|
| `nfl_legends_benefits_brain.py` | Knowledge base + eligibility rules |
| `multi_agent_benefits_coordinator.py` | Multi-agent pipeline |
| `llm_client.py` | Mock / xAI / OpenAI client |
| `app.py` | Streamlit UI |
| `benefits_knowledge.json` | Exported knowledge (21 benefits) |
| `sample_coordination_package.json` | Example Case Package |
| `run_app.sh` | Launcher |
| `requirements.txt` | Dependencies |

## Disclaimer

Educational / reference tool only. Always verify eligibility, amounts, and procedures with official NFL Player Benefits sources, plan SPDs, and the current CBA.
