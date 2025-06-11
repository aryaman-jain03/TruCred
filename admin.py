import streamlit as st
import os
import json
from datetime import datetime

st.set_page_config(page_title="TruCred Admin Dashboard", layout="centered")
st.title("TruCred Admin Dashboard")

# Constants
UPLOAD_FOLDERS = {
    "Rent Proofs": "uploads/rent",
    "Mobile Recharge Proofs": "uploads/mobile",
    "Utility Bill Proofs": "uploads/utility",
}
VERIFICATION_FILE = "verification_status.json"

# Ensure upload directories exist
for folder in UPLOAD_FOLDERS.values():
    os.makedirs(folder, exist_ok=True)

# Load or initialize verification data
if os.path.exists(VERIFICATION_FILE):
    with open(VERIFICATION_FILE, "r") as f:
        verification_data = json.load(f)
else:
    verification_data = {}

# Upgrade old string-based statuses to dict format
for key, value in list(verification_data.items()):
    if isinstance(value, str):
        verification_data[key] = {
            "status": value,
            "uploaded_at": datetime.now().isoformat(),
            "verified_at": None
        }

# Sidebar filters
st.sidebar.header("Filters")
status_filter = st.sidebar.selectbox("Filter by Status", ["All", "Pending", "Verified", "Rejected"])

# Admin UI
st.header("Uploaded Documents Review")

updated = False
deleted = False

for proof_type, folder in UPLOAD_FOLDERS.items():
    st.subheader(f"{proof_type}")
    files = os.listdir(folder)

    if not files:
        st.write("No files uploaded yet.")
        continue

    for filename in files:
        filepath = os.path.join(folder, filename)
        key = f"{proof_type}_{filename}"
        file_entry = verification_data.get(key)

        # Initialize entry if missing or improperly formatted
        if isinstance(file_entry, str):
            file_entry = {
                "status": file_entry,
                "uploaded_at": datetime.now().isoformat(),
                "verified_at": None
            }
            verification_data[key] = file_entry
            updated = True
        elif not file_entry:
            file_entry = {
                "status": "Pending",
                "uploaded_at": datetime.now().isoformat(),
                "verified_at": None
            }
            verification_data[key] = file_entry
            updated = True

        current_status = file_entry["status"]

        # Filter files
        if status_filter != "All" and current_status != status_filter:
            continue

        with st.expander(f"{filename}"):
            st.markdown(f"**Status:** {current_status}")
            st.markdown(f"**Uploaded At:** {file_entry.get('uploaded_at', 'N/A')}")
            st.markdown(f"**Verified At:** {file_entry.get('verified_at', 'Not verified yet')}")

            with open(filepath, "rb") as f:
                st.download_button(
                    label="Download File",
                    data=f,
                    file_name=filename,
                    mime="application/octet-stream",
                    key=f"download_{key}"
                )

            new_status = st.selectbox(
                f"Update Status for {filename}",
                options=["Pending", "Verified", "Rejected"],
                index=["Pending", "Verified", "Rejected"].index(current_status),
                key=f"status_select_{key}"
            )

            if new_status != current_status:
                file_entry["status"] = new_status
                if new_status == "Verified":
                    file_entry["verified_at"] = datetime.now().isoformat()
                else:
                    file_entry["verified_at"] = None
                verification_data[key] = file_entry
                updated = True

            if st.button(f"Delete File: {filename}", key=f"delete_{key}"):
                try:
                    os.remove(filepath)
                    verification_data.pop(key, None)
                    deleted = True
                    st.warning(f"{filename} deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting file: {e}")

# Save verification status
if updated or deleted:
    with open(VERIFICATION_FILE, "w") as f:
        json.dump(verification_data, f, indent=2)

if updated:
    st.success("Verification statuses updated successfully!")

if not updated and not deleted:
    st.info("No changes made to verification statuses.")
