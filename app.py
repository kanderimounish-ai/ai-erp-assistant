import json
import sqlite3
import streamlit as st
from ollama import chat


# -----------------------------
# Page Configuration
# -----------------------------

st.set_page_config(
    page_title="AI ERP Error Assistant",
    page_icon="🤖",
    layout="centered"
)


# -----------------------------
# Database Setup
# -----------------------------

connection = sqlite3.connect("erp_history.db")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    erp_system TEXT,
    error TEXT,
    error_meaning TEXT,
    possible_causes TEXT,
    what_to_check TEXT,
    suggested_resolution TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

connection.commit()


# -----------------------------
# App UI
# -----------------------------

st.title("🤖 AI ERP Error Assistant")

st.write(
    "Select your ERP system, paste the error, "
    "and AI will help troubleshoot it."
)

erp_system = st.selectbox(
    "Select ERP System",
    ["NetSuite", "Workday", "SAP", "Other"]
)

error = st.text_area(
    "ERP Error",
    placeholder="Example: Invalid department reference"
)


# -----------------------------
# Analyze Button
# -----------------------------

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
    "error_meaning": "Short explanation",
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
    "suggested_resolution": "Practical resolution"
}}

Do not include any text outside JSON.

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

            # -----------------------------
            # Save Result to Database
            # -----------------------------

            cursor.execute(
                """
                INSERT INTO history (
                    erp_system,
                    error,
                    error_meaning,
                    possible_causes,
                    what_to_check,
                    suggested_resolution
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    erp_system,
                    error,
                    data["error_meaning"],
                    json.dumps(data["possible_causes"]),
                    json.dumps(data["what_to_check"]),
                    data["suggested_resolution"]
                )
            )

            connection.commit()

            # -----------------------------
            # Display Result
            # -----------------------------

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

            st.error(
                "AI returned an invalid JSON response. "
                "Please try again."
            )


# -----------------------------
# History
# -----------------------------
# -----------------------------
# History
# -----------------------------

st.divider()

st.subheader("Recent Analyses")

cursor.execute("""
SELECT
    id,
    erp_system,
    error,
    error_meaning,
    possible_causes,
    what_to_check,
    suggested_resolution,
    created_at
FROM history
ORDER BY id DESC
LIMIT 5
""")

history = cursor.fetchall()

if history:

    for item in history:

        record_id = item[0]
        record_erp = item[1]
        record_error = item[2]
        record_meaning = item[3]
        record_causes = json.loads(item[4])
        record_checks = json.loads(item[5])
        record_resolution = item[6]
        record_created_at = item[7]

        with st.expander(
            f"{record_erp} — {record_error}"
        ):

            st.caption(
                f"Analysis ID: {record_id} | {record_created_at}"
            )

            st.markdown("### Error Meaning")
            st.write(record_meaning)

            st.markdown("### Possible Causes")

            for cause in record_causes:
                st.write(f"• {cause}")

            st.markdown("### What to Check")

            for check in record_checks:
                st.write(f"• {check}")

            st.markdown("### Suggested Resolution")
            st.write(record_resolution)

else:

    st.write("No analysis history yet.")


connection.close()