import streamlit as st
import os
import json
import base64
import random
from utils import extract_text_from_pdf, extract_text_from_docx
from gemini_chain import get_summary_and_flashcards, chat_with_document
from components import flashcard

st.set_page_config(page_title="Note-ify", layout="centered")

# Load custom CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Custom styled header
st.markdown("""
<div class="main-header">
    <h1>📚 Note-ify (Gemini Edition)</h1>
    <h3>Summarize Notes & Generate Flashcards Using Gemini AI</h3>
</div>
""", unsafe_allow_html=True)

# Load saved chat history if it exists
if 'chat_history' not in st.session_state:
    try:
        try:
            if os.path.exists('chat_history.json'):
                with open('chat_history.json', 'r') as f:
                    st.session_state.chat_history = json.load(f)
        except Exception as e:
            st.error(f"Error loading chat history: {str(e)}")
        else:
            st.session_state.chat_history = []
    except Exception:
        st.session_state.chat_history = []

# Initialize session state variables
if 'flashcard_theme' not in st.session_state:
    st.session_state.flashcard_theme = "blue"
    
if 'flashcard_size' not in st.session_state:
    st.session_state.flashcard_size = "medium"
    
if 'flashcard_pairs' not in st.session_state:
    st.session_state.flashcard_pairs = []

# Callback functions for flashcard customization to prevent full app reruns
def update_flashcard_theme(theme):
    st.session_state.flashcard_theme = st.session_state.theme_selector
    


model_choice = st.selectbox("Choose Model:", ["Gemini 2.5(Most Accurate)", "Gemini 1.5(Most Faster)"], index=1)

uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])

if uploaded_file:
    file_path = os.path.join("temp", uploaded_file.name)
    os.makedirs("temp", exist_ok=True)
    try:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
    except Exception as e:
        st.error(f"Error saving uploaded file: {str(e)}")

    with st.spinner("🔍 Processing your document..."):
        if uploaded_file.name.endswith(".pdf"):
            text = extract_text_from_pdf(file_path)
        else:
            text = extract_text_from_docx(file_path)

        if len(text.strip()) == 0:
            st.error("⚠️ No text found in the document.")
        else:
            # Store the extracted text in session state for later use in chat
            st.session_state.document_text = text
            
            # Select model based on user choice
            model_name = "gemini-2.5-pro-exp-03-25" if model_choice == "Gemini 2.5(Most Accurate)" else "gemini-1.5-flash"
            st.session_state.model_name = model_name
            
            output = get_summary_and_flashcards(text, model_name)
            st.success("✅ Done! Here's what we found:")

            # Extract summary and flashcards sections more robustly
            summary_text = ""
            flashcards_text = ""
            
            # Handle different section header formats
            if "## Summary:" in output or "Summary:" in output:
                # Split by either Summary header format
                parts = output.split("## Summary:") if "## Summary:" in output else output.split("Summary:")
                if len(parts) > 1:
                    remaining_text = parts[1]
                    
                    # Find the flashcards section
                    if "## Flashcards:" in remaining_text:
                        summary_text, flashcards_text = remaining_text.split("## Flashcards:", 1)
                    elif "Flashcards:" in remaining_text:
                        summary_text, flashcards_text = remaining_text.split("Flashcards:", 1)
                    else:
                        # If no flashcards section found, assume all is summary
                        summary_text = remaining_text
                else:
                    # If no summary section found, check if there's a flashcards section
                    if "## Flashcards:" in output:
                        _, flashcards_text = output.split("## Flashcards:", 1)
                    elif "Flashcards:" in output:
                        _, flashcards_text = output.split("Flashcards:", 1)
            
            # Store summary in session state and display it
            if 'summary_text' not in st.session_state or 'current_document' not in st.session_state or st.session_state.current_document != uploaded_file.name:
                st.session_state.summary_text = summary_text.strip()
                st.session_state.current_document = uploaded_file.name
            
            # Add summary section with regenerate button
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown("### 📌 Summary")
            with col2:
                if st.button("🔄 Regenerate"):
                    with st.spinner("Regenerating summary..."):
                        new_output = get_summary_and_flashcards(text, st.session_state.model_name)
                        # Extract new summary
                        new_summary = ""
                        if "## Summary:" in new_output or "Summary:" in new_output:
                            parts = new_output.split("## Summary:") if "## Summary:" in new_output else new_output.split("Summary:")
                            if len(parts) > 1:
                                remaining_text = parts[1]
                                if "## Flashcards:" in remaining_text:
                                    new_summary = remaining_text.split("## Flashcards:", 1)[0]
                                elif "Flashcards:" in remaining_text:
                                    new_summary = remaining_text.split("Flashcards:", 1)[0]
                                else:
                                    new_summary = remaining_text
                        st.session_state.summary_text = new_summary.strip()
            
            # Display the summary
            st.markdown(st.session_state.summary_text)
            
            # Process flashcards section if we have content
            if flashcards_text.strip():
                    flashcard_pairs = []
                    current_q = ""
                    
                    # Split by lines and process each line
                    lines = flashcards_text.strip().split("\n")
                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        
                        # Skip empty lines
                        if not line:
                            i += 1
                            continue
                        
                        # Look for Q: pattern
                        if line.startswith("Q:"):
                            question = line.split(":", 1)[1].strip()
                            
                            # Look ahead for the answer
                            if i + 1 < len(lines) and lines[i + 1].strip().startswith("A:"):
                                answer = lines[i + 1].split(":", 1)[1].strip()
                                flashcard_pairs.append((question, answer))
                                i += 2  # Skip both Q and A lines
                            else:
                                i += 1  # Skip just Q line if no A follows
                        else:
                            i += 1  # Skip non-Q lines
                    
                    # Store flashcards in session state only if they don't exist or if we're processing a new document
                    if not st.session_state.flashcard_pairs or 'current_document' not in st.session_state or st.session_state.current_document != uploaded_file.name:
                        st.session_state.flashcard_pairs = flashcard_pairs
                        # Note: current_document is now set in the summary section
            
            # Display flashcards section (only if we have flashcards to show)
            if 'flashcard_pairs' in st.session_state and st.session_state.flashcard_pairs:
                st.markdown("### 💡 Flashcards")
                st.markdown("<div class='flashcard-container'>", unsafe_allow_html=True)
                
                # Flashcard customization options
                with st.expander("Customize Flashcards"):
                    col1, col2 = st.columns(2)
                    with col1:
                        # Use on_change callback to update theme without triggering a full rerun
                        if 'theme_selector' not in st.session_state:
                            st.session_state.theme_selector = st.session_state.flashcard_theme
                        
                        st.selectbox(
                            "Choose Theme:", 
                            ["blue", "green", "purple", "orange", "dark"],
                            index=["blue", "green", "purple", "orange", "dark"].index(st.session_state.theme_selector),
                            key="theme_selector",
                            on_change=update_flashcard_theme,
                            args=("theme_selector",)
                        )
                    
                    
                
                # Map sizes to dimensions
                size_map = {
                    "small": (250, 200),
                    "medium": (300, 250),
                    "large": (300, 300)
                }
                width, height = size_map[st.session_state.flashcard_size]
                
                # Display flashcards in a grid layout
                cols = st.columns(2)
                for idx, (question, answer) in enumerate(st.session_state.flashcard_pairs):
                    with cols[idx % 2]:
                        # Pass theme to flashcard component
                        flashcard(question, answer, width, height, theme=st.session_state.flashcard_theme)
                
                st.markdown("</div>", unsafe_allow_html=True)

                # --- QUIZ MODE ---
                st.markdown("---")
                st.markdown("### 📝 Quiz Mode: Test Yourself!")
                if 'quiz_active' not in st.session_state:
                    st.session_state.quiz_active = False
                if 'quiz_index' not in st.session_state:
                    st.session_state.quiz_index = 0
                if 'quiz_score' not in st.session_state:
                    st.session_state.quiz_score = 0
                if 'quiz_incorrect' not in st.session_state:
                    st.session_state.quiz_incorrect = 0
                if 'quiz_answers' not in st.session_state:
                    st.session_state.quiz_answers = []
                if 'quiz_feedback' not in st.session_state:
                    st.session_state.quiz_feedback = ""
                if 'quiz_completed' not in st.session_state:
                    st.session_state.quiz_completed = False
                if 'quiz_total' not in st.session_state:
                    st.session_state.quiz_total = len(st.session_state.flashcard_pairs)
                if 'quiz_questions' not in st.session_state:
                    st.session_state.quiz_questions = []
                    st.session_state.quiz_questions = []

                def reset_quiz():
                    st.session_state.quiz_active = True
                    st.session_state.quiz_index = 0
                    st.session_state.quiz_score = 0
                    st.session_state.quiz_incorrect = 0
                    st.session_state.quiz_answers = []
                    st.session_state.quiz_feedback = ""
                    st.session_state.quiz_completed = False
                    # Randomly select 5-10 questions from available flashcards
                    num_questions = min(random.randint(5, 10), len(st.session_state.flashcard_pairs))
                    selected_indices = random.sample(range(len(st.session_state.flashcard_pairs)), num_questions)
                    st.session_state.quiz_questions = [st.session_state.flashcard_pairs[i] for i in selected_indices]
                    st.session_state.quiz_total = len(st.session_state.quiz_questions)

                if not st.session_state.quiz_active or st.session_state.quiz_completed:
                    if st.button("Start Quiz", key="start_quiz"):
                        reset_quiz()

                if st.session_state.quiz_active and not st.session_state.quiz_completed:
                    q_idx = st.session_state.quiz_index
                    total = st.session_state.quiz_total
                    question, correct_answer = st.session_state.quiz_questions[q_idx]
                    st.markdown(f"**Question {q_idx+1} of {total}:**")
                    st.markdown(f"{question}")
                    
                    # Generate multiple choice options
                    options = [correct_answer]
                    # Get 3 random incorrect answers from other flashcards
                    other_answers = [a for q, a in st.session_state.flashcard_pairs if a != correct_answer]
                    if len(other_answers) >= 3:
                        options.extend(random.sample(other_answers, 3))
                    else:
                        # If we don't have enough other answers, use some generic options
                        while len(options) < 4:
                            options.append(f"Alternative Answer {len(options)}")
                    
                    # Shuffle the options and store them in session state
                    if f'options_{q_idx}' not in st.session_state:
                        random.shuffle(options)
                        st.session_state[f'options_{q_idx}'] = options
                    
                    # Display options as radio buttons
                    user_ans = st.radio(
                        "Choose your answer:",
                        st.session_state[f'options_{q_idx}'],
                        key=f"quiz_radio_{q_idx}"
                    )
                    
                    # Show feedback if exists
                    if st.session_state.quiz_feedback:
                        st.markdown(st.session_state.quiz_feedback, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        skip = st.button("Skip", key=f"skip_{q_idx}")
                    with col2:
                        submit = st.button("Submit Answer", key=f"submit_{q_idx}")
                    
                    if skip:
                        # Process skip and move to next question
                        st.session_state.quiz_answers.append({"question": question, "your_answer": "Skipped", "correct_answer": correct_answer, "is_correct": False, "skipped": True})
                        if q_idx + 1 < total:
                            st.session_state.quiz_index += 1
                            st.session_state.quiz_feedback = ""
                            st.rerun()
                        else:
                            st.session_state.quiz_completed = True
                            st.session_state.quiz_active = False
                    
                    if submit:
                        correct = user_ans.strip() == correct_answer.strip()
                        st.session_state.quiz_answers.append({"question": question, "your_answer": user_ans, "correct_answer": correct_answer, "is_correct": correct})
                        
                        if correct:
                            st.session_state.quiz_score += 1
                            st.session_state.quiz_feedback = "✅ Correct! Moving to next question..."
                            if q_idx + 1 < total:
                                st.session_state.quiz_index += 1
                                st.rerun()
                            else:
                                st.session_state.quiz_completed = True
                                st.session_state.quiz_active = False
                        else:
                            st.session_state.quiz_incorrect += 1
                            st.session_state.quiz_feedback = f"❌ Incorrect! The correct answer is: <span style='color: red'>{correct_answer}</span>"
                            st.rerun()
                if st.session_state.quiz_completed:
                    attempted = len([qa for qa in st.session_state.quiz_answers if not qa.get('skipped', False)])
                    skipped = len([qa for qa in st.session_state.quiz_answers if qa.get('skipped', False)])
                    st.success(f"Quiz Completed! Score: {st.session_state.quiz_score} / {attempted} (Skipped: {skipped})")
                    st.markdown("#### Review:")
                    for idx, qa in enumerate(st.session_state.quiz_answers):
                        if qa.get('skipped', False):
                            icon = "⏭️"
                            st.markdown(f"{icon} Q{idx+1}: {qa['question']} (Skipped)")
                            st.markdown(f"Correct answer: {qa['correct_answer']}")
                        else:
                            icon = "✅" if qa["is_correct"] else "❌"
                            st.markdown(f"{icon} Q{idx+1}: {qa['question']}")
                            st.markdown(f"Your answer: {qa['your_answer']}")
                            if not qa["is_correct"]:
                                st.markdown(f"Correct answer: {qa['correct_answer']}")
                    if st.button("Restart Quiz", key="restart_quiz"):
                        reset_quiz()
            # If we couldn't extract structured sections, try to parse the whole output
            if not summary_text.strip() and not flashcards_text.strip():
                st.text("Could not find structured sections in the output. Displaying raw output:")
                st.text(output)
                
                # Try to extract flashcards from the raw output as a fallback
                lines = output.strip().split("\n")
                extracted_pairs = []
                current_q = ""
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if (line.startswith("Q") and ":" in line) or line.lower().startswith("question:"):
                        q_part = line.split(":", 1)[1].strip() if ":" in line else line
                        current_q = q_part
                    elif (line.startswith("A") and ":" in line) or line.lower().startswith("answer:"):
                        a_part = line.split(":", 1)[1].strip() if ":" in line else line
                        if current_q:
                            extracted_pairs.append((current_q, a_part))
                            current_q = ""
                    elif current_q and not any(line.lower().startswith(p) for p in ["q", "question"]):
                        extracted_pairs.append((current_q, line))
                        current_q = ""
                
                # Store flashcards in session state only if they don't exist or if we're processing a new document
                if extracted_pairs and (not st.session_state.flashcard_pairs or 'current_document' not in st.session_state or st.session_state.current_document != uploaded_file.name):
                    st.session_state.flashcard_pairs = extracted_pairs
                    # Note: current_document is now set in the summary section
                    # No need to display flashcards here as they will be shown in the common section below

# Function to create a download link for text content
def get_download_link(content, filename, link_text):
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}" class="download-button">{link_text}</a>'
    return href

# Add download buttons for summary and flashcards if available
if 'summary_text' in st.session_state and st.session_state.summary_text:
    st.markdown("<div class='download-section'>", unsafe_allow_html=True)
    st.markdown("<h3>📋 Download Your Notes</h3>", unsafe_allow_html=True)
    st.markdown(
        get_download_link(st.session_state.summary_text, "summary.txt", "Download Summary"),
        unsafe_allow_html=True
    )
    
    # Create flashcards download if available
    if 'flashcard_pairs' in st.session_state and st.session_state.flashcard_pairs:
        flashcard_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in st.session_state.flashcard_pairs])
        st.markdown(
            get_download_link(flashcard_text, "flashcards.txt", "Download Flashcards"),
            unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)

# Add chat interface section if document is uploaded and processed
if uploaded_file and 'document_text' in st.session_state:
    st.markdown("---")
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    st.markdown("### 💬 Chat with your Document")
    st.markdown("Ask questions about the content of your document and get AI-powered answers.")
    
    # Clear chat history button
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        # Save empty chat history
        with open('chat_history.json', 'w') as f:
            json.dump([], f)
        st.rerun()
    
    # Display chat history with enhanced styling
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            # Display message content directly without HTML wrapper
            st.markdown(message["content"])
    
    # Chat input
    user_question = st.chat_input("Ask a question about your document...")
    if user_question:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_question)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chat_with_document(
                    st.session_state.document_text,
                    user_question,
                    st.session_state.model_name
                )
                
                # Try to highlight relevant context in the response
                highlighted_response = response
                doc_text = st.session_state.document_text.lower()
                
                # Find key phrases from the response that might be in the document
                words = response.split()
                for i in range(len(words) - 2):
                    phrase = " ".join(words[i:i+3]).lower()
                    # If this phrase appears in the document, highlight it
                    if phrase in doc_text and len(phrase) > 10:  # Only highlight substantial phrases
                        highlighted_phrase = f"<span class='highlight'>{' '.join(words[i:i+3])}</span>"
                        highlighted_response = highlighted_response.replace(' '.join(words[i:i+3]), highlighted_phrase)
                
                st.markdown(highlighted_response, unsafe_allow_html=True)
        
        # Add AI response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Save chat history to file
        with open('chat_history.json', 'w') as f:
            json.dump(st.session_state.chat_history, f)
    
    st.markdown("</div>", unsafe_allow_html=True)