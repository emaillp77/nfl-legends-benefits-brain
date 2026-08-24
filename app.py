#!/usr/bin/env python3
"""
NFL Legends Benefits Coordinator — Streamlit App

Interactive UI for eligibility checks, multi-agent coordination,
and optional LLM explanations.
"""

from __future__ import annotations
import json
import streamlit as st
from datetime import datetime

from nfl_legends_benefits_brain import BenefitsBrain, PlayerProfile, BenefitCategory
from multi_agent_benefits_coordinator import MultiAgentBenefitsCoordinator


# ---------------------------------------------------------------------------
# Page config & styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NFL Legends Benefits Brain",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #555;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .eligible-box {
        background: #e8f5e9;
        border-left: 5px solid #2e7d32;
        padding: 0.75rem 1rem;
        margin: 0.4rem 0;
        border-radius: 4px;
    }
    .caution-high {
        background: #ffebee;
        border-left: 5px solid #c62828;
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        border-radius: 4px;
    }
    .caution-medium {
        background: #fff8e1;
        border-left: 5px solid #f9a825;
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        border-radius: 4px;
    }
    .caution-info {
        background: #e3f2fd;
        border-left: 5px solid #1565c0;
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        border-radius: 4px;
    }
    .action-step {
        background: #f5f5f5;
        padding: 0.7rem 1rem;
        margin: 0.35rem 0;
        border-radius: 6px;
        border: 1px solid #e0e0e0;
    }
    .stButton>button {
        background-color: #1a237e;
        color: white;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Cached resources
# ---------------------------------------------------------------------------
@st.cache_resource
def get_brain():
    return BenefitsBrain()


@st.cache_resource
def get_coordinator(enable_explanations: bool = True):
    return MultiAgentBenefitsCoordinator(enable_explanations=enable_explanations)


# ---------------------------------------------------------------------------
# Sidebar — Player Profile
# ---------------------------------------------------------------------------
st.sidebar.markdown("## 👤 Player Profile")
st.sidebar.caption("Enter the Legend’s basic information")

name = st.sidebar.text_input("Name", value="Marcus Reynolds")
credited_seasons = st.sidebar.number_input("Credited Seasons", min_value=0, max_value=25, value=5, step=1)
is_vested = st.sidebar.checkbox("Vested (typically 3+ seasons)", value=True)
age = st.sidebar.number_input("Age", min_value=20, max_value=90, value=40, step=1)
years_since = st.sidebar.number_input("Years since last active season", min_value=0, max_value=40, value=4, step=1)
retired_pre_2013 = st.sidebar.checkbox("Retired by July 2013 (PFRPA dental/vision)", value=False)
has_pension = st.sidebar.checkbox("Already applied for / elected Pension", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("## ⚙️ Options")
enable_llm = st.sidebar.checkbox("Generate natural-language explanation", value=True)
intent = st.sidebar.selectbox(
    "Intent",
    options=["explore", "check", "apply", "urgent"],
    index=0,
    help="explore = broad review; check = specific benefits; apply = action-oriented"
)

# Benefit selection
brain = get_brain()
all_benefit_ids = sorted(brain.benefits.keys())
benefit_labels = {bid: f"{brain.benefits[bid].name}" for bid in all_benefit_ids}

st.sidebar.markdown("### Benefits to review")
selected = st.sidebar.multiselect(
    "Leave empty for automatic exploratory set",
    options=all_benefit_ids,
    format_func=lambda x: benefit_labels.get(x, x),
    default=[],
)

run_button = st.sidebar.button("🚀 Run Coordination", type="primary", use_container_width=True)


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.markdown('<p class="main-header">🏈 NFL Legends Benefits Brain</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Multi-agent eligibility checks, coordination plans, and plain-language guidance for former NFL players</p>',
    unsafe_allow_html=True,
)

# Tabs
tab_coord, tab_knowledge, tab_about = st.tabs(["📋 Coordination", "📚 Knowledge Base", "ℹ️ About"])


with tab_coord:
    if not run_button and "last_package" not in st.session_state:
        st.info("← Fill in the player profile in the sidebar and click **Run Coordination** to begin.")
        st.markdown("""
        **What this app does**
        1. **Intake** — normalizes the player profile and request  
        2. **Eligibility** — runs rule-based award checks  
        3. **Coordination** — builds step-by-step access plans + contacts  
        4. **Caution** — surfaces timing risks and dependencies  
        5. **Recommendation** — prioritizes next actions  
        6. **Explanation** (optional) — plain-language summary via Mock or live LLM  
        """)
    else:
        if run_button:
            player = PlayerProfile(
                name=name,
                credited_seasons=int(credited_seasons),
                is_vested=is_vested,
                age=int(age),
                years_since_last_active=int(years_since),
                retired_before_july_2013=retired_pre_2013,
                has_applied_for_pension=has_pension,
            )
            coordinator = get_coordinator(enable_explanations=enable_llm)
            with st.spinner("Running multi-agent pipeline..."):
                package = coordinator.coordinate(
                    player,
                    benefit_ids=selected if selected else None,
                    intent=intent,
                )
            st.session_state["last_package"] = package
            st.session_state["last_player"] = player

        package = st.session_state.get("last_package")
        if not package:
            st.warning("No results yet.")
        else:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Benefits Reviewed", package["summary"]["benefits_reviewed"])
            col2.metric("Eligible", package["summary"]["eligible_count"])
            col3.metric("Cautions", package["summary"]["cautions_count"])
            col4.metric("Priority Actions", package["summary"]["priority_actions"])

            st.markdown("---")

            # Priority Actions
            st.subheader("🎯 Priority Actions")
            if package.get("priority_actions"):
                for a in package["priority_actions"]:
                    contacts = ", ".join(a.get("contacts") or [])
                    st.markdown(f"""
                    <div class="action-step">
                        <strong>{a['step']}. {a['benefit']}</strong><br>
                        → {a['action']}<br>
                        <small>📞 {contacts}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("No priority actions generated.")

            # Cautions
            st.subheader("⚠️ Cautions")
            if package.get("cautions"):
                for c in package["cautions"]:
                    sev = c.get("severity", "info").lower()
                    css = f"caution-{sev}" if sev in ("high", "medium", "info") else "caution-info"
                    st.markdown(f"""
                    <div class="{css}">
                        <strong>[{c.get('severity','').upper()}] {c.get('benefit_id','')}</strong><br>
                        {c.get('message','')}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("No major cautions identified.")

            # Eligible benefits
            st.subheader("✅ Eligible Benefits")
            for b in package.get("eligible_benefits", []):
                val = f"<br><em>{b['value']}</em>" if b.get("value") else ""
                contacts = ", ".join(b.get("contacts") or [])
                st.markdown(f"""
                <div class="eligible-box">
                    <strong>{b['name']}</strong>{val}<br>
                    <small>Next: {b.get('next_action','')}<br>📞 {contacts}</small>
                </div>
                """, unsafe_allow_html=True)

            # Natural language explanation
            if package.get("natural_language_explanation"):
                st.subheader("💬 Plain-Language Explanation")
                provider = package.get("explanation_provider", "unknown")
                st.caption(f"Generated via {provider}")
                st.markdown(package["natural_language_explanation"])

            # Full plans (expandable)
            with st.expander("📄 Full Coordination Plans"):
                st.json(package.get("full_coordination_plans", {}))

            with st.expander("🔍 Agent Log"):
                for line in package.get("agent_log", []):
                    st.text(line)

            with st.expander("📦 Raw Case Package (JSON)"):
                st.json(package)

            st.markdown("---")
            st.caption(package.get("disclaimer", ""))


with tab_knowledge:
    st.subheader("Benefits Knowledge Base")
    st.caption("All benefits currently loaded in the brain")

    # Filter by category
    categories = sorted({b.category.value for b in brain.benefits.values()})
    cat_filter = st.selectbox("Filter by category", ["All"] + categories)

    for bid, b in sorted(brain.benefits.items(), key=lambda x: x[1].name):
        if cat_filter != "All" and b.category.value != cat_filter:
            continue
        with st.expander(f"{b.name}  ·  `{bid}`"):
            st.markdown(f"**Category:** {b.category.value}")
            st.markdown(f"**Summary:** {b.summary}")
            if b.amount_or_value:
                st.markdown(f"**Value / Amount:** {b.amount_or_value}")
            st.markdown("**Eligibility rules:**")
            for r in b.eligibility_rules:
                st.markdown(f"- {r.description}")
            st.markdown("**How to access:**")
            for step in b.how_to_access:
                st.markdown(f"- {step}")
            st.markdown(f"**Contacts:** {', '.join(b.contacts)}")
            if b.cautions:
                st.markdown("**Cautions:**")
                for c in b.cautions:
                    st.markdown(f"- ⚠️ {c}")


with tab_about:
    st.markdown("""
    ### NFL Legends Benefits Brain

    An educational multi-agent system built from the **NFL Legends Community Resource Guide (2026 / 2020 CBA)**.

    **Agents**
    | Agent | Role |
    |-------|------|
    | IntakeAgent | Validates profile & request |
    | EligibilityAgent | Rule-based award checks |
    | CoordinationAgent | Step-by-step access plans |
    | CautionAgent | Timing risks & dependencies |
    | RecommendationAgent | Prioritized next actions |
    | ExplanationAgent | Plain-language summary (Mock or live LLM) |

    **Important**
    - This is an **educational / reference tool only**.
    - Always verify eligibility, amounts, and procedures with official sources:
      - [NFLPlayerBenefits.com](https://www.nflplayerbenefits.com)
      - Plan Summary Plan Descriptions (SPDs)
      - Current Collective Bargaining Agreement
    - Rules and benefits can change with future CBAs.

    **LLM explanations**
    - Default: Mock (offline, deterministic)
    - Set `XAI_API_KEY` or `OPENAI_API_KEY` for live Grok / OpenAI explanations
    """)

    st.markdown("---")
    st.caption(f"Generated at session start · {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
