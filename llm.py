from dotenv import load_dotenv
import os
from google import genai
from Rag.search import returnable_chunk

def explain_code(code: str):
    load_dotenv()
    llm_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    input_text = returnable_chunk(code)

    interaction = llm_client.interactions.create(
        model="gemini-3.1-flash-lite",
        system_instruction="""
    Your task is to analyze ONLY the provided code and metadata and explain the code in detail.

    Instructions:
    - Carefully read the retrieved code before answering.
    - Use the metadata (function name, class name, parent, identifier, callee, line numbers, etc.) to provide additional context whenever relevant.
    - Explain:
    1. The purpose of the code.
    2. What each important statement or block of code does.
    3. The inputs and outputs, if applicable.
    4. Any important variables, methods, or classes involved.
    5. Any function calls made by the code and their role (if visible from the retrieved chunk or metadata).
    6. Any assumptions, edge cases, or notable implementation details.
    - If the retrieved chunk is a function, explain its parameters, return value, and overall workflow.
    - If it is a class, explain its purpose, important members, and relationships.
    - If it is another construct (variable declaration, import, etc.), explain its role within the program.
    - If the metadata indicates parent-child relationships or callees, incorporate that information naturally into the explanation.
    - If information required to fully explain the code is missing because it is outside the retrieved chunk, explicitly state that instead of making assumptions.
    - Do not invent code, variables, or functionality that are not present in the retrieved chunk or metadata.
    - Structure your explanation with clear headings and bullet points where appropriate.
    - Keep the explanation technically accurate and easy to understand.""",
        input=input_text
    )
    return interaction.output_text