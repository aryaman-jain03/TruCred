import streamlit as st
from scoring import calculate_score
from utils import get_grade
from pdf_generator import generate_pdf
from upi_parser import analyze_upi_csv

st.set_page_config(page_title="TruCred", page_icon="💳")

st.title("TruCred - Alternative Credit Scoring for All")
st.write("Helping gig workers and students access trust-based financial profiles.")

#st.sidebar.image("assets/logo.png", use_column_width=True)
st.sidebar.markdown("**Team:** Aryaman Jain & Imroz Saim Kamboj")

# Form Inputs
with st.form("user_form"):
    st.header("Step 1: Personal & Basic Info")
    name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    phone = st.text_input("Phone Number")

    st.header("Step 2: Financial Inputs")
    rent_paid_on_time = st.number_input("Months of rent paid on time (0-12)", min_value=0, max_value=12, step=1)
    mobile_recharge = st.radio("Do you recharge your mobile regularly?", ["Yes", "No"])
    utility_bill = st.radio("Do you have any utility bills in your name?", ["Yes", "No"])

    st.header("Step 3: UPI Transaction Upload")
    upi_file = st.file_uploader("Upload UPI CSV File", type=["csv"])

    st.header("Step 4: Reference Check")
    reference_name = st.text_input("Reference Name (e.g., landlord, manager)")
    reference_relationship = st.text_input("Relationship")
    reference_feedback = st.selectbox("How would they rate your financial behavior?", ["positive", "neutral", "negative"])

    submitted = st.form_submit_button("Generate Trust Score & PDF Report")

if submitted:
    # Analyze UPI CSV if uploaded
    upi_uploaded = False
    spending_consistent = False
    if upi_file is not None:
        upi_uploaded = True
        spending_consistent = analyze_upi_csv(upi_file)

    # Prepare data dict
    data = {
        "rent_paid_on_time": rent_paid_on_time,
        "mobile_recharge": mobile_recharge,
        "utility_bill": utility_bill,
        "upi_uploaded": upi_uploaded,
        "spending_consistent": spending_consistent,
        "reference_feedback": reference_feedback,
    }

    # Calculate score and grade
    score = calculate_score(data)
    grade = get_grade(score)

    # User data for PDF
    user_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "rent_paid_on_time": rent_paid_on_time,
        "mobile_recharge": mobile_recharge,
        "utility_bill": utility_bill,
        "upi_uploaded": upi_uploaded,
        "spending_consistent": spending_consistent,
        "reference_name": reference_name,
        "reference_relationship": reference_relationship,
        "reference_feedback": reference_feedback,
    }

    # Generate PDF
    pdf_path = generate_pdf(user_data, score, grade)

    # Show results
    st.success(f"Your Trust Score is {score}/100 with Grade '{grade}'")
    st.write("Download your Verified Financial Profile report below:")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name="TruCred_Financial_Report.pdf",
            mime="application/pdf",
        )
