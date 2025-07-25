import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from sklearn.preprocessing import StandardScaler
import re
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('vader_lexicon')

# Word lists for feature extraction
action_verb_list = {'urgent', 'important', 'asap', 'deadline', 'reminder', 'request', 'need', 'required', 'critical', 'action', 'immediate', 'attention', 'review', 'approve', 'complete', 'submit', 'update', 'respond', 'confirm', 'verify'}
urgency_words = {'urgent', 'asap', 'immediate', 'emergency', 'critical', 'important', 'attention', 'deadline', 'due', 'now', 'today', 'tomorrow'}
risk_words = {'risk', 'security', 'breach', 'critical', 'emergency', 'issue', 'problem', 'error', 'failure', 'warning', 'alert', 'threat', 'vulnerability'}

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

def clean_text(text):
    """Clean text by removing special characters and converting to lowercase"""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = ''.join(c for c in text if c.isalnum() or c.isspace())
    return text.strip()

def extract_features(subject, message):
    """Extract features from email subject and message"""
    try:
        # Convert inputs to strings
        subject = str(subject).lower() if subject else ""
        message = str(message).lower() if message else ""
        
        # Initialize features dictionary
        features = {}
        
        # Basic length features
        features['subject_length'] = len(subject)
        features['message_length'] = len(message)
        
        # Word count features
        features['subject_word_count'] = len(subject.split())
        features['message_word_count'] = len(message.split())
        
        # Uppercase word features
        features['subject_uppercase_count'] = sum(1 for word in subject.split() if word.isupper())
        features['message_uppercase_count'] = sum(1 for word in message.split() if word.isupper())
        
        # Special character features
        features['subject_special_chars'] = sum(not c.isalnum() and not c.isspace() for c in subject)
        features['message_special_chars'] = sum(not c.isalnum() and not c.isspace() for c in message)
        
        # Sentiment analysis
        subject_sentiment = sia.polarity_scores(subject)
        message_sentiment = sia.polarity_scores(message)
        
        features['subject_sentiment'] = subject_sentiment['compound']
        features['message_sentiment'] = message_sentiment['compound']
        features['total_sentiment'] = (subject_sentiment['compound'] + message_sentiment['compound']) / 2
        
        # Urgency and risk scores
        features['has_urgency'] = float(has_urgency_words(subject) or has_urgency_words(message))
        features['has_risk'] = float(has_risk_words(subject) or has_risk_words(message))
        
        return features
        
    except Exception as e:
        print(f"Error in extract_features: {str(e)}")
        # Return default features on error
        return {
            'subject_length': 0,
            'message_length': 0,
            'subject_word_count': 0,
            'message_word_count': 0,
            'subject_uppercase_count': 0,
            'message_uppercase_count': 0,
            'subject_special_chars': 0,
            'message_special_chars': 0,
            'subject_sentiment': 0,
            'message_sentiment': 0,
            'total_sentiment': 0,
            'has_urgency': 0,
            'has_risk': 0
        }

def has_casual_words(text):
    """Check if text contains casual/social keywords"""
    text = text.lower()
    casual_words = {
        'lunch', 'dinner', 'coffee', 'break', 'social', 'fun',
        'party', 'gathering', 'celebration', 'birthday', 'holiday',
        'weekend', 'plans', 'invite', 'join', 'catch up', 'chat',
        'casual', 'informal', 'relax', 'enjoy', 'hang out'
    }
    return any(word in text for word in casual_words)

def has_promotional_words(text):
    """Check if text contains promotional or marketing related words"""
    promo_words = {
        'sale', 'discount', 'offer', 'deal', 'save', 'promotion', 'limited time',
        'special', 'exclusive', 'new', 'catalogue', 'catalog', 'newsletter',
        'subscribe', 'unsubscribe', 'marketing', 'advertisement', 'promo',
        'off', 'price', 'pricing', 'buy', 'shop', 'shopping', 'store'
    }
    return any(word.lower() in text.lower() for word in promo_words)

def has_notification_words(text):
    """Check if text contains notification or update related words"""
    notif_words = {
        'notification', 'update', 'digest', 'newsletter', 'weekly', 'daily',
        'monthly', 'follow', 'following', 'likes', 'views', 'posts', 'feed',
        'subscription', 'no-reply', 'noreply', 'automated'
    }
    return any(word.lower() in text.lower() for word in notif_words)

def is_automated_sender(sender):
    """Check if the sender appears to be an automated/system account."""
    if not isinstance(sender, str):
        return False
    
    sender = sender.lower()
    automated_patterns = [
        'noreply', 'no-reply', 'notification', 'alert', 'system', 'auto', 'donotreply',
        'marketing', 'newsletter', 'info@', 'support@', 'hello@', 'updates@', 'news@',
        'announcements@', 'campaign'
    ]
    
    # Check domain for common automated senders
    automated_domains = [
        'linkedin.com', 'instagram.com', 'facebook.com', 'twitter.com',
        'notifications.google.com', 'mail.google.com', 'em.', 'enews.',
        'marketing.', 'campaigns.'
    ]
    
    # Check for automated patterns in sender
    for pattern in automated_patterns:
        if pattern in sender:
            return True
            
    # Check for automated domains
    for domain in automated_domains:
        if domain in sender:
            return True
            
    return False

def load_models():
    """Load trained models for priority prediction"""
    try:
        # Load models
        high_model = xgb.Booster()
        high_model.load_model('Models/high_priority_model.json')
        medium_model = xgb.Booster()
        medium_model.load_model('Models/medium_priority_model.json')
        low_model = xgb.Booster()
        low_model.load_model('Models/low_priority_model.json')
        
        return [high_model, medium_model, low_model]
    except Exception as e:
        print(f"Error loading models: {str(e)}")
        return []

def predict_priority(subject, message, sender=None):
    """
    Predict email priority based on content analysis.
    Returns: (priority, confidence_scores)
    """
    try:
        # Initialize confidence scores
        confidence_scores = {
            'low': 0.0,
            'medium': 0.0, 
            'high': 0.0
        }
        
        # Convert inputs to strings and lowercase
        subject = str(subject).lower() if subject else ""
        message = str(message).lower() if message else ""
        sender = str(sender).lower() if sender else ""
        
        # Check for automated/promotional content first
        if sender and is_automated_sender(sender):
            if has_urgency_words(subject) or has_risk_words(subject):
                confidence_scores['medium'] = 0.7
                confidence_scores['low'] = 0.2
                confidence_scores['high'] = 0.1
                return 'MEDIUM', confidence_scores
            else:
                confidence_scores['low'] = 0.9
                confidence_scores['medium'] = 0.1
                confidence_scores['high'] = 0.0
                return 'LOW', confidence_scores
            
        if has_promotional_words(subject) or has_promotional_words(message):
            if has_urgency_words(subject) or has_risk_words(subject):
                confidence_scores['medium'] = 0.6
                confidence_scores['low'] = 0.3
                confidence_scores['high'] = 0.1
                return 'MEDIUM', confidence_scores
            else:
                confidence_scores['low'] = 0.8
                confidence_scores['medium'] = 0.2
                confidence_scores['high'] = 0.0
                return 'LOW', confidence_scores
            
        # Extract features
        features = extract_features(subject, message)
        sentiment_score = features['total_sentiment']
        
        # Check for high priority indicators
        subject_urgency = has_urgency_words(subject)
        message_urgency = has_urgency_words(message)
        subject_risk = has_risk_words(subject)
        message_risk = has_risk_words(message)
        
        # High priority conditions
        if (subject_urgency and subject_risk) or (subject_urgency and message_risk) or (subject_risk and message_urgency):
            confidence_scores['high'] = 0.8
            confidence_scores['medium'] = 0.2
            confidence_scores['low'] = 0.0
            return 'HIGH', confidence_scores
            
        if subject_urgency or subject_risk:
            if sentiment_score < -0.3:  # Negative sentiment
                confidence_scores['high'] = 0.7
                confidence_scores['medium'] = 0.2
                confidence_scores['low'] = 0.1
                return 'HIGH', confidence_scores
            else:
                confidence_scores['medium'] = 0.7
                confidence_scores['high'] = 0.2
                confidence_scores['low'] = 0.1
                return 'MEDIUM', confidence_scores
                
        if message_urgency or message_risk:
            if sentiment_score < -0.3:  # Negative sentiment
                confidence_scores['medium'] = 0.7
                confidence_scores['high'] = 0.2
                confidence_scores['low'] = 0.1
                return 'MEDIUM', confidence_scores
            else:
                confidence_scores['medium'] = 0.6
                confidence_scores['low'] = 0.3
                confidence_scores['high'] = 0.1
                return 'MEDIUM', confidence_scores
                
        # Default to low priority
        confidence_scores['low'] = 0.6
        confidence_scores['medium'] = 0.3
        confidence_scores['high'] = 0.1
        return 'LOW', confidence_scores
        
    except Exception as e:
        print(f"Error in predict_priority: {str(e)}")
        # Default confidence scores on error
        confidence_scores = {'low': 0.4, 'medium': 0.4, 'high': 0.2}
        return 'MEDIUM', confidence_scores

def has_urgency_words(text):
    """Check if text contains urgency-related words"""
    if not isinstance(text, str):
        return False
        
    text = text.lower()
    urgency_words = [
        'urgent', 'asap', 'immediate', 'emergency', 'critical', 'deadline',
        'important', 'priority', 'time-sensitive', 'due', 'required',
        'action needed', 'action required', 'respond', 'attention',
        'review needed', 'approval needed', 'confirm', 'verify',
        'reminder', 'don\'t forget', 'last chance', 'expiring',
        'limited time', 'closing soon', 'expires', 'final notice'
    ]
    return any(word in text for word in urgency_words)

def has_risk_words(text):
    """Check if text contains risk-related words"""
    if not isinstance(text, str):
        return False
        
    text = text.lower()
    risk_words = [
        'risk', 'warning', 'alert', 'caution', 'danger', 'security',
        'breach', 'violation', 'error', 'failure', 'problem', 'issue',
        'incident', 'unauthorized', 'suspicious', 'compromised',
        'vulnerability', 'threat', 'malicious', 'fraud', 'scam',
        'password', 'login', 'access', 'verification', 'authenticate',
        'blocked', 'restricted', 'overdue', 'missing', 'failed'
    ]
    return any(word in text for word in risk_words)

def explain_prediction(subject, message, priority, confidence_scores, sender=None):
    """Provide an explanation for the priority prediction."""
    try:
        subject = str(subject).lower() if subject else ""
        message = str(message).lower() if message else ""
        sender = str(sender).lower() if sender else ""
        
        explanation = []
        
        # Check sender type
        if sender and is_automated_sender(sender):
            explanation.append("This appears to be an automated email.")
            
        # Check for promotional/notification content
        if has_promotional_words(subject) or has_promotional_words(message):
            explanation.append("This email contains promotional content.")
        elif has_notification_words(subject) or has_notification_words(message):
            explanation.append("This appears to be a notification or update email.")
            
        # Extract features for analysis
        features = extract_features(subject, message)
        
        # Add feature-based explanations
        if features['has_urgency'] > 0.5:
            explanation.append(f"Urgency indicators detected (score: {features['has_urgency']:.2f})")
        if features['has_risk'] > 0.5:
            explanation.append(f"Risk indicators detected (score: {features['has_risk']:.2f})")
        if features['total_sentiment'] < -0.3:
            explanation.append("Negative sentiment detected in the content")
            
        # Add confidence information
        confidence_info = f"Confidence scores: Low ({confidence_scores['low']:.0%}), "
        confidence_info += f"Medium ({confidence_scores['medium']:.0%}), "
        confidence_info += f"High ({confidence_scores['high']:.0%})"
        explanation.append(confidence_info)
        
        return " ".join(explanation)
        
    except Exception as e:
        return f"Error generating explanation: {str(e)}"

def main():
    # Test cases
    test_cases = [
        {
            'subject': 'URGENT: System Maintenance Tonight',
            'message': 'We need to perform critical system maintenance tonight. All systems will be down for 2 hours starting at 10 PM. Please save your work and log out before the maintenance window.',
            'expected': 'high'
        },
        {
            'subject': 'Weekly Team Meeting Reminder',
            'message': 'This is a reminder about our weekly team meeting tomorrow at 2 PM. Please prepare your project updates and join on time.',
            'expected': 'medium'
        },
        {
            'subject': 'Lunch Plans',
            'message': 'Would you like to join me for lunch tomorrow? I was thinking we could try that new restaurant downtown.',
            'expected': 'low'
        },
        {
            'subject': 'CRITICAL: Security Breach Detected',
            'message': 'A security breach has been detected in our system. Immediate action is required. Please follow the emergency protocol and change your passwords immediately.',
            'expected': 'high'
        },
        {
            'subject': 'Project Update Request',
            'message': 'Could you please provide an update on the current project status? We need this information for the monthly review meeting.',
            'expected': 'medium'
        }
    ]
    
    print("Testing Ensemble Models on New Email Examples")
    print("=" * 50)
    
    correct = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Subject: {test_case['subject']}")
        print(f"Expected Priority: {test_case['expected']}")
        
        priority, confidences = predict_priority(test_case['subject'], test_case['message'], test_case['sender'])
        print(f"Predicted Priority: {priority}")
        
        explain_prediction(test_case['subject'], test_case['message'], priority, confidences, test_case['sender'])
        
        if priority == test_case['expected']:
            print("Result: ✓ Correct")
            correct += 1
        else:
            print("Result: ✗ Incorrect")
        
        print("-" * 50)
    
    print(f"\nOverall Accuracy: {correct/total*100:.2f}% ({correct}/{total})")

if __name__ == "__main__":
    main() 