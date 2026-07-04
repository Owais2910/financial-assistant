import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import anthropic

# Page config
st.set_page_config(page_title="AI Finance Assistant", page_icon="💰", layout="wide")
st.title("💰 AI-Powered Personal Finance Assistant")
st.write("Upload your bank statement and get AI-powered spending insights.")

# Load API key from Streamlit secrets
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
    col3.metric("Savings", f"RM {savings:,.2f}")
    col4.metric("Savings Rate", f"{savings_rate:.1f}%")

    # Biggest expense alert
    if len(category_totals) > 0:
        top_cat = category_totals.index[0]
        top_amt = category_totals.iloc[0]
        st.warning(f"⚠️ Biggest expense: **{top_cat}** — RM {top_amt:,.2f}")

    # Charts side by side
    st.subheader("Spending Breakdown")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig1, ax1 = plt.subplots()
        category_totals.plot(kind="bar", color="skyblue", ax=ax1)
        ax1.set_title("Spending by Category")
        ax1.set_xlabel("Category")
        ax1.set_ylabel("Amount (RM)")
        plt.tight_layout()
        st.pyplot(fig1)

    with chart_col2:
        fig2, ax2 = plt.subplots()
        ax2.pie(category_totals, labels=category_totals.index, autopct="%1.1f%%", startangle=90)
        ax2.set_title("Spending Distribution")
        plt.tight_layout()
        st.pyplot(fig2)

    # Transaction data
    st.subheader("Transaction Data")
    st.dataframe(df)

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

# Footer
st.markdown("---")
st.markdown("Built by **Owais Saad Siddiqui** | [GitHub](https://github.com/Owais2910/financial-assistant) | [Live App](https://owais-finance-assistant.streamlit.app)")
