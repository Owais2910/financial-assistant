import pandas as pd
import matplotlib.pyplot as plt
import anthropic
import os

# Load API key from environment
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
# Load the bank statement
df = pd.read_csv("transactions.csv")

# Separate expenses (negative amounts) from income
expenses = df[df["Amount"] < 0].copy()
expenses["Amount"] = expenses["Amount"].abs()

# Total spend by category
category_totals = expenses.groupby("Category")["Amount"].sum().sort_values(ascending=False)

print("=== Spending by Category ===")
print(category_totals)

# Total spent overall
print(f"\nTotal spent: RM {expenses['Amount'].sum():.2f}")

# Total income
income = df[df["Amount"] > 0]["Amount"].sum()
print(f"Total income: RM {income:.2f}")

# Bar chart of spending by category
category_totals.plot(kind="bar", color="skyblue")
plt.title("Spending by Category")
plt.xlabel("Category")
plt.ylabel("Amount (RM)")
plt.tight_layout()
plt.show()

# Prepare spending summary for AI
summary = "\n".join([f"{cat}: RM {amt:.2f}" for cat, amt in category_totals.items()])
total = expenses["Amount"].sum()
income_total = df[df["Amount"] > 0]["Amount"].sum()

prompt = f"""You are a personal finance assistant. Analyze this spending data and give 3-4 specific, actionable insights. Be friendly and specific with RM amounts.

Monthly Income: RM {income_total/3:.2f}
Monthly Spending: RM {total/3:.2f}

Spending by category (3 months total):
{summary}"""

message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}]
)

print("\n=== AI Financial Insights ===")
print(message.content[0].text)
