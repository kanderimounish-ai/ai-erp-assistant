import os
from io import BytesIO

import streamlit as st
from ollama import embed
from pypdf import PdfReader


EMBEDDING_MODEL = "nomic-embed-text"


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
# TEXT CHUNKING
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
        chunks=chunks,
        source_name=os.path.basename(file_name),
        page_number=None
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
# TXT FILE EXTRACTION
# =========================================================

def extract_txt_document(
    file_bytes,
    source_name
):
    try:
        content = file_bytes.decode(
            "utf-8"
        )

    except UnicodeDecodeError:
        return []

    chunks = chunk_text(content)

    return create_embeddings(
        chunks=chunks,
        source_name=source_name,
        page_number=None
    )


# =========================================================
# PDF FILE EXTRACTION
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

    all_chunks = []

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

        page_embeddings = (
            create_embeddings(
                chunks=chunks,
                source_name=source_name,
                page_number=page_number
            )
        )

        all_chunks.extend(
            page_embeddings
        )

    return all_chunks


# =========================================================
# UPLOADED DOCUMENT EMBEDDINGS
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


def retrieve_uploaded_knowledge(
    file_bytes,
    file_type,
    source_name,
    user_error
):
    document_data = (
        load_uploaded_embeddings(
            file_bytes,
            file_type,
            source_name
        )
    )

    return search_embeddings(
        document_data,
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

    query_response = embed(
        model=EMBEDDING_MODEL,
        input=user_error
    )

    query_vector = (
        query_response["embeddings"][0]
    )

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

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    top_results = results[:3]

    context_parts = []
    sources = []

    for index, result in enumerate(
        top_results,
        start=1
    ):
        source_label = result["source"]

        if result["page"] is not None:
            source_label += (
                f" | Page {result['page']}"
            )

        context_parts.append(
            f"[Source {index}: {source_label}]\n"
            f"{result['text']}"
        )

        sources.append(
            {
                "number": index,
                "source": result["source"],
                "page": result["page"],
                "similarity": result["similarity"],
                "excerpt": result["text"]
            }
        )

    context = "\n\n---\n\n".join(
        context_parts
    )

    return {
        "context": context,
        "sources": sources
    }