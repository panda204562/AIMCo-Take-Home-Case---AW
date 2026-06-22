"""Assemble the Question 2 findings (signal + backtest) into a PDF summary report."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1", parent=styles["Heading1"], textColor=colors.HexColor("#1f4e79")))
styles.add(ParagraphStyle("H2", parent=styles["Heading2"], textColor=colors.HexColor("#1f4e79"), spaceBefore=14))
styles.add(ParagraphStyle("Body", parent=styles["BodyText"], spaceAfter=8, leading=14))
styles.add(ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8.5, leading=11, textColor=colors.HexColor("#444444")))

doc = SimpleDocTemplate(
    "Q2_Trading_Signal_Backtest.pdf",
    pagesize=letter,
    topMargin=0.6 * inch, bottomMargin=0.6 * inch,
    leftMargin=0.7 * inch, rightMargin=0.7 * inch,
)

story = []

def h1(t): story.append(Paragraph(t, styles["H1"]))
def h2(t): story.append(Paragraph(t, styles["H2"]))
def body(t): story.append(Paragraph(t, styles["Body"]))
def small(t): story.append(Paragraph(t, styles["Small"]))
def space(h=8): story.append(Spacer(1, h))

img_w = 6.3 * inch

# --- Title ---
h1("Centralized Treasury Take-Home — Question 2")
body("<b>A rich/cheap deployment-timing signal, built from the Question 1 model</b>")
small("Albert Wong &nbsp;|&nbsp; Walk-forward signal + backtest vs. naive even deployment, 2021-04 to 2025-12")
space(10)

# --- BLUF ---
h2("Bottom Line")
body(
    "Reallocating capital deployment toward days the Question 1 model flags as <b>rich</b> (and away "
    "from <b>cheap</b> days), while holding total capital deployed constant, captured an average of "
    "<b>+5.6bp</b> more spread than deploying evenly &mdash; a <b>77% monthly hit rate</b> and "
    "<b>+76bp cumulative advantage</b> over the 57-month out-of-sample backtest. The signal also passes "
    "a basic sanity check: realized spread is monotonic across regimes (cheap 34bp &rarr; neutral 43bp "
    "&rarr; rich 60bp), confirming it carries real information rather than noise."
)
space(6)

# --- Signal definition ---
h2("Signal Definition")
body(
    "<b>Step 1 &mdash; walk-forward fair value.</b> The Question 1 regression is re-estimated on an "
    "expanding window, refit every 21 trading days (~monthly). Each refit uses only data strictly prior "
    "to the refit date, then is applied out-of-sample until the next refit. This matters: using the "
    "full-sample model (fit on all 5 years) to judge whether the spread was “rich” back in 2021 would be "
    "lookahead bias &mdash; those coefficients were estimated partly using 2025 data that didn't exist yet."
)
body(
    "<b>Step 2 &mdash; residual.</b> residual_t = actual spread_t &minus; walk-forward fair value_t."
)
body(
    "<b>Step 3 &mdash; z-score.</b> The residual is standardized using a <b>trailing 60-day</b> window "
    "of past residuals only (no full-sample centering, which also evolves over time as volatility "
    "regimes change)."
)
body(
    "<b>Step 4 &mdash; decision lag.</b> The regime used to decide day t's deployment is the z-score as "
    "of <b>day t&minus;1's close</b> &mdash; the decision never uses same-day information."
)
body("<b>Thresholds:</b> z &gt; +1.0 &rarr; <font color='#1f7a3d'>rich</font> (deploy aggressively). z &lt; &minus;1.0 &rarr; <font color='#c00000'>cheap</font> (delay). Otherwise neutral.")
space(6)

story.append(Image("charts/04_signal_regime.png", width=img_w, height=img_w*5.5/9))
small("Top: realized 3m spread. Bottom: signal z-score (lagged 1 day), colored by regime. Rich/cheap clusters visibly precede the spread's own subsequent swings.")
space(10)

story.append(PageBreak())

# --- Backtest design ---
h2("Backtest Design")
body(
    "Naive baseline: deploy an equal amount each day (equivalent to capturing the simple average spread "
    "over the period). Signal strategy: reallocate the <i>same total capital</i> within each period using "
    "weights &mdash; <b>2.0&times;</b> on rich days, <b>1.0&times;</b> neutral, <b>0.3&times;</b> on cheap "
    "days (mostly, not fully, deferred &mdash; operationally you rarely have unlimited flexibility to "
    "defer cash indefinitely). Because both strategies deploy the same total capital, the difference in "
    "captured spread is attributable purely to <i>timing</i>, not to taking more or less risk overall."
)
space(6)

tbl_data = [
    ["Metric", "Value"],
    ["Naive average captured spread", "46.05 bp"],
    ["Signal-weighted average captured spread", "51.63 bp"],
    ["Advantage from timing", "+5.58 bp"],
    ["Monthly hit rate", "77.2% (44 / 57 months)"],
    ["Average monthly advantage", "+1.33 bp"],
    ["Cumulative advantage (57 months)", "+75.7 bp"],
]
t = Table(tbl_data, colWidths=[3.3*inch, 2.3*inch])
t.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1f4e79")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f2f2f2")]),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
story.append(t)
space(10)

story.append(Image("charts/05_realized_by_regime.png", width=4.5*inch, height=4.5*inch*3.5/6))
space(6)
story.append(Image("charts/06_cumulative_advantage.png", width=img_w, height=img_w*3.8/9))
small("The advantage accrues steadily across the full 4.75-year out-of-sample window rather than being concentrated in one lucky stretch — only 6 of 57 months underperformed naive, and the worst monthly shortfall was −0.51bp.")

story.append(PageBreak())

# --- Limitations ---
h2("Limitations & Assumptions")
body(
    "<b>Lookahead bias</b> is addressed structurally (walk-forward refit, trailing-only z-score, "
    "1-day decision lag) rather than just asserted — but the burn-in period (first ~14 months) had to "
    "be discarded to get a stable initial model, which is itself a modeling choice."
)
body(
    "<b>Weights (2.0 / 1.0 / 0.3) are a stated assumption, not fit to the data.</b> They were chosen to "
    "be a moderate, defensible tilt rather than an aggressive one. Results are a magnitude question, not "
    "a sign question — more aggressive weights would mechanically show a larger advantage, but the "
    "monthly hit rate (which doesn't depend on the weight magnitude as strongly) is the more robust "
    "number to anchor on."
)
body(
    "<b>Transaction costs are not modeled.</b> Shifting deployment day-to-day (rolling TRS/repo "
    "positions earlier or later) has real operational friction and counterparty negotiation costs that "
    "would eat into the ~5.6bp average edge."
)
body(
    "<b>Dealer capacity constraints work against the strategy exactly when it matters most.</b> “Rich” "
    "days often coincide with stressed/volatile conditions (per the Q1 finding) — precisely when dealers "
    "are most likely to be balance-sheet constrained and least able to actually take the other side of "
    "the trade at the rate the signal suggests. The backtest assumes you can always get filled; live "
    "implementation cannot assume that."
)
body(
    "<b>Model risk carries over from Question 1:</b> the underlying regression's relationships were "
    "shown to be partly regime-level co-movement rather than tight daily causation (see the "
    "first-difference robustness check in the Q1 report). If those macro relationships shift structurally "
    "going forward, the walk-forward refit will adapt, but with a lag — there will always be a transition "
    "period where the “fair value” is anchored to a stale regime."
)
body(
    "<b>Residual autocorrelation</b> means consecutive rich/cheap days are not independent bets — the "
    "57 monthly observations are a more honest count of independent trials than the 1,175 daily "
    "observations would suggest."
)

doc.build(story)
print("PDF written: Q2_Trading_Signal_Backtest.pdf")
