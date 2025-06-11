def calculate_score(data, return_breakdown=False):
    """
    Calculates credit score based on user-submitted data.
    Returns the numeric score (0–100 scale) or breakdown if return_breakdown=True.
    """
    breakdown = {
        "rent_paid_on_time": 0,
        "mobile_recharge": 0,
        "upi_uploaded": 0,
        "reference_feedback": 0,
        "spending_consistent": 0,
        "utility_bill": 0,
    }

    # Rent payment consistency
    if data.get("rent_paid_on_time", 0) >= 3:
        breakdown["rent_paid_on_time"] = 20

    # Mobile recharge consistency
    if data.get("mobile_recharge") == "Yes":
        breakdown["mobile_recharge"] = 15

    # UPI upload bonus
    if data.get("upi_uploaded", False):
        breakdown["upi_uploaded"] = 10

    # Reference endorsement
    if data.get("reference_feedback") == "positive":
        breakdown["reference_feedback"] = 20
    elif data.get("reference_feedback") == "neutral":
        breakdown["reference_feedback"] = 10

    # UPI spending consistency
    if data.get("spending_consistent", False):
        breakdown["spending_consistent"] = 15

    # Utility bill presence
    if data.get("utility_bill") == "Yes":
        breakdown["utility_bill"] = 10

    total_score = sum(breakdown.values())

    if return_breakdown:
        return {
            "total": total_score,
            "components": breakdown
        }

    return total_score
