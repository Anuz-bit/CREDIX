import os

# Define log path dynamically relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, "intervention_audit_log.txt")

# --- 1. Risk Engine ---
class RiskEngine:
    @staticmethod
    def get_risk_category(customer_data):
        """
        Derives risk category based on PD and behavioral flags.
        """
        pd = customer_data.get('probability_of_default', 0.0)
        
        if pd > 0.7:
            return "High"
        elif pd > 0.3:
            return "Moderate"
        else:
            return "Low"

    @staticmethod
    def get_stability_points(customer_data):
        """
        Calculates gamified stability points for low risk customers.
        """
        pd = customer_data.get('probability_of_default', 1.0)
        tenure = customer_data.get('tenure_months', 12) # Mock if missing
        
        if pd < 0.3:
            # Base 500 + (Low Risk Bonus) + Tenure Bonus
            points = 500 + int((1 - pd) * 1000) + (tenure * 10)
            return points
        return 0

    @staticmethod
    def get_risk_reasons(customer_data):
        """
        Generates dynamic, plain-language reasons for the intervention.
        """
        reasons = []
        
        # Check specific flags
        if customer_data.get('salary_credit_delay_days', 0) > 5:
            reasons.append("Your salary was credited later than usual.")
        
        if customer_data.get('savings_balance_trend_percent', 0) < -10:
            reasons.append("Your savings balance has reduced recently.")
            
        if customer_data.get('utility_payment_delay_days', 0) > 5:
            reasons.append("Utility payments are happening later than normal.")
            
        if customer_data.get('credit_utilization_percent', 0) > 80:
            reasons.append("Your credit card utilization is higher than recommended.")
            
        if customer_data.get('failed_auto_debits_last_3m', 0) > 0:
            reasons.append("We noticed a recent failed auto-debit.")

        # Fallback if no specific reasons found but risk is high
        if not reasons and customer_data.get('probability_of_default', 0) > 0.5:
             reasons.append("We noticed some unusual patterns in your recent transactions.")

        return reasons[:3] # Return top 3

# --- 2. Plan Engine ---
class PlanEngine:
    @staticmethod
    def get_plans(risk_category, current_emi=15000, current_tenure=24, income=50000, expenses=30000):
        """
        Returns personalized plans based on Risk Category with RICH SIMULATED DATA.
        """
        plans = []
        
        # Base calculations for simulation
        original_total_repayment = current_emi * current_tenure
        
        if risk_category in ["Moderate", "High"]:
            # Plan 1: EMI Restructuring (Extend Tenure, Lower EMI)
            new_tenure_1 = current_tenure + 12
            new_emi_1 = int(original_total_repayment / new_tenure_1 * 1.1) # 10% interest bump for ease
            relief_1 = current_emi - new_emi_1
            
            plans.append({
                "id": "emi_restructure",
                "title": "EMI Restructuring Plan",
                "tagline": "Reduce monthly payments by extending tenure.",
                "type": "Relief",
                "impact_amount": f"₹{relief_1:,}",
                "description": "Convert your outstanding balance into smaller, more manageable EMIs by extending your loan tenure.",
                "reason": "Recommended because your recent account activity shows higher monthly expenses.",
                "best_for": "Long-term affordability",
                
                # Simulation Data for Charts
                "simulation": {
                    "current_emi": current_emi,
                    "new_emi": new_emi_1,
                    "current_tenure": current_tenure,
                    "new_tenure": new_tenure_1,
                    "monthly_relief": relief_1,
                    "total_payment_change": (new_emi_1 * new_tenure_1) - original_total_repayment,
                    
                    # Cashflow Data (Income vs Expenses vs EMI)
                    "cashflow": {
                        "income": income,
                        "expenses": expenses,
                        "current_balance": income - expenses - current_emi,
                        "new_balance": income - expenses - new_emi_1
                    }
                },
                
                "eligibility": [
                    "Account must be standard (no current default).",
                    "Minimum outstanding balance of ₹50,000.",
                    "No previous restructuring in last 12 months."
                ],
                "conditions": [
                    "Interest rate will increase by 0.5% for the extended period.",
                    "Processing fee of ₹500 waived for this offer."
                ]
            })

            # Plan 2: Payment Holiday (Skip 1 Month)
            plans.append({
                "id": "payment_holiday",
                "title": "Payment Holiday",
                "tagline": "Skip this month's EMI with zero penalty.",
                "type": "Holiday",
                "impact_amount": f"₹{current_emi:,}",
                "description": "Take a break from your loan payment this month to manage unexpected expenses. Zero late fees.",
                "reason": "Recommended for short-term cash flow mismatches.",
                "best_for": "Immediate cash relief",
                
                 "simulation": {
                    "current_emi": current_emi,
                    "new_emi": 0, # For this month
                    "current_tenure": current_tenure,
                    "new_tenure": current_tenure + 1,
                    "monthly_relief": current_emi,
                    "total_payment_change": int(current_emi * 0.02), # Small interest accrual
                    
                    "cashflow": {
                        "income": income,
                        "expenses": expenses,
                        "current_balance": income - expenses - current_emi,
                        "new_balance": income - expenses # Full relief this month
                    }
                },
                
                "eligibility": [
                    "Consistent repayment history for last 6 months.",
                    "Not applicable for final EMI."
                ],
                "conditions": [
                    "Interest for the skipped month will be added to the end of tenure.",
                    "Next EMI date remains unchanged."
                ]
            })

        if risk_category == "High":
             # Plan 3: Hardship (Custom)
             plans.append({
                "id": "hardship_assistance",
                "title": "Hardship Assistance Program",
                "tagline": "Customized support for difficult times.",
                "type": "Assistance",
                "impact_amount": "Variable",
                "description": "Work directly with a relationship manager to restructure your debt based on your current income.",
                "reason": "Recommended due to significant changes in income or financial status.",
                "best_for": "Complex financial situations",
                
                "simulation": {
                    "current_emi": current_emi,
                    "new_emi": int(current_emi * 0.5), # Assume 50% relief
                    "current_tenure": current_tenure,
                    "new_tenure": current_tenure + 24, # lengthy extension
                    "monthly_relief": int(current_emi * 0.5),
                    "total_payment_change": 0, # Custom
                    
                    "cashflow": {
                        "income": income,
                        "expenses": expenses,
                        "current_balance": income - expenses - current_emi,
                        "new_balance": income - expenses - int(current_emi * 0.5)
                    }
                },
                "eligibility": ["Proof of income reduction required."],
                "conditions": ["Requires document verification."]
            })
            
        elif risk_category == "Low":
             # STABILITY REWARDS PLANS
             # 1. Reduced Interest Rate
             plans.append({
                "id": "reward_rate_cut",
                "title": "Rate Reduction Benefit",
                "tagline": "Unlock 0.5% lower interest on future loans.",
                "type": "Stability Reward",
                "impact_amount": "-0.5% Interest",
                "description": "As a Stability Rewards member, you qualify for a preferential interest rate on your next personal loan or top-up.",
                "reason": "Earned via consistent on-time payments and high Stability Score.",
                "best_for": "Future borrowing",
                "simulation": None,
                "eligibility": ["Stability Points > 1000", "No late payments in 12 months."],
                "conditions": ["Valid for 90 days."]
            })

             # 2. Credit Limit Increase
             plans.append({
                "id": "reward_limit_increase",
                "title": "Pre-approved Limit Increase",
                "tagline": "Instantly increase your credit limit by 20%.",
                "type": "Stability Reward",
                "impact_amount": "+20% Limit",
                "description": "Get more financial flexibility with a pre-approved credit limit enhancement. No documentation required.",
                "reason": "Reward for maintaining low credit utilization.",
                "best_for": "Financial flexibility",
                "simulation": None,
                "eligibility": ["Stability Points > 1200"],
                "conditions": ["Subject to final CIBIL check."]
            })

             # 3. Priority Support
             plans.append({
                "id": "reward_priority_support",
                "title": "Priority Customer Support",
                "tagline": "Skip the queue with dedicated access.",
                "type": "Stability Reward",
                "impact_amount": "VIP Access",
                "description": "Direct access to our senior relationship managers for any queries or faster loan processing.",
                "reason": "Exclusive benefit for our most reliable customers.",
                "best_for": "Convenience",
                "simulation": None,
                "eligibility": ["Stability Points > 800"],
                "conditions": ["Available 24/7."]
            })

        return plans

# --- 3. Communication Engine ---
class CommunicationEngine:
    @staticmethod
    def generate_message(customer_name, risk_category):
        """
        Generates the proactive alert message.
        """
        # Bank-style, supportive, no jargon.
        if risk_category == "High":
            return f"Hi {customer_name}, we noticed some recent changes in your account activity and would like to help you stay financially comfortable. Please review your personalized options here: [Link]"
        elif risk_category == "Moderate":
             return f"Hi {customer_name}, to help you manage your upcoming payments more easily, we've prepared some flexible options for you. Check them out: [Link]"
        else:
             return f"Hi {customer_name}, thank you for banking with us! We have some new rewards and tips to help you grow your financial health. View here: [Link]"

    @staticmethod
    def generate_secure_token(customer_id):
        # Mock token generation
        return str(customer_id)

    @staticmethod
    def get_customer_by_token(token):
        """
        Retrieves customer data from enriched dataset using the token (customer_id).
        """
        try:
            from utils.data_loader import load_data
            df = load_data()
            
            # Token is assumed to be customer_id
            customer_row = df[df['customer_id'] == token]
            
            if not customer_row.empty:
                return customer_row.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"Error fetching customer by token: {e}")
            return None

# --- 4. Outcome Logger ---
class OutcomeLogger:
    @staticmethod
    def log_outcome(customer_id, plan_id, status, reason=None):
        """
        Logs the customer's decision.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "customer_id": customer_id,
            "plan_id": plan_id,
            "status": status,
            "reason": reason
        }
        # Append to log file
        try:
            with open(LOG_FILE, "a") as f:
                f.write(f"{timestamp} - INTERVENTION_LOG: Customer={customer_id}, Plan={plan_id}, Status={status}\n")
        except Exception as e:
            print(f"Failed to write log to {LOG_FILE}: {e}")
            
        print(f"Outcome Logged: {log_entry}")
        return True