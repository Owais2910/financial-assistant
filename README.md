# 💰 AI-Powered Personal Finance Assistant

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Deployed-red?logo=streamlit)
![Claude AI](https://img.shields.io/badge/Claude_AI-Anthropic-orange)
![GitHub](https://img.shields.io/badge/Status-Active-brightgreen)

A deployed web application that analyzes bank statements and generates AI-powered spending insights using Claude AI (Anthropic).

🔗 **Live App:** [owais-finance-assistant.streamlit.app](https://owais-finance-assistant.streamlit.app)

---

## 🚀 Features

- 📂 **CSV Upload** — Upload any bank statement in CSV format
- 📅 **Monthly Filter** — Analyze spending by specific month or all months
- 📊 **Interactive Charts** — Bar and pie charts powered by Plotly
- 💡 **AI Insights** — Personalized financial recommendations via Claude AI
- 📈 **KPI Dashboard** — Total spent, income, savings, and savings rate
- ⚠️ **Spending Alerts** — Highlights biggest expenses and overspending
- 📥 **Export Report** — Download AI insights as a text file

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core programming language |
| Pandas | Data processing and analysis |
| Plotly | Interactive data visualizations |
| Claude AI (Anthropic) | AI-powered financial insights |
| Streamlit | Web interface and deployment |
| Git & GitHub | Version control |

---

## 📁 CSV Format

Your bank statement should have these columns:

| Date | Description | Category | Amount |
|------|-------------|----------|--------|
| 1/7/2026 | Grab Food | Food | -25.00 |
| 1/7/2026 | Monthly Salary | Income | 4500.00 |

- Expenses should be **negative** amounts
- Income should be **positive** amounts

---

## ⚙️ How to Run Locally

```bash
# Clone the repository
git clone https://github.com/Owais2910/financial-assistant.git
cd financial-assistant

# Install dependencies
pip install pandas plotly anthropic streamlit

# Add your API key to .streamlit/secrets.toml
# ANTHROPIC_API_KEY = "your-key-here"

# Run the app
streamlit run app.py
```

---

## 👤 Built By

**Owais Saad Siddiqui**
Business Management (Business Analytics) | Asia Pacific University

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://linkedin.com/in/owais-saad-siddiqui)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black?logo=github)](https://github.com/Owais2910)