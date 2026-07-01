import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import anthropic

# Page config
st.set_page_config(page_title="AI Finance Assistant", page_icon="💰", layout="wide")
st.title("💰 AI-Powered Personal Finance Assistant")
st.write("Upload your bank statement and get AI-powered spending insights.")

# API key input
api_key = st.sidebar.text_input("Enter your Anthropic API Key", type="password")

# File upload
uploaded_file = st.file_uploader("Upload your bank statement (CSV)", type=["csv"])

if uploaded_file and api_key:
    df = pd.read_csv(uploaded_file)
    expenses = df[df["Amount"] < 0].copy()
    expenses["Amount"] = expenses["Amount"].abs()
    category_totals = expenses.groupby("Category")["Amount"].sum().sort_values(ascending=False)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Spent", f"RM {expenses['Amount'].sum():,.2f}")
    col2.metric("Total Income", f"RM {df[df['Amount'] > 0]['Amount'].sum():,.2f}")
    col3.metric("Top Category", category_totals.index[0])

    st.subheader("Spending by Category")
    fig, ax = plt.subplots()
    category_totals.plot(kind="bar", color="skyblue", ax=ax)
    ax.set_xlabel("Category")
    ax.set_ylabel("Amount (RM)")
    plt.tight_layout()
    st.pyplot(fig)

    st.subheader("Transaction Data")
    st.dataframe(df)

    if st.button("Generate AI Insights"):
        with st.spinner("Analyzing your finances..."):
            summary = "\n".join([f"{cat}: RM {amt:.2f}" for cat, amt in category_totals.items()])
            total = expenses["Amount"].sum()
            income_total = df[df["Amount"] > 0]["Amount"].sum()

            prompt = f"""You are a personal finance assistant. Analyze this spending data and give 3-4 specific, actionable insights. Be friendly and specific with RM amounts.

Monthly Income: RM {income_total/3:.2f}
Monthly Spending: RM {total/3:.2f}

Spending by category (3 months total):
{summary}"""

            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            st.subheader("🤖 AI Financial Insights")
            st.write(message.content[0].text)
else:
    st.info("Please enter your API key in the sidebar and upload a CSV file to get started.")