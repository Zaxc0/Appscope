"""
Free tier analysis: Basic sentiment, complaints, praise, JTBDs, forces, and outcomes
"""

import streamlit as st
import pandas as pd
import re
from collections import Counter
from textblob import TextBlob

from utils import (
    STOP_WORDS, FEATURE_PATTERNS, FORCE_PATTERNS, OUTCOME_DIMENSIONS,
    extract_sentences, find_keyword_in_text, extract_snippet, 
    extract_complete_sentence, extract_jtbd_components
)


def get_sentiment(text):
    """Calculate sentiment polarity using TextBlob"""
    if not text or pd.isna(text):
        return 'neutral'
    blob = TextBlob(str(text))
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return 'positive'
    elif polarity < -0.1:
        return 'negative'
    return 'neutral'


def analyze_complaints_and_praise(df):
    """Analyze complaints and praise with specific issue extraction"""
    negative_reviews = df[df['rating'] <= 2]['review'].dropna()
    positive_reviews = df[df['rating'] >= 4]['review'].dropna()
    
    complaint_analysis = {}
    praise_analysis = {}
    
    # Analyze complaints with clustering
    for category, keywords in FEATURE_PATTERNS.items():
        matching_reviews = []
        
        for review in negative_reviews:
            keyword = find_keyword_in_text(review, keywords)
            if keyword:
                # Get complete sentence
                sentence = extract_complete_sentence(review, keyword)
                if sentence:
                    matching_reviews.append(sentence)
        
        if len(matching_reviews) > 0:
            # Cluster similar complaints
            complaint_themes = cluster_complaints(matching_reviews, category)
            
            complaint_analysis[category] = {
                'total_count': len(matching_reviews),
                'percentage': (len(matching_reviews) / len(negative_reviews)) * 100,
                'themes': complaint_themes
            }
    
    # Analyze praise
    for category, keywords in FEATURE_PATTERNS.items():
        matching_reviews = []
        
        for review in positive_reviews:
            keyword = find_keyword_in_text(review, keywords)
            if keyword:
                sentence = extract_complete_sentence(review, keyword)
                if sentence:
                    matching_reviews.append(sentence)
        
        if len(matching_reviews) > 0:
            praise_themes = cluster_praise(matching_reviews, category)
            
            praise_analysis[category] = {
                'total_count': len(matching_reviews),
                'percentage': (len(matching_reviews) / len(positive_reviews)) * 100,
                'themes': praise_themes
            }
    
    return complaint_analysis, praise_analysis


def cluster_complaints(reviews, category):
    """Cluster complaints into specific themes"""
    # Common complaint patterns by category
    complaint_patterns = {
        '💰 Pricing/Monetization': [
            ('subscription model', ['subscription', 'recurring', 'monthly', 'yearly', 'one-time', 'one time']),
            ('price too high', ['expensive', 'too much', 'overpriced', 'cost', 'price']),
            ('hidden costs', ['hidden', 'not disclosed', 'surprise', 'didnt know', 'wasn\'t told']),
            ('free trial issues', ['trial', 'free version', 'limited'])
        ],
        '🐛 Bugs/Reliability': [
            ('crashes frequently', ['crash', 'crashes', 'crashing', 'freeze', 'frozen']),
            ('data loss', ['lost', 'deleted', 'disappeared', 'missing', 'gone']),
            ('sync failures', ['sync', 'syncing', 'won\'t sync', 'doesn\'t sync']),
            ('broken features', ['doesn\'t work', 'not working', 'broken', 'stopped working'])
        ],
        '☁️ Sync/Backup': [
            ('sync doesn\'t work', ['sync', 'syncing', 'won\'t sync']),
            ('data loss', ['lost', 'disappeared', 'missing']),
            ('icloud issues', ['icloud', 'cloud']),
            ('can\'t restore backup', ['restore', 'backup', 'recover'])
        ],
        '🎨 UI/UX': [
            ('confusing interface', ['confusing', 'unclear', 'don\'t understand', 'complicated']),
            ('hard to navigate', ['navigate', 'navigation', 'find', 'locate']),
            ('poor design', ['ugly', 'design', 'layout', 'interface']),
            ('not intuitive', ['not intuitive', 'unintuitive', 'not easy'])
        ],
        '⚡ Performance': [
            ('slow', ['slow', 'sluggish', 'laggy', 'lag']),
            ('long loading times', ['loading', 'load', 'wait', 'waiting']),
            ('battery drain', ['battery', 'drain', 'power']),
            ('freezes', ['freeze', 'frozen', 'stuck', 'hangs'])
        ],
        '✨ Features/Functionality': [
            ('missing features', ['missing', 'need', 'want', 'wish', 'should have']),
            ('limited options', ['limited', 'can\'t', 'won\'t let me', 'doesn\'t allow']),
            ('feature requests', ['add', 'please add', 'would be nice']),
            ('removed features', ['removed', 'used to have', 'no longer'])
        ],
        '🔍 Search/Filter': [
            ('search doesn\'t work', ['search', 'searching', 'can\'t find']),
            ('poor filtering', ['filter', 'filtering', 'sort', 'sorting']),
            ('can\'t locate items', ['locate', 'find', 'where is'])
        ],
        '📤 Import/Export': [
            ('export issues', ['export', 'can\'t export', 'won\'t export']),
            ('import problems', ['import', 'can\'t import']),
            ('sharing broken', ['share', 'sharing', 'send']),
            ('pdf generation fails', ['pdf', 'generate'])
        ],
        '👥 Multi-device/Sharing': [
            ('doesn\'t sync across devices', ['devices', 'phone', 'ipad', 'mac', 'tablet']),
            ('no family sharing', ['family', 'share', 'multiple users']),
            ('can\'t share with others', ['share', 'sharing', 'collaborate'])
        ],
        '🆘 Support/Help': [
            ('no response from support', ['support', 'no response', 'didn\'t reply', 'contacted']),
            ('poor documentation', ['help', 'documentation', 'instructions', 'tutorial']),
            ('unresponsive developer', ['developer', 'team', 'contact'])
        ]
    }
    
    themes = []
    patterns = complaint_patterns.get(category, [])
    
    for theme_name, theme_keywords in patterns:
        matching = []
        for review in reviews:
            review_lower = review.lower()
            if any(kw in review_lower for kw in theme_keywords):
                matching.append(review)
        
        if len(matching) > 0:
            themes.append({
                'name': theme_name,
                'count': len(matching),
                'examples': matching[:3]  # Top 3 examples
            })
    
    # Sort by count
    themes.sort(key=lambda x: x['count'], reverse=True)
    return themes[:5]  # Top 5 themes


def cluster_praise(reviews, category):
    """Cluster praise into specific themes"""
    # Common praise patterns by category
    praise_patterns = {
        '💰 Pricing/Monetization': [
            ('good value', ['worth', 'value', 'reasonable', 'fair price']),
            ('free version sufficient', ['free', 'no cost', 'without paying']),
            ('one-time purchase', ['one-time', 'one time', 'lifetime'])
        ],
        '🐛 Bugs/Reliability': [
            ('stable and reliable', ['stable', 'reliable', 'never crashes', 'no bugs']),
            ('works perfectly', ['works', 'working', 'perfect', 'flawless']),
            ('no data loss', ['safe', 'secure', 'never lost'])
        ],
        '☁️ Sync/Backup': [
            ('sync works great', ['sync', 'syncs', 'syncing', 'seamless']),
            ('easy backup', ['backup', 'backed up', 'restore']),
            ('icloud integration', ['icloud', 'cloud'])
        ],
        '🎨 UI/UX': [
            ('intuitive design', ['intuitive', 'easy', 'simple', 'clean']),
            ('beautiful interface', ['beautiful', 'gorgeous', 'love the design']),
            ('easy to navigate', ['navigate', 'find', 'organized'])
        ],
        '⚡ Performance': [
            ('fast and responsive', ['fast', 'quick', 'instantly', 'responsive']),
            ('smooth', ['smooth', 'seamless', 'snappy']),
            ('efficient', ['efficient', 'optimized'])
        ],
        '✨ Features/Functionality': [
            ('feature-rich', ['features', 'everything', 'complete', 'comprehensive']),
            ('flexible', ['flexible', 'customizable', 'options']),
            ('powerful', ['powerful', 'capable', 'advanced'])
        ],
        '🔍 Search/Filter': [
            ('search works great', ['search', 'find', 'easy to find']),
            ('good filtering', ['filter', 'sort', 'organize'])
        ],
        '📤 Import/Export': [
            ('easy export', ['export', 'download', 'save']),
            ('sharing works', ['share', 'sharing', 'send']),
            ('pdf generation', ['pdf', 'report'])
        ],
        '👥 Multi-device/Sharing': [
            ('works on all devices', ['devices', 'phone', 'ipad', 'mac']),
            ('family sharing', ['family', 'share', 'multiple']),
            ('cross-platform', ['platform', 'everywhere'])
        ],
        '🆘 Support/Help': [
            ('responsive support', ['support', 'response', 'helpful', 'developer']),
            ('great documentation', ['help', 'documentation', 'tutorial']),
            ('active development', ['updates', 'improving', 'developer cares'])
        ]
    }
    
    themes = []
    patterns = praise_patterns.get(category, [])
    
    for theme_name, theme_keywords in patterns:
        matching = []
        for review in reviews:
            review_lower = review.lower()
            if any(kw in review_lower for kw in theme_keywords):
                matching.append(review)
        
        if len(matching) > 0:
            themes.append({
                'name': theme_name,
                'count': len(matching),
                'examples': matching[:3]
            })
    
    themes.sort(key=lambda x: x['count'], reverse=True)
    return themes[:5]


def extract_jtbds_from_reviews(reviews, limit=100):
    """
    Extract JTBD statements verbatim from reviews
    Look for clear job statements users naturally express
    """
    jtbd_statements = []
    
    # Patterns that indicate a job statement
    job_patterns = [
        r'(I use|I used|We use|We used) (this|it|the app) (to|for) ([^.!?]{20,150})',
        r'(helps? me|helped me) (to )?(to |with )?([^.!?]{15,150})',
        r'(great|perfect|useful|helpful|ideal) for ([^.!?]{15,100})',
        r'(when|whenever) (I|we) (need to|want to|have to|am|was) ([^.!?]{15,150})',
        r'(so I can|so we can|in order to|to help me) ([^.!?]{15,100})',
    ]
    
    for review in reviews.head(limit):
        review_text = str(review)
        
        # Try each pattern
        for pattern in job_patterns:
            matches = re.finditer(pattern, review_text, re.IGNORECASE)
            for match in matches:
                # Get the full sentence containing this match
                sentences = re.split(r'(?<=[.!?])\s+', review_text)
                for sentence in sentences:
                    if match.group(0).lower() in sentence.lower():
                        # Clean and store
                        clean_sentence = sentence.strip()
                        if 20 < len(clean_sentence) < 300:
                            jtbd_statements.append({
                                'statement': clean_sentence,
                                'full_review': review_text[:300]
                            })
                        break
                break
    
    # Deduplicate very similar statements
    unique_jtbds = []
    seen_starts = set()
    
    for jtbd in jtbd_statements:
        # Use first 30 chars as uniqueness check
        start = jtbd['statement'][:30].lower()
        if start not in seen_starts:
            unique_jtbds.append(jtbd)
            seen_starts.add(start)
    
    return unique_jtbds[:10]  # Top 10 clearest statements


def analyze_forces_of_progress(df):
    """
    Analyze forces with feature-specific context
    Focus on WHAT specifically drives each force
    """
    negative_reviews = df[df['rating'] <= 2]['review'].dropna()
    positive_reviews = df[df['rating'] >= 4]['review'].dropna()
    all_reviews = df['review'].dropna()
    
    forces_analysis = {}
    
    # Push: What's failing with current solutions
    push_scenarios = []
    push_keywords = ['cant', 'wont', 'doesnt work', 'broken', 'useless', 'frustrated', 
                     'annoying', 'terrible', 'waste', 'failed', 'problem', 'issue']
    
    for review in negative_reviews:
        review_lower = str(review).lower()
        for keyword in push_keywords:
            if keyword in review_lower:
                sentence = extract_complete_sentence(review, keyword, max_length=250)
                if sentence and len(sentence) > 30:
                    push_scenarios.append(sentence)
                    break
    
    if len(push_scenarios) > 0:
        forces_analysis['push'] = {
            'label': '🔴 Push (Current Solution Fails)',
            'count': len(push_scenarios),
            'scenarios': list(set(push_scenarios))[:5],
            'insight': f"{len(push_scenarios)} mentions of current solution failures"
        }
    
    # Pull: What attracts them to THIS solution specifically
    pull_scenarios = []
    pull_keywords = ['love', 'great', 'perfect', 'exactly', 'finally', 'best', 
                     'favorite', 'awesome', 'amazing', 'easy', 'simple']
    
    for review in positive_reviews:
        review_lower = str(review).lower()
        for keyword in pull_keywords:
            if keyword in review_lower:
                sentence = extract_complete_sentence(review, keyword, max_length=250)
                if sentence and len(sentence) > 30:
                    pull_scenarios.append(sentence)
                    break
    
    if len(pull_scenarios) > 0:
        forces_analysis['pull'] = {
            'label': '🟢 Pull (Why This App)',
            'count': len(pull_scenarios),
            'scenarios': list(set(pull_scenarios))[:5],
            'insight': f"{len(pull_scenarios)} mentions of specific attractions"
        }
    
    # Anxiety: Fears about switching/adoption
    anxiety_scenarios = []
    anxiety_keywords = ['worried', 'concern', 'afraid', 'risk', 'lose', 'lost', 
                       'scary', 'unsure', 'dont trust', 'what if']
    
    for review in all_reviews:
        review_lower = str(review).lower()
        for keyword in anxiety_keywords:
            if keyword in review_lower:
                sentence = extract_complete_sentence(review, keyword, max_length=250)
                if sentence and len(sentence) > 30:
                    anxiety_scenarios.append(sentence)
                    break
    
    if len(anxiety_scenarios) > 0:
        forces_analysis['anxiety'] = {
            'label': '🟡 Anxiety (Switching Fears)',
            'count': len(anxiety_scenarios),
            'scenarios': list(set(anxiety_scenarios))[:5],
            'insight': f"{len(anxiety_scenarios)} mentions of concerns/fears"
        }
    
    # Habit: Inertia/status quo
    habit_scenarios = []
    habit_keywords = ['always', 'used to', 'familiar', 'years', 'long time', 
                     'accustomed', 'comfortable', 'switch from', 'tried other']
    
    for review in all_reviews:
        review_lower = str(review).lower()
        for keyword in habit_keywords:
            if keyword in review_lower:
                sentence = extract_complete_sentence(review, keyword, max_length=250)
                if sentence and len(sentence) > 30:
                    habit_scenarios.append(sentence)
                    break
    
    if len(habit_scenarios) > 0:
        forces_analysis['habit'] = {
            'label': '🔵 Habit (Status Quo)',
            'count': len(habit_scenarios),
            'scenarios': list(set(habit_scenarios))[:5],
            'insight': f"{len(habit_scenarios)} mentions of past solutions/habits"
        }
    
    return forces_analysis


def analyze_outcomes(df):
    """
    Simplified outcome analysis: top pain points and wins
    Skip ODI format, just show what matters with counts
    """
    all_reviews = df['review'].dropna()
    negative_reviews = df[df['rating'] <= 2]['review'].dropna()
    positive_reviews = df[df['rating'] >= 4]['review'].dropna()
    
    # Pain points (things users complain about)
    pain_points = {}
    pain_keywords = {
        'Missing features': ['missing', 'need', 'wish', 'want', 'would be nice', 'should have', 'please add'],
        'Too expensive': ['expensive', 'cost', 'price', 'too much', 'overpriced', 'subscription'],
        'Doesnt work': ['doesnt work', 'not working', 'broken', 'crashes', 'fails', 'error'],
        'Confusing': ['confusing', 'complicated', 'hard to', 'difficult', 'dont understand'],
        'Slow': ['slow', 'laggy', 'takes forever', 'waiting', 'loading'],
        'Data loss': ['lost', 'disappeared', 'deleted', 'missing', 'gone'],
        'No sync': ['sync', 'wont sync', 'doesnt sync', 'cloud', 'backup'],
        'Poor support': ['support', 'no response', 'no help', 'ignored', 'developer']
    }
    
    for pain, keywords in pain_keywords.items():
        examples = []
        for review in negative_reviews:
            review_lower = str(review).lower()
            for keyword in keywords:
                if keyword in review_lower:
                    sentence = extract_complete_sentence(review, keyword, max_length=200)
                    if sentence:
                        examples.append(sentence)
                    break
        
        if len(examples) > 0:
            pain_points[pain] = {
                'count': len(examples),
                'percentage': (len(examples) / len(negative_reviews)) * 100,
                'examples': list(set(examples))[:3]
            }
    
    # Wins (things users love)
    wins = {}
    win_keywords = {
        'Easy to use': ['easy', 'simple', 'intuitive', 'straightforward', 'user-friendly'],
        'Fast': ['fast', 'quick', 'instant', 'immediately', 'quickly'],
        'Feature-rich': ['features', 'everything', 'comprehensive', 'complete', 'all I need'],
        'Reliable': ['reliable', 'stable', 'works great', 'no issues', 'never crashes'],
        'Good value': ['worth it', 'value', 'reasonable', 'fair price', 'one-time'],
        'Great support': ['support', 'responsive', 'helpful', 'developer', 'quick response'],
        'Syncs well': ['sync', 'syncs', 'cloud', 'backup', 'devices'],
        'Beautiful UI': ['beautiful', 'clean', 'design', 'interface', 'looks great']
    }
    
    for win, keywords in win_keywords.items():
        examples = []
        for review in positive_reviews:
            review_lower = str(review).lower()
            for keyword in keywords:
                if keyword in review_lower:
                    sentence = extract_complete_sentence(review, keyword, max_length=200)
                    if sentence:
                        examples.append(sentence)
                    break
        
        if len(examples) > 0:
            wins[win] = {
                'count': len(examples),
                'percentage': (len(examples) / len(positive_reviews)) * 100,
                'examples': list(set(examples))[:3]
            }
    
    return pain_points, wins


def run_free_analysis(df):
    """Main function to run all free analysis and display results - Improved UI"""
    
    # Add sentiment column
    df['text_sentiment'] = df['review'].apply(get_sentiment)
    
    # Run all analyses upfront
    complaint_analysis, praise_analysis = analyze_complaints_and_praise(df)
    
    # === EXECUTIVE SUMMARY (Key Insights at Top) ===
    st.markdown("## 💡 Executive Summary")
    st.caption("Your most important insights at a glance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**#1 Risk**")
        sorted_complaints = sorted(complaint_analysis.items(), key=lambda x: x[1]['total_count'], reverse=True)
        if len(sorted_complaints) > 0 and sorted_complaints[0][1]['themes']:
            top_theme = sorted_complaints[0][1]['themes'][0]
            st.warning(f"**{top_theme['name'].capitalize()}**\n\n{top_theme['count']} mentions\n\n*\"{top_theme['examples'][0][:80]}...\"*")
        else:
            st.info("Not enough data")
    
    with col2:
        st.markdown("**#1 Strength**")
        sorted_praise = sorted(praise_analysis.items(), key=lambda x: x[1]['total_count'], reverse=True)
        if len(sorted_praise) > 0 and sorted_praise[0][1]['themes']:
            top_theme = sorted_praise[0][1]['themes'][0]
            st.success(f"**{top_theme['name'].capitalize()}**\n\n{top_theme['count']} mentions\n\n*\"{top_theme['examples'][0][:80]}...\"*")
        else:
            st.info("Not enough data")
    
    st.markdown("---")
    
    # === TABBED DEEP DIVE ===
    st.markdown("## 📊 Detailed Analysis")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Complaints", "Praise", "Jobs to Be Done", "Forces"])
    
    # TAB 1: COMPLAINTS
    with tab1:
        st.caption("Specific issues mentioned in negative reviews")
        
        sorted_complaints = sorted(complaint_analysis.items(), key=lambda x: x[1]['total_count'], reverse=True)
        
        if len(sorted_complaints) > 0:
            for idx, (category, data) in enumerate(sorted_complaints[:6]):
                with st.expander(
                    f"{category} ({data['total_count']})",
                    expanded=(idx==0)
                ):
                    st.caption(f"{data['percentage']:.0f}% of negative reviews")
                    
                    for theme in data['themes']:
                        st.markdown(f"**{theme['name'].capitalize()}** — {theme['count']} mentions")
                        for example in theme['examples']:
                            st.markdown(f"> {example}")
                        st.markdown("")
        else:
            st.info("Not enough negative reviews to analyze")
    
    # TAB 2: PRAISE
    with tab2:
        st.caption("Most praised aspects in positive reviews")
        
        sorted_praise = sorted(praise_analysis.items(), key=lambda x: x[1]['total_count'], reverse=True)
        
        if len(sorted_praise) > 0:
            for idx, (category, data) in enumerate(sorted_praise[:6]):
                with st.expander(
                    f"{category} ({data['total_count']})",
                    expanded=(idx==0)
                ):
                    st.caption(f"{data['percentage']:.0f}% of positive reviews")
                    
                    for theme in data['themes']:
                        st.markdown(f"**{theme['name'].capitalize()}** — {theme['count']} mentions")
                        for example in theme['examples']:
                            st.markdown(f"> {example}")
                        st.markdown("")
        else:
            st.info("Not enough positive reviews to analyze")
    
    # TAB 3: JOBS TO BE DONE
    with tab3:
        st.caption("What progress are users trying to make?")
        
        positive_reviews = df[df['rating'] >= 4]['review'].dropna()
        jtbd_statements = extract_jtbds_from_reviews(positive_reviews, limit=100)
        
        if len(jtbd_statements) > 0:
            st.markdown(f"**Found {len(jtbd_statements)} clear job statements:**")
            st.markdown("")
            
            for idx, jtbd in enumerate(jtbd_statements, 1):
                st.markdown(f"**{idx}.** {jtbd['statement']}")
                st.markdown("")
        else:
            st.info("No clear job statements found. Users may not be explicitly describing their use cases.")
    
    # TAB 4: FORCES OF PROGRESS
    with tab4:
        st.caption("What drives users toward or away from this app")
        
        forces_analysis = analyze_forces_of_progress(df)
        
        force_order = ['push', 'pull', 'anxiety', 'habit']
        for force in force_order:
            if force in forces_analysis:
                data = forces_analysis[force]
                with st.expander(
                    f"{data['label']} ({data['count']})",
                    expanded=(force in ['push', 'pull'])
                ):
                    st.caption(data['insight'])
                    for idx, scenario in enumerate(data['scenarios'], 1):
                        st.markdown(f"{idx}. {scenario}")
                        st.markdown("")
    
    st.markdown("---")
    
    # === SAMPLE REVIEWS (Collapsed) ===
    with st.expander("📝 Sample Reviews", expanded=False):
        tab_pos, tab_neu, tab_neg = st.tabs(["Positive (4-5★)", "Neutral (3★)", "Negative (1-2★)"])
        
        with tab_pos:
            positive_revs = df[df['rating'] >= 4].head(5)
            for _, review in positive_revs.iterrows():
                title = review['title'][:50] if review['title'] else "No title"
                with st.expander(f"⭐ {review['rating']} - {title}"):
                    st.markdown(review['review'])
                    st.caption(f"👤 {review['author']} • 📅 {review['date']} • 📱 v{review['version']}")
        
        with tab_neu:
            neutral_revs = df[df['rating'] == 3].head(5)
            if len(neutral_revs) > 0:
                for _, review in neutral_revs.iterrows():
                    title = review['title'][:50] if review['title'] else "No title"
                    with st.expander(f"⭐ 3 - {title}"):
                        st.markdown(review['review'])
                        st.caption(f"👤 {review['author']} • 📅 {review['date']} • 📱 v{review['version']}")
            else:
                st.info("No neutral reviews found")
        
        with tab_neg:
            negative_revs = df[df['rating'] <= 2].head(5)
            if len(negative_revs) > 0:
                for _, review in negative_revs.iterrows():
                    title = review['title'][:50] if review['title'] else "No title"
                    with st.expander(f"⭐ {review['rating']} - {title}"):
                        st.markdown(review['review'])
                        st.caption(f"👤 {review['author']} • 📅 {review['date']} • 📱 v{review['version']}")
            else:
                st.info("No negative reviews found")