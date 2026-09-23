import json
import streamlit as st

from rag import (
    retrieve_knowledge,
    retrieve_uploaded_knowledge
)

from llm import analyze_error

from database import (
    initialize_database,
    save_analysis,
    get_recent_analyses
)


# =========================================================
# SETUP
# =========================================================

st.set_page_config(
    page_title="AI ERP Error Assistant",
    page_icon="🤖",
    layout="centered"
)

initialize_database()


# =========================================================
# HEADER
# =========================================================

st.title(
    "🤖 AI ERP Error Assistant"
)

st.write(
    "Select your ERP system, paste an error, "
    "and AI will help troubleshoot it."
)


# =========================================================
# ERP SYSTEM
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
# OPTIONAL DOCUMENT UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    "Upload ERP documentation (optional)",
    type=["txt"]
)

if uploaded_file:

    st.success(
        f"Document loaded: {uploaded_file.name}"
    )


# =========================================================
# ERROR INPUT
# =========================================================

error = st.text_area(
    "ERP Error",
    placeholder=(
        "Example: Invalid department reference"
    ),
    height=120
)


# =========================================================
# ANALYZE
# =========================================================

if st.button(
    "Analyze Error",
    type="primary"
):

    if not error.strip():

        st.warning(
            "Please enter an ERP error."
        )

    else:

        try:

            # -----------------------------------------
            # RETRIEVAL
            # -----------------------------------------

            with st.spinner(
                "Searching ERP knowledge..."
            ):

                if uploaded_file:

                    file_bytes = (
                        uploaded_file.getvalue()
                    )

                    retrieved_knowledge = (
                        retrieve_uploaded_knowledge(
                            file_bytes,
                            error
                        )
                    )

                    knowledge_source = (
                        uploaded_file.name
                    )

                else:

                    retrieved_knowledge = (
                        retrieve_knowledge(
                            erp_system,
                            error
                        )
                    )

                    knowledge_source = (
                        f"{erp_system} local knowledge base"
                    )


            # -----------------------------------------
            # AI ANALYSIS
            # -----------------------------------------

            with st.spinner(
                "Analyzing ERP error..."
            ):

                data = analyze_error(
                    erp_system,
                    error,
                    retrieved_knowledge
                )


            # -----------------------------------------
            # SAVE RESULT
            # -----------------------------------------

            save_analysis(
                erp_system,
                error,
                data
            )


            # -----------------------------------------
            # DISPLAY
            # -----------------------------------------

            st.success(
                "Analysis complete"
            )


            st.subheader(
                "Error Meaning"
            )

            st.info(
                data.get(
                    "error_meaning",
                    "No explanation returned."
                )
            )


            st.subheader(
                "Possible Causes"
            )

            for cause in data.get(
                "possible_causes",
                []
            ):

                st.write(
                    f"• {cause}"
                )


            st.subheader(
                "What to Check"
            )

            for check in data.get(
                "what_to_check",
                []
            ):

                st.write(
                    f"• {check}"
                )


            st.subheader(
                "Suggested Resolution"
            )

            st.success(
                data.get(
                    "suggested_resolution",
                    "No resolution returned."
                )
            )


            # -----------------------------------------
            # RETRIEVED KNOWLEDGE
            # -----------------------------------------

            with st.expander(
                "Retrieved Knowledge"
            ):

                st.caption(
                    f"Source: {knowledge_source}"
                )

                if retrieved_knowledge:

                    st.write(
                        retrieved_knowledge
                    )

                else:

                    st.write(
                        "No relevant documentation found."
                    )


        except json.JSONDecodeError:

            st.error(
                "The AI returned invalid JSON."
            )


        except Exception as e:

            st.error(
                f"Something went wrong: {e}"
            )


# =========================================================
# HISTORY
# =========================================================

st.divider()

st.subheader(
    "Recent Analyses"
)

history = get_recent_analyses()


if history:

    for item in history:

        (
            record_id,
            record_erp,
            record_error,
            record_meaning,
            causes_json,
            checks_json,
            record_resolution,
            created_at
        ) = item


        try:

            causes = json.loads(
                causes_json
            )

        except Exception:

            causes = []


        try:

            checks = json.loads(
                checks_json
            )

        except Exception:

            checks = []


        with st.expander(
            f"{record_erp} — {record_error}"
        ):

            st.caption(
                f"Analysis ID: {record_id} | "
                f"{created_at}"
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

            for cause in causes:

                st.write(
                    f"• {cause}"
                )


            st.markdown(
                "### What to Check"
            )

            for check in checks:

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