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
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles - Light Pastel Background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 50%, #f0f4f8 100%);
        min-height: 100vh;
        background-attachment: fixed;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main-container {
        background: #ffffff;
        backdrop-filter: blur(20px);
        border-radius: 25px;
        padding: 2.5rem;
        margin: 1.5rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        border: 1px solid #e1e8ed;
    }
    
    .main-header {
        background: linear-gradient(135deg, #e8f4f8 0%, #f0f8f4 50%, #f8f4e8 100%);
        padding: 3.5rem 2rem;
        border-radius: 25px;
        margin-bottom: 2.5rem;
        text-align: center;
        color: #1a1a1a;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
        border: 2px solid #d1e7e7;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="#1a1a1a" opacity="0.05"/><circle cx="75" cy="75" r="1" fill="#1a1a1a" opacity="0.05"/><circle cx="50" cy="10" r="0.5" fill="#1a1a1a" opacity="0.05"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
        opacity: 0.6;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 4rem;
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        position: relative;
        z-index: 1;
        color: #000000;
        text-shadow: none;
        letter-spacing: -1px;
    }
    
    .main-header p {
        margin: 1.2rem 0 0 0;
        font-size: 1.4rem;
        color: #333333;
        font-family: 'Inter', sans-serif;
        position: relative;
        z-index: 1;
        font-weight: 500;
    }
    
    .question-section {
        background: #f8f9fa;
        padding: 2.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border: 2px solid #e1e8ed;
        transition: all 0.3s ease;
    }
    
    .question-section:hover {
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
        border-color: #d1e7e7;
    }
    
    .answer-section {
        background: #ffffff;
        padding: 3rem;
        border-radius: 25px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.06);
        border: 2px solid #e1e8ed;
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
        background: linear-gradient(90deg, #a8d5e2 0%, #b8e6d3 50%, #d4e6c7 100%);
    }
    
    .answer-text-container {
        font-size: 1.1rem;
        font-weight: 400;
        color: #000000 !important;
        text-align: left;
        margin: 1.5rem 0;
        font-family: 'Inter', sans-serif;
        line-height: 1.8;
        padding: 1.5rem;
        background: #fafbfc;
        border-radius: 12px;
        border: 2px solid #e1e8ed;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    /* Style for answer area using a wrapper class */
    .answer-content-wrapper {
        background: #ffffff;
        padding: 2rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    /* Target Streamlit markdown elements directly - Dark Black */
    div[data-testid="stMarkdownContainer"] p {
        color: #000000 !important;
        font-size: 1.1rem !important;
        line-height: 1.8 !important;
        margin: 1rem 0 !important;
    }
    
    div[data-testid="stMarkdownContainer"] ul, 
    div[data-testid="stMarkdownContainer"] ol {
        color: #000000 !important;
        margin: 1rem 0 !important;
        padding-left: 2rem !important;
    }
    
    div[data-testid="stMarkdownContainer"] li {
        color: #000000 !important;
        margin: 0.6rem 0 !important;
        line-height: 1.7 !important;
    }
    
    div[data-testid="stMarkdownContainer"] strong,
    div[data-testid="stMarkdownContainer"] b {
        color: #000000 !important;
        font-weight: 700 !important;
    }
    
    /* Ensure all text in markdown containers is visible - Dark Black */
    div[data-testid="stMarkdownContainer"] {
        color: #000000 !important;
    }
    
    div[data-testid="stMarkdownContainer"] * {
        color: #000000 !important;
    }
    
    /* Override any light/white text colors - Force Black */
    div[data-testid="stMarkdownContainer"] p[style*="color"],
    div[data-testid="stMarkdownContainer"] li[style*="color"],
    div[data-testid="stMarkdownContainer"] span[style*="color"],
    div[data-testid="stMarkdownContainer"] div[style*="color"] {
        color: #000000 !important;
    }
    
    .success-badge {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        padding: 0.9rem 2rem;
        border-radius: 30px;
        font-weight: 600;
        font-size: 1rem;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
        border: 2px solid #b8e6c8;
    }
    
    .example-question {
        background: #f8f9fa;
        border: 2px solid #e1e8ed;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.6rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        color: #000000;
    }
    
    .example-question:hover {
        background: #e8f4f8;
        color: #000000;
        border-color: #a8d5e2;
        transform: translateY(-3px);
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
    }
    
    .stTextInput > div > div > input {
        font-size: 1.1rem;
        padding: 1.2rem;
        border-radius: 12px;
        border: 2px solid #e1e8ed;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
        color: #000000 !important;
        background: #ffffff !important;
        caret-color: #000000 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #a8d5e2;
        box-shadow: 0 0 0 4px rgba(168, 213, 226, 0.2);
        color: #000000 !important;
        background: #ffffff !important;
        caret-color: #000000 !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #6c757d !important;
    }
    
    /* Ensure cursor is visible in all input states */
    .stTextInput input,
    .stTextInput input:focus,
    .stTextInput input:active {
        caret-color: #000000 !important;
        color: #000000 !important;
    }
    
    .sidebar .sidebar-content {
        background: #ffffff;
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
        border: 2px solid #e1e8ed;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #e8f4f8 0%, #f0f8f4 100%);
        color: #000000;
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
        border: 2px solid #d1e7e7;
    }
    
    .metric-value {
        font-size: 4rem;
        font-weight: 800;
        margin: 0;
        font-family: 'Poppins', sans-serif;
        color: #000000;
        text-shadow: none;
    }
    
    .metric-label {
        font-size: 1.2rem;
        color: #333333;
        margin: 0.8rem 0 0 0;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
    }
    
    .visualization-container {
        background: #ffffff;
        padding: 2rem;
        border-radius: 20px;
        margin: 2rem 0;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
        border: 2px solid #e1e8ed;
    }
    
    .table-container {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #e1e8ed;
        overflow-x: auto;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #a8d5e2 0%, #b8e6d3 100%);
        color: #000000;
        border: 2px solid #90c5d4;
        border-radius: 12px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15);
        background: linear-gradient(135deg, #98c5d2 0%, #a8d6c3 100%);
        color: #000000;
    }
    
    /* Chart container styling */
    .js-plotly-plot {
        border-radius: 15px;
        overflow: hidden;
    }
    
    /* Loading spinner */
    .loading-spinner {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 3rem;
    }
    
    .spinner {
        width: 50px;
        height: 50px;
        border: 5px solid #f3f3f3;
        border-top: 5px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Section headers - Dark Black */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        color: #000000 !important;
    }
    
    /* All text should be dark */
    p, span, div, li, td, th {
        color: #1a1a1a !important;
    }
    
    /* Improve data frame styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #e1e8ed;
    }
    
    /* CRITICAL: Ensure all markdown text is visible - Dark Black */
    .element-container .stMarkdown,
    .element-container .stMarkdown p,
    .element-container .stMarkdown ul,
    .element-container .stMarkdown ol,
    .element-container .stMarkdown li,
    .element-container .stMarkdown div,
    .element-container .stMarkdown span {
        color: #000000 !important;
    }
    
    /* Force text visibility in answer area - Dark Black */
    .main-container .stMarkdown p,
    .main-container .stMarkdown ul,
    .main-container .stMarkdown ol,
    .main-container .stMarkdown li,
    .main-container .stMarkdown div,
    .main-container .stMarkdown span {
        color: #000000 !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    /* Override any inline styles that might set light/white color */
    .main-container .stMarkdown [style*="color: white"],
    .main-container .stMarkdown [style*="color:#fff"],
    .main-container .stMarkdown [style*="color:white"],
    .main-container .stMarkdown [style*="color: #ffffff"],
    .main-container .stMarkdown [style*="color:#ffffff"],
    .main-container .stMarkdown [style*="color: #f"],
    .main-container .stMarkdown [style*="color:light"],
    .main-container .stMarkdown [style*="color: gray"],
    .main-container .stMarkdown [style*="color:grey"] {
        color: #000000 !important;
    }
    
    /* Sidebar text */
    .sidebar .stMarkdown,
    .sidebar .stMarkdown p,
    .sidebar .stMarkdown li,
    .sidebar .stMarkdown ul {
        color: #000000 !important;
    }
    
    /* All Streamlit text elements */
    .stMarkdown, .stText, .stWrite {
        color: #000000 !important;
    }
    
    .stMarkdown p, .stMarkdown li, .stMarkdown ul, .stMarkdown ol {
        color: #000000 !important;
    }
    
    /* Chart title and text visibility - Force dark text */
    .js-plotly-plot .plotly .gtitle,
    .js-plotly-plot .plotly .xtitle,
    .js-plotly-plot .plotly .ytitle,
    .js-plotly-plot .plotly .legendtext,
    .js-plotly-plot .plotly .xtick text,
    .js-plotly-plot .plotly .ytick text {
        fill: #000000 !important;
        color: #000000 !important;
    }
    
    /* Ensure all Plotly text elements are dark */
    .js-plotly-plot text {
        fill: #000000 !important;
        color: #000000 !important;
    }
    
    /* Chart container background */
    .js-plotly-plot {
        background: #ffffff !important;
    }
    
    /* Custom Debug Info Collapsible - Light background, dark text */
    details.debug-info {
        margin: 1.5rem 0 !important;
        border: 2px solid #e1e8ed !important;
        border-radius: 8px !important;
        background: #f8f9fa !important;
        overflow: hidden !important;
    }
    
    details.debug-info summary {
        padding: 0.75rem 1rem !important;
        cursor: pointer !important;
        font-weight: 600 !important;
        color: #000000 !important;
        background: #f8f9fa !important;
        border-radius: 8px 8px 0 0 !important;
        user-select: none !important;
        font-size: 1rem !important;
        list-style: none !important;
    }
    
    details.debug-info summary::-webkit-details-marker {
        display: none !important;
    }
    
    details.debug-info summary::before {
        content: '▶ ' !important;
        display: inline-block !important;
        margin-right: 0.5rem !important;
        color: #000000 !important;
        transition: transform 0.3s !important;
    }
    
    details.debug-info[open] summary::before {
        transform: rotate(90deg) !important;
    }
    
    details.debug-info > div {
        padding: 1.5rem !important;
        background: #ffffff !important;
        border-top: 2px solid #e1e8ed !important;
        color: #000000 !important;
    }
    
    details.debug-info p,
    details.debug-info div,
    details.debug-info span,
    details.debug-info strong {
        color: #000000 !important;
        background: transparent !important;
    }
    
    details.debug-info pre,
    details.debug-info code {
        background: #f8f9fa !important;
        color: #000000 !important;
        border: 1px solid #e1e8ed !important;
        padding: 1rem !important;
        border-radius: 6px !important;
        overflow-x: auto !important;
        font-size: 0.85rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Main container
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🗄️ QurdDB</h1>
    <p>Your Intelligent Database Assistant - Ask Anything, Get Instant Insights!</p>
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
            
            # Display the formatted response in a single clean container
            st.markdown("## 📊 Answer")
            st.markdown("""
            <div style="background: #ffffff; padding: 2rem; border-radius: 12px; border: 2px solid #e1e8ed; margin: 1.5rem 0; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
                <div class="success-badge">
                    ✅ Query executed successfully!
                </div>
            """, unsafe_allow_html=True)
            # Use Streamlit's markdown which will be styled by our global CSS
            st.markdown(formatted_response)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display visualization if available
            has_chart = vis_result and vis_result.get('chart') is not None
            has_table = vis_result and vis_result.get('table_data') is not None
            is_single_value = vis_result and vis_result.get('metadata', {}).get('is_single_value')
            chart_type = vis_result.get('chart_type', '') if vis_result else ''
            
            # Handle single value display (metric card)
            if is_single_value:
                value = vis_result['metadata'].get('value', 'N/A')
                # Format the value
                if isinstance(value, (int, float)):
                    if value >= 1000:
                        value_str = f"{value:,.0f}"
                    elif isinstance(value, float):
                        value_str = f"{value:,.2f}"
                    else:
                        value_str = f"{value:,}"
                else:
                    value_str = str(value)
                
                st.markdown("### 📊 Result")
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{value_str}</div>
                    <div class="metric-label">Query Result</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Display chart if available
            if has_chart:
                st.markdown("### 📈 Visual Representation")
                st.markdown('<div class="visualization-container">', unsafe_allow_html=True)
                try:
                    # Display the chart
                    chart_fig = vis_result['chart']
                    if chart_fig:
                        st.plotly_chart(chart_fig, use_container_width=True, config={
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
                            'toImageButtonOptions': {
                                'format': 'png',
                                'filename': 'chart',
                                'height': 600,
                                'width': 1200,
                                'scale': 2
                            }
                        })
                except Exception as viz_error:
                    st.error(f"⚠️ Error displaying chart: {str(viz_error)}")
                    if vis_result.get('error'):
                        st.warning(f"Visualization error details: {vis_result.get('error')}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Display table if available (show table alongside chart or alone)
            if has_table:
                table_df = vis_result['table_data']
                if table_df is not None and not table_df.empty:
                    # Only show table header if we don't have a chart, or if it's explicitly a table type
                    if not has_chart or chart_type == 'table':
                        st.markdown("### 📋 Data Table")
                    else:
                        st.markdown("### 📋 Detailed Data")
                    
                    st.markdown('<div class="table-container">', unsafe_allow_html=True)
                    try:
                        # Display the dataframe with proper formatting
                        st.dataframe(
                            table_df,
                            use_container_width=True,
                            height=min(400, len(table_df) * 35 + 50),
                            hide_index=False
                        )
                    except Exception as table_error:
                        st.error(f"⚠️ Error displaying table: {str(table_error)}")
                        # Fallback to simple display
                        st.write(table_df)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Show error if visualization failed and nothing was displayed
            if not has_chart and not has_table and not is_single_value:
                if vis_result and 'error' in vis_result:
                    st.warning(f"⚠️ Could not create visualization: {vis_result.get('error')}")
                    # Try to show raw result as fallback
                    if raw_result:
                        st.info("Showing raw result:")
                        st.code(str(raw_result)[:500])
            
            # Show the original question for context
            st.markdown(f"""
            <div class="question-section">
                <p style="margin: 0; font-size: 1.1rem; color: #000000;"><strong>Question:</strong> {question}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Debug section - Custom HTML with forced light background and dark text
            import html
            raw_result_str = str(raw_result)[:300]
            raw_result_escaped = html.escape(raw_result_str)
            chart_type_escaped = html.escape(str(vis_result.get('chart_type', 'N/A')))
            chart_created = str(vis_result.get('chart') is not None)
            error_msg = html.escape(str(vis_result.get('error', ''))) if vis_result.get('error') else ''
            
            # Add inline style block to force colors
            st.markdown("""
            <style>
            details.debug-info-container,
            details.debug-info-container summary,
            details.debug-info-container div,
            details.debug-info-container p,
            details.debug-info-container pre,
            details.debug-info-container code,
            details.debug-info-container span,
            details.debug-info-container strong {
                color: #000000 !important;
                background-color: #f8f9fa !important;
            }
            details.debug-info-container[open] > div {
                background-color: #ffffff !important;
            }
            details.debug-info-container pre {
                background-color: #f8f9fa !important;
                color: #000000 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            debug_html = f"""
            <details class="debug-info-container" style="margin: 1.5rem 0; border: 2px solid #e1e8ed; border-radius: 8px; background: #f8f9fa;">
                <summary style="padding: 0.75rem 1rem; cursor: pointer; font-weight: 600; color: #000000 !important; background: #f8f9fa !important; border-radius: 8px; user-select: none; font-size: 1rem; list-style: none;">
                    🔍 Debug Info
                </summary>
                <div style="padding: 1.5rem; background: #ffffff !important; border-top: 2px solid #e1e8ed; color: #000000 !important;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; color: #000000 !important;">
                        <div>
                            <p style="color: #000000 !important; font-weight: 600; margin-bottom: 0.5rem; font-size: 1rem;">Raw Database Result:</p>
                            <pre style="background: #f8f9fa !important; padding: 1rem; border-radius: 6px; border: 1px solid #e1e8ed; overflow-x: auto; color: #000000 !important; font-size: 0.85rem; white-space: pre-wrap; word-wrap: break-word; max-height: 300px; overflow-y: auto; margin: 0;">{raw_result_escaped}{"..." if len(str(raw_result)) > 300 else ""}</pre>
                        </div>
                        <div>
                            <p style="color: #000000 !important; font-weight: 600; margin-bottom: 0.5rem; font-size: 1rem;">Visualization:</p>
                            <pre style="background: #f8f9fa !important; padding: 1rem; border-radius: 6px; border: 1px solid #e1e8ed; color: #000000 !important; font-size: 0.85rem; margin-bottom: 0.5rem;">Type: {chart_type_escaped}
Created: {chart_created}</pre>
                            {f'<p style="color: #d32f2f !important; margin-top: 0.5rem; font-weight: 600;">Error: {error_msg}</p>' if error_msg else ''}
                        </div>
                    </div>
                </div>
            </details>
            """
            st.markdown(debug_html, unsafe_allow_html=True)
            
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
<div style="text-align: center; color: #333333; padding: 2rem; font-family: 'Inter', sans-serif;">
    <p style="margin: 0; font-size: 0.9rem; color: #000000;">Built with ❤ using Streamlit and LangChain</p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; color: #333333;">QurdDB - Making databases accessible to everyone</p>
</div>
""", unsafe_allow_html=True)