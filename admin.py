import streamlit as st
import os
from PIL import Image
import json

# Directory to save verification statuses
VERIFICATION_FILE = "verification_status.json"

# Helper function to normalize status strings (remove emojis)
def normalize_status(status_str):
    if "✅" in status_str:
        return "Verified"
    elif "❌" in status_str:
        return "Rejected"
    return status_str # Returns "Pending" or already normalized strings

# Load existing verifications
if os.path.exists(VERIFICATION_FILE):
    with open(VERIFICATION_FILE, "r") as f:
        verification_data_raw = json.load(f)
    # Normalize existing data when loading
    verification_data = {k: normalize_status(v) for k, v in verification_data_raw.items()}
else:
    verification_data = {}

st.title("TruCred Admin Document Review")

categories = {
    "Rent Proofs": "uploads/rent",
    "Mobile Recharge Proofs": "uploads/mobile",
    "Utility Bill Proofs": "uploads/utility"
}

for label, folder in categories.items():
    st.subheader(label)
    # Ensure the folder exists before trying to list its contents
    if not os.path.exists(folder):
        st.info(f"No uploads found yet for {label}.")
        continue

    files = os.listdir(folder)
    # Filter out hidden files like .DS_Store if they exist
    files = [f for f in files if not f.startswith('.')]

    if not files:
        st.write("No files to review.")
    else:
        for file in files:
            file_path = os.path.join(folder, file)
            st.write(f"File: `{file}`")
            ext = file.split('.')[-1].lower()

            # Show preview for images
            if ext in ['jpg', 'jpeg', 'png']:
                st.image(file_path, width=300)
            elif ext == "pdf":
                # For PDF, provide a clickable link to view the file
                st.markdown(f"[View PDF]({file_path})", unsafe_allow_html=True)
            else:
                st.write(f"No preview available for .{ext} files.")


            key = f"{label}_{file}"
            # Retrieve the current status, defaulting to "Pending" if not found
            current_status_for_display = verification_data.get(key, "Pending")

            # Determine the index for the radio button based on the normalized status
            options = ["Pending", "Verified", "Rejected"]
            try:
                # Use the normalized status to find its index in the options list
                selected_index = options.index(current_status_for_display)
            except ValueError:
                # Fallback if somehow current_status_for_display isn't one of the expected options
                selected_index = 0 # Default to "Pending"

            st.write(f"**Current Status:** {current_status_for_display}")

            # The st.radio widget will now display and return values without emojis
            status = st.radio(
                "Mark status:",
                options,
                index=selected_index,
                key=key
            )

            # Save updated status (which will now be emoji-free)
            verification_data[key] = status

            st.markdown("---")

# Save to JSON
# Ensure we save the normalized data back to the file
with open(VERIFICATION_FILE, "w") as f:
    json.dump(verification_data, f, indent=2)