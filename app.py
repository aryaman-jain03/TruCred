import streamlit as st
import os
import json
from PIL import Image

from scoring import calculate_score
from utils import get_grade
from pdf_generator import generate_pdf
from upi_parser import analyze_upi_csv

# Must be the first Streamlit command
st.set_page_config(page_title="TruCred", page_icon="💳")



# --- Load and Display Top Bar with Logo ---
logo_path = "assets/logo.png"
logo_image = Image.open(logo_path)

top_bar = st.container()
with top_bar:
    col1, col2 = st.columns([1.5, 10])
    with col1:
        st.image(logo_image, width=2000)

st.markdown("<br><br>", unsafe_allow_html=True)

# --- Setup Upload folders and verification file ---
VERIFICATION_FILE = "verification_status.json"

UPLOAD_FOLDERS = {
    "Rent Proofs": "uploads/rent",
    "Mobile Recharge Proofs": "uploads/mobile",
    "Utility Bill Proofs": "uploads/utility",
}

for folder in UPLOAD_FOLDERS.values():
    os.makedirs(folder, exist_ok=True)

if os.path.exists(VERIFICATION_FILE):
    with open(VERIFICATION_FILE, "r") as f:
        verification_data = json.load(f)
else:
    verification_data = {}

# --- Page Content ---
st.title("TruCred - Alternative Credit Scoring for All")
st.write("Home for India’s unscored population")
st.sidebar.markdown("Team: Aryaman Jain & Imroz Saim Kamboj")

# --- Session Defaults ---
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

# --- Step 1: Personal Info ---
st.markdown("### Step 1: Personal and Basic Information")
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Full Name", key="personal_name")
with col2:
    email = st.text_input("Email Address", key="personal_email")

phone = st.text_input("Phone Number", key="personal_phone")
st.divider()

# --- Step 2: Financial Inputs ---
st.markdown("### Step 2: Financial Inputs")

with st.expander("Recurring Financial Proof (e.g. EMI / PG Rent / Loan Repayment)"):
    rent_paid_on_time = st.slider("Months of timely payments", min_value=0, max_value=12, step=1, key="financial_rent_time")
    st.session_state["rent_proof_file"] = st.file_uploader("Upload Proof (PDF/JPG/PNG)", type=["pdf", "jpg", "png"], key="rent_proof_uploader")

with st.expander("Mobile Recharge"):
    mobile_recharge_options = ["Please select", "Yes", "No"]
    st.session_state["mobile_recharge_choice"] = st.radio(
        "Do you recharge your mobile regularly?",
        options=mobile_recharge_options,
        index=mobile_recharge_options.index(st.session_state["mobile_recharge_choice"]),
        key="mobile_recharge_radio"
    )
    if st.session_state["mobile_recharge_choice"] == "Yes":
        st.session_state["mobile_proof_file"] = st.file_uploader("Upload Recharge Proof", type=["pdf", "jpg", "png"], key="mobile_proof_uploader")
    else:
        st.session_state["mobile_proof_file"] = None

with st.expander("Utility Bill"):
    utility_bill_options = ["Please select", "Yes", "No"]
    st.session_state["utility_bill_choice"] = st.radio(
        "Do you have any utility bills in your name?",
        options=utility_bill_options,
        index=utility_bill_options.index(st.session_state["utility_bill_choice"]),
        key="utility_bill_radio"
    )
    if st.session_state["utility_bill_choice"] == "Yes":
        st.session_state["utility_proof_file"] = st.file_uploader("Upload Utility Bill", type=["pdf", "jpg", "png"], key="utility_proof_uploader")
    else:
        st.session_state["utility_proof_file"] = None

st.divider()

# --- Step 3: UPI Upload ---
st.markdown("### Step 3: UPI Transaction Upload")
st.session_state["upi_file_obj"] = st.file_uploader("Upload UPI CSV File", type=["csv"], key="upi_uploader")
st.divider()

# --- Step 4: Reference Info ---
with st.form("final_submission_form"):
    st.markdown("### Step 4: Reference Check")
    reference_name = st.text_input("Reference Name (e.g., landlord, manager)", key="ref_name")
    reference_relationship = st.text_input("Relationship", key="ref_relationship")
    reference_feedback = st.selectbox("How would they rate your financial behavior?", ["positive", "neutral", "negative"], key="ref_feedback")
    submitted = st.form_submit_button("Generate Trust Score and PDF Report")

# --- Submission Logic ---
if submitted:
    if st.session_state["mobile_recharge_choice"] == "Please select":
        st.error("Please select an option for mobile recharge.")
        st.stop()
    if st.session_state["utility_bill_choice"] == "Please select":
        st.error("Please select an option for utility bill.")
        st.stop()
    if not st.session_state["rent_proof_file"]:
        st.error("Please upload a rent/loan proof document.")
        st.stop()
    if st.session_state["mobile_recharge_choice"] == "Yes" and not st.session_state["mobile_proof_file"]:
        st.error("Please upload mobile recharge proof.")
        st.stop()
    if st.session_state["utility_bill_choice"] == "Yes" and not st.session_state["utility_proof_file"]:
        st.error("Please upload utility bill proof.")
        st.stop()

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

    for doc_type, file_obj in {
        "Rent Proofs": data["rent_proof"],
        "Mobile Recharge Proofs": data["mobile_proof"],
        "Utility Bill Proofs": data["utility_proof"]
    }.items():
        if file_obj:
            file_path = os.path.join(UPLOAD_FOLDERS[doc_type], f"{data['name']}_{file_obj.name}")
            with open(file_path, "wb") as f:
                f.write(file_obj.getbuffer())
            st.success(f"{doc_type.split()[0]} Proof '{file_obj.name}' uploaded successfully.")

    st.session_state["submitted_data"] = data

# --- Post-submission Trust Score Generation ---
if "submitted_data" in st.session_state:
    data = st.session_state["submitted_data"]

    with open(VERIFICATION_FILE, "r") as f:
        verification_data = json.load(f)

    upi_uploaded = data["upi_file"] is not None
    spending_consistent = analyze_upi_csv(data["upi_file"]) if upi_uploaded else False

    def get_status(key, filename):
        return verification_data.get(f"{key}_{filename}", {}).get("status", "Pending")

    rent_status = get_status("Rent Proofs", f"{data['name']}_{data['rent_proof'].name}") if data["rent_proof"] else "Not uploaded"
    mobile_status = get_status("Mobile Recharge Proofs", f"{data['name']}_{data['mobile_proof'].name}") if data["mobile_recharge"] == "Yes" else "Not applicable"
    utility_status = get_status("Utility Bill Proofs", f"{data['name']}_{data['utility_proof'].name}") if data["utility_bill"] == "Yes" else "Not applicable"

    st.markdown("### Document Verification Status")
    st.write(f"Recurring Payment Proof: **{rent_status}**")
    st.write(f"Mobile Recharge: **{mobile_status}**")
    st.write(f"Utility Bill: **{utility_status}**")

    all_verified = (
        rent_status == "Verified" and
        (mobile_status in ["Verified", "Not applicable"]) and
        (utility_status in ["Verified", "Not applicable"])
    )

    if not all_verified:
        st.info("Documents uploaded but pending verification.")
        if st.button("Refresh Status"):
            st.rerun()
    else:
        breakdown = calculate_score({
            "rent_paid_on_time": data["rent_paid_on_time"],
            "mobile_recharge": data["mobile_recharge"],
            "utility_bill": data["utility_bill"],
            "upi_uploaded": upi_uploaded,
            "spending_consistent": spending_consistent,
            "reference_feedback": data["reference_feedback"],
        }, return_breakdown=True)

        total_score = breakdown["total"]
        grade = get_grade(total_score)

        st.success(f"Your Trust Score: {total_score}/100 | Grade: {grade}")

        st.markdown("### Score Breakdown")
        for k, v in breakdown["components"].items():
            st.write(f"- {k}: **{v}** points")

        pdf_path = generate_pdf({
            **data,
            "upi_uploaded": upi_uploaded,
            "spending_consistent": spending_consistent
        }, total_score, grade, rent_status, mobile_status, utility_status)

        with open(pdf_path, "rb") as f:
            st.download_button(
                "Download Verified Financial Report",
                data=f,
                file_name="TruCred_Financial_Report.pdf",
                mime="application/pdf"
            )

        st.markdown("### Send Report via Email")
        receiver_email = st.text_input("Recipient Email").strip()

        if st.button("Send Email"):
            if receiver_email:
                try:
                    from utils import send_email_with_pdf
                    send_email_with_pdf(
                        receiver_email,
                        "Your TruCred Financial Report",
                        "Hello,\n\nPlease find attached your TruCred Credit Score Report.\n\nThank you.",
                        pdf_path
                    )
                    st.success("Email sent successfully.")
                except Exception as e:
                    st.error(f"Error sending email: {str(e)}")
            else:
                st.warning("Please enter a recipient email.")
