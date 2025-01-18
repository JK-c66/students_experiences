import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
from pathlib import Path
import io
from streamlit_extras.switch_page_button import switch_page
import openpyxl
from openpyxl.chart import PieChart, BarChart, Reference
from openpyxl.styles import Alignment, PatternFill, Font

# Constants
MIN_BATCH_SIZE = 50  # Minimum batch size for processing
MAX_BATCH_SIZE = 80  # Maximum batch size for processing

# Configure Gemini API and page settings
st.set_page_config(
    page_title="تجارب الطلاب",
    page_icon="🎓",
    layout="centered"
)

# Load and apply CSS
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
                "1. Classify the sentiment as exactly one of: {'إيجابي', 'سلبي', 'محايد'}"
                "2. choose the best fit category and subcategory based on the provided catagories and subcategories"
                "3. Provide a brief explanation (1-2 sentences)"
                "Return a JSON array with one object per response:"
                "[\n"
                "    {\n"
                '        "response": "response text",\n'
                '        "classification": {\n'
                '            "type": "sentiment type",\n'
                '            "category": "main category",\n'
                '            "subcategory": "subcategory",\n'
                '            "explanation": "brief explanation"\n'
                "        }\n"
                "    }\n"
                "]\n"
                "Rules:"
                "1. Use 'خطأ' in all type, category, subcategory for any bad or not ralted response"
                "2. All your responses MUST be in Arabic"
                "3. the response must be a valid json array"
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
            

        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        "Please analyze and classify the following responses:",
                        files[0],
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

def get_optimal_batch_size(total_items, responses=None):
    """Calculate optimal batch size based on total items."""
    # For very small datasets, process all at once
    if total_items <= MIN_BATCH_SIZE:
        return total_items
    
    # Use minimum batch size for consistency
    return MIN_BATCH_SIZE

def classify_responses_batch(responses_batch):
    """Classify a batch of responses using Gemini."""
    try:
        if not st.session_state.model:
            raise Exception("Gemini model is not initialized")
        
        # Just send the responses with their IDs
        batch_text = "\n---\n".join([f"response_{i+1}: {str(r)}" for i, r in enumerate(responses_batch)])
        
        # Send request to model
        chat_response = st.session_state.model.send_message(batch_text)
        
        try:
            # Sanitize the response text
            response_text = chat_response.text.strip()
            
            # Basic validation of JSON structure
            if not (response_text.startswith('[') and response_text.endswith(']')):
                raise ValueError("Invalid JSON structure: Response must be an array")
            
            # Parse and validate JSON response
            import json
            classifications = json.loads(response_text)
            
            if not isinstance(classifications, list):
                if isinstance(classifications, dict):
                    classifications = [classifications]
                else:
                    raise ValueError("Invalid response format: expected list or object")
            
            # Process and validate classifications
            validated_results = []
            for classification in classifications:
                try:
                    # Skip invalid entries
                    if not isinstance(classification, dict):
                        continue
                    
                    # Validate required fields
                    if 'response' not in classification or 'classification' not in classification:
                        continue
                    
                    class_data = classification.get('classification', {})
                    if not isinstance(class_data, dict):
                        continue
                    
                    # Normalize type values
                    type_value = class_data.get('type', '').strip()
                    normalized_type = None
                    
                    if type_value in ['إيجابي', 'ايجابي', 'ايجابية', 'إيجابية']:
                        normalized_type = 'إيجابي'
                    elif type_value in ['سلبي', 'سلبية']:
                        normalized_type = 'سلبي'
                    elif type_value in ['محايد', 'محايدة']:
                        normalized_type = 'محايد'
                    else:
                        normalized_type = 'محايد'  # Default to neutral for invalid types
                    
                    # Create validated result with required fields
                    result = {
                        'response': str(classification.get('response', '')).strip(),
                        'classification': {
                            'type': normalized_type,
                            'category': str(class_data.get('category', 'محايد')).strip(),
                            'subcategory': str(class_data.get('subcategory', 'محايد')).strip(),
                            'explanation': str(class_data.get('explanation', '')).strip()
                        }
                    }
                    
                    # Only add if we have a valid response
                    if result['response']:
                        validated_results.append(result)
                        
                except Exception as e:
                    st.warning(f"تم تخطي تصنيف غير صالح: {str(e)}")
                    continue
            
            return validated_results
            
        except json.JSONDecodeError as e:
            st.error(f"فشل في تحليل استجابة النموذج: {str(e)}")
            st.error(f"الاستجابة الأصلية: {response_text}")
            # Try to recover partial results if possible
            try:
                # Find the last complete object
                import re
                pattern = r'\{[^{}]*\}'
                matches = re.finditer(pattern, response_text)
                partial_results = []
                for match in matches:
                    try:
                        obj = json.loads(match.group())
                        if isinstance(obj, dict) and 'response' in obj and 'classification' in obj:
                            partial_results.append(obj)
                    except:
                        continue
                if partial_results:
                    st.warning("تم استرداد بعض النتائج الجزئية")
                    return partial_results
            except:
                pass
            return []
            
    except Exception as e:
        st.error(f"خطأ في التصنيف: {str(e)}")
        return []

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
                    # Use a fixed batch size
                    batch_size = MIN_BATCH_SIZE
                    total_batches = (len(responses) + batch_size - 1) // batch_size
                    
                    # Process responses in batches
                    i = 0
                    while i < len(responses):
                        # Get current batch
                        end_idx = min(i + batch_size, len(responses))
                        batch = responses[i:end_idx]
                        
                        try:
                            classifications = classify_responses_batch(batch)
                            
                            # Show parsed JSON in expander
                            with st.expander("Debug: Parsed JSON"):
                                st.json(classifications)
                            
                            # Process results
                            for response, classification in zip(batch, classifications):
                                if classification and isinstance(classification, dict):
                                    # Get the classification directly - it's not nested
                                    result = {
                                        "response": response,
                                        "classification": classification.get('classification', {})
                                    }
                                    results.append(result)
                                
                            i += len(batch)  # Move to next batch
                            
                        except Exception as e:
                            # If batch fails, try processing one by one
                            for response in batch:
                                try:
                                    classification = classify_responses_batch([response])[0]
                                    if classification and isinstance(classification, dict):
                                        result = {
                                            "response": response,
                                            "classification": classification.get('classification', {})
                                        }
                                        results.append(result)
                                except Exception as e:
                                    st.error(f"Error processing single response: {str(e)}")
                                    continue
                            i += len(batch)
                    
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
    neutral_experiences = [r for r in st.session_state.results if r.get('classification', {}).get('type') == 'محايد']
    
    # Create Excel file in memory
    output = io.BytesIO()
    excel_created = False
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        try:
            # Create properly structured data for DataFrame
            df_data = []
            for result in st.session_state.results:
                if isinstance(result, dict):
                    classification = result.get('classification', {})
                    df_data.append({
                        'الاستجابة': result.get('response', ''),
                        'التصنيف': classification.get('category', ''),
                        'التصنيف الفرعي': classification.get('subcategory', ''),
                        'النوع': classification.get('type', ''),
                        'التفسير': classification.get('explanation', '')
                    })
            
            # Create DataFrame from structured data
            all_results_df = pd.DataFrame(df_data)
            
            if not all_results_df.empty:
                # Create summary sheet
                total_responses = len(all_results_df)
                
                if total_responses > 0:
                    positive_count = len(all_results_df[all_results_df['النوع'] == 'إيجابي'])
                    negative_count = len(all_results_df[all_results_df['النوع'] == 'سلبي'])
                    neutral_count = len(all_results_df[all_results_df['النوع'] == 'محايد'])
                    
                    summary_data = {
                        'المقياس': ['إجمالي الاستجابات', 'التجارب الإيجابية', 'التجارب السلبية', 'التجارب المحايدة',
                                  'نسبة التجارب الإيجابية', 'نسبة التجارب السلبية', 'نسبة التجارب المحايدة'],
                        'القيمة': [
                            total_responses, 
                            positive_count, 
                            negative_count, 
                            neutral_count,
                            f'{(positive_count/total_responses)*100:.1f}%' if total_responses > 0 else '0%',
                            f'{(negative_count/total_responses)*100:.1f}%' if total_responses > 0 else '0%',
                            f'{(neutral_count/total_responses)*100:.1f}%' if total_responses > 0 else '0%'
                        ]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    
                    # Category distribution
                    category_dist = all_results_df['التصنيف'].value_counts().reset_index()
                    category_dist.columns = ['التصنيف', 'العدد']
                    category_dist['النسبة'] = (category_dist['العدد'] / total_responses * 100).round(1).astype(str) + '%'
                    
                    # Write sheets
                    summary_df.to_excel(writer, sheet_name='ملخص التحليل', index=False, startrow=1)
                    category_dist.to_excel(writer, sheet_name='ملخص التحليل', index=False, startrow=9)
                    all_results_df.to_excel(writer, sheet_name='جميع النتائج', index=False)
                    
                    # Write type-specific sheets
                    for df, sheet_name in [
                        (all_results_df[all_results_df['النوع'] == 'إيجابي'], 'التجارب الإيجابية'),
                        (all_results_df[all_results_df['النوع'] == 'سلبي'], 'التجارب السلبية'),
                        (all_results_df[all_results_df['النوع'] == 'محايد'], 'التجارب المحايدة')
                    ]:
                        if not df.empty:
                            df.to_excel(writer, sheet_name=sheet_name, index=False)

                    # Apply styling and create charts
                    workbook = writer.book
                    
                    # Create color fills for different sentiments
                    positive_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')  # Light green
                    negative_fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')  # Light red
                    neutral_fill = PatternFill(start_color='F2F2F2', end_color='F2F2F2', fill_type='solid')   # Light gray
                    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')    # Blue header
                    
                    # Create charts sheet
                    charts_sheet = workbook.create_sheet('الرسوم البيانية')
                    
                    # Create pie chart for sentiment distribution
                    pie = PieChart()
                    labels = Reference(workbook['ملخص التحليل'], min_row=2, max_row=4, min_col=1)
                    data = Reference(workbook['ملخص التحليل'], min_row=2, max_row=4, min_col=2)
                    pie.add_data(data)
                    pie.set_categories(labels)
                    pie.title = "توزيع التجارب"
                    charts_sheet.add_chart(pie, "A1")
                    
                    # Create bar chart for top categories
                    bar = BarChart()
                    cat_labels = Reference(workbook['ملخص التحليل'], min_row=10, max_row=10+len(category_dist), min_col=1)
                    cat_data = Reference(workbook['ملخص التحليل'], min_row=10, max_row=10+len(category_dist), min_col=2)
                    bar.add_data(cat_data)
                    bar.set_categories(cat_labels)
                    bar.title = "توزيع التصنيفات"
                    charts_sheet.add_chart(bar, "A15")
                    
                    # Apply styling to all sheets
                    for sheet_name in workbook.sheetnames:
                        ws = workbook[sheet_name]
                        
                        # Set RTL
                        ws.sheet_view.rightToLeft = True
                        
                        # Style headers
                        for cell in ws[1]:
                            if cell.value:
                                cell.fill = header_fill
                                cell.font = Font(bold=True, color="FFFFFF")  # White text
                                cell.alignment = openpyxl.styles.Alignment(horizontal='right', 
                                                                         vertical='center',
                                                                         wrap_text=True)
                        
                        # Auto-fit columns and apply text wrapping
                        for column in ws.columns:
                            max_length = 0
                            column = list(column)
                            for cell in column:
                                try:
                                    if len(str(cell.value)) > max_length:
                                        max_length = len(str(cell.value))
                                except:
                                    pass
                            adjusted_width = min(max_length + 2, 50)  # Cap width at 50
                            ws.column_dimensions[column[0].column_letter].width = adjusted_width
                            
                            # Apply text wrapping and alignment to all cells
                            for cell in column:
                                if cell.value:
                                    cell.alignment = openpyxl.styles.Alignment(horizontal='right', 
                                                                             vertical='center',
                                                                             wrap_text=True)
                        
                        # Apply sentiment colors to data sheets
                        if sheet_name in ['جميع النتائج', 'التجارب الإيجابية', 'التجارب السلبية', 'التجارب المحايدة']:
                            # Find the sentiment column index
                            sentiment_col = None
                            for idx, cell in enumerate(ws[1], 1):
                                if cell.value == 'النوع':
                                    sentiment_col = idx
                                    break
                            
                            if sentiment_col:
                                # Apply colors based on sentiment
                                for row in ws.iter_rows(min_row=2):  # Skip header
                                    sentiment = row[sentiment_col-1].value
                                    fill = None
                                    if sentiment == 'إيجابي':
                                        fill = positive_fill
                                    elif sentiment == 'سلبي':
                                        fill = negative_fill
                                    elif sentiment == 'محايد':
                                        fill = neutral_fill
                                    
                                    if fill:
                                        for cell in row:
                                            cell.fill = fill
                    
                    excel_created = True
            else:
                st.error("لم يتم العثور على نتائج صالحة للتحليل")
                
        except Exception as e:
            st.error(f"حدث خطأ أثناء إنشاء ملف Excel: {str(e)}")
    
    # Only proceed with download button if Excel was created successfully
    if excel_created:
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
                    category_stats[category] = {'total': 0, 'positive': 0, 'negative': 0, 'neutral': 0}
                category_stats[category]['total'] += 1
                if type_ == 'إيجابي':
                    category_stats[category]['positive'] += 1
                elif type_ == 'سلبي':
                    category_stats[category]['negative'] += 1
                elif type_ == 'محايد':
                    category_stats[category]['neutral'] += 1
        
        # Calculate percentages and sort by total count
        for cat in category_stats:
            total = category_stats[cat]['total']
            positive = category_stats[cat]['positive']
            negative = category_stats[cat]['negative']
            neutral = category_stats[cat]['neutral']
            category_stats[cat]['positive_pct'] = (positive / total) * 100
            category_stats[cat]['negative_pct'] = (negative / total) * 100
            category_stats[cat]['neutral_pct'] = (neutral / total) * 100
        
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
                    <div class="stat-card neutral-stat">
                        <div class="stat-number">{len(neutral_experiences)}</div>
                        <div class="stat-label">تجربة محايدة</div>
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
                        <span class="neutral-pct">{stats['neutral_pct']:.1f}% محايد</span>
                    </div>
                </div>"""
        
        summary_html += """
                    </div>
                </div>
            </div>
        """
        
        # Add CSS for neutral styling
        st.markdown("""
            <style>
            .neutral-stat .stat-number {
                background: linear-gradient(45deg, #9E9E9E, #BDBDBD);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .neutral-stat .stat-label::after {
                background: linear-gradient(90deg, #9E9E9E, #BDBDBD);
            }
            
            .neutral-stat::after {
                content: '📊';
            }
            
            .neutral-pct {
                color: #9E9E9E;
                padding: 0.2rem 0.5rem;
                border-radius: 12px;
                transition: all 0.3s ease;
                background: rgba(255, 255, 255, 0.5);
                border: 1px solid rgba(158, 158, 158, 0.2);
            }
            
            .summary-stats {
                grid-template-columns: repeat(3, 1fr) !important;
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
        