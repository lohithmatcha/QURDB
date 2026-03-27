import streamlit as st
import pandas as pd
from langchain_helper import get_few_shot_db_chain, format_database_result
from visualization_helper import format_with_chart
import re
from decimal import Decimal
import time

# Page configuration
st.set_page_config(
    page_title="QurdDB - Database Q&A",
    page_icon="🗄",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': "https://github.com/your-repo/issues",
        'About': "# QurdDB - Making databases accessible to everyone"
    }
)

# Custom CSS for modern, professional styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
        opacity: 0.3;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 3.5rem;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        position: relative;
        z-index: 1;
    }
    
    .main-header p {
        margin: 1rem 0 0 0;
        font-size: 1.3rem;
        opacity: 0.9;
        font-family: 'Inter', sans-serif;
        position: relative;
        z-index: 1;
    }
    
    .question-section {
        background: #ffffff;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        border: 1px solid #e9ecef;
    }
    
    .answer-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        padding: 3rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
        border: 1px solid #e9ecef;
        position: relative;
        overflow: hidden;
    }
    
    .answer-section::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    .answer-text {
        font-size: 2rem;
        font-weight: 600;
        color: #2c3e50;
        text-align: center;
        margin: 0;
        font-family: 'Inter', sans-serif;
        line-height: 1.4;
    }
    
    .success-badge {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .example-question {
        background: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
        font-family: 'Inter', sans-serif;
    }
    
    .example-question:hover {
        background: #667eea;
        color: white;
        border-color: #667eea;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stTextInput > div > div > input {
        font-size: 1.2rem;
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #e9ecef;
        font-family: 'Inter', sans-serif;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .sidebar .sidebar-content {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    }
    
    .metric-value {
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        font-family: 'Inter', sans-serif;
    }
    
    .metric-label {
        font-size: 1.1rem;
        opacity: 0.9;
        margin: 0.5rem 0 0 0;
        font-family: 'Inter', sans-serif;
    }
    
    .loading-spinner {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
    }
    
    .spinner {
        width: 40px;
        height: 40px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

# Main container
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🗄 QurdDB</h1>
    <p>Simplifying database access through natural language queries - Type or Speak!</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with project info
with st.sidebar:
    st.markdown("## 🚀 About QurdDB")
    st.markdown("""
    *QurdDB* is an intelligent database interface that allows you to:
    
    • Ask questions in natural language
    • **Speak your questions** 🎤
    • Get instant database insights
    • No SQL knowledge required
    • Clean, readable results
    
    Simply type or speak your question and get answers from your database!
    """)
    
    st.markdown("## 📊 Database Features")
    st.markdown("""
    - *T-Shirt Inventory Management*
    - *Sales Analytics*
    - *Stock Tracking*
    - *Revenue Calculations*
    - *Discount Analysis*
    """)
    
    st.markdown("## 🎤 Voice Input")
    st.markdown("""
    Click the microphone button to record your question!
    
    **Supported Browsers:**
    - Chrome ✅
    - Edge ✅
    - Safari ✅
    - Firefox ⚠️ (limited support)
    
    **Note:** Voice input works best with clear pronunciation.
    """)

# Initialize session state
if 'selected_question' not in st.session_state:
    st.session_state.selected_question = ""

# Main content area
st.markdown('<div class="question-section">', unsafe_allow_html=True)
st.markdown("## 💬 Ask Your Question")

# Voice input section
col1, col2 = st.columns([2, 1])

with col1:
    # Question input
    question = st.text_input(
        "What would you like to know about your t-shirt database?",
        placeholder="e.g., How many Nike t-shirts do we have in stock?",
        value=st.session_state.selected_question,
        key="question_input"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🎤 Voice Input")
    
    # Custom HTML for speech recognition
    speech_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .mic-button {
                padding: 15px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 30px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                transition: all 0.3s ease;
            }
            .mic-button:hover {
                transform: scale(1.05);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
            }
            .mic-button:disabled {
                opacity: 0.7;
                cursor: not-allowed;
            }
            .status {
                margin-top: 15px;
                font-weight: bold;
                font-size: 14px;
            }
            .transcript {
                margin-top: 10px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                display: none;
            }
            .transcript-text {
                margin-top: 8px;
                color: #667eea;
                font-weight: 600;
                font-size: 15px;
            }
            .copy-btn {
                padding: 8px 16px;
                background: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 10px;
                font-weight: 600;
                display: none;
            }
            .copy-btn:hover {
                background: #218838;
            }
        </style>
    </head>
    <body>
        <div style="text-align: center; padding: 15px;">
            <button id="micBtn" class="mic-button" onclick="startRecognition()">
                🎙️ Click to Record
            </button>
            <div id="status" class="status" style="color: #666;">Ready to record</div>
            <div id="transcript" class="transcript">
                <strong>📝 Your Question:</strong>
                <div id="transcript-text" class="transcript-text"></div>
            </div>
            <button id="copyBtn" class="copy-btn" onclick="copyToClipboard()">
                📋 Copy to Clipboard
            </button>
        </div>

        <script>
            let transcriptValue = '';
            
            function startRecognition() {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                
                if (!SpeechRecognition) {
                    document.getElementById('status').textContent = '❌ Not supported. Use Chrome, Edge, or Safari.';
                    document.getElementById('status').style.color = 'red';
                    return;
                }

                const recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';

                const btn = document.getElementById('micBtn');
                const status = document.getElementById('status');
                const transcriptDiv = document.getElementById('transcript');
                const transcriptText = document.getElementById('transcript-text');
                const copyBtn = document.getElementById('copyBtn');
                
                btn.disabled = true;
                btn.innerHTML = '🔴 Recording...';
                status.textContent = '🎤 Listening... Speak now!';
                status.style.color = '#FF0000';
                transcriptDiv.style.display = 'none';
                copyBtn.style.display = 'none';

                recognition.onresult = function(event) {
                    transcriptValue = event.results[0][0].transcript;
                    status.textContent = '✅ Transcribed successfully!';
                    status.style.color = '#28a745';
                    transcriptText.textContent = transcriptValue;
                    transcriptDiv.style.display = 'block';
                    copyBtn.style.display = 'inline-block';
                    btn.disabled = false;
                    btn.innerHTML = '🎙️ Record Again';
                };

                recognition.onerror = function(event) {
                    status.textContent = '❌ Error: ' + event.error;
                    status.style.color = 'red';
                    btn.disabled = false;
                    btn.innerHTML = '🎙️ Click to Record';
                };

                recognition.onend = function() {
                    if (btn.disabled) {
                        btn.disabled = false;
                        btn.innerHTML = '🎙️ Click to Record';
                    }
                };

                recognition.start();
            }
            
            function copyToClipboard() {
                navigator.clipboard.writeText(transcriptValue).then(function() {
                    alert('Copied! Paste it into the question box above.');
                }).catch(function(err) {
                    // Fallback for older browsers
                    const textArea = document.createElement('textarea');
                    textArea.value = transcriptValue;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    alert('Copied! Paste it into the question box above.');
                });
            }
        </script>
    </body>
    </html>
    """
    
    # Render the component
    import streamlit.components.v1 as components
    components.html(speech_html, height=280)
    
    # Instructions
    st.markdown("---")
    st.markdown("**💡 How to use:**")
    st.markdown("""
    1. Click the 🎙️ button above
    2. **Allow microphone** when prompted
    3. Speak your question clearly
    4. Click 📋 to copy the text
    5. **Paste it** into the question box on the left
    """)
    st.info("**Supported browsers:** Chrome, Edge, Safari")

# Example questions
st.markdown("## 💡 Example Questions")
example_questions = [
    "How many Nike t-shirts do we have in stock?",
    "What's the average price of white t-shirts?",
    "Which brand has the most t-shirts?",
    "What's the total revenue from all S-size t-shirts?",
    "How many red t-shirts do we have?"
]

cols = st.columns(2)
for i, example in enumerate(example_questions):
    with cols[i % 2]:
        if st.button(f"💬 {example}", key=f"example_{i}"):
            st.session_state.selected_question = example
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Process question and display results
if question:
    # Create a custom loading animation
    with st.spinner("🔍 Analyzing your question and querying the database..."):
        try:
            # Get the database chain
            chain = get_few_shot_db_chain()
            
            # Execute the query
            raw_result = chain.run(question)
            
            # Show processing steps
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🔍 Executing database query...")
            progress_bar.progress(25)
            time.sleep(0.5)
            
            status_text.text("🤖 Creating intelligent visualization...")
            progress_bar.progress(50)
            
            # Format the result using LLM
            formatted_response = format_database_result(raw_result, question)
            
            # Create visualization
            vis_result = format_with_chart(question, raw_result)
            
            status_text.text("✨ Finalizing response...")
            progress_bar.progress(75)
            time.sleep(0.5)
            
            progress_bar.progress(100)
            status_text.text("✅ Complete!")
            time.sleep(0.5)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Display the formatted response
            st.markdown("## 📊 Answer")
            st.markdown(f"""
            <div class="answer-section">
                <div class="success-badge">
                    ✅ Query executed successfully!
                </div>
                <p class="answer-text">{formatted_response}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display visualization if available
            has_chart = vis_result and vis_result.get('chart') is not None
            has_table = vis_result and vis_result.get('table_data') is not None
            is_single_value = vis_result and vis_result.get('metadata', {}).get('is_single_value')
            
            visualization_displayed = False
            
            if has_chart:
                st.markdown("### 📈 Visual Representation")
                try:
                    st.plotly_chart(vis_result['chart'], use_container_width=True)
                    visualization_displayed = True
                except Exception as viz_error:
                    st.error(f"Error displaying chart: {viz_error}")
                    st.write(vis_result.get('error', 'No error message'))
            
            if not visualization_displayed and has_table:
                st.markdown("### 📋 Tabular Data")
                st.dataframe(vis_result['table_data'], use_container_width=True)
                visualization_displayed = True
            
            if not visualization_displayed and is_single_value:
                st.markdown("### 📊 Result")
                st.markdown(f"""
                <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px;">
                    <h1 style="color: white; font-size: 4rem; margin: 0;">{vis_result['metadata'].get('value', 'N/A')}</h1>
                    <p style="color: white; opacity: 0.9; margin: 1rem 0 0 0;">Total Count / Value</p>
                </div>
                """, unsafe_allow_html=True)
                visualization_displayed = True
            
            # If nothing was displayed
            if not visualization_displayed:
                # Try to at least show something useful
                if vis_result and 'error' in vis_result:
                    st.error(f"Could not create visualization: {vis_result.get('error')}")
            
            # Show the original question for context
            st.markdown(f"""
            <div class="question-section">
                <p style="margin: 0; font-size: 1.1rem; color: #6c757d;"><strong>Question:</strong> {question}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Minimal debug section
            with st.expander("🔍 Debug Info"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Raw Database Result:**")
                    st.code(str(raw_result)[:200] + "..." if len(str(raw_result)) > 200 else str(raw_result))
                with col2:
                    st.write("**Visualization:**")
                    st.code(f"Type: {vis_result.get('chart_type', 'N/A')}")
                    st.code(f"Created: {vis_result.get('chart') is not None}")
                    if vis_result.get('error'):
                        st.error(f"Error: {vis_result.get('error')}")
            
            # Clear the selected question after processing
            st.session_state.selected_question = ""
                
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ Error processing your question: {error_msg}")
            
            # Provide specific help based on error type
            if "SQL syntax" in error_msg or "syntax" in error_msg.lower():
                st.info("💡 This appears to be a SQL syntax error. Try rephrasing your question more simply.")
            elif "connection" in error_msg.lower() or "database" in error_msg.lower():
                st.info("💡 Database connection issue. Please check if your database is running.")
            elif "column" in error_msg.lower() or "table" in error_msg.lower():
                st.info("💡 This might be a database schema issue. Try asking about different data.")
            else:
                st.info("💡 Try rephrasing your question or check if the database connection is working.")

# Close main container
st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; color: #6c757d; padding: 2rem; font-family: 'Inter', sans-serif;">
    <p style="margin: 0; font-size: 0.9rem;">Built with ❤ using Streamlit and LangChain</p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; opacity: 0.8;">QurdDB - Making databases accessible to everyone</p>
</div>
""", unsafe_allow_html=True)