import streamlit as st
import os
import json
import base64
from PIL import Image
from io import BytesIO

from scoring import calculate_score
from utils import get_grade, send_email_with_pdf
from pdf_generator import generate_pdf
from upi_parser import analyze_upi_csv

# Streamlit Page Config
st.set_page_config(page_title="TruCred", page_icon="💳", layout="wide")

# Background & CSS Styling
st.markdown("""
    <style>
    .stApp {
        background: #4CA1AF;
        background: -webkit-linear-gradient(to right, #C4E0E5, #4CA1AF);
        background: linear-gradient(to right, #C4E0E5, #4CA1AF);
    }

    /* Cards (Glassmorphism) */
    .stContainer, .stExpander, .stColumn, .stForm {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .stContainer:hover,
    .stExpander:hover,
    .stColumn:hover,
    .stForm:hover {
        transform: scale(1.02);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25);
    }

    /* Navbar */
    .navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(to right, #C4E0E5, #4CA1AF);
        padding: 0.4rem 1.2rem;
        border-bottom: 1px solid #e0e0e0;
        margin: -3rem -3rem 1rem -3rem;
        position: sticky;
        top: 0;
        z-index: 999;
    }
    .navbar-left {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .navbar-logo {
        height: 100px;
        margin-right: 0.5rem;
        vertical-align: middle;
        cursor: pointer;
    }
    .navbar-buttons {
        display: flex;
        gap: 1rem;
    }
    .nav-button {
        font-size: 15px;
        font-weight: 500;
        padding: 0.4rem 1rem;
        color: white;
        background-color: #003366;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .nav-button:hover {
        background-color: #002244;
    }

    /* Input Box Gradient */
    input[type="text"], input[type="email"], .stTextInput input {
        background-color: rgba(0, 51, 102, 0.1);
        color: black;
        border-radius: 8px !important;
        border: 1px solid rgba(0, 0, 0, 0.2);
    }

    /* Styled Submit Button */
    div.stButton > button:first-child {
        background-color: #003366;
        color: white;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        border-radius: 6px;
    }
    div.stButton > button:first-child:hover {
        background-color: #002244;
    }
    </style>
""", unsafe_allow_html=True)

# Load Logo
def load_logo_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

logo_base64 = load_logo_base64("assets/logo.png")

# Navbar
st.markdown(f"""
<div class="navbar">
    <div class="navbar-left">
        <img src="data:image/png;base64,{logo_base64}" class="navbar-logo"/>
    </div>
    <div class="navbar-buttons">
        <form action="" method="get">
            <input type="submit" name="page" value="Home" class="nav-button">
            <input type="submit" name="page" value="About" class="nav-button">
            <input type="submit" name="page" value="Contact" class="nav-button">
        </form>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation
page = st.query_params.get("page", "Home")

# --- Home Page ---
if page == "Home":
    st.title("TruCred - Alternative Credit Scoring for All")
    st.write("Home for India’s unscored population")
    st.sidebar.markdown("Team: Aryaman Jain & Imroz Saim Kamboj")

    VERIFICATION_FILE = "verification_status.json"
    UPLOAD_FOLDERS = {
        "Rent Proofs": "uploads/rent",
        "Mobile Recharge Proofs": "uploads/mobile",
        "Utility Bill Proofs": "uploads/utility",
    }
    for folder in UPLOAD_FOLDERS.values():
        os.makedirs(folder, exist_ok=True)

    verification_data = {}
    if os.path.exists(VERIFICATION_FILE):
        with open(VERIFICATION_FILE, "r") as f:
            verification_data = json.load(f)

    # Step 1: Personal Info
    st.markdown("### Step 1: Personal and Basic Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input("Full Name")
    with col2:
        email = st.text_input("Email Address")
    with col3:   
        phone = st.text_input("Phone Number")
    st.divider()

    # Step 2: Financial Inputs
    st.markdown("### Step 2: Financial Inputs")
    with st.expander("Recurring Financial Proof (e.g. EMI / PG Rent / Loan Repayment)"):
        rent_paid_on_time = st.slider("Months of timely payments", 0, 12)
        rent_proof_file = st.file_uploader("Upload Proof (PDF/JPG/PNG)", type=["pdf", "jpg", "png"])

    with st.expander("Mobile Recharge"):
        mobile_choice = st.radio("Do you recharge your mobile regularly?", ["Please select", "Yes", "No"])
        mobile_proof_file = None
        if mobile_choice == "Yes":
            mobile_proof_file = st.file_uploader("Upload Recharge Proof", type=["pdf", "jpg", "png"])

    with st.expander("Utility Bill"):
        utility_choice = st.radio("Do you have any utility bills in your name?", ["Please select", "Yes", "No"])
        utility_proof_file = None
        if utility_choice == "Yes":
            utility_proof_file = st.file_uploader("Upload Utility Bill", type=["pdf", "jpg", "png"])

    st.divider()

    # Step 3: UPI Upload
    st.markdown("### Step 3: UPI Transaction Upload")
    upi_file_obj = st.file_uploader("Upload UPI CSV File", type=["csv"])
    st.divider()

    # Step 4: Reference Check
    with st.form("final_submission_form"):
        st.markdown("### Step 4: Reference Check")
        reference_name = st.text_input("Reference Name")
        reference_relationship = st.text_input("Relationship")
        reference_feedback = st.selectbox("How would they rate your financial behavior?", ["positive", "neutral", "negative"])
        submitted = st.form_submit_button("Generate Trust Score and PDF Report")

    if submitted:
        for condition, error_msg in [
            (mobile_choice == "Please select", "Please select an option for mobile recharge."),
            (utility_choice == "Please select", "Please select an option for utility bill."),
            (not rent_proof_file, "Please upload a rent/loan proof document."),
            (mobile_choice == "Yes" and not mobile_proof_file, "Please upload mobile recharge proof."),
            (utility_choice == "Yes" and not utility_proof_file, "Please upload utility bill proof."),
        ]:
            if condition:
                st.error(error_msg)
                st.stop()

        data = {
            "name": name, "email": email, "phone": phone,
            "rent_paid_on_time": rent_paid_on_time,
            "mobile_recharge": mobile_choice,
            "utility_bill": utility_choice,
            "upi_file": upi_file_obj,
            "reference_name": reference_name,
            "reference_relationship": reference_relationship,
            "reference_feedback": reference_feedback,
            "rent_proof": rent_proof_file,
            "mobile_proof": mobile_proof_file,
            "utility_proof": utility_proof_file,
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

    # Post Submission
    if "submitted_data" in st.session_state:
        data = st.session_state["submitted_data"]
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

# About Page
elif page == "About":
    st.title("About TruCred")
    st.markdown("""
        TruCred is an alternative credit scoring platform for India’s unscored population — such as students, gig workers, and those without formal credit history.

        We use simple, understandable financial behaviors (like regular mobile recharges, timely rent payments, and spending patterns) to generate a trust score and generate a verified PDF report that can be shared with landlords, vendors, or fintech providers.

        **Created by Aryaman Jain & Imroz Saim Kamboj.**
    """)

# Contact Page
elif page == "Contact":
    st.title("Contact Us")
    st.markdown("""
        **Email:** trucred.contact@gmail.com  
        **Phone:** +91 9876543210  
        **Location:** Manipal University Jaipur  
        
        For support or inquiries, feel free to reach out!
    """)