import json
from ollama import chat


def analyze_error(
    erp_system,
    error,
    retrieved_knowledge
):

    prompt = f"""
You are an experienced {erp_system} ERP support analyst.

The user received this ERP error:

{error}

RELEVANT DOCUMENTATION:

{retrieved_knowledge}

INSTRUCTIONS:

Use the retrieved documentation when relevant.

If the documentation is insufficient,
you may use general ERP knowledge.

Do not invent system-specific facts.

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

    "suggested_resolution":
        "Practical resolution"
}}

Do not return markdown.

Do not return text before or after JSON.
"""

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

    return json.loads(
        response.message.content
    )