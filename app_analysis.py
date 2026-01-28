import streamlit as st
import os
from dotenv import load_dotenv
import plotly.graph_objects as go

from utils import extract_app_id
from scraper import scrape_app_reviews, get_app_metadata
from analysis_free import run_free_analysis

# Load environment variables
load_dotenv()

# === DESIGN SYSTEM ===
COLORS = {
    'primary': '#2563EB',
    'primary_dark': '#1D4ED8',
    'success': '#059669',
    'warning': '#D97706',
    'danger': '#DC2626',
    'neutral_50': '#F9FAFB',
    'neutral_100': '#F3F4F6',
    'neutral_200': '#E5E7EB',
    'neutral_500': '#6B7280',
    'neutral_700': '#374151',
    'neutral_900': '#111827',
}

SPACING = {
    'xs': '0.25rem',
    'sm': '0.5rem',
    'md': '1rem',
    'lg': '1.5rem',
    'xl': '2rem',
    'xxl': '3rem',
}

# Page config
st.set_page_config(
    page_title="AppScope - App Store Analytics",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS Theme  
st.markdown(f"""
<style>
    /* Light main background */
    .main .block-container {{
        background: {COLORS['neutral_50']};
    }}
    
    /* Keep sidebar dark - just ensure text is visible */
    [data-testid="stSidebar"] {{
        background-color: #1E293B;
    }}
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {{
        color: #E5E7EB !important;
    }}
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {{
        color: white !important;
    }}
    
    /* Main content text */
    .main .main-header {{
        font-size: 2.5rem;
        font-weight: 700;
        color: #111827 !important;
        margin-bottom: 0.5rem;
    }}
    .main .subtitle {{
        font-size: 1.1rem;
        color: #374151 !important;
        margin-bottom: 2rem;
    }}
    
    /* Metrics - dark text on light background */
    .main [data-testid="stMetricValue"] {{
        color: #111827 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }}
    .main [data-testid="stMetricLabel"] {{
        color: #374151 !important;
        font-weight: 500 !important;
    }}
    
    /* All headers in main */
    .main h1, .main h2, .main h3, .main h4, .main h5 {{
        color: #111827 !important;
    }}
    
    /* Button styling */
    .stButton > button {{
        background: {COLORS['primary']} !important;
        color: white !important;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        border: none;
    }}
    .stButton > button:hover {{
        background: {COLORS['primary_dark']} !important;
    }}
    
    /* Tabs */
    .main .stTabs [data-baseweb="tab"] {{
        color: #374151 !important;
    }}
    .main .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: {COLORS['primary']} !important;
    }}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🔍 AppScope</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Deep insights from App Store reviews in minutes</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🔍 AppScope")
    st.markdown("*App Store Sentiment Analyzer*")
    
    st.markdown("---")
    st.subheader("⚙️ Analysis Settings")
    
    analysis_mode = st.radio(
        "Choose Analysis Mode:",
        ["🆓 Free (Basic)", "🤖 AI-Powered"],
        help="Free: Basic sentiment analysis\nAI: Deep insights with Claude (~$0.15/app)"
    )
    
    # API Key handling
    api_key = None
    
    if analysis_mode == "🤖 AI-Powered":
        st.info("💡 AI analysis requires your Anthropic API key. Get $5 free credits at [console.anthropic.com](https://console.anthropic.com)")
        
        api_key = st.text_input(
            "Enter your Anthropic API Key:",
            type="password",
            help="Your API key is only used for this session and never stored. Cost: ~$0.15 per app analysis."
        )
        
        if api_key:
            st.success("✅ API key ready")
        else:
            st.warning("⚠️ Enter your API key above to enable AI analysis")
    
    st.markdown("---")
    st.subheader("📊 Usage Stats")
    
    if 'analyses_run' not in st.session_state:
        st.session_state['analyses_run'] = 0
    if 'total_cost' not in st.session_state:
        st.session_state['total_cost'] = 0.0
    
    st.metric("Analyses Run", st.session_state['analyses_run'])
    st.metric("Total API Cost", f"${st.session_state['total_cost']:.3f}")
    
    st.markdown("---")
    st.markdown("### 💡 How It Works")
    st.markdown("""
    1. Paste any App Store URL
    2. We scrape up to 500 reviews
    3. Get instant sentiment analysis
    4. Optional: Deep AI insights
    """)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    app_url = st.text_input(
        "📱 App Store URL",
        placeholder="https://apps.apple.com/us/app/example-app/id1234567890",
        label_visibility="collapsed"
    )

with col2:
    analyze_btn = st.button("🔍 Analyze Reviews", type="primary", use_container_width=True)

# Example apps
with st.expander("📌 Try These Examples"):
    examples = {
        "Under My Roof": "https://apps.apple.com/us/app/under-my-roof-home-inventory/id1524335878",
        "MyStuff2 Pro": "https://apps.apple.com/us/app/mystuff2-pro/id550892332",
        "Home Contents": "https://apps.apple.com/us/app/home-contents/id420151922"
    }
    
    cols = st.columns(3)
    for idx, (name, url) in enumerate(examples.items()):
        with cols[idx]:
            if st.button(f"📱 {name}", use_container_width=True):
                st.session_state['selected_url'] = url
                st.rerun()

if 'selected_url' in st.session_state:
    app_url = st.session_state['selected_url']

# Main scraping flow
if analyze_btn or app_url:
    app_id = extract_app_id(app_url)
    
    if not app_id:
        st.error("❌ Invalid App Store URL. Please check and try again.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(page, status):
            progress_bar.progress(page * 10)
            status_text.text(status)
        
        with st.spinner("🔄 Scraping reviews..."):
            # Get overall app metadata first
            app_metadata = get_app_metadata(app_id)
            df = scrape_app_reviews(app_id, max_pages=10, progress_callback=progress_callback)
        
        progress_bar.progress(100)
        status_text.text("✅ Scraping complete!")
        
        if len(df) == 0:
            st.error("❌ No reviews found.")
        else:
            st.session_state['reviews_df'] = df
            st.session_state['app_metadata'] = app_metadata
            st.session_state['analyses_run'] += 1
            
            st.success(f"✅ Successfully analyzed **{len(df)}** recent reviews!")
            
            # Quick Stats
            st.markdown("### 📊 Quick Stats")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Show total reviews from App Store, not just scraped
                total = app_metadata.get('total_reviews', 0)
                if total:
                    st.metric("Total Reviews", f"{total:,}")
                    st.caption(f"Analyzed: {len(df):,}")
                else:
                    st.metric("Analyzed Reviews", f"{len(df):,}")
            
            with col2:
                # Show overall App Store rating, not average of scraped
                overall_rating = app_metadata.get('overall_rating')
                if overall_rating:
                    st.metric("App Store Rating", f"{overall_rating:.1f} ⭐")
                    scraped_avg = df['rating'].mean()
                    st.caption(f"Recent avg: {scraped_avg:.1f}⭐")
                else:
                    avg_rating = df['rating'].mean()
                    st.metric("Average Rating", f"{avg_rating:.1f} ⭐")
            
            with col3:
                positive_pct = (df['rating'] >= 4).sum() / len(df) * 100
                st.metric("Positive", f"{positive_pct:.0f}%")
            
            with col4:
                negative_pct = (df['rating'] <= 2).sum() / len(df) * 100
                st.metric("Negative", f"{negative_pct:.0f}%")
            
            st.markdown("")  # Spacing
            
            # Rating distribution with Plotly
            st.markdown('<p class="section-header">📈 Rating Distribution</p>', unsafe_allow_html=True)
            
            rating_counts = df['rating'].value_counts().sort_index()
            colors = ['#DC2626', '#F97316', '#EAB308', '#84CC16', '#22C55E']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=[f"{'⭐' * int(r)}" for r in rating_counts.index],
                    y=rating_counts.values,
                    marker_color=[colors[int(r)-1] for r in rating_counts.index],
                    text=rating_counts.values,
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>%{y} reviews<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title=None,
                xaxis_title=None,
                yaxis_title="Number of Reviews",
                height=350,
                margin=dict(t=20, b=40, l=60, r=20),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter, sans-serif", size=12),
                xaxis=dict(tickfont=dict(size=14)),
                yaxis=dict(gridcolor='#E5E7EB', gridwidth=1),
            )
            
            st.plotly_chart(fig, use_container_width=True)

# Analysis Section
if 'reviews_df' in st.session_state:
    df = st.session_state['reviews_df']
    
    st.markdown("---")
    st.markdown("### 🤖 Deep Insights")
    
    if analysis_mode == "🆓 Free (Basic)":
        if st.button("🚀 Run Free Analysis", use_container_width=True):
            with st.spinner("Analyzing reviews..."):
                run_free_analysis(df)
    
    else:  # AI Mode
        positive_sample = df[df['rating'] >= 4].head(30)
        negative_sample = df[df['rating'] <= 2].head(30)
        
        total_chars = sum(len(str(r)) for r in positive_sample['review']) + \
                      sum(len(str(r)) for r in negative_sample['review'])
        
        estimated_tokens = total_chars // 4
        estimated_cost = (estimated_tokens * 3 / 1_000_000) + (2000 * 15 / 1_000_000)
        
        st.info(f"💰 Estimated cost: **${estimated_cost:.3f}** | {estimated_tokens:,} tokens")
        
        if st.button("🚀 Generate AI Insights", use_container_width=True):
            if not api_key:
                st.error("❌ Please add your Anthropic API key in the sidebar")
            else:
                with st.spinner("🤖 Claude is analyzing your reviews... (30-60 seconds)"):
                    
                    prompt = f"""Analyze these app reviews and provide structured insights for a product manager:

POSITIVE REVIEWS (4-5 stars):
{chr(10).join(f"- {r[:300]}" for r in positive_sample['review'].dropna())}

NEGATIVE REVIEWS (1-2 stars):
{chr(10).join(f"- {r[:300]}" for r in negative_sample['review'].dropna())}

Provide a structured analysis:

## 1. CRITICAL JOBS TO BE DONE (2-4 only)
Identify HIGH-STAKES jobs users are hiring this app for. Requirements for each job:
- Must have 5+ mentions OR be high-stakes (insurance claims, moving, estate planning, disaster recovery)
- Show clear BEFORE/AFTER pain point being solved
- Be specific enough to build features for

DO NOT include:
- Generic feature usage like "organize belongings" or "track items" (that's what the app does, not a job)
- Vague goals like "stay organized" or "manage stuff"

Format each as:
- **Specific Job Title** | Mentions: X | Stakes: [High/Critical] | Quote: "..." | So What: [why this matters to users]

Example GOOD job: "Maximize insurance payout after home disaster by proving ownership with photos and values"
Example BAD job: "Organize and track home belongings" (too generic)

## 2. TOP 5 FEATURES USERS LOVE
Format:
- **Feature** | Mentions: X | Why: [explanation] | Quote: "..." | Recommendation: [how to leverage this]

## 3. TOP 5 CRITICAL COMPLAINTS
Focus on complaints that cause churn or block adoption. Format:
- **Issue** | Mentions: X | Impact: [Churn/Blocker/Friction] | Quote: "..." | Fix Priority: [P0/P1/P2]

## 4. COMPETITIVE POSITIONING
Based on what users say about alternatives or comparisons:
- What makes this app unique vs. competitors mentioned?
- What do users wish this app had from competitors?
- Where is this app vulnerable?

## 5. SURPRISING INSIGHTS
2-3 non-obvious patterns that would change product strategy:
- Unexpected use cases or user segments
- Counter-intuitive behavior patterns
- Hidden opportunities

End each section with actionable "So What?" implications for the product team."""

                    try:
                        import anthropic
                        
                        client = anthropic.Anthropic(api_key=api_key)
                        
                        message = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=2500,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        
                        analysis = message.content[0].text
                        
                        input_tokens = message.usage.input_tokens
                        output_tokens = message.usage.output_tokens
                        actual_cost = (input_tokens * 3 / 1_000_000) + (output_tokens * 15 / 1_000_000)
                        
                        st.session_state['total_cost'] += actual_cost
                        
                        st.success(f"✅ Analysis complete! Cost: ${actual_cost:.3f}")
                        st.markdown(analysis)
                        
                        st.download_button(
                            "📥 Download Report",
                            analysis,
                            "ai_insights.md",
                            "text/markdown",
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"❌ API Error: {e}")

# Sample Reviews
if 'reviews_df' in st.session_state:
    df = st.session_state['reviews_df']
    
    st.markdown("---")
    st.markdown("### 📝 Sample Reviews")
    
    tab1, tab2, tab3 = st.tabs(["😊 Positive (4-5 ⭐)", "😐 Neutral (3 ⭐)", "😞 Negative (1-2 ⭐)"])
    
    with tab1:
        positive = df[df['rating'] >= 4].head(10)
        if len(positive) == 0:
            st.info("No positive reviews found")
        else:
            for idx, row in positive.iterrows():
                with st.expander(f"⭐ {row['rating']} stars - {row['title']}", expanded=(idx==positive.index[0])):
                    st.write(row['review'])
                    st.caption(f"👤 **{row['author']}** • 📅 {row['date'][:10]} • 📱 Version {row['version']}")
    
    with tab2:
        neutral = df[df['rating'] == 3].head(10)
        if len(neutral) == 0:
            st.info("No neutral reviews found")
        else:
            for idx, row in neutral.iterrows():
                with st.expander(f"⭐ {row['rating']} stars - {row['title']}", expanded=(idx==neutral.index[0])):
                    st.write(row['review'])
                    st.caption(f"👤 **{row['author']}** • 📅 {row['date'][:10]} • 📱 Version {row['version']}")
    
    with tab3:
        negative = df[df['rating'] <= 2].head(10)
        if len(negative) == 0:
            st.info("No negative reviews found")
        else:
            for idx, row in negative.iterrows():
                with st.expander(f"⭐ {row['rating']} stars - {row['title']}", expanded=(idx==negative.index[0])):
                    st.write(row['review'])
                    st.caption(f"👤 **{row['author']}** • 📅 {row['date'][:10]} • 📱 Version {row['version']}")
    
    st.markdown("---")
    st.download_button(
        "📥 Download Full Dataset (CSV)",
        df.to_csv(index=False),
        "reviews.csv",
        "text/csv",
        use_container_width=True
    )
