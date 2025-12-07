from typing import List
from app.schemas.risk import CustomerFeatures, RuleTrigger

def evaluate_rules(customer: CustomerFeatures) -> List[RuleTrigger]:
    rules: List[RuleTrigger] = []

    if customer.utilisation_pct > 80:
        rules.append(
            RuleTrigger(
                rule_name="High utilisation",
                reason=f"Utilisation {customer.utilisation_pct:.1f}% > 80%",
                suggested_outreach="Send payment reminder and partial payment plan suggestion.",
            )
        )

    if customer.recent_spend_change_pct < -30:
        rules.append(
            RuleTrigger(
                rule_name="Spend drop",
                reason=f"Recent spend change {customer.recent_spend_change_pct:.1f}% < -30%",
                suggested_outreach="Reach out via call to confirm financial stress.",
            )
        )

    if customer.cash_withdrawal_pct > 40:
        rules.append(
            RuleTrigger(
                rule_name="High cash withdrawal",
                reason=f"Cash withdrawal {customer.cash_withdrawal_pct:.1f}% > 40%",
                suggested_outreach="Offer EMI restructuring and educate on revolving interest.",
            )
        )

    if customer.avg_payment_ratio < 40:
        rules.append(
            RuleTrigger(
                rule_name="Low average payment",
                reason=f"Average payment ratio {customer.avg_payment_ratio:.1f}% < 40%",
                suggested_outreach="Send payment reminder and partial payment plan suggestion.",
            )
        )

    if customer.min_due_paid_freq > 70:
        rules.append(
            RuleTrigger(
                rule_name="High minimum due frequency",
                reason=f"Min due paid frequency {customer.min_due_paid_freq:.1f}% > 70%",
                suggested_outreach="Reach out via call to confirm financial stress.",
            )
        )

    if customer.merchant_mix_index < 0.4:
        rules.append(
            RuleTrigger(
                rule_name="Low merchant mix",
                reason=f"Merchant mix index {customer.merchant_mix_index:.2f} < 0.40",
                suggested_outreach="Review spending patterns and suggest budgeting tools.",
            )
        )

    return rules
