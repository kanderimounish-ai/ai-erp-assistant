import json
import streamlit as st

from rag import (
    retrieve_knowledge,
    retrieve_multiple_documents
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

st.title("🤖 AI ERP Error Assistant")

st.write(
    "Upload ERP documentation, paste an error, "
    "and AI will search the documents and help troubleshoot it."
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

uploaded_files = st.file_uploader(
    "Upload ERP documentation (optional)",
    type=["txt", "pdf"],
    accept_multiple_files=True,
    key="erp_documents"
)


# =========================================================
# KNOWLEDGE MODE
# =========================================================

if uploaded_files:

    st.success(
        f"{len(uploaded_files)} document(s) loaded"
    )

    st.info(
        "Knowledge Mode: Uploaded Documents"
    )

    with st.expander(
        "Uploaded Documents"
    ):
        for uploaded_file in uploaded_files:

            st.write(
                f"• {uploaded_file.name}"
            )

else:

    st.info(
        f"Knowledge Mode: Local {erp_system} Knowledge Base"
    )


# =========================================================
# ERROR INPUT
# =========================================================

error = st.text_area(
    "ERP Error",
    placeholder=(
        "Example: Vendor creation failed "
        "because company name already exists"
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

                # -------------------------------------
                # MODE 1: UPLOADED DOCUMENTS
                # -------------------------------------

                if len(uploaded_files) > 0:

                    documents = []

                    for uploaded_file in uploaded_files:

                        file_type = (
                            uploaded_file.name
                            .rsplit(".", 1)[-1]
                            .lower()
                        )

                        documents.append(
                            {
                                "name":
                                    uploaded_file.name,

                                "type":
                                    file_type,

                                "bytes":
                                    uploaded_file.getvalue()
                            }
                        )

                    retrieval_result = (
                        retrieve_multiple_documents(
                            documents,
                            error
                        )
                    )

                    retrieval_mode = (
                        "Uploaded Documents"
                    )


                # -------------------------------------
                # MODE 2: LOCAL KNOWLEDGE BASE
                # -------------------------------------

                else:

                    retrieval_result = (
                        retrieve_knowledge(
                            erp_system,
                            error
                        )
                    )

                    retrieval_mode = (
                        f"Local {erp_system} Knowledge Base"
                    )


                retrieved_knowledge = (
                    retrieval_result.get(
                        "context",
                        ""
                    )
                )

                retrieved_sources = (
                    retrieval_result.get(
                        "sources",
                        []
                    )
                )


            # =========================================
            # IMPORTANT:
            # DO NOT SILENTLY FALL BACK
            # =========================================

            if (
                uploaded_files
                and not retrieved_sources
            ):

                st.warning(
                    "The uploaded documents did not contain "
                    "a sufficiently relevant match. "
                    "The app will not silently use the local "
                    "knowledge base instead."
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
            # SAVE
            # =========================================

            save_analysis(
                erp_system,
                error,
                data
            )


            # =========================================
            # ANSWER
            # =========================================

            st.success(
                "Analysis complete"
            )

            st.caption(
                f"Knowledge source mode: {retrieval_mode}"
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
            # SOURCES
            # =========================================

            st.subheader(
                "Sources"
            )

            if retrieved_sources:

                for source in retrieved_sources:

                    source_label = (
                        f"Source {source['number']}: "
                        f"{source['source']}"
                    )

                    if source["page"] is not None:

                        source_label += (
                            f" — Page {source['page']}"
                        )

                    st.write(
                        f"**{source_label}**"
                    )

            else:

                if uploaded_files:

                    st.warning(
                        "No sufficiently relevant source "
                        "was found in the uploaded documents."
                    )

                else:

                    st.write(
                        "No relevant local source was found."
                    )


            # =========================================
            # EVIDENCE
            # =========================================

            with st.expander(
                "View Retrieved Evidence"
            ):

                if retrieved_sources:

                    for source in retrieved_sources:

                        title = (
                            f"Source {source['number']} — "
                            f"{source['source']}"
                        )

                        if source["page"] is not None:

                            title += (
                                f" — Page {source['page']}"
                            )

                        st.markdown(
                            f"### {title}"
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
                        "No evidence retrieved."
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