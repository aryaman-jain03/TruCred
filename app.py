import streamlit as st
import os
import json

from scoring import calculate_score
from utils import get_grade
from pdf_generator import generate_pdf
from upi_parser import analyze_upi_csv

VERIFICATION_FILE = "verification_status.json"

# Define upload folders
UPLOAD_FOLDERS = {
    "Rent Proofs": "uploads/rent",
    "Mobile Recharge Proofs": "uploads/mobile",
    "Utility Bill Proofs": "uploads/utility",
}

# Ensure upload directories exist
for folder in UPLOAD_FOLDERS.values():
    os.makedirs(folder, exist_ok=True)

# Load or initialize verification data
if os.path.exists(VERIFICATION_FILE):
    with open(VERIFICATION_FILE, "r") as f:
        verification_data = json.load(f)
else:
    verification_data = {}

st.set_page_config(page_title="TruCred", page_icon="💳")
st.title("TruCred - Alternative Credit Scoring for All")
st.write("Home for India’s unscored population")

st.sidebar.markdown("**Team:** Aryaman Jain & Imroz Saim Kamboj")

# --- Initialize session state for real-time updates ---
# These variables will hold the state of widgets that are outside the main form
if "mobile_recharge_choice" not in st.session_state:
    st.session_state["mobile_recharge_choice"] = "Please select"
if "utility_bill_choice" not in st.session_state:
    st.session_state["utility_bill_choice"] = "Please select"
if "rent_proof_file" not in st.session_state:
    st.session_state["rent_proof_file"] = None
if "mobile_proof_file" not in st.session_state:
    st.session_state["mobile_proof_file"] = None
if "utility_proof_file" not in st.session_state:
    st.session_state["utility_proof_file"] = None
if "upi_file_obj" not in st.session_state:
    st.session_state["upi_file_obj"] = None

# --- UI Sections (mostly outside the main submission form for instant updates) ---

st.header("Step 1: Personal & Basic Info")
# These inputs will be gathered by the final submission form
name = st.text_input("Full Name", key="personal_name")
email = st.text_input("Email Address", key="personal_email")
phone = st.text_input("Phone Number", key="personal_phone")

st.header("Step 2: Financial Inputs")
rent_paid_on_time = st.number_input("Months of rent paid on time (0-12)", min_value=0, max_value=12, step=1, key="financial_rent_time")

st.subheader("Rent Payment Proof")
# This uploader is always visible, so it stays outside the main form
st.session_state["rent_proof_file"] = st.file_uploader("Upload Rent Payment Proof", type=["pdf", "jpg", "png"], key="rent_proof_uploader")


st.subheader("Mobile Recharge")
mobile_recharge_options = ["Please select", "Yes", "No"]
# The radio button updates session_state directly for instant visibility
st.session_state["mobile_recharge_choice"] = st.radio(
    "Do you recharge your mobile regularly?",
    options=mobile_recharge_options,
    index=mobile_recharge_options.index(st.session_state["mobile_recharge_choice"]),
    key="mobile_recharge_radio"
)
# Mobile proof uploader appears ONLY if "Yes" is selected (instantly)
if st.session_state["mobile_recharge_choice"] == "Yes":
    st.session_state["mobile_proof_file"] = st.file_uploader("Upload Mobile Recharge Proof", type=["pdf", "jpg", "png"], key="mobile_proof_uploader")
else:
    # Clear the file if the uploader is no longer visible
    st.session_state["mobile_proof_file"] = None

st.subheader("Utility Bills")
utility_bill_options = ["Please select", "Yes", "No"]
# The radio button updates session_state directly for instant visibility
st.session_state["utility_bill_choice"] = st.radio(
    "Do you have any utility bills in your name?",
    options=utility_bill_options,
    index=utility_bill_options.index(st.session_state["utility_bill_choice"]),
    key="utility_bill_radio"
)
# Utility proof uploader appears ONLY if "Yes" is selected (instantly)
if st.session_state["utility_bill_choice"] == "Yes":
    st.session_state["utility_proof_file"] = st.file_uploader("Upload Utility Bill Proof", type=["pdf", "jpg", "png"], key="utility_proof_uploader")
else:
    # Clear the file if the uploader is no longer visible
    st.session_state["utility_proof_file"] = None


st.header("Step 3: UPI Transaction Upload")
# UPI uploader also outside the main form for instant update/value
st.session_state["upi_file_obj"] = st.file_uploader("Upload UPI CSV File", type=["csv"], key="upi_uploader")

### Final Submission Form

with st.form("final_submission_form"):
    st.header("Step 4: Reference Check")
    reference_name = st.text_input("Reference Name (e.g., landlord, manager)", key="ref_name")
    reference_relationship = st.text_input("Relationship", key="ref_relationship")
    reference_feedback = st.selectbox("How would they rate your financial behavior?", ["positive", "neutral", "negative"], key="ref_feedback")

    submitted = st.form_submit_button("Generate Trust Score & PDF Report")

# --- Processing Logic (runs ONLY after the final form is submitted) ---
if submitted:
    # --- Input Validation ---
    if st.session_state["mobile_recharge_choice"] == "Please select":
        st.error("Please select an option for 'Do you recharge your mobile regularly?'.")
        st.stop() # Stop execution if validation fails
    if st.session_state["utility_bill_choice"] == "Please select":
        st.error("Please select an option for 'Do you have any utility bills in your name?'.")
        st.stop() # Stop execution if validation fails
    if not st.session_state["rent_proof_file"]:
        st.error("Please upload Rent Payment Proof.")
        st.stop()
    if st.session_state["mobile_recharge_choice"] == "Yes" and not st.session_state["mobile_proof_file"]:
        st.error("Please upload Mobile Recharge Proof as you selected 'Yes'.")
        st.stop()
    if st.session_state["utility_bill_choice"] == "Yes" and not st.session_state["utility_proof_file"]:
        st.error("Please upload Utility Bill Proof as you selected 'Yes'.")
        st.stop()

    # Collect all data from both form and session state
    data = {
        "name": name,
        "email": email,
        "phone": phone,
        "rent_paid_on_time": rent_paid_on_time,
        "mobile_recharge": st.session_state["mobile_recharge_choice"],
        "utility_bill": st.session_state["utility_bill_choice"],
        "upi_file": st.session_state["upi_file_obj"],
        "reference_name": reference_name,
        "reference_relationship": reference_relationship,
        "reference_feedback": reference_feedback,
        "rent_proof": st.session_state["rent_proof_file"],
        "mobile_proof": st.session_state["mobile_proof_file"],
        "utility_proof": st.session_state["utility_proof_file"],
    }

    # Save uploaded files to disk
    if data["rent_proof"]:
        file_path = os.path.join(UPLOAD_FOLDERS["Rent Proofs"], f"{data['name']}_{data['rent_proof'].name}")
        with open(file_path, "wb") as f:
            f.write(data["rent_proof"].getbuffer())
        st.success(f"Rent Proof '{data['rent_proof'].name}' uploaded successfully!")

    if data["mobile_recharge"] == "Yes" and data["mobile_proof"]:
        file_path = os.path.join(UPLOAD_FOLDERS["Mobile Recharge Proofs"], f"{data['name']}_{data['mobile_proof'].name}")
        with open(file_path, "wb") as f:
            f.write(data["mobile_proof"].getbuffer())
        st.success(f"Mobile Proof '{data['mobile_proof'].name}' uploaded successfully!")

    if data["utility_bill"] == "Yes" and data["utility_proof"]:
        file_path = os.path.join(UPLOAD_FOLDERS["Utility Bill Proofs"], f"{data['name']}_{data['utility_proof'].name}")
        with open(file_path, "wb") as f:
            f.write(data["utility_proof"].getbuffer())
        st.success(f"Utility Proof '{data['utility_proof'].name}' uploaded successfully!")

    # Store all submitted data in session state for displaying results
    st.session_state["submitted_data"] = data



### Displaying Results and Verification Status

if "submitted_data" in st.session_state:
    data = st.session_state["submitted_data"]

    upi_uploaded = False
    spending_consistent = False
    if data["upi_file"] is not None:
        upi_uploaded = True
        spending_consistent = analyze_upi_csv(data["upi_file"])

    rent_status = "Not uploaded"
    mobile_status = "Not applicable" if data["mobile_recharge"] == "No" else \
                    ("Please select option" if data["mobile_recharge"] == "Please select" else "Not uploaded")
    utility_status = "Not applicable" if data["utility_bill"] == "No" else \
                     ("Please select option" if data["utility_bill"] == "Please select" else "Not uploaded")

    if data["rent_proof"]:
        saved_rent_filename = f"{data['name']}_{data['rent_proof'].name}"
        rent_key = f"Rent Proofs_{saved_rent_filename}"
        rent_status = verification_data.get(rent_key, "Pending")

    if data["mobile_recharge"] == "Yes" and data["mobile_proof"]:
        saved_mobile_filename = f"{data['name']}_{data['mobile_proof'].name}"
        mobile_key = f"Mobile Recharge Proofs_{saved_mobile_filename}"
        mobile_status = verification_data.get(mobile_key, "Pending")

    if data["utility_bill"] == "Yes" and data["utility_proof"]:
        saved_utility_filename = f"{data['name']}_{data['utility_proof'].name}"
        utility_key = f"Utility Bill Proofs_{saved_utility_filename}"
        utility_status = verification_data.get(utility_key, "Pending")

    st.subheader("Document Verification Status")
    st.write(f"Rent Proof: **{rent_status}**")
    st.write(f"Mobile Recharge Proof: **{mobile_status}**")
    st.write(f"Utility Bill Proof: **{utility_status}**")

    all_required_proofs_uploaded = True
    if not data["rent_proof"]:
        all_required_proofs_uploaded = False
    if data["mobile_recharge"] == "Please select" or (data["mobile_recharge"] == "Yes" and not data["mobile_proof"]):
        all_required_proofs_uploaded = False
    if data["utility_bill"] == "Please select" or (data["utility_bill"] == "Yes" and not data["utility_proof"]):
        all_required_proofs_uploaded = False

    all_verified = True
    if rent_status != "Verified":
        all_verified = False
    if mobile_status not in ["Verified", "Not applicable", "Please select option"]:
        all_verified = False
    if utility_status not in ["Verified", "Not applicable", "Please select option"]:
        all_verified = False

    if not all_required_proofs_uploaded:
        st.warning("Please upload all required documents to proceed.")
    elif not all_verified:
        st.info("Your documents are uploaded but still under review.")
        if st.button("Refresh Status"):
            st.rerun()
    else:
        score = calculate_score({
            "rent_paid_on_time": data["rent_paid_on_time"],
            "mobile_recharge": data["mobile_recharge"],
            "utility_bill": data["utility_bill"],
            "upi_uploaded": upi_uploaded,
            "spending_consistent": spending_consistent,
            "reference_feedback": data["reference_feedback"],
        })

        grade = get_grade(score)

        user_data = {
            "name": data["name"],
            "email": data["email"],
            "phone": data["phone"],
            "rent_paid_on_time": data["rent_paid_on_time"],
            "mobile_recharge": data["mobile_recharge"],
            "utility_bill": data["utility_bill"],
            "upi_uploaded": upi_uploaded,
            "spending_consistent": spending_consistent,
            "reference_name": data["reference_name"],
            "reference_relationship": data["reference_relationship"],
            "reference_feedback": data["reference_feedback"],
        }

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