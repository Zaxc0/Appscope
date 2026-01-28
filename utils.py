"""
Utility functions and constants for AppScope
"""

import re
from collections import Counter

# Comprehensive stop words
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
    'of', 'with', 'is', 'was', 'it', 'this', 'that', 'i', 'my', 'app',
    'have', 'has', 'had', 'be', 'been', 'are', 'am', 'you', 'your',
    'not', 'can', 'will', 'just', 'so', 'than', 'very', 'really',
    'all', 'get', 'use', 'using', 'used', 'would', 'could', 'should',
    'like', 'do', 'does', 'did', 'one', 'two', 'even', 'also', 'me',
    'up', 'out', 'if', 'about', 'which', 'when', 'where', 'who', 'how',
    'their', 'them', 'they', 'there', 'these', 'those', 'then', 'from',
    'what', 'because', 'were', 'being', 'into', 'through', 'during'
}

# Universal feature categories (work for any app)
FEATURE_PATTERNS = {
    '💰 Pricing/Monetization': [
        'subscription', 'price', 'cost', 'expensive', 'cheap', 'free', 'paid',
        'pay', 'purchase', 'buy', 'money', 'dollar', 'trial', 'refund'
    ],
    '🐛 Bugs/Reliability': [
        'crash', 'crashes', 'bug', 'bugs', 'freeze', 'error', 'glitch',
        'broken', 'stopped', 'working', 'fail', 'failed', 'problem'
    ],
    '☁️ Sync/Backup': [
        'sync', 'syncing', 'synchronize', 'backup', 'restore', 'cloud',
        'icloud', 'save', 'saved', 'autosave', 'lost', 'data'
    ],
    '🎨 UI/UX': [
        'interface', 'design', 'layout', 'navigation', 'confusing', 'easy',
        'simple', 'intuitive', 'complicated', 'ugly', 'beautiful', 'clean'
    ],
    '⚡ Performance': [
        'slow', 'fast', 'speed', 'lag', 'loading', 'quick', 'responsive',
        'smooth', 'sluggish', 'performance'
    ],
    '✨ Features/Functionality': [
        'feature', 'features', 'function', 'functionality', 'option', 'options',
        'missing', 'need', 'want', 'wish', 'add', 'remove'
    ],
    '🔍 Search/Filter': [
        'search', 'find', 'filter', 'sort', 'lookup', 'locate'
    ],
    '📤 Import/Export': [
        'import', 'export', 'share', 'sharing', 'download', 'upload',
        'pdf', 'csv', 'email'
    ],
    '👥 Multi-device/Sharing': [
        'device', 'devices', 'phone', 'ipad', 'mac', 'tablet', 'share',
        'family', 'multiple'
    ],
    '🆘 Support/Help': [
        'support', 'help', 'customer', 'service', 'contact', 'response',
        'developer', 'team', 'reply'
    ]
}

# Forces of Progress patterns (Switch framework)
FORCE_PATTERNS = {
    'push': {
        'keywords': ['frustrated', 'annoying', 'difficult', 'problem', 'struggle', 'hate', 
                   'cant', 'wont', 'doesnt work', 'broken', 'terrible', 'awful', 'waste'],
        'label': '🔴 Push (Problems with Current)',
        'jtbd_format': 'Current solution fails when...'
    },
    'pull': {
        'keywords': ['love', 'great', 'amazing', 'easy', 'simple', 'perfect', 'exactly', 
                   'finally', 'awesome', 'excellent', 'best', 'favorite'],
        'label': '🟢 Pull (Attraction to New)',
        'jtbd_format': 'New solution appeals because...'
    },
    'anxiety': {
        'keywords': ['worried', 'concern', 'afraid', 'risk', 'lose', 'lost', 'scary', 
                   'trust', 'security', 'privacy', 'safe', 'unsure'],
        'label': '🟡 Anxiety (Fears about Switching)',
        'jtbd_format': 'Users worry that...'
    },
    'habit': {
        'keywords': ['always', 'usually', 'used to', 'familiar', 'comfortable', 
                   'stick with', 'years', 'long time', 'accustomed'],
        'label': '🔵 Habit (Inertia/Status Quo)',
        'jtbd_format': 'Users stay because...'
    }
}

# Outcome dimensions (ODI-style)
OUTCOME_DIMENSIONS = {
    'Speed/Time': {
        'positive': ['fast', 'quick', 'quickly', 'instant', 'immediate', 'save time'],
        'negative': ['slow', 'takes forever', 'waste time', 'waiting', 'delayed'],
        'odi_template': 'Minimize the time it takes to'
    },
    'Ease of Use': {
        'positive': ['easy', 'easier', 'simple', 'simpler', 'intuitive', 'straightforward'],
        'negative': ['difficult', 'hard', 'complicated', 'confusing', 'complex', 'unclear'],
        'odi_template': 'Minimize the difficulty in'
    },
    'Reliability': {
        'positive': ['reliable', 'stable', 'consistent', 'dependable', 'works'],
        'negative': ['crash', 'bug', 'broken', 'fail', 'error', 'glitch'],
        'odi_template': 'Minimize the likelihood of'
    },
    'Completeness': {
        'positive': ['complete', 'comprehensive', 'everything', 'all', 'thorough'],
        'negative': ['missing', 'incomplete', 'lacking', 'need more', 'forgot'],
        'odi_template': 'Minimize the number of missing'
    },
    'Control/Flexibility': {
        'positive': ['control', 'customize', 'flexible', 'options', 'adjust', 'configure'],
        'negative': ['limited', 'stuck', 'cant change', 'locked', 'restricted'],
        'odi_template': 'Increase the ability to'
    },
    'Confidence': {
        'positive': ['confident', 'trust', 'sure', 'certain', 'reliable'],
        'negative': ['worried', 'unsure', 'concerned', 'doubt', 'risk'],
        'odi_template': 'Increase confidence that'
    }
}


def extract_app_id(url):
    """Extract app ID from App Store URL"""
    match = re.search(r'/id(\d+)', url)
    return match.group(1) if match else None


def extract_sentences(text):
    """Split text into sentences"""
    return re.split(r'[.!?]+', str(text))


def find_keyword_in_text(text, keywords):
    """Check if any keyword exists in text, return first match"""
    text_lower = str(text).lower()
    for keyword in keywords:
        if keyword in text_lower:
            return keyword
    return None


def extract_snippet(text, keyword, before=30, after=100):
    """Extract a snippet of text around a keyword"""
    text_str = str(text)
    text_lower = text_str.lower()
    
    if keyword not in text_lower:
        return None
    
    idx = text_lower.find(keyword)
    start = max(0, idx - before)
    end = min(len(text_str), idx + after)
    
    return text_str[start:end].strip()


def extract_complete_sentence(text, keyword, max_length=400):
    """Extract complete sentence(s) containing a keyword"""
    text_str = str(text)
    text_lower = text_str.lower()
    
    if keyword not in text_lower:
        return None
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text_str)
    
    # Find sentence containing keyword
    for i, sentence in enumerate(sentences):
        if keyword in sentence.lower():
            result = sentence.strip()
            
            # If sentence is too short, add adjacent sentences
            if len(result) < 50 and i + 1 < len(sentences):
                result += " " + sentences[i + 1].strip()
            if len(result) < 50 and i > 0:
                result = sentences[i - 1].strip() + " " + result
            
            # Cap at max length
            if len(result) > max_length:
                result = result[:max_length] + "..."
            
            return result
    
    return None


def extract_jtbd_components(text):
    """Extract situation, action, and outcome from review text"""
    text_lower = str(text).lower()
    
    # Situation signals
    situation_patterns = [
        r'when (i|we) (need|want|have to|am|was) ([^,\.]{10,80})',
        r'(after|during|while|before) ([^,\.]{10,80})',
        r'for (my|our) ([^,\.]{10,50})',
    ]
    
    # Outcome signals
    outcome_patterns = [
        r'so (i|we) can ([^,\.]{10,80})',
        r'(helps|helped|allows|lets) (me|us) (to )?([^,\.]{10,80})',
        r'in order to ([^,\.]{10,80})',
        r'because (i|we) (need|want) ([^,\.]{10,80})',
    ]
    
    situation = None
    outcome = None
    
    # Extract situation
    for pattern in situation_patterns:
        match = re.search(pattern, text_lower)
        if match:
            situation = match.group(0)
            break
    
    # Extract outcome
    for pattern in outcome_patterns:
        match = re.search(pattern, text_lower)
        if match:
            outcome = match.group(0)
            break
    
    return situation, outcome