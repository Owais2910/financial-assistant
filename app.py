import streamlit as st
import pandas as pd
import plotly.express as px
import anthropic

# Page config
st.set_page_config(page_title="AI Finance Assistant", page_icon="💰", layout="wide")

# Header
st.title("💰 AI-Powered Personal Finance Assistant")
st.write("Upload your bank statement and get AI-powered spending insights.")

# Sidebar instructions
with st.sidebar:
    st.header("📖 How to Use")
    st.write("1. Upload your bank statement as a CSV file")
    st.write("2. Select a specific month or view all months")
    st.write("3. Explore your spending charts")
    st.write("4. Click **Generate AI Insights** for personalized recommendations")
    st.write("5. Download your insights as a text file")
    st.markdown("---")
    st.markdown("Built by **Owais Saad Siddiqui**")
    st.markdown("[GitHub](https://github.com/Owais2910/financial-assistant)")

# Load API key
api_key = st.secrets["ANTHROPIC_API_KEY"]

# File upload
uploaded_file = st.file_uploader("Upload your bank statement (CSV)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

    # Month filter
    months = ["All Months"] + sorted(df["Date"].dt.strftime("%B %Y").unique().tolist())
    selected_month = st.selectbox("Select Month", months)

    if selected_month != "All Months":
        df = df[df["Date"].dt.strftime("%B %Y") == selected_month]

    expenses = df[df["Amount"] < 0].copy()
    expenses["Amount"] = expenses["Amount"].abs()
    income_total = df[df["Amount"] > 0]["Amount"].sum()
    total_spent = expenses["Amount"].sum()
    savings = income_total - total_spent
    savings_rate = (savings / income_total * 100) if income_total > 0 else 0
    category_totals = expenses.groupby("Category")["Amount"].sum().sort_values(ascending=False)

    # KPI metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Spent", f"RM {total_spent:,.2f}")
    col2.metric("Total Income", f"RM {income_total:,.2f}")
    col3.metric("Savings", f"RM {savings:,.2f}", delta=f"{savings_rate:.1f}% savings rate")
    col4.metric("Top Category", category_totals.index[0] if len(category_totals) > 0 else "N/A")

    # Spending progress bar
    st.markdown("### Spending vs Income")
    spend_pct = min(total_spent / income_total, 1.0) if income_total > 0 else 0
    bar_color = "green" if spend_pct < 0.7 else "orange" if spend_pct < 0.9 else "red"
    st.progress(spend_pct)
    if spend_pct >= 1.0:
        st.error(f"⚠️ You have overspent by RM {abs(savings):,.2f} this period!")
    elif spend_pct >= 0.9:
        st.warning(f"⚠️ You've used {spend_pct*100:.1f}% of your income — close to your limit!")
    else:
        st.success(f"✅ You've used {spend_pct*100:.1f}% of your income — you're on track!")

    # Biggest expense alert
    if len(category_totals) > 0:
        top_cat = category_totals.index[0]
        top_amt = category_totals.iloc[0]
        st.warning(f"⚠️ Biggest expense: **{top_cat}** — RM {top_amt:,.2f}")

    # Plotly charts side by side
    st.subheader("Spending Breakdown")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig1 = px.bar(
            x=category_totals.index,
            y=category_totals.values,
            labels={"x": "Category", "y": "Amount (RM)"},
            title="Spending by Category",
            color=category_totals.index,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    with chart_col2:
        fig2 = px.pie(
            values=category_totals.values,
            names=category_totals.index,
            title="Spending Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Transaction data
    st.subheader("Transaction Data")
    st.dataframe(df, use_container_width=True)

    # AI Insights
    if st.button("🤖 Generate AI Insights"):
        with st.spinner("Analyzing your finances..."):
            summary = "\n".join([f"{cat}: RM {amt:.2f}" for cat, amt in category_totals.items()])
            period = selected_month if selected_month != "All Months" else "All Months"

            prompt = f"""You are a personal finance assistant. Analyze this spending data and give 3-4 specific, actionable insights. Be friendly and specific with RM amounts.

Period: {period}
Total Income: RM {income_total:.2f}
Total Spending: RM {total_spent:.2f}
Savings: RM {savings:.2f} ({savings_rate:.1f}% savings rate)

Spending by category:
{summary}"""

            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            st.subheader("🤖 AI Financial Insights")
            st.write(message.content[0].text)

            export_text = f"""AI-Powered Personal Finance Assistant
Period: {period}
Generated by: owais-finance-assistant.streamlit.app

SPENDING SUMMARY
Total Income: RM {income_total:.2f}
Total Spent: RM {total_spent:.2f}
Savings: RM {savings:.2f} ({savings_rate:.1f}% savings rate)

SPENDING BY CATEGORY
{summary}

AI INSIGHTS
{message.content[0].text}
"""
            st.download_button(
                label="📥 Download Insights as Text File",
                data=export_text,
                file_name=f"finance_insights_{period.replace(' ', '_')}.txt",
                mime="text/plain"
            )

# Footer
st.markdown("---")
st.markdown("Built by **Owais Saad Siddiqui** | [GitHub](https://github.com/Owais2910/financial-assistant) | [Live App](https://owais-finance-assistant.streamlit.app)")