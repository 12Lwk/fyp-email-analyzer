import joblib
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

def clean_text(text):
    """Clean and preprocess text"""
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and extra whitespace
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    text = ' '.join(text.split())
    return text

def preprocess_email(subject, message):
    """Clean and preprocess email text"""
    # Basic cleaning
    cleaned_subject = clean_text(subject)
    cleaned_message = clean_text(message)
    
    # Enhanced feature sets
    urgency_words = {
        'urgent', 'asap', 'emergency', 'immediate', 'critical', 'important',
        'priority', 'urgent priority', 'high priority', 'deadline', 'due',
        'escalation', 'escalated', 'time sensitive', 'action required'
    }
    
    risk_words = {
        'risk', 'warning', 'alert', 'danger', 'critical', 'serious',
        'issue', 'problem', 'failure', 'error', 'outage', 'breach',
        'security', 'compliance', 'violation', 'incident'
    }
    
    action_verbs = {
        'review', 'approve', 'confirm', 'update', 'respond', 'complete',
        'submit', 'verify', 'check', 'investigate', 'resolve', 'fix',
        'implement', 'test', 'deploy', 'analyze', 'assess', 'evaluate'
    }
    
    # Calculate flags with word context
    message_words = cleaned_message.split()
    subject_words = cleaned_subject.split()
    combined_text = cleaned_subject + ' ' + cleaned_message
    
    # Enhanced urgency detection
    urgency_flag = int(
        any(word in combined_text.split() for word in urgency_words) or
        ('asap' in combined_text) or
        ('as soon as possible' in combined_text) or
        ('right away' in combined_text) or
        ('immediately' in combined_text)
    )
    
    # Enhanced risk detection
    risk_flag = int(
        any(word in combined_text.split() for word in risk_words) or
        ('high impact' in combined_text) or
        ('affected' in combined_text and ('user' in combined_text or 'system' in combined_text)) or
        ('down' in combined_text and ('system' in combined_text or 'service' in combined_text))
    )
    
    urgency_and_risk = int(urgency_flag and risk_flag)
    
    # Enhanced action verb counting
    num_action_verbs = sum(1 for word in action_verbs if word in combined_text.split())
    
    # Enhanced uppercase analysis
    num_uppercase_words_subject = sum(1 for word in subject.split() if word.isupper() and len(word) > 1)
    
    # Question analysis
    num_questions = message.count('?')
    has_question = int(num_questions > 0)
    
    # Create a DataFrame with enhanced features
    features = pd.DataFrame({
        'Cleaned_Subject': [cleaned_subject],
        'Cleaned_Message': [cleaned_message],
        'urgency_flag': [urgency_flag],
        'risk_flag': [risk_flag],
        'urgency_and_risk': [urgency_and_risk],
        'num_action_verbs': [num_action_verbs],
        'num_uppercase_words_subject': [num_uppercase_words_subject],
        'subject_len': [len(subject)],
        'has_question': [has_question]
    })
    
    return features

def predict_priority(features, model):
    """Predict email priority using the trained model"""
    # Make prediction using the model's pipeline
    priority = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    
    # Map numeric priority to labels
    priority_map = {0: 'Low', 1: 'Medium', 2: 'High'}
    predicted_priority = priority_map[priority]
    
    # Calculate confidence
    confidence = probabilities[priority] * 100
    
    return predicted_priority, confidence, probabilities

def explain_prediction(features):
    """Generate explanation for the prediction"""
    explanation = []
    
    # Check urgency and risk
    if features['urgency_and_risk'].iloc[0]:
        explanation.append("Contains both urgency and risk indicators (Critical priority)")
    elif features['urgency_flag'].iloc[0]:
        explanation.append("Contains urgency indicators (High priority)")
    elif features['risk_flag'].iloc[0]:
        explanation.append("Contains risk indicators (High priority)")
    
    # Check action verbs
    if features['num_action_verbs'].iloc[0] > 0:
        explanation.append(f"Contains {features['num_action_verbs'].iloc[0]} action items")
    
    # Check emphasis
    if features['num_uppercase_words_subject'].iloc[0] > 0:
        explanation.append(f"Some emphasis in subject ({features['num_uppercase_words_subject'].iloc[0]} uppercase words)")
    
    # Check questions
    if features['has_question'].iloc[0]:
        explanation.append("Contains questions")
    
    return explanation

def test_email_examples():
    # Load the model
    model = joblib.load('Models/priority_model_v2.joblib')
    
    # Define test email examples
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
            'subject': 'New Task: Documentation Review',
            'message': 'Please review and update the project documentation by end of day Friday. This is part of our regular maintenance cycle.',
            'expected_priority': 'Medium'
        },
        {
            'subject': 'Team Building Event - Next Week',
            'message': 'Join us for our quarterly team building event next Thursday. Lunch will be provided. RSVP by Monday if you plan to attend.',
            'expected_priority': 'Low'
        },
        {
            'subject': 'SECURITY ALERT: Unusual Login Attempt',
            'message': 'We detected an unusual login attempt on your account. Please verify your recent activity and change your password immediately.',
            'expected_priority': 'High'
        },
        {
            'subject': 'Project Status: Behind Schedule',
            'message': 'The project is currently behind schedule. We need to discuss mitigation strategies in our next meeting.',
            'expected_priority': 'Medium'
        },
        {
            'subject': 'Important: New Security Policy',
            'message': 'Please review the attached new security policy document. Compliance is required by the end of this month.',
            'expected_priority': 'Medium'
        }
    ]
    
    # Test each email
    results = []
    for email in test_emails:
        # Preprocess the email
        processed_features = preprocess_email(email['subject'], email['message'])
        
        # Make prediction
        predicted_priority, confidence, probabilities = predict_priority(
            processed_features, model
        )
        
        # Get explanation
        explanation = explain_prediction(processed_features)
        
        # Store results
        results.append({
            'Subject': email['subject'],
            'Expected Priority': email['expected_priority'],
            'Predicted Priority': predicted_priority,
            'Confidence': f"{confidence:.2f}%",
            'Low Probability': f"{probabilities[0]:.2f}%",
            'Medium Probability': f"{probabilities[1]:.2f}%",
            'High Probability': f"{probabilities[2]:.2f}%",
            'Correct': predicted_priority == email['expected_priority'],
            'Key Factors': explanation
        })
    
    # Convert results to DataFrame for better display
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