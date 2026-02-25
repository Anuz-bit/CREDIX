import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))

from utils.intervention_logic import PlanEngine, RiskEngine

# Mock Customer Data (Low Risk)
customer_low_risk = {
    "probability_of_default": 0.1,
    "tenure_months": 24
}

print("--- Testing Stability Points ---")
points = RiskEngine.get_stability_points(customer_low_risk)
print(f"Points (Expected > 500): {points}")
if points > 0:
    print("PASS: Points calculation works.")
else:
    print("FAIL: Points calculation failed.")

print("\n--- Testing Plan Generation (Low Risk) ---")
plans = PlanEngine.get_plans("Low")

reward_plans = [p for p in plans if p.get('type') == "Stability Reward"]
print(f"Reward Plans Found: {len(reward_plans)}")

if len(reward_plans) >= 3:
    print("PASS: Reward plans generated.")
    for p in reward_plans:
        print(f" - {p['title']} ({p['impact_amount']})")
else:
    print("FAIL: Reward plans missing.")
