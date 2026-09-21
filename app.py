import json
import streamlit as st
from ollama import chat

st.set_page_config(
    page_title="AI ERP Error Assistant",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 AI ERP Error Assistant")

st.write(
    "Select your ERP system, paste the error, and AI will help troubleshoot it."
)

erp_system = st.selectbox(
    "Select ERP System",
    ["NetSuite", "Workday", "SAP", "Other"]
)

error = st.text_area(
    "ERP Error",
    placeholder="Example: Invalid department reference"
)

if st.button("Analyze Error", type="primary"):

    if error.strip() == "":
        st.warning("Please enter an ERP error.")

    else:

        prompt = f"""
You are an experienced {erp_system} support analyst.

Analyze this ERP error:

{error}

Return ONLY valid JSON using exactly this structure:

{{
    "error_meaning": "Short explanation of what the error means",
    "possible_causes": [
        "Cause 1",
        "Cause 2",
        "Cause 3"
    ],
    "what_to_check": [
        "Check 1",
        "Check 2",
        "Check 3"
    ],
    "suggested_resolution": "Practical recommended resolution"
}}

Do not include any text outside the JSON.
Do not invent system-specific facts if you are unsure.
"""

        with st.spinner("Analyzing error..."):

            response = chat(
                model="llama3.2:3b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                format="json"
            )

        try:

            data = json.loads(response.message.content)

            st.success("Analysis complete")

            st.subheader("Error Meaning")
            st.info(data["error_meaning"])

            st.subheader("Possible Causes")

            for cause in data["possible_causes"]:
                st.write(f"• {cause}")

            st.subheader("What to Check")

            for check in data["what_to_check"]:
                st.write(f"• {check}")

            st.subheader("Suggested Resolution")
            st.success(data["suggested_resolution"])

        except json.JSONDecodeError:

            st.error("The AI returned an invalid response. Please try again.")