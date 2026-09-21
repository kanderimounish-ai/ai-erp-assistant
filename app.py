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


def get_section(text, start_marker, end_marker=None):
    if start_marker not in text:
        return "No information returned."

    section = text.split(start_marker, 1)[1]

    if end_marker and end_marker in section:
        section = section.split(end_marker, 1)[0]

    return section.strip()


if st.button("Analyze Error", type="primary"):

    if error.strip() == "":
        st.warning("Please enter an ERP error.")

    else:

        prompt = f"""
You are an experienced {erp_system} support analyst.

The user received this error:

{error}

Respond using exactly these headings:

ERROR MEANING:
Explain what the error means.

POSSIBLE CAUSES:
List the likely causes.

WHAT TO CHECK:
Give practical troubleshooting steps.

SUGGESTED RESOLUTION:
Explain how the issue could be resolved.

Keep the answer practical and concise.
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
                ]
            )

        answer = response.message.content

        error_meaning = get_section(
            answer,
            "ERROR MEANING:",
            "POSSIBLE CAUSES:"
        )

        possible_causes = get_section(
            answer,
            "POSSIBLE CAUSES:",
            "WHAT TO CHECK:"
        )

        what_to_check = get_section(
            answer,
            "WHAT TO CHECK:",
            "SUGGESTED RESOLUTION:"
        )

        suggested_resolution = get_section(
            answer,
            "SUGGESTED RESOLUTION:"
        )

        st.success("Analysis complete")

        st.subheader("Error Meaning")
        st.info(error_meaning)

        st.subheader("Possible Causes")
        st.warning(possible_causes)

        st.subheader("What to Check")
        st.info(what_to_check)

        st.subheader("Suggested Resolution")
        st.success(suggested_resolution)