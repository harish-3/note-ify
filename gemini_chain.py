import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyCT56Gh8mbyhe6jdDsaz5bd0ja7BZ4RxMg")  # Replace with your key

model = genai.GenerativeModel("gemini-2.5-pro-exp-03-25")

PROMPT = """
You are an assistant that helps students study. Based on the following academic note, perform two tasks:

## Summary:
Summarize the content in concise bullet points.

## Flashcards:
Create as many as possible clear Q&A flashcards to help revise this topic. Follow this EXACT format for each flashcard (including the Q and A prefixes):

Q: [Question]
A: [Answer]

Ensure each flashcard:
1. Has both a Q: prefix for questions and A: prefix for answers
2. Contains complete, clear questions and answers
3. Covers key concepts from the text

Notes:
{text}
"""

def get_summary_and_flashcards(text, model_name):
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(PROMPT.format(text=text))
    return response.text

# Chat with document prompt
CHAT_PROMPT = """
You are a helpful assistant that answers questions based on the provided document content.
Use the following document content to answer the user's question.
If the answer cannot be found in the document, politely say so and don't make up information.

Document content:
{text}

User question: {question}
"""

def chat_with_document(text, question, model_name):
    """Generate a response to a question based on document content"""
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(CHAT_PROMPT.format(text=text, question=question))
    return response.text