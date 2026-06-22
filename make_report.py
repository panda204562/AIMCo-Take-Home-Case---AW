"""Assemble the Question 1 findings into a PDF summary report."""

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
    "Q1_Financing_Spread_Drivers.pdf",
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

# --- Title ---
h1("Centralized Treasury Take-Home — Question 1")
body("<b>What drives the S&amp;P 500 equity financing spread over SOFR?</b>")
small("Albert Wong &nbsp;|&nbsp; Regression analysis of financing_spreads.csv (Jan 2020 – Dec 2025) against public macro/vol features")
space(10)

# --- BLUF ---
h2("Bottom Line")
body(
    "The 3-month financing spread is best explained by four features: <b>VIX</b>, the "
    "<b>SOFR&minus;EFFR basis</b>, <b>ON RRP usage</b>, and <b>trailing 1-month S&amp;P 500 return</b> "
    "(R&sup2; = 0.46). The spread is fundamentally <b>demand-driven, not supply-driven</b>: in calm, "
    "low-vol markets investors lever up into synthetic equity exposure, pushing the spread up; in "
    "risk-off/high-vol periods, deleveraging collapses demand for synthetic longs faster than dealer "
    "balance-sheet capacity shrinks, compressing the spread. As of the last observation in the data "
    "(2025-12-31), the model's fair value is <b>94.4bp</b> vs. an actual <b>57.5bp</b> &mdash; the spread "
    "is currently running about <b>37bp cheap</b> to fundamentals."
)
space(6)

# --- Model ---
h2("The Model")
body(
    "spread_3m_bp&nbsp;=&nbsp;92.4&nbsp;&minus;&nbsp;1.61&middot;VIX&nbsp;+&nbsp;1.22&middot;(SOFR&minus;EFFR basis, bp)"
    "&nbsp;&minus;&nbsp;0.015&middot;(RRP usage, $bn)&nbsp;&minus;&nbsp;88.4&middot;(SPX 21-day return)"
)
small("OLS, Newey-West HAC standard errors (5 lags) to correct for daily autocorrelation in the spread. n = 1,487 trading days. All four coefficients significant at p &lt; 0.001.")
space(6)

tbl_data = [
    ["Feature", "Coefficient", "Std. coef.", "p-value", "Mechanism"],
    ["VIX", "-1.61", "-0.46", "<0.001", "Vol → risk appetite for synthetic exposure (see below)"],
    ["SOFR−EFFR basis (bp)", "+1.22", "+0.19", "<0.001", "Collateral/repo market stress"],
    ["RRP usage ($bn)", "-0.015", "-0.45", "<0.001", "System-wide cash/liquidity slack"],
    ["SPX 21d return", "-88.4", "-0.17", "<0.001", "Risk-on momentum / deleveraging"],
]
t = Table(tbl_data, colWidths=[1.3*inch, 0.85*inch, 0.75*inch, 0.6*inch, 2.5*inch])
t.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1f4e79")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f2f2f2")]),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
]))
story.append(t)
space(10)

img_w = 6.3 * inch
story.append(Image("charts/02_feature_importance.png", width=img_w, height=img_w*3.5/7))
space(4)
small("Standardized coefficients let us compare features measured in wildly different units (VIX points vs. $bn vs. bp) on one scale.")
space(10)

h2("Why the 3-Month Tenor?")
body(
    "All four regressors are <i>spot/current</i> readings &mdash; today's VIX, today's liquidity "
    "conditions. The 3m spread reflects near-term financing conditions, so it's a clean horizon match "
    "for spot inputs. The 1y spread reflects <i>expectations</i> about financing conditions a year out "
    "&mdash; explaining that with only today's spot VIX (rather than the market's expected VIX path) is "
    "a horizon mismatch. More importantly, Question 2 is about a <i>tactical</i> decision &mdash; when to "
    "deploy capital day-to-day &mdash; which is naturally tied to the near-term rate, not a 1-year "
    "structural one. To be transparent: the 1y model is not a worse fit &mdash; it has a slightly "
    "<i>higher</i> R&sup2; (0.474 vs. 0.457) on the same four features. 3m is the headline tenor because "
    "it's the more decision-relevant one for what Treasury actually does with this, not because it "
    "fits the data better."
)
space(6)

# --- The surprise ---
h2("The Counterintuitive Finding: Why Is VIX Negative?")
body(
    "Going in, the expected sign on VIX was <b>positive</b> &mdash; higher volatility should mean higher "
    "dealer hedging/balance-sheet costs, which should be passed through as a wider spread. The data "
    "says the opposite, and it's not a fluke: the negative relationship holds (a) in the raw univariate "
    "correlation, (b) when the COVID crash window (Feb&ndash;Aug 2020) is excluded entirely, and (c) it is "
    "the <i>only</i> feature that remains significant when the model is re-estimated on day-over-day "
    "<b>changes</b> rather than levels (a robustness check run specifically because the levels regression "
    "had severe residual autocorrelation, Durbin-Watson = 0.10 &mdash; a classic warning sign that two "
    "persistent series can appear related simply because both trend over time)."
)
body(
    "The corrected interpretation: this spread is <b>demand-driven</b>. In calm markets, investors lever "
    "up and chase synthetic equity exposure because it's capital-efficient &mdash; demand for financing "
    "rises, and so does its price. In a vol spike, investors deleverage and demand for synthetic long "
    "exposure collapses faster than dealer capacity does, so the spread compresses. RRP's negative sign "
    "tells the same liquidity story: more idle cash parked at the Fed (ample system liquidity) coincides "
    "with a cheaper financing spread."
)
story.append(Image("charts/01_spread_vs_vix.png", width=img_w, height=img_w*4/9))
small("Spread (blue, 3m solid / 1y faded) vs. VIX (red). Note the inverse relationship: VIX spikes in 2020 coincide with the spread cratering (even going negative); the spread's highest levels (2024–25) occur while VIX stayed low.")
space(6)

h2("Robustness Caveat")
body(
    "Re-estimating on day-over-day changes (rather than levels) drops R&sup2; to 0.04 and only VIX stays "
    "significant. The basis, RRP, and SPX-return relationships look like slow, multi-month regime "
    "co-movement (sensible — liquidity conditions and term structure evolve gradually) rather than tight "
    "daily causation. Both framings are legitimate for different purposes, but the levels-model R&sup2; "
    "should be read as “what regime are we in,” not “what moved the spread today.”"
)
space(6)

story.append(Image("charts/03_actual_vs_fitted.png", width=img_w, height=img_w*5.5/9))
small("Model fit over time, with the residual (actual minus fair value) shown below. The latest reading (2025-12-31, also year-end) sits 37bp below fair value — unusually cheap.")

story.append(PageBreak())

# --- Features considered but not used ---
h2("Features Considered But Not Used")
body(
    "<b>Curve slope (T10Y3M)</b> &mdash; insignificant in both the 3m (p=0.37) and 1y (p=0.54) models; "
    "dropping it cost only 0.003 of R&sup2;. Might matter more as a regressor on the <i>1y-minus-3m spread "
    "differential</i> itself rather than on either level."
)
body(
    "<b>SPX realized vol (21d)</b> &mdash; 82% correlated with VIX (VIF 3&ndash;4) and insignificant once VIX "
    "is included; redundant, not wrong. A future cut: the <i>implied-minus-realized vol gap</i> (the vol "
    "risk premium) rather than either series alone."
)
body(
    "<b>Treasury General Account (TGA) level</b> &mdash; only available weekly on FRED (WTREGEN); "
    "forward-filling to daily creates a step-function feature that understates true daily variation. "
    "A true daily TGA series exists on Treasury's Fiscal Data API (different source) and would be the "
    "cleaner fix."
)
body(
    "<b>Quarter-end calendar dummy</b> &mdash; not built into this version. Notably, the dataset's last "
    "observation (2025-12-31) is itself a year/quarter-end, and its residual is unusually large (&minus;37bp). "
    "A 0/1 flag (or days-to-quarter-end countdown) for the dealer balance-sheet “turn” effect would mainly "
    "help <i>clean up the residual</i> for a follow-on trading-signal exercise &mdash; without it, a few "
    "mechanically predictable days per quarter would otherwise look like genuine mispricing."
)
space(6)

# --- Data sources table ---
h2("Data Sources Used vs. Considered")
src_data = [
    ["Source", "Used?", "Why / future path"],
    ["FRED", "Yes — backbone", "VIX, SOFR, EFFR, RRP, SPX all sourced here. Free, reliable, no rate limits."],
    ["CFTC Commitments of Traders", "No", "Conceptually strong (asset-manager net futures positioning = direct demand proxy) but weekly frequency and a non-trivial file format to parse. Would sharpen the demand-side story with more time."],
    ["CBOE VIX term structure", "No — used spot VIX", "Spot VIX already dominates the model. Term structure (VIX9D/VIX3M) could be compared against the spread's own 3m/1y tenors directly in a future cut."],
    ["Yahoo Finance ETF flows", "No — substituted SPX returns", "Yahoo does not actually publish creation/redemption flow data (that's a paid feed — ETF.com/Bloomberg/ICI); price data is redundant with FRED's SP500 series, which is more reliable."],
]
t2 = Table(src_data, colWidths=[1.5*inch, 1.1*inch, 4.0*inch])
t2.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1f4e79")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f2f2f2")]),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
story.append(t2)
space(10)

h2("Current Expected Financing Cost")
body(
    "Plugging the latest available feature values (2025-12-31) into the model: <b>model fair value = "
    "94.4bp</b> (3m) vs. <b>actual = 57.5bp</b> &mdash; a 37bp gap. For the 1y tenor: fair value = 79.5bp "
    "vs. actual = 60.5bp (19bp gap). On both tenors, financing is currently priced <b>cheap</b> relative "
    "to what VIX, repo conditions, system liquidity, and recent equity momentum would suggest."
)

doc.build(story)
print("PDF written: Q1_Financing_Spread_Drivers.pdf")
