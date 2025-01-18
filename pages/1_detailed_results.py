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
    
    /* Text alignment for all elements */
    .stMarkdown, .stText, .stTitle, div[data-testid="stText"] {
        text-align: right !important;
        direction: rtl !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* RTL support for tabs */
    .stTabs [data-baseweb="tab-list"] {
        direction: rtl !important;
        gap: 1em !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Cairo', sans-serif !important;
        font-size: 1.1em !important;
        padding: 1em 2em !important;
        background: #f8f9fa !important;
        border-radius: 8px !important;
        margin-left: 0.5em !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #2196F3 !important;
        color: white !important;
        font-weight: 600 !important;
    }

    .stTabs [data-baseweb="tab-panel"] {
        direction: rtl !important;
        font-family: 'Cairo', sans-serif !important;
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

    /* Info bubble styling */
    .info-link-container {
        position: absolute !important;
        left: 15px !important;
        top: 15px !important;
    }

    .info-link {
        display: inline-block !important;
        width: 24px !important;
        height: 24px !important;
        background: #2196F3 !important;
        color: white !important;
        border-radius: 50% !important;
        text-align: center !important;
        line-height: 24px !important;
        text-decoration: none !important;
        font-weight: bold !important;
    }

    .info-bubble {
        display: none !important;
        position: absolute !important;
        left: 30px !important;
        top: 0 !important;
        background: white !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 10px !important;
        width: 250px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        z-index: 1000 !important;
    }

    .info-link:hover + .info-bubble {
        display: block !important;
    }
</style>
""", unsafe_allow_html=True)

def create_charts():
    """Create visualization charts for the data"""
    if 'results' in st.session_state and st.session_state.results:
        # Prepare data
        results = st.session_state.results
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

# Page title
st.markdown('<h1 style="text-align: right;">تفاصيل تجارب الطلاب</h1>', unsafe_allow_html=True)

# Check if we have results in session state
if 'results' in st.session_state and st.session_state.results:
    # Create charts first
    create_charts()
    
    # Filter experiences
    positive_experiences = [r for r in st.session_state.results if r.get('classification', {}).get('type') == 'إيجابي']
    negative_experiences = [r for r in st.session_state.results if r.get('classification', {}).get('type') == 'سلبي']
    
    # Create tabs for positive and negative experiences
    pos_tab, neg_tab = st.tabs(["التجارب الإيجابية", "التجارب السلبية"])
    
    with pos_tab:
        for result in positive_experiences:
            display_experience(result, "positive")
    
    with neg_tab:
        for result in negative_experiences:
            display_experience(result, "negative")
else:
    st.warning("لم يتم العثور على نتائج التصنيف. الرجاء الرجوع إلى الصفحة الرئيسية وتحميل الملف أولاً.") 