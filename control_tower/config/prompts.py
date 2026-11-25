"""
Prompt templates for Gemini API calls.
Used by agents to generate natural-language explanations and recommendations.
Populated in Phase 2 (Agent Layer).
"""

# ── System prompt shared by all agents ─────────────────────────────
SYSTEM_PROMPT = """You are an AI warehouse operations analyst for a hypothetical
e-commerce warehouse near Delhi NCR. Your role is to interpret COMPUTED data from
the warehouse dataset and provide clear, actionable analysis.

RULES:
1. Only reference numbers that come from the tool outputs. Never invent data.
2. Clearly label every number as [COMPUTED] when citing a calculated value.
3. When making recommendations, label them as [AI ANALYSIS] and explain your
   reasoning by citing the supporting data.
4. If you do not have sufficient data to answer, say so honestly.
5. The dataset is SYNTHETIC (academic project). Do not claim it is real.
6. Use Indian business context (₹ for currency, Indian cities, shifts).
"""

# ── Agent-specific prompt templates (placeholders for Phase 2) ─────

DATA_ANALYSIS_PROMPT = """Analyse the following warehouse KPI data and provide
a clear summary for a warehouse operations manager.

DATA:
{computed_data}

Provide:
1. A 2-3 sentence executive summary.
2. Key highlights (use bullet points).
3. Any concerning trends.
"""

DELAY_INVESTIGATION_PROMPT = """Investigate the following order delay and explain
the root cause in business terms.

ORDER DETAILS:
{order_data}

STAGE ANALYSIS:
{stage_analysis}

CONTEXTUAL FACTORS:
{factors}

Provide a step-by-step investigation narrative explaining:
1. What happened to this order at each stage.
2. Which stage caused the delay and why.
3. Whether this is a systemic issue or a one-off.
"""

BOTTLENECK_ANALYSIS_PROMPT = """Analyse the following bottleneck detection results
and explain the operational implications.

BOTTLENECK DATA:
{bottleneck_data}

STAGE RANKING:
{stage_ranking}

Provide:
1. Which stage is the primary bottleneck and why.
2. Whether this is a chronic or episodic issue.
3. The operational impact on delivery performance.
"""

RECOMMENDATION_PROMPT = """Based on the following verified operational data,
generate practical recommendations for the warehouse manager.

BOTTLENECK ANALYSIS:
{bottleneck_data}

SHIFT PERFORMANCE:
{shift_data}

INVENTORY STATUS:
{inventory_data}

COST ANALYSIS:
{cost_data}

Generate 3-5 actionable recommendations. For each:
1. State the recommendation clearly.
2. Cite the specific data point that supports it.
3. Estimate the difficulty (Low/Medium/High).
4. Flag if it requires management approval.
"""

REPORT_SUMMARY_PROMPT = """Write an executive summary (3-4 paragraphs) for the
following warehouse operations report.

KPI DATA:
{kpi_data}

BOTTLENECK:
{bottleneck}

The tone should be professional but accessible to non-technical managers.
Mention specific numbers. End with 1-2 priority action items.
"""
