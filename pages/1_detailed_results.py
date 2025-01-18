import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="تفاصيل التجارب",
    page_icon="📊",
    layout="centered"
)

# Add the same CSS from main app for consistency
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

    /* Global RTL settings */
    .main {
        direction: rtl !important;
        font-family: 'Cairo', sans-serif !important;
        padding: 1em !important;
    }
    
    /* Enhanced number badge styling */
    .number-badge {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-width: 2.5em !important;
        height: 1.8em !important;
        padding: 0.2em 1em !important;
        border-radius: 25px !important;
        margin-right: 0.8em !important;
        font-size: 1.1em !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .number-badge::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        background: linear-gradient(45deg, rgba(255,255,255,0.1), rgba(255,255,255,0)) !important;
        opacity: 0 !important;
        transition: opacity 0.3s ease !important;
    }

    .number-badge:hover {
        transform: translateY(-2px) scale(1.05) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }

    .number-badge:hover::before {
        opacity: 1 !important;
    }

    /* Default badge (total) */
    .number-badge.total {
        background: linear-gradient(135deg, #2196F3, #1976D2) !important;
        color: white !important;
    }

    /* Positive experiences badge */
    .number-badge.positive {
        background: linear-gradient(135deg, #4CAF50, #388E3C) !important;
        color: white !important;
    }

    /* Negative experiences badge */
    .number-badge.negative {
        background: linear-gradient(135deg, #f44336, #d32f2f) !important;
        color: white !important;
    }
    
    /* Text alignment for all elements */
    .stMarkdown, .stText, .stTitle, div[data-testid="stText"] {
        text-align: right !important;
        direction: rtl !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* RTL support for tabs */
    .stTabs [data-baseweb="tab-list"] {
        direction: rtl !important;
        gap: 0.5em !important;
        background: #f8f9fa !important;
        padding: 0.5em !important;
        border-radius: 12px !important;
        border: 1px solid #e0e0e0 !important;
        margin-bottom: 1em !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Cairo', sans-serif !important;
        font-size: 1em !important;
        padding: 0.8em 1.5em !important;
        background: white !important;
        border-radius: 8px !important;
        margin: 0 !important;
        border: 1px solid #e0e0e0 !important;
        color: #666 !important;
        transition: all 0.3s ease !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: #f1f3f4 !important;
        border-color: #d0d7dc !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #2196F3, #1976D2) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(33, 150, 243, 0.3) !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 3px 6px rgba(33, 150, 243, 0.4) !important;
    }

    .stTabs [data-baseweb="tab-panel"] {
        direction: rtl !important;
        font-family: 'Cairo', sans-serif !important;
        padding: 1em 0.5em !important;
    }

    /* Chart container styling */
    .chart-container {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5em;
        margin: 1em 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }

    /* Experience cards styling */
    .experience-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5em;
        margin: 1em 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
        font-family: 'Cairo', sans-serif !important;
        transition: all 0.3s ease;
        position: relative;
        display: flex !important;
        flex-direction: column !important;
    }

    .experience-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .experience-card.positive {
        border-right: 5px solid #4CAF50;
    }

    .experience-card.negative {
        border-right: 5px solid #f44336;
    }

    /* Response text highlight styling */
    .response-text {
        margin-bottom: 0.8em !important;
        line-height: 1.75 !important;
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 0.5em !important;
        align-items: flex-start !important;
    }

    .response-text strong {
        white-space: nowrap !important;
    }

    .response-highlight-wrapper {
        display: inline-block !important;
        padding: 0.2em 0.6em !important;
        border-radius: 6px !important;
        line-height: 1.75 !important;
        flex: 1 !important;
        min-width: 0 !important; /* Allows text to wrap */
    }

    .experience-card.positive .response-highlight-wrapper {
        background-color: rgba(76, 175, 80, 0.1) !important;
        border-left: 3px solid rgba(76, 175, 80, 0.5) !important;
    }

    .experience-card.negative .response-highlight-wrapper {
        background-color: rgba(244, 67, 54, 0.1) !important;
        border-left: 3px solid rgba(244, 67, 54, 0.5) !important;
    }

    .experience-card.positive:hover .response-highlight-wrapper {
        background-color: rgba(76, 175, 80, 0.15) !important;
    }

    .experience-card.negative:hover .response-highlight-wrapper {
        background-color: rgba(244, 67, 54, 0.15) !important;
    }

    /* Content container */
    .card-content {
        padding-left: 40px !important;
        width: 100% !important;
    }

    .category-text {
        margin-bottom: 0.5em !important;
        word-wrap: break-word !important;
        max-width: calc(100% - 40px) !important; /* Account for info bubble */
    }

    /* Info bubble styling */
    .info-link-container {
        position: absolute !important;
        left: 15px !important;
        top: 15px !important;
        z-index: 10 !important;
        width: 28px !important; /* Fixed width */
    }

    .info-link {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 28px !important;
        height: 28px !important;
        background: linear-gradient(135deg, #2196F3, #1976D2) !important;
        color: white !important;
        border-radius: 50% !important;
        text-align: center !important;
        text-decoration: none !important;
        font-weight: bold !important;
        font-size: 14px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        transition: all 0.3s ease !important;
        border: 2px solid rgba(255,255,255,0.2) !important;
    }

    .info-link:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }

    .info-bubble {
        display: none !important;
        position: absolute !important;
        top: 38px !important;
        left: -150px !important;
        background: linear-gradient(to bottom right, #ffffff, #f8f9fa) !important;
        border: 1px solid rgba(33, 150, 243, 0.1) !important;
        border-radius: 12px !important;
        padding: 15px !important;
        width: 300px !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.12) !important;
        z-index: 1000 !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        color: #333 !important;
        transition: opacity 0.3s ease, transform 0.3s ease !important;
        opacity: 0 !important;
        transform: translateY(-10px) !important;
    }

    .info-bubble::before {
        content: '' !important;
        position: absolute !important;
        top: -8px !important;
        left: 150px !important;
        width: 0 !important;
        height: 0 !important;
        border-left: 8px solid transparent !important;
        border-right: 8px solid transparent !important;
        border-bottom: 8px solid white !important;
        filter: drop-shadow(0 -2px 2px rgba(0,0,0,0.1)) !important;
    }

    .info-link:hover + .info-bubble {
        display: block !important;
        opacity: 1 !important;
        transform: translateY(0) !important;
    }

    .info-bubble:hover {
        display: block !important;
        opacity: 1 !important;
        transform: translateY(0) !important;
    }

    /* Filter section styling - RTL only */
    .filter-section {
        direction: rtl !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* Filter headers styling */
    .filter-header {
        margin-bottom: 0.2em !important;
        font-size: 0.9em !important;
        color: #666 !important;
        font-weight: 600 !important;
    }

    /* RTL support for inputs */
    .stTextInput input {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* RTL support for text */
    .stMarkdown, .stText {
        text-align: right !important;
        direction: rtl !important;
        font-family: 'Cairo', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)

def create_charts():
    """Create visualization charts for the data"""
    if 'filtered_results' in st.session_state and st.session_state.filtered_results:
        # Prepare data
        results = st.session_state.filtered_results
        positive_count = len([r for r in results if r.get('classification', {}).get('type') == 'إيجابي'])
        negative_count = len([r for r in results if r.get('classification', {}).get('type') == 'سلبي'])
        
        # Category counts
        category_counts = {}
        subcategory_counts = {}
        category_sentiment = {}  # Track sentiment distribution per category
        
        for r in results:
            cat = r.get('classification', {}).get('category', '')
            subcat = r.get('classification', {}).get('subcategory', '').split('-')[0].strip() if r.get('classification', {}).get('subcategory', '') else ''
            sentiment = r.get('classification', {}).get('type', '')
            
            if cat:
                category_counts[cat] = category_counts.get(cat, 0) + 1
                if cat not in category_sentiment:
                    category_sentiment[cat] = {'إيجابي': 0, 'سلبي': 0}
                category_sentiment[cat][sentiment] = category_sentiment[cat].get(sentiment, 0) + 1
            
            if subcat:
                subcategory_counts[subcat] = subcategory_counts.get(subcat, 0) + 1
        
        # Create layout with tabs for different visualizations
        viz_tabs = st.tabs(["نظرة عامة", "تحليل التصنيفات", "تحليل المشاعر"])
        
        with viz_tabs[0]:  # Overview tab
            col1, col2 = st.columns(2)
            
            with col1:
                # Enhanced donut chart for sentiment distribution
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['تجارب إيجابية', 'تجارب سلبية'],
                    values=[positive_count, negative_count],
                    hole=.6,
                    marker_colors=['#4CAF50', '#f44336'],
                    textinfo='value+percent',
                    textposition='inside',
                    insidetextorientation='horizontal',
                    hovertemplate="<b>%{label}</b><br>" +
                                "العدد: %{value}<br>" +
                                "النسبة: %{percent}<extra></extra>"
                )])
                
                # Add total count in center
                total_count = positive_count + negative_count
                fig_pie.add_annotation(
                    text=f'المجموع<br>{total_count}',
                    x=0.5, y=0.5,
                    font=dict(size=20, family='Cairo'),
                    showarrow=False
                )
                
                fig_pie.update_layout(
                    title={
                        'text': 'توزيع التجارب',
                        'x': 0.5,
                        'xanchor': 'center',
                        'font': {'family': 'Cairo', 'size': 20}
                    },
                    font={'family': 'Cairo', 'size': 14},
                    showlegend=True,
                    legend={'orientation': 'h', 'yanchor': 'bottom', 'y': -0.2, 'xanchor': 'center', 'x': 0.5}
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Treemap for category distribution
                fig_treemap = go.Figure(go.Treemap(
                    labels=[k for k, v in category_counts.items()],
                    parents=[''] * len(category_counts),
                    values=[v for k, v in category_counts.items()],
                    textinfo="label+value",
                    hovertemplate="<b>%{label}</b><br>" +
                                "العدد: %{value}<br>" +
                                "<extra></extra>",
                    marker=dict(
                        colors=[
                            '#2196F3', '#64B5F6', '#90CAF9', '#BBDEFB',
                            '#1976D2', '#42A5F5', '#81D4FA', '#B3E5FC'
                        ]
                    )
                ))
                
                fig_treemap.update_layout(
                    title={
                        'text': 'توزيع التصنيفات',
                        'x': 0.5,
                        'xanchor': 'center',
                        'font': {'family': 'Cairo', 'size': 20}
                    },
                    font={'family': 'Cairo', 'size': 14},
                )
                st.plotly_chart(fig_treemap, use_container_width=True)
        
        with viz_tabs[1]:  # Categories analysis tab
            # Enhanced horizontal bar chart for categories
            categories_data = sorted(category_counts.items(), key=lambda x: x[1])  # Show all categories
            
            fig_cat = go.Figure()
            
            # Add bars with custom colors
            fig_cat.add_trace(go.Bar(
                x=[x[1] for x in categories_data],
                y=[x[0] for x in categories_data],
                orientation='h',
                marker_color=['#FF9800', '#2196F3', '#4CAF50', '#9C27B0', '#F44336', '#009688', '#3F51B5', '#FFC107', '#795548', '#607D8B'],
                text=[x[1] for x in categories_data],
                textposition='auto',
                hovertemplate="<b>%{y}</b><br>" +
                            "العدد: %{x}<br>" +
                            "<extra></extra>"
            ))
            
            # Add target line for average
            avg_count = sum(v for k, v in category_counts.items()) / len(category_counts)
            fig_cat.add_vline(
                x=avg_count,
                line_dash="dash",
                line_color="#FF9800",
                annotation_text="المتوسط",
                annotation_position="top right"
            )
            
            fig_cat.update_layout(
                title={
                    'text': 'توزيع التصنيفات',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'family': 'Cairo', 'size': 20}
                },
                font={'family': 'Cairo', 'size': 14},
                xaxis={
                    'title': 'عدد التجارب',
                    'side': 'bottom',  # Changed from 'top' to 'bottom'
                    'gridcolor': '#eee'
                },
                yaxis={
                    'title': 'التصنيف',
                    'autorange': 'reversed',
                    'gridcolor': '#eee'
                },
                height=max(400, 50 * len(categories_data)),  # Dynamic height based on number of categories
                margin={'t': 100, 'b': 100},  # Adjusted bottom margin for xlabel
                plot_bgcolor='white'
            )
            st.plotly_chart(fig_cat, use_container_width=True)
            
            # Subcategories analysis
            subcategories_data = sorted(subcategory_counts.items(), key=lambda x: x[1])  # Show all subcategories
            
            fig_subcat = go.Figure()
            
            # Add bars with gradient colors
            fig_subcat.add_trace(go.Bar(
                x=[x[1] for x in subcategories_data],
                y=[x[0] for x in subcategories_data],
                orientation='h',
                marker=dict(
                    color=[x[1] for x in subcategories_data],
                    colorscale='Turbo',  # Using a more vibrant colorscale
                    showscale=True,
                    colorbar=dict(
                        title="عدد التجارب",
                        titleside="top",
                        tickfont=dict(family='Cairo'),
                        titlefont=dict(family='Cairo'),
                        len=0.8,  # Adjust colorbar length
                        thickness=20,  # Adjust colorbar thickness
                        x=1.02  # Adjust position
                    )
                ),
                text=[x[1] for x in subcategories_data],
                textposition='auto',
                hovertemplate="<b>%{y}</b><br>" +
                            "العدد: %{x}<br>" +
                            "<extra></extra>"
            ))
            
            fig_subcat.update_layout(
                title={
                    'text': 'توزيع التصنيفات الفرعية',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'family': 'Cairo', 'size': 20}
                },
                font={'family': 'Cairo', 'size': 14},
                xaxis={
                    'title': 'عدد التجارب',
                    'side': 'bottom',
                    'gridcolor': '#eee'
                },
                yaxis={
                    'title': 'التصنيف الفرعي',
                    'autorange': 'reversed',
                    'gridcolor': '#eee'
                },
                height=max(400, 30 * len(subcategories_data)),  # Dynamic height based on number of subcategories
                margin={'t': 100, 'b': 100},
                plot_bgcolor='white'
            )
            st.plotly_chart(fig_subcat, use_container_width=True)
        
        with viz_tabs[2]:  # Sentiment analysis tab
            # Create stacked bar chart for sentiment distribution by category
            categories = []
            positive_counts = []
            negative_counts = []
            
            for cat, stats in category_sentiment.items():
                categories.append(cat)
                positive_counts.append(stats['إيجابي'])
                negative_counts.append(stats['سلبي'])
            
            # Create figure
            fig_sentiment = go.Figure()
            
            # Add positive bars
            fig_sentiment.add_trace(go.Bar(
                name='تجارب إيجابية',
                y=categories,
                x=positive_counts,
                orientation='h',
                marker_color='#4CAF50',
                text=[f"{count} ({(count/(count + category_sentiment[cat]['سلبي'])*100):.1f}%)" for count, cat in zip(positive_counts, categories)],
                textposition='auto',
                hovertemplate="<b>%{y}</b><br>" +
                            "تجارب إيجابية: %{x}<br>" +
                            "<extra></extra>"
            ))
            
            # Add negative bars
            fig_sentiment.add_trace(go.Bar(
                name='تجارب سلبية',
                y=categories,
                x=negative_counts,
                orientation='h',
                marker_color='#f44336',
                text=[f"{count} ({(count/(count + category_sentiment[cat]['إيجابي'])*100):.1f}%)" for count, cat in zip(negative_counts, categories)],
                textposition='auto',
                hovertemplate="<b>%{y}</b><br>" +
                            "تجارب سلبية: %{x}<br>" +
                            "<extra></extra>"
            ))
            
            # Update layout
            fig_sentiment.update_layout(
                title={
                    'text': 'توزيع المشاعر حسب التصنيف',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'family': 'Cairo', 'size': 20},
                    'y': 0.95
                },
                barmode='relative',
                bargap=0.2,
                bargroupgap=0.1,
                xaxis_title="عدد التجارب",
                xaxis_title_standoff=20,
                yaxis_title_standoff=20,
                font={'family': 'Cairo', 'size': 14},
                showlegend=True,
                legend={'orientation': 'h', 'yanchor': 'bottom', 'y': -0.3, 'xanchor': 'center', 'x': 0.5},
                height=max(400, 100 * len(categories)),  # Dynamic height based on number of categories
                margin={'t': 100, 'b': 100, 'l': 100, 'r': 50, 'pad': 10}
            )
            
            st.plotly_chart(fig_sentiment, use_container_width=True)

def display_experience(result, experience_type):
    """Enhanced display function for experiences"""
    try:
        card_class = "positive" if experience_type == "positive" else "negative"
        
        st.markdown(f"""
            <div class="experience-card {card_class}">
                <div class="card-content">
                    <div class="response-text">
                        <strong>الاستجابة:</strong>
                        <div class="response-highlight-wrapper">{result.get('response', '')}</div>
                    </div>
                    <div class="category-text">
                        <strong>التصنيف:</strong> {result.get('classification', {}).get('category', '')}
                    </div>
                    <div class="category-text">
                        <strong>التصنيف الفرعي:</strong> {result.get('classification', {}).get('subcategory', '')}
                    </div>
                </div>
                <div class="info-link-container">
                    <a href="#" class="info-link">
                        <span class="info-icon">i</span>
                    </a>
                    <div class="info-bubble">
                        <strong>التفسير:</strong><br>
                        {result.get('classification', {}).get('explanation', 'لا يوجد تفسير')}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"خطأ في عرض التجربة: {str(e)}")

def get_unique_categories(results):
    """Get unique categories and subcategories from results"""
    categories = set()
    subcategories = set()
    for r in results:
        cat = r.get('classification', {}).get('category', '')
        subcat = r.get('classification', {}).get('subcategory', '')
        if cat:
            categories.add(cat)
        if subcat:
            subcategories.add(subcat)
    return sorted(list(categories)), sorted(list(subcategories))

def filter_results(results, category=None, subcategory=None, search_text=None):
    """Filter results based on selected criteria"""
    filtered = results.copy()
    
    if category:
        filtered = [r for r in filtered if r.get('classification', {}).get('category') == category]
    
    if subcategory:
        filtered = [r for r in filtered if r.get('classification', {}).get('subcategory') == subcategory]
    
    if search_text:
        search_text = search_text.lower()
        filtered = [r for r in filtered if (
            search_text in r.get('response', '').lower() or
            search_text in r.get('classification', {}).get('category', '').lower() or
            search_text in r.get('classification', {}).get('subcategory', '').lower() or
            search_text in r.get('classification', {}).get('explanation', '').lower()
        )]
    
    return filtered

# Main content
st.markdown('<h1 style="text-align: right;">تفاصيل التجارب</h1>', unsafe_allow_html=True)

if 'results' in st.session_state and st.session_state.results:
    results = st.session_state.results
    
    # Get unique categories and subcategories
    categories, subcategories = get_unique_categories(results)
    
    # Filter section
    st.markdown('### تصفية النتائج', unsafe_allow_html=True)
    
    # Create three columns for filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<p class="filter-header">التصنيف الرئيسي</p>', unsafe_allow_html=True)
        selected_category = st.selectbox(
            "التصنيف الرئيسي",  # Proper label for accessibility
            ["الكل"] + categories,
            key="category_filter",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown('<p class="filter-header">التصنيف الفرعي</p>', unsafe_allow_html=True)
        selected_subcategory = st.selectbox(
            "التصنيف الفرعي",  # Proper label for accessibility
            ["الكل"] + subcategories,
            key="subcategory_filter",
            label_visibility="collapsed"
        )
    
    with col3:
        st.markdown('<p class="filter-header">بحث في النتائج</p>', unsafe_allow_html=True)
        search_text = st.text_input(
            "بحث في النتائج",  # Proper label for accessibility
            key="search_filter",
            placeholder="اكتب للبحث...",
            label_visibility="collapsed"
        )
    
    # Apply filters
    filtered_results = filter_results(
        results,
        category=selected_category if selected_category != "الكل" else None,
        subcategory=selected_subcategory if selected_subcategory != "الكل" else None,
        search_text=search_text if search_text else None
    )
    
    # Update session state with filtered results for charts
    st.session_state.filtered_results = filtered_results
    
    # Display charts with filtered data
    create_charts()
    
    # Display filtered experiences
    st.markdown(f'<h2 style="text-align: right;">التجارب <span class="number-badge total">{len(filtered_results)}</span></h2>', unsafe_allow_html=True)
    
    # Separate positive and negative experiences
    positive_experiences = [r for r in filtered_results if r.get('classification', {}).get('type') == 'إيجابي']
    negative_experiences = [r for r in filtered_results if r.get('classification', {}).get('type') == 'سلبي']
    
    # Create tabs for positive and negative experiences
    exp_tabs = st.tabs(["التجارب الإيجابية", "التجارب السلبية"])
    
    with exp_tabs[0]:
        st.markdown(f'<h3 style="text-align: right;">التجارب الإيجابية <span class="number-badge positive">{len(positive_experiences)}</span></h3>', unsafe_allow_html=True)
        for exp in positive_experiences:
            display_experience(exp, "positive")
    
    with exp_tabs[1]:
        st.markdown(f'<h3 style="text-align: right;">التجارب السلبية <span class="number-badge negative">{len(negative_experiences)}</span></h3>', unsafe_allow_html=True)
        for exp in negative_experiences:
            display_experience(exp, "negative")
else:
    st.warning("لا توجد نتائج للعرض. يرجى العودة إلى الصفحة الرئيسية وتحميل البيانات أولاً.") 