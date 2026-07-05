import streamlit as st
import pandas as pd
import plotly.express as px
import anthropic
import base64
import io

# Page config
st.set_page_config(page_title="AI Finance Assistant", page_icon="💰", layout="wide")

# Header
st.title("💰 AI-Powered Personal Finance Assistant")
st.write("Upload your bank statement and get AI-powered spending insights.")

# Sidebar instructions
with st.sidebar:
    st.header("📖 How to Use")
    st.write("1. Select your currency")
    st.write("2. Upload your bank statement as a CSV or PDF file")
    st.write("3. Select a specific month or view all months")
    st.write("4. Explore your spending charts")
    st.write("5. Click **Generate AI Insights** for personalized recommendations")
    st.write("6. Chat with the AI about your spending")
    st.write("7. Download your insights as a text file")
    st.markdown("---")
    st.markdown("Built by **Owais Saad Siddiqui**")
    st.markdown("[GitHub](https://github.com/Owais2910/financial-assistant)")

# Load API key
api_key = st.secrets["ANTHROPIC_API_KEY"]
client = anthropic.Anthropic(api_key=api_key)

# Currency selector
currency = st.selectbox("Select your currency", [
    "RM (Malaysian Ringgit)",
    "USD (US Dollar)",
    "GBP (British Pound)",
    "EUR (Euro)",
    "SGD (Singapore Dollar)",
    "AUD (Australian Dollar)",
    "INR (Indian Rupee)",
    "IDR (Indonesian Rupiah)",
    "PHP (Philippine Peso)",
    "THB (Thai Baht)",
    "Other"
])
currency_symbol = currency.split(" ")[0]

# File upload — CSV or PDF
upload_type = st.radio("Select file type", ["CSV", "PDF"])
uploaded_file = st.file_uploader(
    f"Upload your bank statement ({upload_type})",
    type=["csv"] if upload_type == "CSV" else ["pdf"]
)

df = None

if uploaded_file:
    if upload_type == "CSV":
        df = pd.read_csv(uploaded_file)
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

    elif upload_type == "PDF":
        with st.spinner("Reading your PDF bank statement with AI..."):
            pdf_bytes = uploaded_file.read()
            pdf_base64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

            extraction_message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_base64
                            }
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
1/7/2026,Monthly Salary,Income,3500.00"""
                        }
                    ]
                }]
            )

            csv_text = extraction_message.content[0].text.strip()

            try:
                df = pd.read_csv(io.StringIO(csv_text))
                df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
                st.success(f"✅ Successfully extracted {len(df)} transactions from your PDF!")
                st.subheader("Extracted Transactions")
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error("Could not extract transactions from this PDF. Please make sure it's a bank statement.")
                st.stop()

if df is not None:
    # Month filter
    months = ["All Months"] + sorted(df["Date"].dt.strftime("%B %Y").unique().tolist(), key=lambda x: pd.to_datetime(x, format="%B %Y"))
    selected_month = st.selectbox("Select Month", months)

    if selected_month != "All Months":
        df_filtered = df[df["Date"].dt.strftime("%B %Y") == selected_month].copy()
    else:
        df_filtered = df.copy()

    expenses = df_filtered[df_filtered["Amount"] < 0].copy()
    expenses["Amount"] = expenses["Amount"].abs()
    income_total = df_filtered[df_filtered["Amount"] > 0]["Amount"].sum()
    total_spent = expenses["Amount"].sum()
    savings = income_total - total_spent
    savings_rate = (savings / income_total * 100) if income_total > 0 else 0
    category_totals = expenses.groupby("Category")["Amount"].sum().sort_values(ascending=False)

    # KPI metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Spent", f"{currency_symbol} {total_spent:,.2f}")
    col2.metric("Total Income", f"{currency_symbol} {income_total:,.2f}")
    col3.metric("Savings", f"{currency_symbol} {savings:,.2f}", delta=f"{savings_rate:.1f}% savings rate")
    col4.metric("Top Category", category_totals.index[0] if len(category_totals) > 0 else "N/A")

    # Spending progress bar
    st.markdown("### Spending vs Income")
    spend_pct = min(total_spent / income_total, 1.0) if income_total > 0 else 0
    st.progress(spend_pct)
    if spend_pct >= 1.0:
        st.error(f"⚠️ You have overspent by {currency_symbol} {abs(savings):,.2f} this period!")
    elif spend_pct >= 0.9:
        st.warning(f"⚠️ You've used {spend_pct*100:.1f}% of your income — close to your limit!")
    else:
        st.success(f"✅ You've used {spend_pct*100:.1f}% of your income — you're on track!")

    # Biggest expense alert
    if len(category_totals) > 0:
        top_cat = category_totals.index[0]
        top_amt = category_totals.iloc[0]
        st.warning(f"⚠️ Biggest expense: **{top_cat}** — {currency_symbol} {top_amt:,.2f}")

    # Plotly charts
    st.subheader("Spending Breakdown")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig1 = px.bar(
            x=category_totals.index,
            y=category_totals.values,
            labels={"x": "Category", "y": f"Amount ({currency_symbol})"},
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
    if upload_type == "CSV":
        st.subheader("Transaction Data")
        st.dataframe(df_filtered, use_container_width=True)

    # AI Insights
    if st.button("🤖 Generate AI Insights"):
        with st.spinner("Analyzing your finances..."):
            summary = "\n".join([f"{cat}: {currency_symbol} {amt:.2f}" for cat, amt in category_totals.items()])
            period = selected_month if selected_month != "All Months" else "All Months"

            prompt = f"""You are a personal finance assistant. Analyze this spending data and give 3-4 specific, actionable insights. Be friendly and specific with {currency_symbol} amounts.

Period: {period}
Total Income: {currency_symbol} {income_total:.2f}
Total Spending: {currency_symbol} {total_spent:.2f}
Savings: {currency_symbol} {savings:.2f} ({savings_rate:.1f}% savings rate)

Spending by category:
{summary}"""

            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            st.subheader("🤖 AI Financial Insights")
            st.write(message.content[0].text)

            export_text = f"""AI-Powered Personal Finance Assistant
Period: {period}
Currency: {currency}
Generated by: owais-finance-assistant.streamlit.app

SPENDING SUMMARY
Total Income: {currency_symbol} {income_total:.2f}
Total Spent: {currency_symbol} {total_spent:.2f}
Savings: {currency_symbol} {savings:.2f} ({savings_rate:.1f}% savings rate)

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

    # AI Chatbot
    st.markdown("---")
    st.subheader("💬 Chat With Your Financial Data")
    st.write("Ask anything about your spending — I'll answer based on your uploaded data.")

    summary = "\n".join([f"{cat}: {currency_symbol} {amt:.2f}" for cat, amt in category_totals.items()])
    period = selected_month if selected_month != "All Months" else "All Months"
    transactions_str = df_filtered.to_string(index=False)

    system_prompt = f"""You are a helpful personal finance assistant. The user has uploaded their bank statement.
Here is their financial data for {period}:

SUMMARY:
Total Income: {currency_symbol} {income_total:.2f}
Total Spent: {currency_symbol} {total_spent:.2f}
Savings: {currency_symbol} {savings:.2f} ({savings_rate:.1f}% savings rate)

SPENDING BY CATEGORY:
{summary}

FULL TRANSACTION LIST:
{transactions_str}

Answer the user's questions based on this data. Be specific with amounts in {currency_symbol}. Be friendly and concise."""

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Ask about your spending e.g. 'How much did I spend on food?' or 'Which category is highest?'")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                messages_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history]
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    system=system_prompt,
                    messages=messages_for_api
                )
                reply = response.content[0].text
                st.write(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

# Footer
st.markdown("---")
st.markdown("Built by **Owais Saad Siddiqui** | [GitHub](https://github.com/Owais2910/financial-assistant) | [Live App](https://owais-finance-assistant.streamlit.app)")