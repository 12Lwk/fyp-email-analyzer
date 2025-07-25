import joblib
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

def clean_text(text):
    """Clean and preprocess text"""
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and extra whitespace
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    text = ' '.join(text.split())
    return text

def preprocess_email(subject, message):
    """Clean and preprocess email text with enhanced features"""
    # Basic cleaning
    cleaned_subject = clean_text(subject)
    cleaned_message = clean_text(message)
    
    # Enhanced feature sets
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
    
    # Calculate flags with word context
    message_words = cleaned_message.split()
    subject_words = cleaned_subject.split()
    combined_text = cleaned_subject + ' ' + cleaned_message
    
    # Enhanced urgency detection with context
    urgency_score = sum(2 if word in subject_words else 1 
                       for word in urgency_words 
                       if word in combined_text.split())
    
    # Enhanced risk detection with context
    risk_score = sum(2 if word in subject_words else 1 
                    for word in risk_words 
                    if word in combined_text.split())
    
    # Calculate normalized scores
    max_urgency = len(urgency_words) * 2  # Maximum possible urgency score
    max_risk = len(risk_words) * 2  # Maximum possible risk score
    
    urgency_flag = min(urgency_score / max_urgency, 1.0)
    risk_flag = min(risk_score / max_risk, 1.0)
    urgency_and_risk = urgency_flag * risk_flag
    
    # Enhanced action verb counting with context
    num_action_verbs = sum(2 if word in subject_words else 1 
                          for word in action_verbs 
                          if word in combined_text.split())
    
    # Enhanced uppercase analysis
    num_uppercase_words_subject = sum(1 for word in subject.split() 
                                    if word.isupper() and len(word) > 1)
    
    # Enhanced deadline detection
    deadline_words = ['deadline', 'due', 'by']
    has_deadline_word = any(word in combined_text for word in deadline_words)
    has_deadline_pattern = bool(re.search(r'by\s+\w+day|due\s+\w+day|until\s+\w+day', combined_text))
    has_immediate_pattern = bool(re.search(r'(today|tomorrow|asap|immediate)', combined_text))
    has_deadline = int(has_deadline_word or has_deadline_pattern or has_immediate_pattern)
    
    # Question analysis
    num_questions = combined_text.count('?')
    has_question = int(num_questions > 0)
    
    # Time sensitivity detection
    time_words = ['today', 'tomorrow', 'asap', 'immediate', 'urgent']
    has_time_word = any(word in combined_text for word in time_words)
    has_time_pattern = bool(re.search(r'in\s+\d+\s+(hour|minute|day)', combined_text))
    time_sensitive = int(has_time_word or has_time_pattern)
    
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
        'has_question': [has_question],
        'has_deadline': [has_deadline],
        'time_sensitive': [time_sensitive]
    })
    
    return features

def predict_priority(features, model):
    """Predict email priority using the trained model with enhanced thresholds"""
    # Make prediction using the model
    probabilities = model.predict_proba(features)[0]
    
    # Calculate priority score based on features
    priority_score = 0.0
    
    # Add points for urgency and risk (increased weights)
    priority_score += features['urgency_flag'].iloc[0] * 3.0  # Increased weight for urgency
    priority_score += features['risk_flag'].iloc[0] * 3.5     # Increased weight for risk
    priority_score += features['urgency_and_risk'].iloc[0] * 2.0  # Increased bonus for combined
    
    # Add points for action verbs and uppercase words
    priority_score += min(features['num_action_verbs'].iloc[0] * 0.8, 2.5)  # Increased cap
    priority_score += min(features['num_uppercase_words_subject'].iloc[0] * 0.5, 1.5)  # Increased cap
    
    # Add points for deadlines and time sensitivity
    priority_score += features['has_deadline'].iloc[0] * 1.5
    priority_score += features['time_sensitive'].iloc[0] * 2.0
    
    # Subtract points for questions (usually indicates lower priority)
    priority_score -= features['has_question'].iloc[0] * 0.8
    
    # Normalize priority score to 0-1 range
    priority_score = min(max(priority_score / 10.0, 0.0), 1.0)
    
    # Determine priority based on both model probabilities and priority score
    if (probabilities[2] >= 0.25 or  # Lowered threshold for high priority
        (priority_score >= 0.6 and probabilities[2] >= 0.15) or  # Lowered thresholds
        (features['risk_flag'].iloc[0] >= 0.7 and probabilities[2] >= 0.1)):  # Lowered thresholds
        priority = 2  # High priority
    elif (probabilities[0] >= 0.3 or  # Lowered threshold for low priority
          (priority_score <= 0.4 and probabilities[1] <= 0.8)):  # Adjusted thresholds
        priority = 0  # Low priority
    else:
        priority = 1  # Medium priority
    
    # Map numeric priority to labels
    priority_map = {0: 'Low', 1: 'Medium', 2: 'High'}
    predicted_priority = priority_map[priority]
    
    # Calculate confidence based on both model probability and priority score
    if priority == 2:  # High priority
        confidence = max(probabilities[2] * 100, priority_score * 100)
    elif priority == 0:  # Low priority
        confidence = max(probabilities[0] * 100, (1 - priority_score) * 100)
    else:  # Medium priority
        confidence = probabilities[1] * 100
    
    return predicted_priority, confidence, probabilities

def explain_prediction(features):
    """Generate detailed explanation for the prediction with enhanced reasoning"""
    explanation = []
    
    # Calculate priority indicators
    urgency_level = features['urgency_flag'].iloc[0]
    risk_level = features['risk_flag'].iloc[0]
    combined_level = features['urgency_and_risk'].iloc[0]
    
    # Explain urgency and risk with more detail
    if combined_level > 0.5:
        explanation.append(f"High priority: Contains both urgency ({urgency_level:.1%}) and risk ({risk_level:.1%}) indicators")
    elif urgency_level > 0.5:
        explanation.append(f"Elevated priority: Strong urgency indicators ({urgency_level:.1%})")
    elif risk_level > 0.5:
        explanation.append(f"Elevated priority: Significant risk factors ({risk_level:.1%})")
    
    # Explain action items with context
    num_actions = features['num_action_verbs'].iloc[0]
    if num_actions > 2:
        explanation.append(f"Multiple action items required ({num_actions} items)")
    elif num_actions > 0:
        explanation.append(f"Contains {num_actions} action item(s)")
    
    # Explain emphasis with impact
    num_uppercase = features['num_uppercase_words_subject'].iloc[0]
    if num_uppercase > 1:
        explanation.append(f"Strong emphasis in subject ({num_uppercase} uppercase words)")
    elif num_uppercase == 1:
        explanation.append("Emphasized subject line")
    
    # Explain time factors
    if features['has_deadline'].iloc[0] and features['time_sensitive'].iloc[0]:
        explanation.append("Time-critical: Contains both deadline and immediate time constraints")
    elif features['has_deadline'].iloc[0]:
        explanation.append("Contains specific deadline")
    elif features['time_sensitive'].iloc[0]:
        explanation.append("Time-sensitive content")
    
    # Explain priority-reducing factors
    if features['has_question'].iloc[0]:
        explanation.append("Contains questions (typically indicates lower priority)")
    
    # Add summary if no significant factors
    if not explanation:
        explanation.append("No significant priority indicators found")
    
    return explanation

def test_email_examples():
    """Test the model with example emails"""
    # Load the model
    model = joblib.load('Models/lr_priority_model.joblib')
    
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
            'Low Probability': f"{probabilities[0]*100:.2f}%",
            'Medium Probability': f"{probabilities[1]*100:.2f}%",
            'High Probability': f"{probabilities[2]*100:.2f}%",
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