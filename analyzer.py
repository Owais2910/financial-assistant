import pandas as pd

# Load the bank statement
df = pd.read_csv("transactions.csv")

# Separate expenses (negative amounts) from income
expenses = df[df["Amount"] < 0].copy()
expenses["Amount"] = expenses["Amount"].abs()  # make positive for easier reading

# Total spend by category
category_totals = expenses.groupby("Category")["Amount"].sum().sort_values(ascending=False)

print("=== Spending by Category ===")
print(category_totals)

# Total spent overall
print(f"\nTotal spent: RM {expenses['Amount'].sum():.2f}")

# Total income
income = df[df["Amount"] > 0]["Amount"].sum()
print(f"Total income: RM {income:.2f}")
import matplotlib.pyplot as plt

# Bar chart of spending by category
category_totals.plot(kind="bar", color="skyblue")
plt.title("Spending by Category")
plt.xlabel("Category")
plt.ylabel("Amount (RM)")
plt.tight_layout()
plt.show()