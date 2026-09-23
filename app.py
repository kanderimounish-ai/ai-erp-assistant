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
    "Select your ERP system, upload optional documentation, "
    "paste an ERP error, and AI will help troubleshoot it."
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
# DOCUMENT UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    "Upload ERP documentation (optional)",
    type=[
        "txt",
        "pdf"
    ]
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

            # =========================================
            # RETRIEVAL
            # =========================================

            with st.spinner(
                "Searching ERP documentation..."
            ):

                if uploaded_file:
                    file_bytes = (
                        uploaded_file.getvalue()
                    )

                    file_type = (
                        uploaded_file.name
                        .rsplit(".", 1)[-1]
                        .lower()
                    )

                    retrieval_result = (
                        retrieve_uploaded_knowledge(
                            file_bytes,
                            file_type,
                            uploaded_file.name,
                            error
                        )
                    )

                else:
                    retrieval_result = (
                        retrieve_knowledge(
                            erp_system,
                            error
                        )
                    )

                retrieved_knowledge = (
                    retrieval_result["context"]
                )

                retrieved_sources = (
                    retrieval_result["sources"]
                )


            # =========================================
            # AI ANALYSIS
            # =========================================

            with st.spinner(
                "Analyzing ERP error..."
            ):
                data = analyze_error(
                    erp_system,
                    error,
                    retrieved_knowledge
                )


            # =========================================
            # SAVE HISTORY
            # =========================================

            save_analysis(
                erp_system,
                error,
                data
            )


            # =========================================
            # DISPLAY ANSWER
            # =========================================

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

            possible_causes = data.get(
                "possible_causes",
                []
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

            checks = data.get(
                "what_to_check",
                []
            )

            if checks:
                for check in checks:
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
                data.get(
                    "suggested_resolution",
                    "No resolution returned."
                )
            )


            # =========================================
            # SOURCE CITATIONS
            # =========================================

            st.subheader(
                "Sources"
            )

            if retrieved_sources:
                for source in retrieved_sources:

                    source_text = (
                        f"Source {source['number']}: "
                        f"{source['source']}"
                    )

                    if source["page"] is not None:
                        source_text += (
                            f" — Page {source['page']}"
                        )

                    st.write(
                        f"**{source_text}**"
                    )

            else:
                st.write(
                    "No local documentation source was found. "
                    "The response may rely on general model knowledge."
                )


            # =========================================
            # RETRIEVED EVIDENCE
            # =========================================

            with st.expander(
                "View Retrieved Evidence"
            ):

                if retrieved_sources:

                    for source in retrieved_sources:

                        source_title = (
                            f"Source {source['number']} — "
                            f"{source['source']}"
                        )

                        if source["page"] is not None:
                            source_title += (
                                f" — Page {source['page']}"
                            )

                        st.markdown(
                            f"### {source_title}"
                        )

                        st.write(
                            source["excerpt"]
                        )

                        st.caption(
                            "Semantic similarity: "
                            f"{source['similarity']:.3f}"
                        )

                        st.divider()

                else:
                    st.write(
                        "No relevant evidence retrieved."
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