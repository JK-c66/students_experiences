import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import time
from pathlib import Path
import io
from streamlit_extras.switch_page_button import switch_page
import openpyxl
import yaml

# Constants
MIN_BATCH_SIZE = 30  # Minimum to ensure some parallelization
MAX_BATCH_SIZE = 100  # Maximum for very short responses
MAX_TOKENS_PER_BATCH = 6000  # Conservative limit for Gemini's context window
TOKENS_PER_CHAR_ESTIMATE = 0.5  # Rough estimate of tokens per character
PROMPT_TEMPLATE_TOKENS = 500  # Estimated tokens for the classification prompt template

# Configure Gemini API and page settings
st.set_page_config(
    page_title="تجارب الطلاب",
    page_icon="🎓",
    layout="centered"
)

# Load and apply external CSS
with open('static/css/main.css', encoding='utf-8') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

#------------------------------------------------------------------------------
# Gemini Communication
#------------------------------------------------------------------------------

def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    try:
        # Use pathlib for cross-platform path handling
        base_path = Path(__file__).parent
        file_path = base_path / path
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        file = genai.upload_file(str(file_path), mime_type=mime_type)
        print(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file
    except Exception as e:
        st.error(f"Failed to upload file: {e}")
        return None

def wait_for_files_active(files):
    """Waits for the given files to be active."""
    print("Waiting for file processing...")
    try:
        for file in files:
            if file is None:
                raise Exception("Invalid file object")

            name = file.name
            file = genai.get_file(name)
            while file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(2)
                file = genai.get_file(name)
            if file.state.name != "ACTIVE":
                raise Exception(f"File {file.name} failed to process")
        print("...all files ready")
        print()
    except Exception as e:
        st.error(f"File processing failed: {e}")
        return False
    return True

def initialize_gemini():
    """Initialize Gemini model with categories and types."""
    try:
        # Get API key from streamlit secrets
        api_key = st.secrets["GEMINI_API_KEY"]
        if not api_key:
            st.error("API key not found in secrets. Please check your .streamlit/secrets.toml file.")
            return None

        genai.configure(api_key=api_key)

        # Create the model
        generation_config = {
            "temperature": 0,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            system_instruction=(
                "according to the categories mentioned, classify the provided text into the most appropriate category, "
                "subcategory, and type. You must use categories, subcategories, and types from the file only. "
                "Choose what fits the case the most. The output should be in Arabic."
            )
        )

        if 'uploaded_files' not in st.session_state:
            # Upload and process the categories file
            files = [
                upload_to_gemini("data/Classes.txt", mime_type="text/plain"),
            ]

            # Check if file upload was successful
            if None in files:
                raise Exception("Failed to upload required files")

            # Wait for files to be processed
            if not wait_for_files_active(files):
                raise Exception("File processing failed")
            
            st.session_state.uploaded_files = files

        # Load types from configuration
        with open("data/Classes.txt", 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            types = data.get('types', [])
            types_str = ', '.join(types)

        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        "Please analyze the following responses and classify them based on the categories in the file. "
                        f"For each response, determine if it is one of these types: {types_str}. "
                        "Provide the classification in the following format:\n"
                        "{\n"
                        "  'response': 'the original response',\n"
                        "  'classification': {\n"
                        "    'type': 'the experience type',\n"
                        "    'category': 'main category',\n"
                        "    'subcategory': 'subcategory',\n"
                        "    'explanation': 'brief explanation of the classification'\n"
                        "  }\n"
                        "}",
                        st.session_state.uploaded_files[0],
                    ],
                },
            ]
        )
        return chat_session
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")
        return None

def read_csv_with_encoding(file):
    """Read CSV file with multiple encoding attempts."""
    encodings = ['utf-8', 'utf-8-sig', 'cp1256', 'iso-8859-6']
    df = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file, encoding=encoding)
            if not df.empty and len(df.columns) > 0:
                return df
        except Exception:
            continue
    
    return None

def process_responses(file, file_type, column_name=None, separator=None):
    """Process uploaded file and extract responses."""
    try:
        # Clear preview data from other tabs
        st.session_state.preview_data = None
        
        if file_type == 'txt':
            content = file.getvalue().decode('utf-8')
            responses = [r.strip() for r in content.split(separator) if r.strip()]
        elif file_type == 'csv':
            if st.session_state.current_df is None:
                raise Exception("لم يتم تحميل الملف بشكل صحيح")
            
            df = st.session_state.current_df
            responses = df[column_name].dropna().tolist()
        elif file_type == 'excel':
            df = pd.read_excel(file)
            if df.empty or len(df.columns) == 0:
                raise Exception("لم يتم العثور على أعمدة صالحة في الملف. تأكد من تنسيق ملف Excel")
            responses = df[column_name].dropna().tolist()
        
        # Update preview data
        preview_df = pd.DataFrame({"الاستجابات": responses})
        st.session_state.preview_data = preview_df
        
        return responses
    except pd.errors.EmptyDataError:
        st.error("الملف فارغ أو لا يحتوي على بيانات صالحة")
        return []
    except KeyError:
        st.error(f"لم يتم العثور على العمود '{column_name}' في الملف")
        return []
    except Exception as e:
        st.error(f"حدث خطأ أثناء معالجة الملف: {str(e)}")
        return []

def estimate_tokens(text):
    """Estimate the number of tokens in a text using character count."""
    return len(str(text)) * TOKENS_PER_CHAR_ESTIMATE

def get_optimal_batch_size(total_items, responses=None):
    """Calculate optimal batch size based on total items and response lengths.
    
    Args:
        total_items: Total number of responses to process
        responses: List of actual responses (optional)
    
    Returns:
        Optimal batch size that considers both item count and token limits
    """
    # For very small datasets, process all at once
    if total_items <= MIN_BATCH_SIZE:
        return total_items
    
    # If we have actual responses, use them to calculate average length
    if responses:
        # Calculate average tokens per response
        total_tokens = sum(estimate_tokens(r) for r in responses)
        avg_tokens_per_response = total_tokens / len(responses)
        
        # Calculate how many responses we can fit within token limit
        tokens_available = MAX_TOKENS_PER_BATCH - PROMPT_TEMPLATE_TOKENS
        suggested_size = int(tokens_available / avg_tokens_per_response)
        
        # Ensure we stay within MIN/MAX bounds
        batch_size = max(MIN_BATCH_SIZE, min(suggested_size, MAX_BATCH_SIZE))
        
        return min(batch_size, total_items)
    
    # Without responses, use a more conservative approach
    suggested_size = max(MIN_BATCH_SIZE, min(total_items // 4, MAX_BATCH_SIZE))
    return suggested_size

def get_batch_token_estimate(responses_batch):
    """Estimate total tokens for a batch of responses."""
    response_tokens = sum(estimate_tokens(r) for r in responses_batch)
    return response_tokens + PROMPT_TEMPLATE_TOKENS

def classify_responses_batch(responses_batch):
    """Classify a batch of responses using Gemini."""
    try:
        if not st.session_state.model:
            raise Exception("نموذج Gemini غير مهيأ")
        
        # Combine responses into a single request with clear separation
        batch_text = "\n=====\n".join([f"Response {i+1}: {str(r)}" for i, r in enumerate(responses_batch)])
        
        # Create prompt with escaped curly braces for the example
        prompt = (
            f"Please classify these {len(responses_batch)} responses. For each response, determine:\n"
            "1. Category (التصنيف)\n"
            "2. Subcategory (التصنيف_فرعي)\n"
            "3. Type (نوع) - must be either 'إيجابي' or 'سلبي'\n"
            "4. Explanation (تفسير)\n\n"
            "Return a JSON array with one object per response. Example format:\n"
            "[\n"
            "    {{\n"
            '        "category": "example_category",\n'
            '        "subcategory": "example_subcategory",\n'
            '        "type": "إيجابي",\n'
            '        "explanation": "example_explanation"\n'
            "    }}\n"
            "]\n\n"
            "Here are the responses to classify:\n\n"
            f"{batch_text}"
        )

        # Send request to model
        chat_response = st.session_state.model.send_message(prompt)
        
        try:
            # Try to parse as JSON first
            import json
            classifications = json.loads(chat_response.text)
            
        except json.JSONDecodeError as e:
            # Try to clean the response and parse again
            try:
                # Remove any markdown formatting if present
                cleaned_text = chat_response.text.strip('`').strip()
                if cleaned_text.startswith('json'):
                    cleaned_text = cleaned_text[4:].strip()
                classifications = json.loads(cleaned_text)
            except json.JSONDecodeError as e2:
                st.markdown("""
                    <div class="toast error">
                        فشل في تحليل استجابة النموذج: تنسيق JSON غير صالح
                    </div>
                """, unsafe_allow_html=True)
                return [None] * len(responses_batch)
        
        # Ensure we have a list
        if not isinstance(classifications, list):
            st.markdown("""
                <div class="toast error">
                    استجابة النموذج ليست قائمة صالحة
                </div>
            """, unsafe_allow_html=True)
            classifications = [classifications]
        
        # Validate and normalize each classification
        validated_classifications = []
        for i, classification in enumerate(classifications):
            try:
                if not isinstance(classification, dict):
                    validated_classifications.append(None)
                    continue
                
                # Get type value, handling different possible keys
                type_value = classification.get('type', classification.get('نوع', ''))
                
                # Normalize type values
                if type_value.strip() in ['إيجابي', 'سلبي', 'ايجابية', 'سلبية', 'ايجابي', 'إيجابية']:
                    normalized_type = 'إيجابي' if type_value.strip() in ['إيجابي', 'ايجابية', 'ايجابي'] else 'سلبي'
                    
                    validated_classifications.append({
                        'type': normalized_type,
                        'category': classification.get('category', classification.get('تصنيف', '')).strip(),
                        'subcategory': classification.get('subcategory', classification.get('تصنيف_فرعي', '')).strip(),
                        'explanation': classification.get('explanation', classification.get('تفسير', '')).strip()
                    })
                else:
                    validated_classifications.append(None)
            except Exception as e:
                validated_classifications.append(None)
        
        return validated_classifications
        
    except Exception as e:
        st.markdown(f"""
            <div class="toast error">
                خطأ في التصنيف: {str(e)}
            </div>
        """, unsafe_allow_html=True)
        return [None] * len(responses_batch)

def display_experience(result, experience_type):
    """Enhanced display function for experiences"""
    try:
        card_class = "positive" if experience_type == "positive" else "negative"
        
        st.markdown(f"""
            <div class="experience-card {card_class}">
                <div class="response-text">
                    <strong>الاستجابة:</strong> {result.get('response', '')}
                </div>
                <div class="category-text">
                    <strong>التصنيف:</strong> {result.get('classification', {}).get('category', '')}
                </div>
                <div class="category-text">
                    <strong>التصنيف الفرعي:</strong> {result.get('classification', {}).get('subcategory', '')}
                </div>
                <div class="info-link-container">
                    <a href="#" class="info-link">
                        <span class="info-icon">i</span>
                    </a>
                    <div class="info-bubble">
                        {result.get('classification', {}).get('explanation', 'لا يوجد تفسير')}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"خطأ في عرض التجربة: {str(e)}")

# Initialize session state variables
if 'preview_data' not in st.session_state:
    st.session_state.preview_data = None
if 'model' not in st.session_state:
    st.session_state.model = None
if 'classification_results' not in st.session_state:
    st.session_state.classification_results = None
if 'current_df' not in st.session_state:
    st.session_state.current_df = None
if 'results' not in st.session_state:
    st.session_state.results = []
if 'previous_file_type' not in st.session_state:
    st.session_state.previous_file_type = None

# Initialize Gemini at startup if not already initialized
if st.session_state.model is None:
    st.session_state.model = initialize_gemini()

st.markdown("""
    <div class="header-container">
        <div class="header-content">
            <div class="header-icon">🎓</div>
            <h1 class="header-title">محلل تجارب الطلاب</h1>
            <div class="header-subtitle">تحليل وتصنيف تجارب الطلاب باستخدام الذكاء الاصطناعي</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Replace tabs with select box for file type
file_type = st.selectbox(
    "اختر نوع الملف",
    ["ملف CSV", "ملف نصي", "ملف Excel"],
    key="file_type_selector"
)

# Clear preview data when file type changes
if st.session_state.previous_file_type != file_type:
    st.session_state.preview_data = None
    st.session_state.current_df = None
    st.session_state.previous_file_type = file_type

responses = []
if file_type == "ملف نصي":
    st.markdown("""
        <style>
            @keyframes pulseBox {
                0% { box-shadow: 0 0 0 0 rgba(33, 150, 243, 0.4); }
                70% { box-shadow: 0 0 0 10px rgba(33, 150, 243, 0); }
                100% { box-shadow: 0 0 0 0 rgba(33, 150, 243, 0); }
            }
            
            .important-note {
                background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 100%);
                padding: 20px;
                border-radius: 12px;
                border-right: 4px solid #2196F3;
                margin: 20px 0;
                box-shadow: 0 4px 15px rgba(33, 150, 243, 0.1);
                animation: pulseBox 2s infinite;
                position: relative;
                overflow: hidden;
            }
            
            .important-note::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 2px;
                background: linear-gradient(90deg, #2196F3, #64B5F6);
            }
            
            .note-icon {
                font-size: 1.5em;
                margin-left: 10px;
                color: #2196F3;
                vertical-align: middle;
            }
            
            .note-header {
                font-family: 'Cairo', sans-serif;
                font-size: 1.3em;
                font-weight: 700;
                color: #1565C0;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
            }
            
            .note-content {
                font-family: 'Cairo', sans-serif;
                font-size: 1.1em;
                color: #1f1f1f;
                line-height: 1.6;
                margin: 0;
                padding-right: 15px;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .important-note {
                animation: fadeIn 0.5s ease-out, pulseBox 2s infinite;
            }
        </style>
        <div class="important-note">
            <div class="note-header">
                <span class="note-icon">ℹ️</span>
                <span>تنبيه مهم</span>
            </div>
            <p class="note-content">
                يجب أن تكون كل استجابة في سطر جديد في الملف النصي للمعالجة الصحيحة للبيانات
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    txt_file = st.file_uploader("تحميل ملف نصي", type=['txt'], key="txt_uploader")
    if txt_file:
        responses = process_responses(txt_file, 'txt', separator="\n")

elif file_type == "ملف CSV":
    csv_file = st.file_uploader("تحميل ملف CSV", type=['csv'], key="csv_uploader")
    if csv_file:
        df = read_csv_with_encoding(csv_file)
        if df is not None:
            st.session_state.current_df = df
            columns = df.columns.tolist()
            column_name = st.selectbox("حدد العمود الذي يحتوي على استجابات الطلاب:", columns, key="csv_column")
            if column_name:
                responses = process_responses(csv_file, 'csv', column_name=column_name)
        else:
            st.error("لم يتم العثور على أعمدة صالحة في الملف. تأكد من تنسيق الملف CSV وترميزه")

else:  # Excel file
    excel_file = st.file_uploader("تحميل ملف Excel", type=['xlsx'], key="excel_uploader")
    if excel_file:
        df = pd.read_excel(excel_file)
        columns = df.columns.tolist()
        column_name = st.selectbox("حدد العمود الذي يحتوي على استجابات الطلاب:", columns, key="excel_column")
        if column_name:
            responses = process_responses(excel_file, 'excel', column_name=column_name)

# Preview section with compact design
if st.session_state.preview_data is not None:
    st.markdown("""
        <style>
        /* Preview section styling */
        .preview-section {
            margin: 2em 0;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(33, 150, 243, 0.08);
            border: 1px solid #e0e0e0;
            overflow: hidden;
        }

        .preview-header-container {
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            padding: 1em 1.5em;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            direction: rtl;
        }

        .preview-icon {
            font-size: 1.5em;
            margin-left: 0.8em;
            background: linear-gradient(45deg, #2196F3, #64B5F6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: float 3s ease-in-out infinite;
        }

        .preview-title {
            font-family: 'Cairo', sans-serif;
            font-size: 1.4em;
            font-weight: 600;
            color: #1f1f1f;
            margin: 0;
            position: relative;
        }

        .preview-title::after {
            content: '';
            position: absolute;
            bottom: -5px;
            right: 0;
            width: 40px;
            height: 3px;
            background: linear-gradient(90deg, #2196F3, #64B5F6);
            border-radius: 2px;
            transition: width 0.3s ease;
        }

        .preview-header-container:hover .preview-title::after {
            width: 100%;
        }

        /* Text preview specific styling */
        .txt-preview {
            max-height: 300px;
            overflow-y: auto;
            direction: rtl;
            background: #ffffff;
            font-family: 'Cairo', sans-serif;
            line-height: 1.6;
            padding: 0;
            margin: 0;
        }

        .responses-container {
            padding: 15px 45px 15px 15px;
            counter-reset: response-counter;
        }

        .response-item {
            position: relative;
            padding: 8px 15px;
            margin: 5px 0;
            border-radius: 6px;
            background: #f8f9fa;
            transition: all 0.2s ease;
            border-right: 3px solid #2196F3;
            counter-increment: response-counter;
        }

        .response-item::before {
            content: counter(response-counter);
            position: absolute;
            right: -30px;
            top: 50%;
            transform: translateY(-50%);
            color: #666;
            font-size: 0.9em;
            width: 20px;
            text-align: left;
        }

        .response-item:hover {
            background: #f1f8fe;
            transform: translateX(-2px);
            box-shadow: 0 2px 5px rgba(33, 150, 243, 0.1);
        }

        /* Scrollbar styling */
        .txt-preview::-webkit-scrollbar {
            width: 8px;
        }

        .txt-preview::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 4px;
        }

        .txt-preview::-webkit-scrollbar-thumb {
            background: #2196F3;
            border-radius: 4px;
        }

        .txt-preview::-webkit-scrollbar-thumb:hover {
            background: #1976D2;
        }

        /* Preview content wrapper */
        .preview-content {
            padding: 1.5em;
            background: #ffffff;
            max-height: 300px;
            overflow-y: auto;
        }

        /* Dataframe specific styling */
        .preview-content .dataframe {
            width: 100%;
            direction: rtl;
            text-align: right;
        }

        @media (max-width: 768px) {
            .preview-header-container {
                padding: 1em;
            }
            
            .preview-title {
                font-size: 1.2em;
            }
            
            .preview-icon {
                font-size: 1.3em;
            }

            .txt-preview {
                max-height: 250px;
            }
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="preview-section">
            <div class="preview-header-container">
                <div class="preview-icon">📊</div>
                <div class="preview-title">معاينة البيانات</div>
            </div>
    """, unsafe_allow_html=True)
    
    if file_type == "ملف نصي":
        # Create numbered list of responses
        responses_html = ""
        for i, response in enumerate(st.session_state.preview_data["الاستجابات"], 1):
            responses_html += f'<div class="response-item">{response}</div>'
            
        st.markdown(f"""
            <div class="txt-preview">
                <div class="responses-container">
                    {responses_html}
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.dataframe(
            st.session_state.preview_data,
            use_container_width=True,
            height=300,
            hide_index=True
        )
    
    st.markdown('</div></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("تصنيف الاستجابات", key="classify_button"):
            if not st.session_state.model:
                st.markdown("""
                    <div class="toast error">
                        لم يتم تهيئة نموذج Gemini بشكل صحيح. يرجى التحقق من مفتاح API
                    </div>
                """, unsafe_allow_html=True)
            else:
                processing_container = st.empty()
                processing_container.markdown("""
                    <div class="processing-container">
                        <div class="loader">
                            <div class="loader-ring loader-ring-1"></div>
                            <div class="loader-ring loader-ring-2"></div>
                            <div class="loader-ring loader-ring-3"></div>
                        </div>
                        <div class="processing-text">جاري معالجة الاستجابات...</div>
                        <div class="processing-progress">
                            <div class="progress-bar"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                results = []
                
                try:
                    # Calculate initial optimal batch size based on responses
                    batch_size = get_optimal_batch_size(len(responses), responses)
                    total_batches = (len(responses) + batch_size - 1) // batch_size
                    
                    # Process responses in batches with dynamic size adjustment
                    i = 0
                    consecutive_failures = 0
                    while i < len(responses):
                        # Get current batch
                        end_idx = min(i + batch_size, len(responses))
                        batch = responses[i:end_idx]
                        
                        # Estimate tokens for this batch
                        estimated_tokens = get_batch_token_estimate(batch)
                        
                        # If estimated tokens too high, reduce batch size
                        if estimated_tokens > MAX_TOKENS_PER_BATCH:
                            # Reduce batch size by 25%
                            batch_size = max(MIN_BATCH_SIZE, int(batch_size * 0.75))
                            continue  # Retry with smaller batch
                        
                        try:
                            classifications = classify_responses_batch(batch)
                            
                            # Check if classification was successful
                            if all(c is not None for c in classifications):
                                # Success - process results
                                for response, classification in zip(batch, classifications):
                                    if classification:
                                        results.append({
                                            "response": response,
                                            "classification": classification
                                        })
                                # Reset failure counter and potentially increase batch size
                                consecutive_failures = 0
                                if batch_size < MAX_BATCH_SIZE:
                                    # Increase by 20% if we've had success
                                    batch_size = min(MAX_BATCH_SIZE, int(batch_size * 1.2))
                                i += len(batch)  # Move to next batch
                            else:
                                # Partial failure - reduce batch size
                                consecutive_failures += 1
                                batch_size = max(MIN_BATCH_SIZE, int(batch_size * 0.75))
                                if consecutive_failures >= 3:
                                    # If we've failed 3 times, process one at a time
                                    batch_size = MIN_BATCH_SIZE
                        except Exception as e:
                            # Error processing batch - reduce size and retry
                            consecutive_failures += 1
                            batch_size = max(MIN_BATCH_SIZE, int(batch_size * 0.75))
                            if consecutive_failures >= 3:
                                # If we've failed 3 times, process one at a time
                                batch_size = MIN_BATCH_SIZE
                            continue
                    
                    # Clear processing indicator
                    processing_container.empty()
                    
                    # Store results in session state for persistence
                    st.session_state.classification_results = results
                    st.session_state.results = results
                    
                    # Show success message
                    st.markdown("""
                        <div class="toast success">
                            تم تصنيف الاستجابات بنجاح!
                        </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    processing_container.empty()
                    st.markdown(f"""
                        <div class="toast error">
                            حدث خطأ أثناء التصنيف: {str(e)}
                        </div>
                    """, unsafe_allow_html=True)

# After classification is complete, display results
if st.session_state.get('results'):
    st.markdown('<h2 class="centered">نتائج التصنيف</h2>', unsafe_allow_html=True)
    
    # Filter experiences
    positive_experiences = [r for r in st.session_state.results if r.get('classification', {}).get('type') == 'إيجابي']
    negative_experiences = [r for r in st.session_state.results if r.get('classification', {}).get('type') == 'سلبي']
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Create a combined DataFrame with all results
        all_results_df = pd.DataFrame([
            {
                'الاستجابة': r['response'],
                'التصنيف': r['classification']['category'],
                'التصنيف الفرعي': r['classification']['subcategory'],
                'النوع': r['classification']['type'],
                'التفسير': r['classification']['explanation']
            }
            for r in st.session_state.results
        ])

        # Add timestamp
        all_results_df['تاريخ التحليل'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

        # Create summary sheet
        summary_sheet = pd.DataFrame()
        total_responses = len(all_results_df)
        positive_count = len(all_results_df[all_results_df['النوع'] == 'إيجابي'])
        negative_count = len(all_results_df[all_results_df['النوع'] == 'سلبي'])
        
        summary_data = {
            'المقياس': ['إجمالي الاستجابات', 'التجارب الإيجابية', 'التجارب السلبية', 
                      'نسبة التجارب الإيجابية', 'نسبة التجارب السلبية'],
            'القيمة': [total_responses, positive_count, negative_count,
                     f'{(positive_count/total_responses)*100:.1f}%',
                     f'{(negative_count/total_responses)*100:.1f}%']
        }
        summary_df = pd.DataFrame(summary_data)
        
        # Category distribution
        category_dist = all_results_df['التصنيف'].value_counts().reset_index()
        category_dist.columns = ['التصنيف', 'العدد']
        category_dist['النسبة'] = (category_dist['العدد'] / total_responses * 100).round(1).astype(str) + '%'

        # Write sheets
        summary_df.to_excel(writer, sheet_name='ملخص التحليل', index=False, startrow=1)
        category_dist.to_excel(writer, sheet_name='ملخص التحليل', index=False, startrow=7)
        all_results_df.to_excel(writer, sheet_name='جميع النتائج', index=False)
        
        # Separate positive and negative experiences
        positive_df = all_results_df[all_results_df['النوع'] == 'إيجابي']
        negative_df = all_results_df[all_results_df['النوع'] == 'سلبي']
        positive_df.to_excel(writer, sheet_name='التجارب الإيجابية', index=False)
        negative_df.to_excel(writer, sheet_name='التجارب السلبية', index=False)

        # Create pivot tables
        pivot_sheet_name = 'تحليل التصنيفات'
        category_pivot = pd.pivot_table(
            all_results_df,
            values='الاستجابة',
            index=['التصنيف', 'التصنيف الفرعي'],
            columns=['النوع'],
            aggfunc='count',
            fill_value=0
        ).reset_index()
        category_pivot.to_excel(writer, sheet_name=pivot_sheet_name)

        # Get workbook and sheets
        workbook = writer.book
        
        # Add charts
        from openpyxl.chart import PieChart, BarChart, Reference
        
        # Summary sheet formatting
        summary_sheet = writer.sheets['ملخص التحليل']
        summary_sheet.sheet_view.rightToLeft = True
        
        # Add title
        summary_sheet['A1'] = 'ملخص تحليل تجارب الطلاب'
        summary_sheet['A1'].font = openpyxl.styles.Font(size=14, bold=True)
        summary_sheet.merge_cells('A1:B1')
        
        # Create pie chart for positive/negative distribution
        pie = PieChart()
        pie.title = 'توزيع التجارب'
        labels = Reference(summary_sheet, min_col=1, min_row=3, max_row=4)
        data = Reference(summary_sheet, min_col=2, min_row=3, max_row=4)
        pie.add_data(data)
        pie.set_categories(labels)
        summary_sheet.add_chart(pie, "D2")

        # Create bar chart for category distribution
        bar = BarChart()
        bar.title = 'توزيع التصنيفات'
        bar.type = "col"
        bar.style = 10
        bar.y_axis.title = 'العدد'
        bar.x_axis.title = 'التصنيف'
        
        data = Reference(summary_sheet, min_col=2, min_row=8, max_row=8+len(category_dist))
        cats = Reference(summary_sheet, min_col=1, min_row=8, max_row=8+len(category_dist))
        bar.add_data(data)
        bar.set_categories(cats)
        summary_sheet.add_chart(bar, "D15")

        # Apply conditional formatting and styling to all sheets
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            worksheet.sheet_view.rightToLeft = True
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column = list(column)
                for cell in column:
                    try:
                        # Skip merged cells
                        if isinstance(cell, openpyxl.cell.cell.MergedCell):
                            continue
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                # Only adjust if we found a valid column letter
                if column and not isinstance(column[0], openpyxl.cell.cell.MergedCell):
                    adjusted_width = (max_length + 2) * 1.2
                    worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
            
            # Add header styling
            for cell in worksheet[1]:
                cell.font = openpyxl.styles.Font(bold=True, size=12)
                cell.fill = openpyxl.styles.PatternFill(start_color='E3F2FD', end_color='E3F2FD', fill_type='solid')
                cell.border = openpyxl.styles.Border(bottom=openpyxl.styles.Side(style='medium'))
            
            # Add zebra striping
            for row in range(2, worksheet.max_row + 1):
                if row % 2 == 0:
                    for cell in worksheet[row]:
                        cell.fill = openpyxl.styles.PatternFill(start_color='F8F9FA', end_color='F8F9FA', fill_type='solid')
            
            # Add conditional formatting for positive/negative
            if 'النوع' in [cell.value for cell in worksheet[1]]:
                type_col = None
                for idx, cell in enumerate(worksheet[1], 1):
                    if cell.value == 'النوع':
                        type_col = idx
                        break
                
                if type_col:
                    for row in range(2, worksheet.max_row + 1):
                        cell = worksheet.cell(row=row, column=type_col)
                        if cell.value == 'إيجابي':
                            cell.font = openpyxl.styles.Font(color='4CAF50')
                        elif cell.value == 'سلبي':
                            cell.font = openpyxl.styles.Font(color='F44336')

    # Reset pointer and get value
    output.seek(0)
    excel_data = output.getvalue()
    
    # Calculate top categories and their percentages
    category_stats = {}
    for r in st.session_state.results:
        category = r.get('classification', {}).get('category', '')
        type_ = r.get('classification', {}).get('type', '')
        if category:
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'positive': 0}
            category_stats[category]['total'] += 1
            if type_ == 'إيجابي':
                category_stats[category]['positive'] += 1
    
    # Calculate percentages and sort by total count
    for cat in category_stats:
        total = category_stats[cat]['total']
        positive = category_stats[cat]['positive']
        category_stats[cat]['positive_pct'] = (positive / total) * 100
        category_stats[cat]['negative_pct'] = ((total - positive) / total) * 100
    
    # Get top 4 categories by total count
    top_categories = sorted(category_stats.items(), key=lambda x: x[1]['total'], reverse=True)[:4]
    
    # Display enhanced summary section
    summary_html = f"""
        <div class="summary-container">
            <div class="summary-header">ملخص التحليل</div>
            <div class="summary-stats">
                <div class="stat-card positive-stat">
                    <div class="stat-number">{len(positive_experiences)}</div>
                    <div class="stat-label">تجربة إيجابية</div>
                </div>
                <div class="stat-card negative-stat">
                    <div class="stat-number">{len(negative_experiences)}</div>
                    <div class="stat-label">تجربة سلبية</div>
                </div>
            </div>
            <div class="top-categories">
                <div class="top-categories-header">أبرز التصنيفات</div>
                <div class="category-grid">"""
    
    # Add category cards with enhanced structure
    for cat, stats in top_categories:
        summary_html += f"""
            <div class="category-card">
                <div class="category-count">{stats['total']}</div>
                <div class="category-name">{cat}</div>
                <div class="category-percentages">
                    <span class="positive-pct">{stats['positive_pct']:.1f}% إيجابي</span>
                    <span class="negative-pct">{stats['negative_pct']:.1f}% سلبي</span>
                </div>
            </div>"""
    
    summary_html += """
                </div>
            </div>
        </div>
    """
    
    # Add CSS for percentages
    st.markdown("""
        <style>
        .category-percentages {
            margin-top: 5px;
            font-size: 0.8em;
            display: flex;
            flex-direction: column;
            gap: 2px;
            text-align: center;
        }
        
        .positive-pct {
            color: #4CAF50;
        }
        
        .negative-pct {
            color: #f44336;
        }
        
        .category-card {
            padding: 15px 10px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(summary_html, unsafe_allow_html=True)
    
    # Add download button
    st.download_button(
        "تحميل النتائج كملف Excel",
        excel_data,
        "classification_results.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key='download_excel',
        use_container_width=True,
    )
    
    # Add page switching button
    if st.button("عرض التفاصيل", use_container_width=True):
        switch_page("detailed_results")
    