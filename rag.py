import os
import streamlit as st
from ollama import embed


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

    return dot_product / (magnitude1 * magnitude2)


@st.cache_data
def load_knowledge_embeddings(
    erp_system,
    file_modified_time
):

    file_name = (
        f"knowledge_base/{erp_system.lower()}.txt"
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

    paragraphs = [
        paragraph.strip()
        for paragraph in content.split("\n\n")
        if paragraph.strip()
    ]

    embedded_paragraphs = []

    for paragraph in paragraphs:

        response = embed(
            model="nomic-embed-text",
            input=paragraph
        )

        embedded_paragraphs.append(
            {
                "text": paragraph,
                "embedding":
                    response["embeddings"][0]
            }
        )

    return embedded_paragraphs


def retrieve_knowledge(
    erp_system,
    user_error
):

    file_name = (
        f"knowledge_base/{erp_system.lower()}.txt"
    )

    if not os.path.exists(file_name):
        return ""

    modified_time = os.path.getmtime(file_name)

    document_data = load_knowledge_embeddings(
        erp_system,
        modified_time
    )

    if not document_data:
        return ""

    query_response = embed(
        model="nomic-embed-text",
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
            (
                similarity,
                item["text"]
            )
        )

    results.sort(
        key=lambda item: item[0],
        reverse=True
    )

    top_results = results[:3]

    return "\n\n".join(
        text
        for score, text in top_results
    )