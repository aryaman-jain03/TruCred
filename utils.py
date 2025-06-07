def get_grade(score):
    """
    Converts numerical score into a trust grade.
    """
    if score >= 80:
        return "A"
    elif score >= 50:
        return "B"
    else:
        return "C"
