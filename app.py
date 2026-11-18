import io
import base64

import anthropic
import pandas as pd
import plotly.express as px
import streamlit as st

# ── Page config (must be the first Streamlit call) ─────────────────────────
st.set_page_config(page_title="SAYA · AI Finance Assistant", page_icon="💰", layout="wide")

MODEL = "claude-haiku-4-5-20251001"
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

CURRENCIES = [
    "RM (Malaysian Ringgit)",
    "USD (US Dollar)",
    "GBP (British Pound)",
    "EUR (Euro)",
    "SGD (Singapore Dollar)",
    "AUD (Australian Dollar)",
    "INR (Indian Rupee)",
    "SAR (Saudi Riyal)",
    "AED (UAE Dirham - Dubai)",
    "IDR (Indonesian Rupiah)",
    "PHP (Philippine Peso)",
    "THB (Thai Baht)",
    "Other",
]

SAMPLE_CSV = """Date,Description,Category,Amount
1/7/2026,Monthly Salary,Income,3500.00
1/7/2026,Rent,Bills,-900.00
2/7/2026,TNB Electricity,Bills,-118.40
2/7/2026,Grab Food,Food,-24.50
3/7/2026,99 Speedmart,Groceries,-67.30
3/7/2026,Touch n Go Reload,Transport,-50.00
4/7/2026,Tealive,Food,-14.90
5/7/2026,Shopee,Shopping,-129.00
6/7/2026,Netflix,Entertainment,-55.00
7/7/2026,Mamak Corner,Food,-18.60
8/7/2026,Shell Petrol,Transport,-80.00
9/7/2026,Watsons,Health,-42.80
10/7/2026,Grab Ride,Transport,-23.40
11/7/2026,Giant,Groceries,-154.20
12/7/2026,McDonald's,Food,-27.90
13/7/2026,TGV Cinema,Entertainment,-38.00
14/7/2026,Unifi Internet,Bills,-129.00
15/7/2026,Padini,Shopping,-189.90
16/7/2026,Grab Food,Food,-31.20
18/7/2026,Udemy Course,Education,-49.90
20/7/2026,AEON,Groceries,-98.60
22/7/2026,Clinic Visit,Health,-65.00
25/7/2026,Spotify,Entertainment,-16.90
28/7/2026,Old Town Coffee,Food,-22.40
1/8/2026,Monthly Salary,Income,3500.00
1/8/2026,Rent,Bills,-900.00
3/8/2026,Grab Food,Food,-28.70
5/8/2026,Tesco,Groceries,-132.10
9/8/2026,Mr DIY,Shopping,-76.50
12/8/2026,Shell Petrol,Transport,-75.00
"""

# ── Styling ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
.block-container {padding-top: 2rem; max-width: 1200px;}
.hero {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 55%, #db2777 100%);
    padding: 2rem 2.2rem; border-radius: 20px; color: white; margin-bottom: 1.4rem;
}
.hero h1 {margin: 0; font-size: 2.1rem; color: white; line-height: 1.2;}
.hero p {margin: .5rem 0 0; opacity: .93; font-size: 1.05rem;}
div[data-testid="stMetric"] {
    background: rgba(128,128,128,0.10);
    border: 1px solid rgba(128,128,128,0.25);
    padding: 14px 18px; border-radius: 14px;
}
button[data-baseweb="tab"] {font-size: 1.05rem; font-weight: 600; padding: 10px 18px;}
.side-title {font-size: 1.5rem; font-weight: 800; margin-bottom: 0;}
.side-sub {opacity: .7; margin-top: 0;}
</style>
""",
    unsafe_allow_html=True,
)


# ── Helpers ────────────────────────────────────────────────────────────────
class StatementError(Exception):
    """Raised for problems we can explain to the user."""


def ask_claude(system, messages, max_tokens=1024):
    response = client.messages.create(
        model=MODEL, max_tokens=max_tokens, system=system, messages=messages
    )
    return response.content[0].text


def clean_dataframe(raw):
    df = raw.copy()
    df.columns = [str(c).strip().title() for c in df.columns]
    required = ["Date", "Description", "Category", "Amount"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise StatementError(
            f"Missing column(s): {', '.join(missing)}. Your file needs: Date, Description, Category, Amount."
        )
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df["Amount"] = pd.to_numeric(
        df["Amount"].astype(str).str.replace(",", "", regex=False), errors="coerce"
    )
    df = df.dropna(subset=["Date", "Amount"])
    df["Category"] = df["Category"].fillna("Other").astype(str)
    if df.empty:
        raise StatementError("No valid transactions found in this file.")
    df["MonthLabel"] = df["Date"].dt.strftime("%B %Y")
    return df.sort_values("Date").reset_index(drop=True)


def extract_pdf(pdf_bytes):
    pdf_base64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")
    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": """Extract all transactions from this bank statement and return them as a CSV with exactly these columns: Date,Description,Category,Amount

Rules:
- Date format: D/M/YYYY (e.g. 1/7/2026)
- Amount: negative for expenses, positive for income
- Category: pick the most fitting from: Food, Transport, Bills, Shopping, Entertainment, Groceries, Health, Education, Income, Other
- Return ONLY the CSV data, no explanation, no markdown, no backticks

Example output:
Date,Description,Category,Amount
1/7/2026,Grab Food,Food,-25.00
1/7/2026,Monthly Salary,Income,3500.00""",
                    },
                ],
            }
        ],
    )
    csv_text = response.content[0].text.strip()
    csv_text = "\n".join(l for l in csv_text.splitlines() if not l.strip().startswith("```"))
    try:
        return pd.read_csv(io.StringIO(csv_text))
    except Exception:
        raise StatementError("Couldn't extract transactions from this PDF. Is it a text-based bank statement?")


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="side-title">💰 SAYA</p>', unsafe_allow_html=True)
    st.markdown('<p class="side-sub">Your personal AI finance companion</p>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("#### ✨ What you get")
    st.markdown(
        "- 📊 Interactive spending charts\n"
        "- 💡 Instant AI insights\n"
        "- 🧾 Category breakdown\n"
        "- 💬 SAYA, your AI chatbot\n"
        "- 📥 Downloadable reports"
    )

    with st.expander("📄 File format"):
        st.write("Upload a **CSV** with these columns, or a text-based **PDF** bank statement.")
        st.code("Date,Description,Category,Amount\n1/7/2026,Grab Food,Food,-25.00\n1/7/2026,Salary,Income,3500", language="text")
        st.caption("Expenses are negative, income is positive.")
        st.download_button("Download sample CSV", SAMPLE_CSV, file_name="sample_transactions.csv", mime="text/csv")

    st.markdown("---")
    st.caption(
        "🔒 Files are used only during your session and aren't saved by this app. "
        "AI features send your data to Anthropic's API to generate results."
    )
    st.markdown("Built by **Owais Saad Siddiqui**")
    st.markdown("[GitHub](https://github.com/Owais2910/financial-assistant)")

# ── Hero ───────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero">
  <h1>💰 AI-Powered Personal Finance Assistant</h1>
  <p>Upload a bank statement to get instant charts, AI insights and a personal finance chatbot, SAYA.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Currency + upload ──────────────────────────────────────────────────────
top_left, top_right = st.columns([1, 2])

with top_left:
    currency = st.selectbox("💱 Currency", CURRENCIES)
    if currency == "Other":
        sym = st.text_input("Currency code or symbol", value="$", max_chars=5).strip() or "$"
    else:
        sym = currency.split(" ")[0]

with top_right:
    uploaded_file = st.file_uploader("📂 Upload your bank statement (CSV or PDF)", type=["csv", "pdf"])
    if uploaded_file is None and not st.session_state.get("use_sample"):
        if st.button("✨ Try with sample data"):
            st.session_state["use_sample"] = True
            st.rerun()
    elif uploaded_file is None and st.session_state.get("use_sample"):
        st.caption("Using sample data.")
        if st.button("Clear sample data"):
            st.session_state["use_sample"] = False
            st.rerun()

# ── Load data (cached per file so we don't re-run the AI on every rerun) ──
df, file_key, load_error = None, None, None

if uploaded_file is not None:
    st.session_state["use_sample"] = False
    file_key = f"{uploaded_file.name}-{uploaded_file.size}"
elif st.session_state.get("use_sample"):
    file_key = "sample-data"

if file_key:
    if st.session_state.get("loaded_key") == file_key:
        df = st.session_state["df"]
    elif st.session_state.get("failed_key") == file_key:
        load_error = st.session_state.get("load_error")
    else:
        try:
            with st.spinner("Reading your statement..."):
                if uploaded_file is None:
                    raw = pd.read_csv(io.StringIO(SAMPLE_CSV))
                elif uploaded_file.name.lower().endswith(".pdf"):
                    raw = extract_pdf(uploaded_file.getvalue())
                else:
                    raw = pd.read_csv(uploaded_file)
                df = clean_dataframe(raw)
            st.session_state["df"] = df
            st.session_state["loaded_key"] = file_key
        except Exception as e:
            load_error = (
                str(e)
                if isinstance(e, StatementError)
                else "Couldn't read this file. Please check it's a valid CSV or a text-based PDF statement."
            )
            st.session_state["failed_key"] = file_key
            st.session_state["load_error"] = load_error
else:
    for k in ("df", "loaded_key", "failed_key", "load_error"):
        st.session_state.pop(k, None)

if load_error:
    st.error(load_error)

# ── Empty state ────────────────────────────────────────────────────────────
if df is None and not load_error:
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("### 1️⃣ Upload")
            st.write("Drop in a CSV or PDF bank statement, or try the sample data.")
    with c2:
        with st.container(border=True):
            st.markdown("### 2️⃣ Get insights")
            st.write("Charts, a breakdown and AI-written insights appear instantly.")
    with c3:
        with st.container(border=True):
            st.markdown("### 3️⃣ Ask SAYA")
            st.write("Chat with SAYA about your spending. She's available any time.")

# ── Data processing ────────────────────────────────────────────────────────
selected_month = "All Months"

if df is not None:
    months = ["All Months"] + list(dict.fromkeys(df["MonthLabel"]))
    f1, f2 = st.columns([1, 2])
    with f1:
        selected_month = st.selectbox("📅 Period", months)
    with f2:
        st.caption(f"{len(df):,} transactions loaded")

    df_f = df if selected_month == "All Months" else df[df["MonthLabel"] == selected_month]
    expenses = df_f[df_f["Amount"] < 0].copy()
    expenses["Amount"] = expenses["Amount"].abs()
    income_total = df_f.loc[df_f["Amount"] > 0, "Amount"].sum()
    total_spent = expenses["Amount"].sum()
    savings = income_total - total_spent
    savings_rate = (savings / income_total * 100) if income_total > 0 else 0
    category_totals = expenses.groupby("Category")["Amount"].sum().sort_values(ascending=False)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Spent", f"{sym} {total_spent:,.2f}")
    k2.metric("Total Income", f"{sym} {income_total:,.2f}")
    k3.metric("Savings", f"{sym} {savings:,.2f}", delta=f"{savings_rate:.1f}% savings rate")
    k4.metric("Top Category", category_totals.index[0] if len(category_totals) > 0 else "N/A")

# ── Tabs ───────────────────────────────────────────────────────────────────
tab_charts, tab_insights, tab_breakdown, tab_saya = st.tabs(
    ["📊 Charts", "💡 Insights", "🧾 Breakdown", "💬 Chat with SAYA"]
)

PLACEHOLDER = "Upload a bank statement (or try the sample data) to unlock this tab."
palette = px.colors.qualitative.Bold

# --- Charts
with tab_charts:
    if df is None:
        st.info(PLACEHOLDER)
    elif expenses.empty:
        st.info("No expenses found for this period.")
    else:
        spend_pct = min(total_spent / income_total, 1.0) if income_total > 0 else 1.0
        st.markdown("##### Spending vs income")
        st.progress(spend_pct)
        if income_total > 0 and total_spent > income_total:
            st.error(f"⚠️ You overspent by {sym} {abs(savings):,.2f} this period.")
        elif spend_pct >= 0.9:
            st.warning(f"⚠️ You've used {spend_pct * 100:.1f}% of your income, close to your limit.")
        else:
            st.success(f"✅ You've used {spend_pct * 100:.1f}% of your income. You're on track.")

        cat_df = category_totals.reset_index()
        cat_df.columns = ["Category", "Amount"]

        c1, c2 = st.columns(2)
        with c1:
            fig_bar = px.bar(
                cat_df, x="Category", y="Amount", color="Category",
                title="Spending by category",
                labels={"Amount": f"Amount ({sym})"},
                color_discrete_sequence=palette,
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar)
        with c2:
            fig_pie = px.pie(
                cat_df, values="Amount", names="Category", hole=0.45,
                title="Spending distribution", color_discrete_sequence=palette,
            )
            st.plotly_chart(fig_pie)

        daily = expenses.groupby(expenses["Date"].dt.normalize())["Amount"].sum().reset_index()
        fig_daily = px.area(
            daily, x="Date", y="Amount", title="Daily spending",
            labels={"Amount": f"Amount ({sym})"}, color_discrete_sequence=[palette[0]],
        )
        st.plotly_chart(fig_daily)

# --- Insights (generated automatically, cached per file / period / currency)
with tab_insights:
    if df is None:
        st.info(PLACEHOLDER)
    elif expenses.empty:
        st.info("No expenses found for this period, so there's nothing to analyse yet.")
    else:
        summary = "\n".join(f"{cat}: {sym} {amt:,.2f}" for cat, amt in category_totals.items())
        top_lines = "\n".join(
            f"- {r.Date:%d %b}: {r.Description} ({sym} {r.Amount:,.2f})"
            for r in expenses.nlargest(5, "Amount").itertuples()
        )
        insight_key = f"{file_key}|{selected_month}|{sym}"
        cache = st.session_state.setdefault("insights", {})
        insights_text = cache.get(insight_key)

        if insights_text is None:
            st.toast("SAYA is analysing your finances...", icon="🤖")
            with st.spinner("SAYA is analysing your finances..."):
                prompt = f"""Analyse this spending data for {selected_month}.

Total income: {sym} {income_total:,.2f}
Total spending: {sym} {total_spent:,.2f}
Savings: {sym} {savings:,.2f} ({savings_rate:.1f}% savings rate)

Spending by category:
{summary}

Five biggest expenses:
{top_lines}

Respond in markdown with:
1. A one-line headline verdict.
2. 3-4 specific insights, each starting with an emoji and a bold title, quoting amounts in {sym}.
3. One "Quick win" the user can do this month to save money.
Be friendly, specific and keep it under 250 words."""
                try:
                    insights_text = ask_claude(
                        "You are SAYA, a friendly and practical personal finance assistant.",
                        [{"role": "user", "content": prompt}],
                    )
                    cache[insight_key] = insights_text
                except Exception:
                    st.error("SAYA couldn't generate insights right now. Please try again in a moment.")

        if insights_text:
            st.markdown("### 🤖 SAYA's insights")
            st.markdown(insights_text)

            export_text = f"""AI-Powered Personal Finance Assistant
Period: {selected_month}
Currency: {currency}
Generated by: owais-finance-assistant.streamlit.app

SPENDING SUMMARY
Total Income: {sym} {income_total:,.2f}
Total Spent: {sym} {total_spent:,.2f}
Savings: {sym} {savings:,.2f} ({savings_rate:.1f}% savings rate)

SPENDING BY CATEGORY
{summary}

SAYA'S INSIGHTS
{insights_text}
"""
            d1, d2 = st.columns([1, 1])
            with d1:
                st.download_button(
                    "📥 Download insights",
                    export_text,
                    file_name=f"finance_insights_{selected_month.replace(' ', '_')}.txt",
                    mime="text/plain",
                )
            with d2:
                if st.button("🔄 Regenerate insights"):
                    cache.pop(insight_key, None)
                    st.rerun()

# --- Breakdown
with tab_breakdown:
    if df is None:
        st.info(PLACEHOLDER)
    elif expenses.empty:
        st.info("No expenses found for this period.")
    else:
        st.markdown("#### Spending by category")
        breakdown = (
            expenses.groupby("Category")
            .agg(Total=("Amount", "sum"), Transactions=("Amount", "count"), Average=("Amount", "mean"))
            .sort_values("Total", ascending=False)
            .reset_index()
        )
        breakdown["Share"] = breakdown["Total"] / breakdown["Total"].sum() * 100
        st.dataframe(
            breakdown,
            hide_index=True,
            column_config={
                "Total": st.column_config.NumberColumn(f"Total ({sym})", format="%.2f"),
                "Average": st.column_config.NumberColumn(f"Avg per transaction ({sym})", format="%.2f"),
                "Share": st.column_config.ProgressColumn(
                    "Share of spending", format="%.1f%%", min_value=0, max_value=100
                ),
            },
        )

        st.markdown("#### 🔝 Top 5 expenses")
        top5 = expenses.nlargest(5, "Amount")[["Date", "Description", "Category", "Amount"]].copy()
        top5["Date"] = top5["Date"].dt.strftime("%d %b %Y")
        st.dataframe(
            top5,
            hide_index=True,
            column_config={"Amount": st.column_config.NumberColumn(f"Amount ({sym})", format="%.2f")},
        )

        with st.expander("📋 All transactions"):
            all_tx = df_f[["Date", "Description", "Category", "Amount"]].copy()
            all_tx["Date"] = all_tx["Date"].dt.strftime("%d %b %Y")
            st.dataframe(
                all_tx,
                hide_index=True,
                column_config={"Amount": st.column_config.NumberColumn(f"Amount ({sym})", format="%.2f")},
            )

# --- SAYA chatbot (always available, with or without data)
with tab_saya:
    st.markdown("### 💬 Hi, I'm SAYA")
    if df is not None:
        st.caption(f"I can see your {selected_month} data. Ask me anything about it.")
    else:
        st.caption("Ask me any money question, or upload a statement for personalised answers.")

    if df is not None:
        ctx = df_f[["Date", "Description", "Category", "Amount"]].copy()
        ctx["Date"] = ctx["Date"].dt.strftime("%Y-%m-%d")
        ctx_csv = ctx.head(400).to_csv(index=False)
        truncated_note = "\n(Only the first 400 transactions are shown.)" if len(ctx) > 400 else ""
        cat_summary = "\n".join(f"{cat}: {sym} {amt:,.2f}" for cat, amt in category_totals.items())
        system_prompt = f"""You are SAYA, a friendly and practical personal finance assistant. The user has uploaded their bank statement.
Period: {selected_month}. Currency: {sym}.

SUMMARY:
Total income: {sym} {income_total:,.2f}
Total spent: {sym} {total_spent:,.2f}
Savings: {sym} {savings:,.2f} ({savings_rate:.1f}% savings rate)

SPENDING BY CATEGORY:
{cat_summary}

TRANSACTIONS (CSV):
{ctx_csv}{truncated_note}

Answer based on this data. Be specific with amounts in {sym}. Be friendly and concise."""
        suggestions = ["Where am I overspending?", "How can I save more?", "What was my biggest expense?"]
    else:
        system_prompt = f"""You are SAYA, a friendly and practical personal finance assistant.
The user hasn't uploaded a bank statement yet, so answer general personal finance questions (budgeting, saving, debt, investing basics).
Mention that uploading a statement lets you give personalised answers. Currency preference: {sym}. Be concise."""
        suggestions = ["How do I build a budget?", "What is the 50/30/20 rule?", "How big should my emergency fund be?"]

    history = st.session_state.setdefault("chat_history", [])

    quick = None
    q_cols = st.columns(3)
    for col, q in zip(q_cols, suggestions):
        if col.button(q, key=f"quick_{q}"):
            quick = q

    if not history:
        with st.chat_message("assistant", avatar="✨"):
            st.write("Hi! I'm SAYA, your AI finance companion. What would you like to know?")

    for msg in history:
        with st.chat_message(msg["role"], avatar="✨" if msg["role"] == "assistant" else None):
            st.write(msg["content"])

    user_text = st.chat_input("Ask SAYA anything about your money...") or quick

    if user_text:
        history.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.write(user_text)

        with st.chat_message("assistant", avatar="✨"):
            with st.spinner("SAYA is thinking..."):
                try:
                    # last 19 messages keeps the list starting with a user turn
                    reply = ask_claude(system_prompt, history[-19:])
                except Exception:
                    reply = "Sorry, I couldn't respond just now. Please try again in a moment."
            st.write(reply)
        history.append({"role": "assistant", "content": reply})

    if history and st.button("🗑️ Clear chat"):
        st.session_state["chat_history"] = []
        st.rerun()

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "Built by **Owais Saad Siddiqui** | [GitHub](https://github.com/Owais2910/financial-assistant) | "
    "[Live App](https://owais-finance-assistant.streamlit.app)"
)