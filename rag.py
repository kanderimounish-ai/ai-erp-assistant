import os
from io import BytesIO

import streamlit as st
from ollama import embed
from pypdf import PdfReader


EMBEDDING_MODEL = "nomic-embed-text"

MIN_SIMILARITY = 0.45
MAX_SCORE_GAP = 0.10
MAX_CONTEXT_CHUNKS = 5
MAX_UNIQUE_SOURCES = 3


# =========================================================
# COSINE SIMILARITY
# =========================================================

def cosine_similarity(vector1, vector2):
    dot_product = sum(
        a * b
        for a, b in zip(vector1, vector2)
    )

    magnitude1 = sum(
        a * a
        for a in vector1
    ) ** 0.5

    magnitude2 = sum(
        b * b
        for b in vector2
    ) ** 0.5

    if magnitude1 == 0 or magnitude2 == 0:
        return 0

    return dot_product / (
        magnitude1 * magnitude2
    )


# =========================================================
# CHUNK TEXT
# =========================================================

def chunk_text(
    text,
    chunk_size=180,
    overlap=30
):
    words = text.split()

    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size

        chunk = " ".join(
            words[start:end]
        )

        chunks.append(chunk)

        if end >= len(words):
            break

        start = end - overlap

    return chunks


# =========================================================
# CREATE EMBEDDINGS
# =========================================================

def create_embeddings(
    chunks,
    source_name,
    page_number=None
):
    embedded_chunks = []

    for chunk in chunks:
        response = embed(
            model=EMBEDDING_MODEL,
            input=chunk
        )

        embedded_chunks.append(
            {
                "text": chunk,
                "embedding": response["embeddings"][0],
                "source": source_name,
                "page": page_number
            }
        )

    return embedded_chunks


# =========================================================
# STATIC KNOWLEDGE BASE
# =========================================================

@st.cache_data
def load_knowledge_embeddings(
    erp_system,
    file_modified_time
):
    file_name = (
        f"knowledge_base/"
        f"{erp_system.lower()}.txt"
    )

    try:
        with open(
            file_name,
            "r",
            encoding="utf-8"
        ) as file:
            content = file.read()

    except FileNotFoundError:
        return []

    chunks = chunk_text(content)

    return create_embeddings(
        chunks,
        os.path.basename(file_name)
    )


def retrieve_knowledge(
    erp_system,
    user_error
):
    file_name = (
        f"knowledge_base/"
        f"{erp_system.lower()}.txt"
    )

    if not os.path.exists(file_name):
        return {
            "context": "",
            "sources": []
        }

    modified_time = os.path.getmtime(
        file_name
    )

    document_data = load_knowledge_embeddings(
        erp_system,
        modified_time
    )

    return search_embeddings(
        document_data,
        user_error
    )


# =========================================================
# TXT EXTRACTION
# =========================================================

def extract_txt_document(
    file_bytes,
    source_name
):
    try:
        text = file_bytes.decode(
            "utf-8"
        )

    except UnicodeDecodeError:
        return []

    chunks = chunk_text(text)

    return create_embeddings(
        chunks,
        source_name
    )


# =========================================================
# PDF EXTRACTION
# =========================================================

def extract_pdf_document(
    file_bytes,
    source_name
):
    try:
        reader = PdfReader(
            BytesIO(file_bytes)
        )

    except Exception:
        return []

    document_chunks = []

    for page_index, page in enumerate(
        reader.pages
    ):
        page_text = (
            page.extract_text() or ""
        )

        if not page_text.strip():
            continue

        page_number = page_index + 1

        chunks = chunk_text(
            page_text
        )

        page_data = create_embeddings(
            chunks,
            source_name,
            page_number
        )

        document_chunks.extend(
            page_data
        )

    return document_chunks


# =========================================================
# CACHE UPLOADED DOCUMENT
# =========================================================

@st.cache_data
def load_uploaded_embeddings(
    file_bytes,
    file_type,
    source_name
):
    if file_type == "txt":
        return extract_txt_document(
            file_bytes,
            source_name
        )

    if file_type == "pdf":
        return extract_pdf_document(
            file_bytes,
            source_name
        )

    return []


# =========================================================
# MULTIPLE DOCUMENT RETRIEVAL
# =========================================================

def retrieve_multiple_documents(
    documents,
    user_error
):
    all_document_data = []

    for document in documents:
        document_data = (
            load_uploaded_embeddings(
                document["bytes"],
                document["type"],
                document["name"]
            )
        )

        all_document_data.extend(
            document_data
        )

    return search_embeddings(
        all_document_data,
        user_error
    )


# =========================================================
# SEMANTIC SEARCH
# =========================================================

def search_embeddings(
    document_data,
    user_error
):
    if not document_data:
        return {
            "context": "",
            "sources": []
        }

    # -----------------------------------------------------
    # Create embedding for user's query
    # -----------------------------------------------------

    query_response = embed(
        model=EMBEDDING_MODEL,
        input=user_error
    )

    query_vector = (
        query_response["embeddings"][0]
    )


    # -----------------------------------------------------
    # Compare query against every document chunk
    # -----------------------------------------------------

    results = []

    for item in document_data:
        similarity = cosine_similarity(
            query_vector,
            item["embedding"]
        )

        results.append(
            {
                "similarity": similarity,
                "text": item["text"],
                "source": item["source"],
                "page": item["page"]
            }
        )


    # -----------------------------------------------------
    # Best results first
    # -----------------------------------------------------

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    if not results:
        return {
            "context": "",
            "sources": []
        }


    # -----------------------------------------------------
    # RELEVANCE FILTER
    #
    # Example:
    #
    # best result = 0.71
    #
    # MAX_SCORE_GAP = 0.10
    #
    # threshold = 0.61
    #
    # Results far below the best match are rejected.
    # -----------------------------------------------------

    best_score = results[0]["similarity"]

    dynamic_threshold = max(
        MIN_SIMILARITY,
        best_score - MAX_SCORE_GAP
    )

    relevant_results = [
        result
        for result in results
        if result["similarity"] >= dynamic_threshold
    ]


    # -----------------------------------------------------
    # Limit number of chunks sent to LLM
    # -----------------------------------------------------

    relevant_results = (
        relevant_results[
            :MAX_CONTEXT_CHUNKS
        ]
    )


    if not relevant_results:
        return {
            "context": "",
            "sources": []
        }


    # -----------------------------------------------------
    # BUILD AI CONTEXT
    #
    # Multiple chunks from the same document are okay here.
    # AI benefits from having all relevant text.
    # -----------------------------------------------------

    context_parts = []

    for index, result in enumerate(
        relevant_results,
        start=1
    ):
        source_label = result["source"]

        if result["page"] is not None:
            source_label += (
                f" | Page {result['page']}"
            )

        context_parts.append(
            f"[Evidence {index}: {source_label}]\n"
            f"{result['text']}"
        )

    context = "\n\n---\n\n".join(
        context_parts
    )


    # -----------------------------------------------------
    # DEDUPLICATE DISPLAY SOURCES
    #
    # Same PDF + same page should appear once in UI.
    # -----------------------------------------------------

    unique_sources = []

    seen_sources = set()

    for result in relevant_results:
        source_key = (
            result["source"],
            result["page"]
        )

        if source_key in seen_sources:
            continue

        seen_sources.add(
            source_key
        )

        unique_sources.append(
            {
                "number":
                    len(unique_sources) + 1,

                "source":
                    result["source"],

                "page":
                    result["page"],

                "similarity":
                    result["similarity"],

                "excerpt":
                    result["text"]
            }
        )

        if (
            len(unique_sources)
            >= MAX_UNIQUE_SOURCES
        ):
            break


    return {
        "context": context,
        "sources": unique_sources
    }