import json
import sqlite3
import streamlit as st
from ollama import chat


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI ERP Error Assistant",
    page_icon="🤖",
    layout="centered"
)


# =========================================================
# RAG - RETRIEVE KNOWLEDGE
# =========================================================

def retrieve_knowledge(erp_system, user_error):

    file_name = f"knowledge_base/{erp_system.lower()}.txt"

    try:
        with open(file_name, "r", encoding="utf-8") as file:
            content = file.read()

    except FileNotFoundError:
        return ""

    # Split documentation into paragraphs
    paragraphs = content.split("\n\n")

    # Convert user error into individual words
    error_words = set(user_error.lower().split())

    scored_paragraphs = []

    for paragraph in paragraphs:

        paragraph_words = set(paragraph.lower().split())

        # Find matching words
        score = len(
            error_words.intersection(paragraph_words)
        )

        if score > 0:
            scored_paragraphs.append(
                (score, paragraph)
            )

    # Highest matching paragraphs first
    scored_paragraphs.sort(
        key=lambda item: item[0],
        reverse=True
    )

    # Take top 3 relevant paragraphs
    top_results = scored_paragraphs[:3]

    retrieved_text = "\n\n".join(
        paragraph
        for score, paragraph in top_results
    )

    return retrieved_text


# =========================================================
# DATABASE SETUP
# =========================================================

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


# =========================================================
# APP HEADER
# =========================================================

st.title("🤖 AI ERP Error Assistant")

st.write(
    "Select your ERP system, paste an error, "
    "and AI will help explain and troubleshoot it."
)


# =========================================================
# ERP SYSTEM SELECTION
# =========================================================

erp_system = st.selectbox(
    "Select ERP System",
    [
        "NetSuite",
        "Workday",
        "SAP",
        "Other"
    ]
)


# =========================================================
# ERROR INPUT
# =========================================================

error = st.text_area(
    "ERP Error",
    placeholder="Example: Invalid department reference",
    height=120
)


# =========================================================
# ANALYZE BUTTON
# =========================================================

if st.button(
    "Analyze Error",
    type="primary"
):

    if error.strip() == "":

        st.warning(
            "Please enter an ERP error."
        )

    else:

        # ---------------------------------------------
        # Retrieve relevant documentation
        # ---------------------------------------------

        retrieved_knowledge = retrieve_knowledge(
            erp_system,
            error
        )

        # ---------------------------------------------
        # Build AI prompt
        # ---------------------------------------------

        prompt = f"""
You are an experienced {erp_system} ERP support analyst.

The user received this ERP error:

{error}


RELEVANT DOCUMENTATION FROM THE LOCAL KNOWLEDGE BASE:

{retrieved_knowledge}


INSTRUCTIONS:

Use the documentation above when it is relevant.

If the documentation does not contain enough information,
you may use general ERP knowledge.

Do not invent system-specific facts if you are unsure.

Return ONLY valid JSON.

Use exactly this JSON structure:

{{
    "error_meaning": "Short and clear explanation of the error",

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

    "suggested_resolution":
        "Practical recommendation for resolving the issue"
}}

Do not return markdown.

Do not return text before or after the JSON.
"""

        # ---------------------------------------------
        # Call Local Ollama AI
        # ---------------------------------------------

        try:

            with st.spinner(
                "Analyzing ERP error..."
            ):

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

            # ---------------------------------------------
            # Convert AI JSON into Python dictionary
            # ---------------------------------------------

            data = json.loads(
                response.message.content
            )

            # ---------------------------------------------
            # Read individual fields
            # ---------------------------------------------

            error_meaning = data.get(
                "error_meaning",
                "No explanation returned."
            )

            possible_causes = data.get(
                "possible_causes",
                []
            )

            what_to_check = data.get(
                "what_to_check",
                []
            )

            suggested_resolution = data.get(
                "suggested_resolution",
                "No resolution returned."
            )

            # ---------------------------------------------
            # Save analysis into database
            # ---------------------------------------------

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

                    error_meaning,

                    json.dumps(
                        possible_causes
                    ),

                    json.dumps(
                        what_to_check
                    ),

                    suggested_resolution
                )
            )

            connection.commit()

            # ---------------------------------------------
            # Display AI Result
            # ---------------------------------------------

            st.success(
                "Analysis complete"
            )

            st.subheader(
                "Error Meaning"
            )

            st.info(
                error_meaning
            )


            st.subheader(
                "Possible Causes"
            )

            if possible_causes:

                for cause in possible_causes:

                    st.write(
                        f"• {cause}"
                    )

            else:

                st.write(
                    "No possible causes returned."
                )


            st.subheader(
                "What to Check"
            )

            if what_to_check:

                for check in what_to_check:

                    st.write(
                        f"• {check}"
                    )

            else:

                st.write(
                    "No troubleshooting checks returned."
                )


            st.subheader(
                "Suggested Resolution"
            )

            st.success(
                suggested_resolution
            )


            # ---------------------------------------------
            # Show retrieved RAG knowledge
            # ---------------------------------------------

            with st.expander(
                "Retrieved Knowledge"
            ):

                if retrieved_knowledge:

                    st.write(
                        retrieved_knowledge
                    )

                else:

                    st.write(
                        "No matching documentation was found "
                        "in the local knowledge base."
                    )


        except json.JSONDecodeError:

            st.error(
                "The AI returned an invalid JSON response. "
                "Please try again."
            )


        except Exception as e:

            st.error(
                f"Something went wrong: {e}"
            )


# =========================================================
# HISTORY SECTION
# =========================================================

st.divider()

st.subheader(
    "Recent Analyses"
)


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

        record_created_at = item[7]


        try:

            record_causes = json.loads(
                item[4]
            )

        except Exception:

            record_causes = []


        try:

            record_checks = json.loads(
                item[5]
            )

        except Exception:

            record_checks = []


        record_resolution = item[6]


        with st.expander(
            f"{record_erp} — {record_error}"
        ):

            st.caption(
                f"Analysis ID: {record_id} | "
                f"{record_created_at}"
            )


            st.markdown(
                "### Error Meaning"
            )

            st.write(
                record_meaning
            )


            st.markdown(
                "### Possible Causes"
            )

            for cause in record_causes:

                st.write(
                    f"• {cause}"
                )


            st.markdown(
                "### What to Check"
            )

            for check in record_checks:

                st.write(
                    f"• {check}"
                )


            st.markdown(
                "### Suggested Resolution"
            )

            st.write(
                record_resolution
            )


else:

    st.write(
        "No analysis history yet."
    )


# =========================================================
# CLOSE DATABASE CONNECTION
# =========================================================

connection.close()