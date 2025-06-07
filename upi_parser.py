import pandas as pd
from datetime import datetime

def analyze_upi_csv(file):
    """
    Checks if UPI transactions are consistent.
    Returns True if user transacts in >2 different weeks of the month.
    """

    try:
        df = pd.read_csv(file)

        # Ensure there's a 'Date' column
        if 'Date' not in df.columns:
            return False

        # Parse and normalize dates
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])

        # Extract week numbers (ISO week format)
        df['Week'] = df['Date'].dt.isocalendar().week

        # Count distinct weeks
        active_weeks = df['Week'].nunique()

        return active_weeks >= 3

    except Exception as e:
        print(f"UPI Analysis Error: {e}")
        return False
