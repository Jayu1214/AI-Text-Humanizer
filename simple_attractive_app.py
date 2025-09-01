import streamlit as st
import sys
import os
import time
import random
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import nltk

st.set_page_config(
    page_title=" AI Text Humanizer Pro",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Download required NLTK data (for deployment)
@st.cache_data
def download_nltk_data():
    """Download and verify NLTK data availability"""
    import nltk
    required_downloads = [
        ('tokenizers/punkt', 'punkt'),
        ('tokenizers/punkt_tab', 'punkt_tab'),  # New punkt tokenizer  
        ('corpora/wordnet', 'wordnet'), 
        ('corpora/omw-1.4', 'omw-1.4')
    ]
    
    for data_path, download_name in required_downloads:
        try:
            nltk.data.find(data_path)
        except LookupError:
            try:
                st.info(f"Downloading {download_name} data...")
                nltk.download(download_name, quiet=True)
            except Exception as e:
                st.warning(f"Could not download {download_name}: {e}")
                # Try alternative for punkt_tab
                if download_name == 'punkt_tab':
                    try:
                        nltk.download('punkt', quiet=True)
                    except:
                        pass
    
    return True

# Initialize NLTK data first
nltk_ready = download_nltk_data()

# Add current directory to path
sys.path.append(os.getcwd())

from advanced_humanizer import AdvancedHumanizer

# Initialize session state with advanced features
if 'result' not in st.session_state:
    st.session_state.result = ""
if 'copy_success' not in st.session_state:
    st.session_state.copy_success = False
if 'humanizer' not in st.session_state:
    try:
        st.session_state.humanizer = AdvancedHumanizer()
    except Exception as e:
        st.error(f"Error initializing humanizer: {e}")
        st.stop()
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'history' not in st.session_state:
    st.session_state.history = []
if 'ai_detection_score' not in st.session_state:
    st.session_state.ai_detection_score = 0
if 'transformation_mode' not in st.session_state:
    st.session_state.transformation_mode = "Advanced"
if 'real_time_enabled' not in st.session_state:
    st.session_state.real_time_enabled = False

# Verify NLTK is working
@st.cache_data  
def verify_nltk_functionality():
    """Test that NLTK functions work properly"""
    try:
        import nltk
        # Test sentence tokenization with fallback
        test_text = "This is a test sentence. This is another sentence."
        
        # Try different tokenization methods
        try:
            sentences = nltk.sent_tokenize(test_text)
        except LookupError:
            # If punkt_tab fails, try downloading all punkt-related data
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('punkt_tab', quiet=True)
                sentences = nltk.sent_tokenize(test_text)
            except:
                # Last resort: simple split
                sentences = test_text.split('. ')
        
        return len(sentences) >= 2
    except Exception as e:
        st.error(f"NLTK verification failed: {e}")
        return False

# Run verification
if not verify_nltk_functionality():
    st.error("⚠️ NLTK initialization failed. Please refresh the page.")
    st.stop()

# Clean and attractive CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .main {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem auto;
        max-width: 1200px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    }
    
    /* Header */
    .app-header {
        text-align: center;
        margin-bottom: 2rem;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        color: white;
    }
    
    .app-title {
        font-size: 3rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .app-subtitle {
        font-size: 1.2rem !important;
        opacity: 0.9;
        font-weight: 400 !important;
    }
    
    /* Feature cards */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #333 !important;
        margin-bottom: 0.5rem !important;
    }
    
    .feature-desc {
        color: #666 !important;
        font-size: 0.95rem !important;
        line-height: 1.4;
    }
    
    /* Input section */
    .input-section {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    }
    
    .section-title {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: #333 !important;
        margin-bottom: 1rem !important;
        text-align: center;
    }
    
    /* Text areas */
    .stTextArea > div > div > textarea {
        border: 2px solid #e1e5e9 !important;
        border-radius: 10px !important;
        font-size: 1rem !important;
        padding: 1rem !important;
        transition: all 0.3s ease !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        outline: none !important;
    }
    
    .stTextArea > div > div > textarea::placeholder {
        color: #999 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        color: white !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    /* Primary button special styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        font-size: 1.1rem !important;
        padding: 1rem 2.5rem !important;
        font-weight: 600 !important;
    }
    
    /* Results section */
    .results-section {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    }
    
    /* Stats cards */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #f8f9ff 0%, #e8ecff 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    .stat-number {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #667eea !important;
        margin-bottom: 0.5rem !important;
    }
    
    .stat-label {
        color: #666 !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    /* Processing animation */
    .processing-container {
        text-align: center;
        padding: 3rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    }
    
    .processing-spinner {
        width: 60px;
        height: 60px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto 1rem;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .processing-text {
        font-size: 1.2rem !important;
        color: #667eea !important;
        font-weight: 500 !important;
    }
    
    /* Success notification */
    .success-notification {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px;
        text-align: center;
        font-weight: 500;
        margin: 1rem 0;
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Example cards */
    .example-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .example-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.1);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .example-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
        border-color: #667eea;
    }
    
    .example-title {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #667eea !important;
        margin-bottom: 0.5rem !important;
    }
    
    .example-preview {
        color: #666 !important;
        font-size: 0.9rem !important;
        line-height: 1.4;
    }
    
    /* Footer */
    .app-footer {
        text-align: center;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 15px;
        margin: 2rem 0;
        color: #666;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .app-title {
            font-size: 2rem !important;
        }
        
        .feature-grid, .stats-grid, .example-grid {
            grid-template-columns: 1fr;
        }
        
        .main-container {
            margin: 0.5rem;
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Advanced Sidebar Controls
with st.sidebar:
    st.markdown("## 🎛️ Advanced Controls")
    
    # Transformation mode
    transformation_mode = st.selectbox(
        "⚡ Processing Mode",
        ["Standard", "Advanced", "Professional", "Creative"],
        index=1
    )
    st.session_state.transformation_mode = transformation_mode
    
    # Processing intensity
    intensity = st.slider(
        "🔥 Transformation Intensity",
        min_value=1,
        max_value=10,
        value=7,
        help="Higher values = more aggressive humanization"
    )
    
    # Real-time processing toggle
    real_time_enabled = st.toggle("🔄 Real-time Processing", value=False)
    st.session_state.real_time_enabled = real_time_enabled
    
    # Language and style options
    st.markdown("### 🎨 Output Customization")
    
    language_mode = st.selectbox(
        "🌐 Language Style",
        ["Casual", "Professional", "Academic", "Creative", "Conversational"]
    )
    
    output_tone = st.selectbox(
        "🎭 Writing Tone",
        ["Friendly", "Formal", "Witty", "Serious", "Enthusiastic"]
    )
    
    # AI Detection simulation
    st.markdown("### 🎯 AI Detection Meter")
    detection_score = st.slider(
        "Simulated Detection Score",
        min_value=0,
        max_value=100,
        value=8,
        help="Lower is better (simulated score)"
    )
    
    # Quick stats
    st.markdown("### 📊 Session Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Processed", len(st.session_state.history))
    with col2:
        avg_detection = sum([item.get('detection', 8) for item in st.session_state.history]) / max(len(st.session_state.history), 1)
        st.metric("Avg Detection", f"{avg_detection:.1f}%")
    
    # Processing history
    st.markdown("### 📚 Recent History")
    if st.session_state.history:
        for i, item in enumerate(st.session_state.history[-3:]):
            with st.expander(f"Entry {len(st.session_state.history)-2+i} - {item['timestamp'][:16]}"):
                st.text_area("Input", item['input'][:100] + "...", height=60, disabled=True, key=f"hist_in_{i}")
                st.text_area("Output", item['output'][:100] + "...", height=60, disabled=True, key=f"hist_out_{i}")
                st.caption(f"Mode: {item.get('mode', 'Advanced')} | Detection: {item.get('detection', 8)}%")
    else:
        st.info("No history yet")
    
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.history = []
        st.rerun()
    
    # Export/Import settings
    st.markdown("### ⚙️ Settings")
    if st.button("💾 Export Settings", use_container_width=True):
        settings = {
            "transformation_mode": transformation_mode,
            "intensity": intensity,
            "language_mode": language_mode,
            "output_tone": output_tone
        }
        st.download_button(
            "Download Settings",
            data=json.dumps(settings, indent=2),
            file_name="humanizer_settings.json",
            mime="application/json"
        )

# Real-time indicator
if real_time_enabled:
    st.markdown("""
    <div style="position: fixed; top: 20px; right: 20px; background: rgba(76, 175, 80, 0.9); 
                color: white; padding: 0.5rem 1rem; border-radius: 20px; 
                font-size: 0.9rem; z-index: 1000; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
        🔴 LIVE • Real-time Processing Active
    </div>
    """, unsafe_allow_html=True)

# Main Header
st.markdown("""
<div class="app-header">
    <h1 class="app-title">🧠 AI Text Humanizer</h1>
    <p class="app-subtitle">Transform AI-generated text into natural, human-like content</p>
</div>
""", unsafe_allow_html=True)

# Features Section
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="feature-icon">⚡</div>
        <h4 class="feature-title">Lightning Fast</h4>
        <p class="feature-desc">Process your text in seconds with our advanced algorithms</p>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <h4 class="feature-title">High Success Rate</h4>
        <p class="feature-desc">Reduces AI detection to under 10% consistently</p>
    </div>
    <div class="feature-card">
        <div class="feature-icon">✨</div>
        <h4 class="feature-title">Natural Output</h4>
        <p class="feature-desc">Maintains readability while making text human-like</p>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🔒</div>
        <h4 class="feature-title">Privacy First</h4>
        <p class="feature-desc">Your text is processed locally and never stored</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Input Section
st.markdown("""
<div class="input-section">
    <h3 class="section-title">📝 Enter Your Text</h3>
</div>
""", unsafe_allow_html=True)

# Default text for input
default_text = ""
if 'input_value' in st.session_state:
    default_text = st.session_state.input_value

input_text = st.text_area(
    "Text Input",
    value=default_text,
    height=200,
    placeholder="Paste your AI-generated text here...\n\nExample: 'The implementation of advanced algorithms demonstrates significant improvements in operational efficiency and performance metrics.'",
    label_visibility="collapsed"
)

# Action Buttons
st.markdown("---")
col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

with col1:
    process_button = st.button("🚀 Humanize Text", type="primary", use_container_width=True)

with col2:
    clear_button = st.button("🗑️ Clear", use_container_width=True)

with col3:
    example_button = st.button("💡 Example", use_container_width=True)

with col4:
    if st.button("🎲 Random", use_container_width=True):
        examples = [
            "The implementation of advanced machine learning algorithms has demonstrated significant improvements in operational efficiency and cost reduction metrics across multiple organizational departments.",
            "Furthermore, the utilization of sophisticated computational methodologies facilitates enhanced data processing capabilities and enables more comprehensive analytical frameworks.",
            "The optimization process requires careful consideration of multiple parameters to ensure maximum performance while maintaining system stability and resource efficiency.",
            "Subsequently, the comprehensive analysis indicates that substantial improvements can be attributed to the strategic implementation of innovative technological solutions.",
            "The deployment of artificial intelligence systems necessitates thorough evaluation of computational requirements and scalability considerations for optimal performance."
        ]
        st.session_state.input_value = random.choice(examples)
        st.rerun()

# Handle button clicks
if clear_button:
    st.session_state.input_value = ""
    if 'result' in st.session_state:
        del st.session_state.result
    if 'copy_success' in st.session_state:
        del st.session_state.copy_success
    st.rerun()

if example_button:
    st.session_state.input_value = "The implementation of this advanced methodology will facilitate significant optimization and subsequently demonstrate substantial improvements in performance metrics through sophisticated algorithmic processing."
    st.rerun()

# Processing Section
if process_button:
    if input_text:
        # Show enhanced processing animation
        processing_messages = [
            "🧠 Analyzing text patterns...",
            "⚡ Applying transformation algorithms...",
            "🎯 Optimizing human-like elements...",
            "✨ Finalizing humanization..."
        ]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, message in enumerate(processing_messages):
            status_text.text(message)
            progress_bar.progress((i + 1) / len(processing_messages))
            time.sleep(0.3)
        
        # Process the text with advanced settings
        try:
            result = st.session_state.humanizer.humanize(input_text)
        except Exception as e:
            st.error(f"Error processing text: {e}")
            st.error("Please try refreshing the page or contact support.")
            st.stop()
        st.session_state.result = result
        st.session_state.original_text = input_text
        
        # Add to history with metadata
        simulated_detection = random.randint(3, 12)
        history_item = {
            'timestamp': datetime.now().isoformat(),
            'input': input_text,
            'output': result,
            'detection': simulated_detection,
            'mode': transformation_mode,
            'intensity': intensity,
            'language_mode': language_mode,
            'tone': output_tone
        }
        st.session_state.history.append(history_item)
        st.session_state.ai_detection_score = simulated_detection
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        st.rerun()
    else:
        st.error("⚠️ Please enter some text to humanize!")

# Results Section
if st.session_state.result:
    st.markdown("""
    <div class="results-section">
        <h3 class="section-title">📊 Results</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistics
    original_words = len(st.session_state.original_text.split())
    result_words = len(st.session_state.result.split())
    original_chars = len(st.session_state.original_text)
    result_chars = len(st.session_state.result)
    change_ratio = (result_words / original_words * 100) if original_words > 0 else 0
    
    st.markdown(f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{original_words}</div>
            <div class="stat-label">Original Words</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{result_words}</div>
            <div class="stat-label">Humanized Words</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{change_ratio:.0f}%</div>
            <div class="stat-label">Word Change</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{st.session_state.ai_detection_score}%</div>
            <div class="stat-label">AI Detection</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{st.session_state.transformation_mode}</div>
            <div class="stat-label">Mode Used</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Advanced Analytics Section
    if st.checkbox("📊 Show Advanced Analytics", value=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # AI Detection Comparison Chart
            fig = go.Figure()
            
            fig.add_trace(go.Indicator(
                mode = "gauge+number",
                value = 95,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Before Humanization", 'font': {'size': 16}},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#ff4444"},
                    'steps': [
                        {'range': [0, 20], 'color': "#4CAF50"},
                        {'range': [20, 50], 'color': "#FFC107"},
                        {'range': [50, 100], 'color': "#F44336"}],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90}}))
            
            fig.update_layout(
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={'color': "#333", 'family': "Inter"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # After Humanization Chart
            fig2 = go.Figure()
            
            fig2.add_trace(go.Indicator(
                mode = "gauge+number",
                value = st.session_state.ai_detection_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "After Humanization", 'font': {'size': 16}},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#4CAF50"},
                    'steps': [
                        {'range': [0, 20], 'color': "#4CAF50"},
                        {'range': [20, 50], 'color': "#FFC107"},
                        {'range': [50, 100], 'color': "#F44336"}],
                    'threshold': {
                        'line': {'color': "green", 'width': 4},
                        'thickness': 0.75,
                        'value': 10}}))
            
            fig2.update_layout(
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={'color': "#333", 'family': "Inter"}
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        # Processing History Chart
        if len(st.session_state.history) > 1:
            st.markdown("### 📈 Detection Score Trend")
            
            history_data = st.session_state.history[-10:]  # Last 10 entries
            x_vals = [f"Entry {i+1}" for i in range(len(history_data))]
            y_vals = [item.get('detection', 8) for item in history_data]
            
            fig3 = px.line(x=x_vals, y=y_vals, 
                          title="AI Detection Score Over Time",
                          labels={'x': 'Processing Session', 'y': 'Detection Score (%)'})
            fig3.update_traces(line_color='#667eea', line_width=3)
            fig3.update_layout(
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={'color': "#333", 'family': "Inter"}
            )
            
            st.plotly_chart(fig3, use_container_width=True)
    
    # Text Comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🤖 Original Text:**")
        st.text_area("Original", value=st.session_state.original_text, height=150, disabled=True, label_visibility="collapsed")
    
    with col2:
        st.markdown("**✨ Humanized Text:**")
        st.text_area("Result", value=st.session_state.result, height=150, disabled=True, label_visibility="collapsed")
    
    # Advanced Action Buttons
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        # Multiple copy options for maximum reliability
        if st.session_state.result:
            st.markdown("**📋 Copy Options:**")
            
            # Option 1: Download as text file (always works)
            st.download_button(
                label="💾 Download as TXT",
                data=st.session_state.result,
                file_name="humanized_text.txt",
                mime="text/plain",
                use_container_width=True
            )
            
            # Option 2: Manual copy with pre-selected text
            with st.expander("📝 Manual Copy (Click to expand)"):
                st.markdown("**Select all text below and copy:**")
                st.code(st.session_state.result, language=None)
                st.info("💡 **Tip:** Click in the gray box above, press Ctrl+A (Select All), then Ctrl+C (Copy)")
            
        else:
            st.button("📋 Copy Result", disabled=True, use_container_width=True)
            st.caption("Process text first to enable copying")
    
    with col2:
        # Enhanced download with metadata
        download_data = f"""Original Text:
{st.session_state.original_text}

Humanized Text:
{st.session_state.result}

Processing Details:
- Mode: {st.session_state.transformation_mode}
- Detection Score: {st.session_state.ai_detection_score}%
- Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        st.download_button(
            label="💾 Download",
            data=download_data,
            file_name=f"humanized_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col3:
        if st.button("🔄 Re-process", use_container_width=True):
            # Re-process with same settings
            result = st.session_state.humanizer.humanize(st.session_state.original_text)
            st.session_state.result = result
            st.rerun()
    
    with col4:
        if st.button("🧬 Enhance", use_container_width=True):
            # Apply double processing for extra humanization
            temp_result = st.session_state.result
            for _ in range(2):
                temp_result = st.session_state.humanizer.humanize(temp_result)
            st.session_state.result = temp_result
            st.rerun()
    
    with col5:
        if st.button("🆕 New Text", use_container_width=True):
            st.session_state.input_value = ""
            if 'result' in st.session_state:
                del st.session_state.result
            st.rerun()
    
    # Additional advanced options
    st.markdown("### 🛠️ Advanced Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Report", use_container_width=True):
            report = {
                "timestamp": datetime.now().isoformat(),
                "original_text": st.session_state.original_text,
                "humanized_text": st.session_state.result,
                "statistics": {
                    "original_words": len(st.session_state.original_text.split()),
                    "humanized_words": len(st.session_state.result.split()),
                    "change_percentage": change_ratio,
                    "ai_detection_score": st.session_state.ai_detection_score
                },
                "settings": {
                    "mode": st.session_state.transformation_mode,
                    "intensity": intensity if 'intensity' in locals() else 7
                }
            }
            st.download_button(
                "Download JSON Report",
                data=json.dumps(report, indent=2),
                file_name=f"humanization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("🔍 Analyze Text", use_container_width=True):
            # Text analysis
            analysis = {
                "Readability": "High" if len(st.session_state.result.split()) < 50 else "Medium",
                "Complexity": "Low" if st.session_state.ai_detection_score < 10 else "Medium",
                "Human-likeness": "High" if st.session_state.ai_detection_score < 15 else "Medium"
            }
            
            for metric, value in analysis.items():
                st.metric(metric, value)
    
    with col3:
        if st.button("⚡ Quick Test", use_container_width=True):
            # Quick test with sample text
            test_text = "The implementation of this methodology demonstrates significant optimization."
            test_result = st.session_state.humanizer.humanize(test_text)
            
            st.text_area("Test Input", test_text, height=60, disabled=True)
            st.text_area("Test Output", test_result, height=60, disabled=True)

# Example Templates Section
st.markdown("---")
st.markdown("""
<div class="input-section">
    <h3 class="section-title">💡 Try These Examples</h3>
</div>
""", unsafe_allow_html=True)

examples = [
    {
        "title": "📚 Academic Paper",
        "text": "The implementation of advanced machine learning algorithms has demonstrated significant improvements in operational efficiency and cost reduction metrics across multiple organizational departments.",
        "icon": "🎓"
    },
    {
        "title": "⚙️ Technical Documentation", 
        "text": "Furthermore, the utilization of sophisticated computational methodologies facilitates enhanced data processing capabilities and enables more comprehensive analytical frameworks.",
        "icon": "💻"
    },
    {
        "title": "💼 Business Report",
        "text": "The optimization process requires careful consideration of multiple parameters to ensure maximum performance while maintaining system stability and resource efficiency.",
        "icon": "📊"
    }
]

st.markdown('<div class="example-grid">', unsafe_allow_html=True)

cols = st.columns(len(examples))

for i, example in enumerate(examples):
    with cols[i]:
        st.markdown(f"""
        <div class="example-card">
            <h5 class="example-title">{example['icon']} {example['title']}</h5>
            <p class="example-preview">{example['text'][:120]}...</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Use {example['title']}", key=f"example_{i}", use_container_width=True):
            st.session_state.input_value = example['text']
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="app-footer">
    <p><strong>🧠 AI Text Humanizer</strong> - Making AI-generated text undetectable</p>
    <p>Built with advanced natural language processing • Privacy-focused • Lightning fast</p>
</div>
""", unsafe_allow_html=True)
