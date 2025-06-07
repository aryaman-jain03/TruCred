def calculate_score(data):
    """
    Calculates credit score based on user-submitted data.
    Returns the numeric score (0–100 scale).
    """

    score = 0

    # Rent payment consistency
    if data.get("rent_paid_on_time", 0) >= 3:
        score += 20

    # Mobile recharge consistency
    if data.get("mobile_recharge") == "Yes":
        score += 15

    # UPI upload bonus
    if data.get("upi_uploaded", False):
        score += 10

    # Reference endorsement
    if data.get("reference_feedback") == "positive":
        score += 20
    elif data.get("reference_feedback") == "neutral":
        score += 10
    else:
        score += 0

    # UPI spending consistency (to be decided via upi_parser)
    if data.get("spending_consistent", False):
        score += 15

    # Utility bill presence
    if data.get("utility_bill") == "Yes":
        score += 10

    return score
