import streamlit as st
import os
import json

from scoring import calculate_score
from utils import get_grade
from pdf_generator import generate_pdf
from upi_parser import analyze_upi_csv

VERIFICATION_FILE = "verification_status.json"

if os.path.exists(VERIFICATION_FILE):
    with open(VERIFICATION_FILE, "r") as f:
        verification_data = json.load(f)
else:
    verification_data = {}

st.set_page_config(page_title="TruCred", page_icon="💳")
st.title("TruCred - Alternative Credit Scoring for All")
st.write("Home for India’s unscored population")

# st.sidebar.image("assets/logo.png", use_column_width=True)
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

    st.subheader("Upload Proofs")

    rent_proof = st.file_uploader("Upload Rent Payment Proof", type=["pdf", "jpg", "png"], key="rent")
    mobile_proof = st.file_uploader("Upload Mobile Recharge Proof", type=["pdf", "jpg", "png"], key="mobile")
    utility_proof = st.file_uploader("Upload Utility Bill Proof", type=["pdf", "jpg", "png"], key="utility")

    submitted = st.form_submit_button("Generate Trust Score & PDF Report")

if submitted:
    upi_uploaded = False
    spending_consistent = False
    if upi_file is not None:
        upi_uploaded = True
        spending_consistent = analyze_upi_csv(upi_file)

    data = {
        "rent_paid_on_time": rent_paid_on_time,
        "mobile_recharge": mobile_recharge,
        "utility_bill": utility_bill,
        "upi_uploaded": upi_uploaded,
        "spending_consistent": spending_consistent,
        "reference_feedback": reference_feedback,
    }

    score = calculate_score(data)
    grade = get_grade(score)

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

    # Save uploaded files
    rent_key = mobile_key = utility_key = None
    rent_status = mobile_status = utility_status = "Not uploaded"

    if rent_proof:
        rent_key = f"Rent Proofs_{name}_{rent_proof.name}"
        rent_path = f"uploads/rent/{rent_key.split('_', 1)[1]}"
        with open(rent_path, "wb") as f:
            f.write(rent_proof.getbuffer())
        rent_status = verification_data.get(rent_key, "Pending")

    if mobile_proof:
        mobile_key = f"Mobile Recharge Proofs_{name}_{mobile_proof.name}"
        mobile_path = f"uploads/mobile/{mobile_key.split('_', 1)[1]}"
        with open(mobile_path, "wb") as f:
            f.write(mobile_proof.getbuffer())
        mobile_status = verification_data.get(mobile_key, "Pending")

    if utility_proof:
        utility_key = f"Utility Bill Proofs_{name}_{utility_proof.name}"
        utility_path = f"uploads/utility/{utility_key.split('_', 1)[1]}"
        with open(utility_path, "wb") as f:
            f.write(utility_proof.getbuffer())
        utility_status = verification_data.get(utility_key, "Pending")

    # Show statuses
    st.subheader("Document Verification Status")
    st.write(f"Rent Proof: **{rent_status}**")
    st.write(f"Mobile Recharge Proof: **{mobile_status}**")
    st.write(f"Utility Bill Proof: **{utility_status}**")

    # Generate and offer PDF download
    pdf_path = generate_pdf(user_data, score, grade, rent_status, mobile_status, utility_status)

    st.success(f"Your Trust Score is {score}/100 with Grade '{grade}'")
    st.write("Download your Verified Financial Profile report below:")

    with open(pdf_path, "rb") as f:
        st.download_button(
            label="Download PDF Report",
            data=f,
            file_name="TruCred_Financial_Report.pdf",
            mime="application/pdf",
        )
