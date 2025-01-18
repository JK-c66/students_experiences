import streamlit as st
import os
import yaml
import pandas as pd

# Set page config
st.set_page_config(
    page_title="إدارة التصنيفات",
    page_icon="📑",
    layout="centered"
)

# Add custom CSS for RTL support
st.markdown("""
    <style>
        /* Import IBM Plex Sans Arabic font */
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap');
        
        /* Global font settings */
        * {
            font-family: 'IBM Plex Sans Arabic', sans-serif !important;
        }
        
        /* Global RTL settings */
        .main {
            direction: rtl;
        }
        
        /* Headers and text */
        div[data-testid="stMarkdownContainer"],
        .element-container,
        .stMarkdown,
        h1, h2, h3, p {
            direction: rtl;
            text-align: right;
        }
        
        /* Form elements */
        .stSelectbox > div[role="button"],
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            direction: rtl;
            text-align: right;
        }
        
        /* DataFrames RTL support */
        .dataframe {
            direction: rtl !important;
            text-align: right !important;
        }
        
        .dataframe th {
            text-align: right !important;
        }
        
        /* Enhanced Tabs Design */
        .stTabs {
            background: #ffffff;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            padding: 10px;
        }

        .stTabs [data-baseweb="tab-list"] {
            direction: rtl;
            gap: 8px;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 10px;
        }
        
        .stTabs [data-baseweb="tab"] {
            direction: rtl;
            text-align: right;
            background: #ffffff;
            border: none !important;
            border-radius: 8px;
            color: #666;
            transition: all 0.3s ease;
            padding: 8px 16px !important;
            font-weight: 600;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background: #e9ecef;
            color: #1f77b4;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: #1f77b4 !important;
            color: white !important;
            box-shadow: 0 2px 8px rgba(31, 119, 180, 0.3);
        }

        /* Category-specific styles */
        .category-card[data-category="خدمات رقمية"] {
            border-right: 4px solid #1f77b4;
        }
        .category-card[data-category="البنية التقنية"] {
            border-right: 4px solid #7b2cbf;
        }
        .category-card[data-category="السكن"] {
            border-right: 4px solid #2d936c;
        }
        .category-card[data-category="الطعام"] {
            border-right: 4px solid #e85d04;
        }
        .category-card[data-category="النقل"] {
            border-right: 4px solid #d00000;
        }

        /* Enhanced category card */
        .category-card {
            background: #ffffff;
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            border: 1px solid rgba(0, 0, 0, 0.1);
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .category-card:hover {
            transform: translateX(-5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .category-title {
            color: #2c3e50;
            font-size: 1.1em;
            margin-bottom: 8px;
            font-weight: bold;
            border-bottom: 1px solid #e9ecef;
            padding-bottom: 5px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .category-title .count-badge {
            background: #f8f9fa;
            color: #2c3e50;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.9em;
            min-width: 24px;
            text-align: center;
            border: 1px solid rgba(0, 0, 0, 0.1);
        }
        
        /* Compact subcategory display */
        .subcategories-container {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            padding: 5px 0;
        }

        .subcategory-item {
            background: #f8f9fa;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.9em;
            display: inline-block;
            border: 1px solid rgba(0, 0, 0, 0.05);
        }

        /* Categories container */
        .categories-container {
            display: grid;
            gap: 10px;
            padding: 5px;
        }

        /* Vertical separator enhancement */
        .vertical-separator {
            width: 3px;
            background: linear-gradient(to bottom, #f1f3f5, #1f77b4, #f1f3f5);
            height: 100%;
            margin: auto;
            border-radius: 3px;
            box-shadow: 0 0 15px rgba(0,0,0,0.1);
            opacity: 0.7;
        }

        /* Structure title enhancement */
        .structure-title {
            background: linear-gradient(45deg, #1f77b4, #4a90e2);
            color: white;
            padding: 15px 25px;
            border-radius: 12px;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 4px 15px rgba(31, 119, 180, 0.2);
            font-size: 1.4em;
            position: relative;
            overflow: hidden;
        }

        .structure-title::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1));
            transform: translateX(-100%);
            transition: transform 0.5s ease;
        }

        .structure-title:hover::after {
            transform: translateX(100%);
        }

        /* Other RTL elements */
        button, select, input {
            direction: rtl !important;
        }
        
        .stButton > button {
            float: right;
        }

        /* Enhanced Data Editor Styling */
        [data-testid="stDataFrame"] {
            background: #ffffff;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid rgba(31, 119, 180, 0.1);
            margin: 10px 0;
        }

        [data-testid="stDataFrame"] [data-testid="stTable"] {
            border-radius: 8px;
            overflow: hidden;
        }

        /* Table header styling */
        [data-testid="stDataFrame"] th {
            background: linear-gradient(45deg, #1f77b4, #4a90e2) !important;
            color: white !important;
            padding: 12px 15px !important;
            font-weight: 600;
            border: none !important;
        }

        /* Table cell styling */
        [data-testid="stDataFrame"] td {
            padding: 10px 15px !important;
            border-bottom: 1px solid #f0f0f0 !important;
            transition: background-color 0.2s ease;
        }

        [data-testid="stDataFrame"] tr:hover td {
            background-color: rgba(31, 119, 180, 0.05);
        }

        /* Enhanced Button Styling */
        .stButton > button {
            background: linear-gradient(45deg, #1f77b4, #4a90e2) !important;
            color: white !important;
            border: none !important;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(31, 119, 180, 0.2) !important;
            width: auto !important;
            min-width: 200px !important;
            margin: 10px 0 !important;
        }

        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 15px rgba(31, 119, 180, 0.3) !important;
        }

        .stButton > button:active {
            transform: translateY(0) !important;
            box-shadow: 0 2px 8px rgba(31, 119, 180, 0.2) !important;
        }

        /* Enhanced Select Box Styling */
        .stSelectbox > div[role="button"] {
            background: white !important;
            border: 1px solid rgba(31, 119, 180, 0.2) !important;
            border-radius: 8px !important;
            padding: 8px 15px !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
            transition: all 0.3s ease !important;
        }

        .stSelectbox > div[role="button"]:hover {
            border-color: #1f77b4 !important;
            box-shadow: 0 4px 12px rgba(31, 119, 180, 0.1) !important;
        }

        /* Section Headers */
        .edit-section-header {
            color: #1f77b4;
            font-size: 1.2em;
            font-weight: 600;
            margin: 20px 0 10px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid rgba(31, 119, 180, 0.1);
        }

        /* Edit Panel Container */
        .edit-panel {
            background: linear-gradient(145deg, #ffffff, #f8f9fa);
            border-radius: 15px;
            padding: 25px;
            margin: 15px 0;
            border: 1px solid rgba(31, 119, 180, 0.1);
            box-shadow: 0 8px 20px rgba(0,0,0,0.05);
        }

        /* Success Message Styling */
        .element-container:has(.stSuccess) {
            animation: slideIn 0.5s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .stSuccess {
            background: linear-gradient(45deg, #4CAF50, #81C784) !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 16px !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2) !important;
        }

        /* Add animation for tab transitions */
        .stTabs [data-baseweb="tab-panel"] {
            animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(5px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Enhanced Button Container */
        .button-container {
            display: flex;
            justify-content: center;
            width: 100%;
            padding: 10px 0;
            margin: 10px 0;
        }

        /* Enhanced Button Styling */
        .stButton > button {
            background: linear-gradient(45deg, #1f77b4, #4a90e2) !important;
            color: white !important;
            border: none !important;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(31, 119, 180, 0.2) !important;
            width: 100% !important;
            max-width: 300px !important;
            margin: 10px auto !important;
            display: block !important;
            text-align: center !important;
            font-size: 1em !important;
        }

        /* Category Pills/Boxes Styling */
        .stTabs [data-baseweb="tab"] {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 15px !important;
            padding: 10px 24px !important;
            font-weight: 500 !important;
            border: 1px solid rgba(0, 0, 0, 0.05) !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
            transition: all 0.3s ease !important;
            margin: 0 5px !important;
            position: relative;
            overflow: hidden;
        }

        /* Category-specific colors */
        .stTabs [data-baseweb="tab"][aria-selected="true"][aria-label*="خدمات رقمية"] {
            background: linear-gradient(135deg, #1a73e8 0%, #1557b0 100%) !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"][aria-label*="البنية التقنية"] {
            background: linear-gradient(135deg, #7b2cbf 0%, #5a1d8a 100%) !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"][aria-label*="السكن"] {
            background: linear-gradient(135deg, #2d936c 0%, #1e6e4f 100%) !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"][aria-label*="الطعام"] {
            background: linear-gradient(135deg, #e85d04 0%, #bc4b02 100%) !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"][aria-label*="النقل"] {
            background: linear-gradient(135deg, #d00000 0%, #9d0208 100%) !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            border-color: rgba(0, 0, 0, 0.1) !important;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: white !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .stTabs [data-baseweb="tab"]::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .stTabs [data-baseweb="tab"]:hover::before {
            opacity: 1;
        }

        .stTabs [data-baseweb="tab-list"] {
            background: transparent !important;
            padding: 15px 10px !important;
            gap: 12px !important;
        }

        /* Container styling */
        .stTabs {
            background: transparent !important;
            box-shadow: none !important;
        }

        .types-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .type-badge {
            background: linear-gradient(135deg, #1f77b4, #4a90e2);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .type-badge:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
    </style>
""", unsafe_allow_html=True)

# Function to load categories
def load_categories():
    try:
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Classes.txt")
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            return data.get('categories', {}), data.get('types', [])
    except FileNotFoundError:
        return {}, []

# Function to save categories
def save_categories(categories, types):
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Classes.txt")
    with open(file_path, 'w', encoding='utf-8') as file:
        yaml.dump({'types': types, 'categories': categories}, file, allow_unicode=True)

# Convert categories to dataframe format
def categories_to_df(categories):
    return pd.DataFrame({"التصنيف": list(categories.keys())})

def types_to_df(types):
    return pd.DataFrame({"النوع": types})

def subcategories_to_df(categories, selected_category):
    if selected_category and selected_category in categories:
        subcats = categories[selected_category]['subcategories']
        return pd.DataFrame({"التصنيف الفرعي": subcats})
    return pd.DataFrame({"التصنيف الفرعي": []})

# Load existing categories and types
categories, types = load_categories()

# Title
st.title("إدارة التصنيفات")

# Create tabs
tab1, tab2, tab3 = st.tabs(["عرض التصنيفات", "تعديل التصنيفات", "إدارة الأنواع"])

# View Categories Tab
with tab1:
    st.markdown('<h2 class="structure-title">هيكل التصنيفات الحالي</h2>', unsafe_allow_html=True)
    
    # Display types section
    st.markdown('<div class="edit-section-header">الأنواع المتاحة</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="types-container">' + 
        ''.join([f'<span class="type-badge">{t}</span>' for t in types]) + 
        '</div>',
        unsafe_allow_html=True
    )
    
    st.markdown('<div class="edit-section-header">التصنيفات</div>', unsafe_allow_html=True)
    
    # Sort categories by size
    sorted_categories = sorted(
        categories.items(),
        key=lambda x: len(x[1].get('subcategories', [])),
        reverse=True
    )

    # Create columns for better organization
    struct_cols = st.columns(3)

    # Distribute categories across columns
    categories_per_col = len(sorted_categories) // 3 + (1 if len(sorted_categories) % 3 else 0)
    columns_data = [[], [], []]

    for i, (category, details) in enumerate(sorted_categories):
        col_idx = i // categories_per_col
        if col_idx < 3:
            columns_data[2 - col_idx].append((category, details))

    # Display categories in columns with enhanced design
    for col_idx, col_categories in enumerate(columns_data):
        with struct_cols[col_idx]:
            st.markdown('<div class="categories-container">', unsafe_allow_html=True)
            for category, details in col_categories:
                subcats_count = len(details.get('subcategories', []))
                st.markdown(f"""
                    <div class="category-card" data-category="{category}">
                        <div class="category-title">
                            <span>📑 {category}</span>
                            <span class="count-badge">{subcats_count}</span>
                        </div>
                        <div class="subcategories-container">
                            {''.join([f'<div class="subcategory-item">{subcat}</div>' for subcat in details.get('subcategories', [])])}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# Edit Categories Tab
with tab2:    
    # Create three columns - middle one for separator
    col1, col_sep, col2 = st.columns([10, 1, 10])

    with col2:  # Main categories on right
        st.markdown('<div class="edit-section-header">التصنيفات الرئيسية</div>', unsafe_allow_html=True)
        categories_df = categories_to_df(categories)
        
        edited_categories_df = st.data_editor(
            categories_df,
            num_rows="dynamic",
            key="categories_editor",
            use_container_width=True
        )
        
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        if st.button("حفظ التغييرات في التصنيفات الرئيسية"):
            new_categories = {}
            for _, row in edited_categories_df.iterrows():
                category_name = row["التصنيف"]
                if category_name and not pd.isna(category_name):
                    if category_name in categories:
                        new_categories[category_name] = categories[category_name]
                    else:
                        new_categories[category_name] = {'subcategories': []}
            
            categories = new_categories
            save_categories(categories, types)
            st.success("✅ تم حفظ التغييرات بنجاح")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Add vertical separator
    with col_sep:
        st.markdown('<div class="vertical-separator"></div>', unsafe_allow_html=True)

    with col1:  # Subcategories on left
        st.markdown('<div class="edit-section-header">التصنيفات الفرعية</div>', unsafe_allow_html=True)
        selected_category = st.selectbox("اختر التصنيف", list(categories.keys()), key="subcategory_selector")
        
        if selected_category:
            subcategories_df = subcategories_to_df(categories, selected_category)
            
            edited_subcategories_df = st.data_editor(
                subcategories_df,
                num_rows="dynamic",
                key="subcategories_editor",
                use_container_width=True
            )
            
            st.markdown('<div class="button-container">', unsafe_allow_html=True)
            if st.button("حفظ التغييرات في التصنيفات الفرعية"):
                new_subcategories = []
                for _, row in edited_subcategories_df.iterrows():
                    subcat = row["التصنيف الفرعي"]
                    if subcat and not pd.isna(subcat):
                        new_subcategories.append(subcat)
                
                categories[selected_category]['subcategories'] = new_subcategories
                save_categories(categories, types)
                st.success("✅ تم حفظ التغييرات بنجاح")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Types Management Tab
with tab3:
    st.markdown('<div class="edit-section-header">إدارة أنواع التجارب</div>', unsafe_allow_html=True)
    
    types_df = types_to_df(types)
    edited_types_df = st.data_editor(
        types_df,
        num_rows="dynamic",
        key="types_editor",
        use_container_width=True
    )
    
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    if st.button("حفظ التغييرات في الأنواع"):
        new_types = []
        for _, row in edited_types_df.iterrows():
            type_name = row["النوع"]
            if type_name and not pd.isna(type_name):
                new_types.append(type_name)
        
        types = new_types
        save_categories(categories, types)
        st.success("✅ تم حفظ التغييرات بنجاح")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
