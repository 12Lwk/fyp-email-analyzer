import xgboost as xgb
import joblib
import pandas as pd
import numpy as np
import re
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

# Download required NLTK data
nltk.download('vader_lexicon', quiet=True)

def clean_text(text):
    """Clean and preprocess text"""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    text = ' '.join(text.split())
    return text

def preprocess_email(subject, message):
    """Preprocess email and extract features"""
    # Clean text
    cleaned_subject = clean_text(subject)
    cleaned_message = clean_text(message)
    combined_text = cleaned_subject + ' ' + cleaned_message
    
    # Initialize sentiment analyzer
    sia = SentimentIntensityAnalyzer()
    
    # Feature sets
    urgency_words = {
        'urgent', 'asap', 'emergency', 'immediate', 'critical', 'important',
        'priority', 'urgent priority', 'high priority', 'deadline', 'due',
        'escalation', 'escalated', 'time sensitive', 'action required',
        'now', 'immediately', 'right away', 'expedite', 'rush'
    }
    
    risk_words = {
        'risk', 'warning', 'alert', 'danger', 'critical', 'serious',
        'issue', 'problem', 'failure', 'error', 'outage', 'breach',
        'security', 'compliance', 'violation', 'incident', 'crash',
        'malfunction', 'broken', 'down', 'vulnerability'
    }
    
    action_verbs = {
        'review', 'approve', 'confirm', 'update', 'respond', 'complete',
        'submit', 'verify', 'check', 'investigate', 'resolve', 'fix',
        'implement', 'test', 'deploy', 'analyze', 'assess', 'evaluate',
        'execute', 'finalize', 'process', 'validate'
    }
    
    # Low priority indicators
    informational_words = {
        'newsletter', 'digest', 'update', 'roundup', 'summary', 'weekly',
        'monthly', 'quarterly', 'announcement', 'news', 'introduction',
        'welcome', 'fyi', 'info', 'information', 'reminder', 'notification'
    }
    
    social_words = {
        'social', 'event', 'party', 'celebration', 'lunch', 'dinner',
        'game', 'fun', 'activity', 'survey', 'poll', 'feedback',
        'rsvp', 'invitation', 'celebrate', 'join', 'team building'
    }
    
    optional_phrases = {
        'when you have time', 'at your convenience', 'if you want',
        'feel free', 'optional', 'if you would like', 'if you wish',
        'no action required', 'for your information', 'when possible',
        'at your earliest convenience', 'when you get a chance'
    }
    
    # Calculate features
    subject_words = cleaned_subject.split()
    message_words = cleaned_message.split()
    
    # Sentiment scores
    subject_sentiment = sia.polarity_scores(subject)
    message_sentiment = sia.polarity_scores(message)
    
    # Urgency and risk scores
    urgency_score = sum(2 if word in subject_words else 1 
                      for word in urgency_words 
                      if word in combined_text.split())
    risk_score = sum(2 if word in subject_words else 1 
                    for word in risk_words 
                    if word in combined_text.split())
    
    # Normalize scores
    max_urgency = len(urgency_words) * 2
    max_risk = len(risk_words) * 2
    
    urgency_flag = min(urgency_score / max_urgency, 1.0)
    risk_flag = min(risk_score / max_risk, 1.0)
    urgency_and_risk = urgency_flag * risk_flag
    
    # Action verbs
    num_action_verbs = sum(2 if word in subject_words else 1 
                         for word in action_verbs 
                         if word in combined_text.split())
    
    # Uppercase words and emphasis
    num_uppercase_words = sum(1 for word in subject.split() 
                            if word.isupper() and len(word) > 1)
    num_exclamation = message.count('!')
    
    # Text length features
    subject_len = len(subject)
    message_len = len(message)
    combined_len = len(combined_text)
    
    # Question detection
    num_questions = combined_text.count('?')
    has_question = int(num_questions > 0)
    
    # Deadline detection
    deadline_words = ['deadline', 'due', 'by']
    has_deadline_word = any(word in combined_text for word in deadline_words)
    has_deadline_pattern = bool(re.search(r'by\s+\w+day|due\s+\w+day|until\s+\w+day', combined_text))
    has_immediate_pattern = bool(re.search(r'(today|tomorrow|asap|immediate)', combined_text))
    has_deadline = int(has_deadline_word or has_deadline_pattern or has_immediate_pattern)
    
    # Time sensitivity
    time_words = ['today', 'tomorrow', 'asap', 'immediate', 'urgent']
    has_time_word = any(word in combined_text for word in time_words)
    has_time_pattern = bool(re.search(r'in\s+\d+\s+(hour|minute|day)', combined_text))
    time_sensitive = int(has_time_word or has_time_pattern)
    
    # Word counts
    num_words_subject = len(subject_words)
    num_words_message = len(message_words)
    
    # Low priority indicators
    informational_score = sum(1 for word in informational_words if word in combined_text.split())
    social_score = sum(1 for word in social_words if word in combined_text.split())
    optional_score = sum(1 for phrase in optional_phrases if phrase in combined_text)
    
    # Normalize low priority scores
    max_informational = len(informational_words)
    max_social = len(social_words)
    max_optional = len(optional_phrases)
    
    informational_flag = min(informational_score / max_informational, 1.0)
    social_flag = min(social_score / max_social, 1.0)
    optional_flag = min(optional_score / max_optional, 1.0)
    
    # Create feature array
    features = np.array([
        urgency_flag,
        risk_flag,
        urgency_and_risk,
        num_action_verbs,
        num_uppercase_words,
        num_exclamation,
        subject_len,
        message_len,
        combined_len,
        has_question,
        has_deadline,
        time_sensitive,
        num_words_subject,
        num_words_message,
        informational_flag,
        social_flag,
        optional_flag,
        subject_sentiment['neg'],
        subject_sentiment['neu'],
        subject_sentiment['pos'],
        subject_sentiment['compound'],
        message_sentiment['neg'],
        message_sentiment['neu'],
        message_sentiment['pos'],
        message_sentiment['compound']
    ]).reshape(1, -1)
    
    return features

def predict_priority(subject, message):
    """Predict email priority using ensemble of models"""
    # Load models and scalers
    low_model = xgb.Booster()
    low_model.load_model('Models/low_priority_model.json')
    medium_model = xgb.Booster()
    medium_model.load_model('Models/medium_priority_model.json')
    high_model = xgb.Booster()
    high_model.load_model('Models/high_priority_model.json')
    
    low_scaler = joblib.load('Models/low_priority_scaler.joblib')
    medium_scaler = joblib.load('Models/medium_priority_scaler.joblib')
    high_scaler = joblib.load('Models/high_priority_scaler.joblib')
    
    # Preprocess email and extract features
    features = preprocess_email(subject, message)
    
    # Get predictions from each model
    features_scaled = high_scaler.transform(features)
    dmatrix = xgb.DMatrix(features_scaled)
    high_prob = high_model.predict(dmatrix)[0]
    
    features_scaled = medium_scaler.transform(features)
    dmatrix = xgb.DMatrix(features_scaled)
    medium_prob = medium_model.predict(dmatrix)[0]
    
    features_scaled = low_scaler.transform(features)
    dmatrix = xgb.DMatrix(features_scaled)
    low_prob = low_model.predict(dmatrix)[0]
    
    # Adjust probabilities based on model confidence and priority characteristics
    urgency_score = features[0, 0] * 2.0
    risk_score = features[0, 1] * 2.0
    action_score = features[0, 3] * 1.5
    deadline_score = features[0, 9] * 2.0
    time_sensitive_score = features[0, 10] * 2.0
    
    informational_score = features[0, 14] * 3.0
    social_score = features[0, 15] * 2.5
    optional_score = features[0, 16] * 2.0
    
    # Calculate priority scores
    high_priority_score = (
        urgency_score +
        risk_score +
        action_score +
        deadline_score +
        time_sensitive_score
    ) / 9.5
    
    low_priority_score = (
        informational_score +
        social_score +
        optional_score
    ) / 7.5
    
    # Adjust probabilities based on scores
    if high_priority_score > 0.4:
        high_prob *= (1 + high_priority_score)
    if low_priority_score > 0.4:
        low_prob *= (1 + low_priority_score)
    
    # Normalize probabilities
    total_prob = high_prob + medium_prob + low_prob
    if total_prob > 0:
        high_prob /= total_prob
        medium_prob /= total_prob
        low_prob /= total_prob
    
    # Make final decision
    probs = [low_prob, medium_prob, high_prob]
    max_prob = max(probs)
    priority_idx = probs.index(max_prob)
    
    priority_map = {0: 'Low', 1: 'Medium', 2: 'High'}
    return priority_map[priority_idx], max_prob, probs

def explain_prediction(subject, message):
    """Generate explanation for the prediction"""
    features = preprocess_email(subject, message)[0]
    
    explanation = []
    
    # Urgency and risk explanation
    if features[0] > 0.3 or features[1] > 0.3:
        if features[0] > 0.3:
            explanation.append(f"Urgency indicators detected ({features[0]:.1%})")
        if features[1] > 0.3:
            explanation.append(f"Risk indicators detected ({features[1]:.1%})")
        if features[2] > 0.2:
            explanation.append("Combined urgency and risk factors")
    
    # Action verbs explanation
    if features[3] > 2:
        explanation.append(f"Multiple action items ({int(features[3])})")
    
    # Emphasis explanation
    if features[4] > 0:
        explanation.append(f"Emphasized words in subject ({int(features[4])})")
    if features[5] > 0:
        explanation.append(f"Exclamation marks detected ({int(features[5])})")
    
    # Deadline and time sensitivity explanation
    if features[10] == 1:
        explanation.append("Contains deadline")
    if features[11] == 1:
        explanation.append("Time-sensitive content")
    
    # Question explanation
    if features[9] == 1:
        explanation.append("Contains questions")
    
    # Sentiment explanation
    subject_compound = features[20]
    message_compound = features[24]
    if abs(subject_compound) > 0.3:
        sentiment = "negative" if subject_compound < 0 else "positive"
        explanation.append(f"Subject has {sentiment} sentiment ({abs(subject_compound):.1%})")
    if abs(message_compound) > 0.3:
        sentiment = "negative" if message_compound < 0 else "positive"
        explanation.append(f"Message has {sentiment} sentiment ({abs(message_compound):.1%})")
    
    # Low priority indicators
    low_priority_indicators = []
    if features[14] > 0.3:
        low_priority_indicators.append("informational content")
    if features[15] > 0.3:
        low_priority_indicators.append("social content")
    if features[16] > 0.3:
        low_priority_indicators.append("optional content")
    
    if low_priority_indicators:
        explanation.append("Low priority indicators: " + ", ".join(low_priority_indicators))
    
    return explanation

def test_email_examples():
    """Test the model with example emails"""
    test_emails = [
        {
            'subject': 'Team Meeting - Project Review',
            'message': 'Hi team, please join us for our weekly project review meeting tomorrow at 2 PM. We\'ll discuss the current progress and next steps.',
            'expected_priority': 'Medium'
        },
        {
            'subject': 'ALERT: Server Down - Production Impact',
            'message': 'Critical: Our main production server is down. All services are affected. Immediate action required. Please check the monitoring dashboard and respond ASAP.',
            'expected_priority': 'High'
        },
        {
            'subject': 'Monthly Tech Digest - March 2024',
            'message': 'Here\'s our monthly roundup of the latest technology trends and company updates. Feel free to read at your convenience.',
            'expected_priority': 'Low'
        },
        {
            'subject': 'CRITICAL: Data Breach Detected',
            'message': 'URGENT: We have detected unauthorized access to our customer database. Immediate investigation and response required. All hands on deck.',
            'expected_priority': 'High'
        },
        {
            'subject': 'Reminder: Fill Timesheet',
            'message': 'Just a friendly reminder to submit your timesheet for this week. Please complete it by Friday.',
            'expected_priority': 'Low'
        },
        {
            'subject': 'System Update Available',
            'message': 'A new system update is available. Please install it within the next 48 hours to ensure security compliance.',
            'expected_priority': 'Medium'
        },
        {
            'subject': 'EMERGENCY: Production Pipeline Failure',
            'message': 'The main production pipeline has failed. Customer deliveries are impacted. Urgent fix needed. Conference bridge opened.',
            'expected_priority': 'High'
        },
        {
            'subject': 'Office Snacks Survey',
            'message': 'Help us choose new snacks for the office kitchen! Fill out this quick survey when you have time.',
            'expected_priority': 'Low'
        },
        {
            'subject': 'Code Review Request - Feature X',
            'message': 'I\'ve completed the implementation of Feature X. Please review the code by EOD tomorrow so we can meet the sprint deadline.',
            'expected_priority': 'Medium'
        },
        {
            'subject': 'URGENT: Client Meeting Rescheduled',
            'message': 'The client meeting scheduled for 2 PM today has been moved to 3 PM. Please update your calendars immediately.',
            'expected_priority': 'High'
        },
        {
            'subject': 'New Employee Introduction',
            'message': 'Please welcome Jane Doe, who will be joining our team next week as a Senior Developer.',
            'expected_priority': 'Low'
        },
        {
            'subject': 'Sprint Planning Tomorrow',
            'message': 'Reminder: Sprint planning meeting tomorrow at 10 AM. Please review the backlog and prepare your updates.',
            'expected_priority': 'Medium'
        },
        {
            'subject': 'CRITICAL: SSL Certificate Expiring',
            'message': 'Our main domain SSL certificate will expire in 24 hours. Immediate renewal required to prevent service disruption.',
            'expected_priority': 'High'
        },
        {
            'subject': 'Friday Fun Activity',
            'message': 'Join us for pizza and games this Friday afternoon! RSVP if you\'d like to participate.',
            'expected_priority': 'Low'
        },
        {
            'subject': 'Project Milestone Update Required',
            'message': 'Please update your project milestones in the tracking system by end of week for the quarterly review.',
            'expected_priority': 'Medium'
        }
    ]
    
    results = []
    for email in test_emails:
        predicted_priority, confidence, probabilities = predict_priority(
            email['subject'], email['message']
        )
        explanation = explain_prediction(email['subject'], email['message'])
        
        results.append({
            'Subject': email['subject'],
            'Expected Priority': email['expected_priority'],
            'Predicted Priority': predicted_priority,
            'Confidence': f"{confidence*100:.2f}%",
            'Low Probability': f"{probabilities[0]*100:.2f}%",
            'Medium Probability': f"{probabilities[1]*100:.2f}%",
            'High Probability': f"{probabilities[2]*100:.2f}%",
            'Correct': predicted_priority == email['expected_priority'],
            'Key Factors': explanation
        })
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    
    # Print results
    print("\nEmail Priority Classification Test Results")
    print("=" * 80)
    
    for idx, result in results_df.iterrows():
        print(f"\nTest Case {idx + 1}:")
        print(f"Subject: {result['Subject']}")
        print(f"Expected Priority: {result['Expected Priority']}")
        print(f"Predicted Priority: {result['Predicted Priority']} (Confidence: {result['Confidence']})")
        print(f"Probability Distribution:")
        print(f"  - Low: {result['Low Probability']}")
        print(f"  - Medium: {result['Medium Probability']}")
        print(f"  - High: {result['High Probability']}")
        print(f"Correct Classification: {'✓' if result['Correct'] else '✗'}")
        print("\nKey Factors:")
        for factor in result['Key Factors']:
            print(f"  - {factor}")
        print("-" * 80)
    
    # Print summary statistics
    total_tests = len(results_df)
    correct_predictions = results_df['Correct'].sum()
    accuracy = (correct_predictions / total_tests) * 100
    
    print("\nSummary Statistics")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Correct Predictions: {correct_predictions}")
    print(f"Accuracy: {accuracy:.2f}%")
    
    # Calculate per-priority accuracy
    priority_accuracy = {}
    for priority in ['Low', 'Medium', 'High']:
        priority_cases = results_df[results_df['Expected Priority'] == priority]
        if len(priority_cases) > 0:
            accuracy = (priority_cases['Correct'].sum() / len(priority_cases)) * 100
            priority_accuracy[priority] = accuracy
    
    print("\nAccuracy by Priority Level:")
    for priority, accuracy in priority_accuracy.items():
        print(f"{priority}: {accuracy:.2f}%")
    
    # Print confusion matrix
    print("\nConfusion Matrix")
    print("=" * 80)
    confusion_matrix = pd.crosstab(
        results_df['Expected Priority'],
        results_df['Predicted Priority'],
        margins=True
    )
    print(confusion_matrix)

if __name__ == "__main__":
    test_email_examples() 