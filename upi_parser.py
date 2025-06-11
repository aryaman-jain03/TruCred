import pandas as pd
import io

def analyze_upi_csv(file):
    """
    Analyze UPI CSV to determine consistent monthly spending on key categories.
    Returns True if patterns are found across 3+ months; else False.
    """

    try:
        df = pd.read_csv(file if isinstance(file, str) else io.StringIO(file.getvalue().decode()))
    except Exception as e:
        print("CSV read error:", e)
        return False

    if df.empty or 'Date' not in df.columns or 'Description' not in df.columns or 'Amount' not in df.columns:
        return False

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])

    df['Month'] = df['Date'].dt.to_period('M')
    df['Category'] = df['Description'].apply(lambda x: detect_category(x))

    monthly_categories = df.groupby(['Month', 'Category'])['Amount'].sum().unstack(fill_value=0)

    rent_months = monthly_categories['Rent'].gt(0).sum() if 'Rent' in monthly_categories else 0
    utility_months = monthly_categories['Utility'].gt(0).sum() if 'Utility' in monthly_categories else 0
    mobile_months = monthly_categories['Mobile'].gt(0).sum() if 'Mobile' in monthly_categories else 0

    consistent = (rent_months >= 3) or (utility_months >= 3) or (mobile_months >= 3)
    return consistent


def detect_category(description):
    """
    Classify UPI transaction descriptions into basic categories.
    """
    desc = description.lower()
    if "rent" in desc or "landlord" in desc:
        return "Rent"
    if "electricity" in desc or "bijli" in desc or "power" in desc:
        return "Utility"
    if "mobile" in desc or "airtel" in desc or "jio" in desc or "vodafone" in desc:
        return "Mobile"
    return "Other"
