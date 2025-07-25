import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import re

def preprocess_email(subject, message):
    """Clean and preprocess email text"""
    # Basic cleaning
    def clean_text(text):
        # Convert to lowercase
        text = text.lower()
        # Remove special characters and extra whitespace
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        text = ' '.join(text.split())
        return text
    
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
    
    medium_indicators = {
        'review', 'update', 'feedback', 'status', 'progress', 'weekly',
        'monthly', 'report', 'meeting', 'discuss', 'follow up', 'schedule',
        'plan', 'proposal', 'suggestion', 'recommendation'
    }
    
    low_indicators = {
        'fyi', 'newsletter', 'announcement', 'info', 'thanks', 'thank you',
        'sharing', 'heads up', 'reminder', 'optional', 'when convenient',
        'no rush', 'take your time', 'for reference', 'just letting you know'
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
    
    # Count medium and low priority indicators
    num_medium_indicators = sum(1 for word in medium_indicators if word in combined_text.split())
    num_low_indicators = sum(1 for word in low_indicators if word in combined_text.split())
    
    # Enhanced uppercase analysis
    num_uppercase_words_subject = sum(1 for word in subject.split() if word.isupper() and len(word) > 1)
    num_uppercase_words_message = sum(1 for word in message.split() if word.isupper() and len(word) > 1)
    
    # Time sensitivity detection
    has_deadline = int(
        any(word in combined_text for word in ['deadline', 'due', 'by']) and
        any(word in combined_text for word in ['today', 'tomorrow', 'asap', 'immediate'])
    )
    
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
        'num_medium_indicators': [num_medium_indicators],
        'num_low_indicators': [num_low_indicators],
        'num_uppercase_words_subject': [num_uppercase_words_subject],
        'num_uppercase_words_message': [num_uppercase_words_message],
        'subject_len': [len(subject)],
        'has_question': [has_question],
        'num_questions': [num_questions],
        'has_deadline': [has_deadline]
    })
    
    return features

def predict_priority(model, subject, message):
    """Predict email priority using the trained model"""
    # Preprocess the email
    features = preprocess_email(subject, message)
    
    # Make prediction
    priority = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    
    # Calculate priority scores with enhanced logic
    high_score = 0
    medium_score = 0
    low_score = 0
    
    # High priority scoring with context awareness
    if features['urgency_and_risk'].iloc[0]:
        high_score += 15  # Critical combination
    if features['urgency_flag'].iloc[0]:
        high_score += 10  # Strong urgency
    if features['risk_flag'].iloc[0]:
        high_score += 10  # Strong risk
    if features['has_deadline'].iloc[0]:
        high_score += 8   # Immediate deadline
    
    # Action-based scoring
    if features['num_action_verbs'].iloc[0] > 3:
        high_score += 8   # Multiple critical actions
    elif features['num_action_verbs'].iloc[0] > 1:
        medium_score += 6 # Several actions
    elif features['num_action_verbs'].iloc[0] == 1:
        medium_score += 4 # Single action
    else:
        low_score += 5    # No actions
    
    # Emphasis scoring
    if features['num_uppercase_words_subject'].iloc[0] > 2:
        high_score += 6   # Strong emphasis
    elif features['num_uppercase_words_subject'].iloc[0] > 0:
        high_score += 3   # Some emphasis
    
    if features['num_uppercase_words_message'].iloc[0] > 2:
        high_score += 4   # Message emphasis
    
    # Medium priority indicators
    if features['num_medium_indicators'].iloc[0] > 2:
        medium_score += 8 # Strong medium signals
    elif features['num_medium_indicators'].iloc[0] > 0:
        medium_score += 5 # Some medium signals
    
    if features['has_question'].iloc[0]:
        if features['num_questions'].iloc[0] > 2:
            medium_score += 6 # Multiple questions
        else:
            medium_score += 4 # Some questions
    
    # Low priority indicators
    if features['num_low_indicators'].iloc[0] > 2:
        low_score += 10   # Strong low signals
    elif features['num_low_indicators'].iloc[0] > 0:
        low_score += 6    # Some low signals
    
    if not any([features['urgency_flag'].iloc[0], features['risk_flag'].iloc[0], 
                features['has_deadline'].iloc[0], features['has_question'].iloc[0]]):
        low_score += 8    # No urgency indicators
    
    # Calculate priority weights
    total_score = high_score + medium_score + low_score
    if total_score == 0:
        total_score = 1  # Prevent division by zero
    
    high_weight = high_score / total_score
    medium_weight = medium_score / total_score
    low_weight = low_score / total_score
    
    # Adjust probabilities with sophisticated weighting
    adjusted_probabilities = probabilities.copy()
    
    # Apply non-linear scaling with stronger bias reduction
    adjusted_probabilities[2] *= (1 + high_weight) ** 3    # High priority (stronger boost)
    adjusted_probabilities[1] *= (1 + medium_weight)       # Medium priority (no boost)
    adjusted_probabilities[0] *= (1 + low_weight) ** 3     # Low priority (stronger boost)
    
    # Apply score-based adjustments
    if high_score >= 20:
        adjusted_probabilities[2] *= 4.0  # Very strong high boost
    elif high_score >= 15:
        adjusted_probabilities[2] *= 3.0  # Strong high boost
    
    if low_score >= 15:
        adjusted_probabilities[0] *= 4.0  # Very strong low boost
    elif low_score >= 10:
        adjusted_probabilities[0] *= 3.0  # Strong low boost
    
    # Aggressive medium priority reduction
    if high_score > 0 or low_score > 0:
        reduction_factor = min(0.5, max(0.1, 1.0 - (high_score + low_score) / 40))
        adjusted_probabilities[1] *= reduction_factor
    
    # Additional adjustments for clear signals
    if high_score >= 15 and high_score > (medium_score + low_score):
        adjusted_probabilities[2] *= 2.0  # Clear high priority
        adjusted_probabilities[1] *= 0.5  # Reduce medium
    
    if low_score >= 15 and low_score > (medium_score + high_score):
        adjusted_probabilities[0] *= 2.0  # Clear low priority
        adjusted_probabilities[1] *= 0.5  # Reduce medium
    
    # Normalize probabilities
    adjusted_probabilities = adjusted_probabilities / adjusted_probabilities.sum()
    
    # Dynamic thresholds with more aggressive values
    high_threshold = 0.25 if high_score >= 15 else 0.30
    low_threshold = 0.25 if low_score >= 15 else 0.30
    
    # Determine priority with confidence-based classification
    max_prob = max(adjusted_probabilities)
    max_index = list(adjusted_probabilities).index(max_prob)
    
    # More aggressive classification rules
    if adjusted_probabilities[2] >= high_threshold or (max_index == 2 and high_score >= 12):
        predicted_priority = 'High'
        confidence = adjusted_probabilities[2] * 100
    elif adjusted_probabilities[0] >= low_threshold or (max_index == 0 and low_score >= 12):
        predicted_priority = 'Low'
        confidence = adjusted_probabilities[0] * 100
    else:
        # Only classify as medium if neither high nor low conditions are met
        predicted_priority = 'Medium'
        confidence = adjusted_probabilities[1] * 100
    
    # Get probability for each class
    class_probabilities = {
        'Low': adjusted_probabilities[0] * 100,
        'Medium': adjusted_probabilities[1] * 100,
        'High': adjusted_probabilities[2] * 100
    }
    
    return predicted_priority, confidence, class_probabilities, features

def explain_prediction(predicted_priority, confidence, class_probabilities, features):
    """Explain the prediction with enhanced detail"""
    print("\nPrediction Analysis:")
    print(f"Predicted Priority: {predicted_priority}")
    print(f"Confidence: {confidence:.2f}%")
    
    print("\nClass Probabilities:")
    for priority, prob in class_probabilities.items():
        print(f"{priority}: {prob:.2f}%")
    
    print("\nKey Factors:")
    
    # Urgency and risk analysis
    if features['urgency_and_risk'].iloc[0]:
        print("- Contains both urgency and risk indicators (Critical priority)")
    elif features['urgency_flag'].iloc[0]:
        print("- Contains urgency indicators (High priority)")
    elif features['risk_flag'].iloc[0]:
        print("- Contains risk indicators (High priority)")
    
    # Action verbs analysis
    if features['num_action_verbs'].iloc[0] > 3:
        print(f"- Contains multiple action items ({features['num_action_verbs'].iloc[0]} actions)")
    elif features['num_action_verbs'].iloc[0] > 1:
        print(f"- Contains {features['num_action_verbs'].iloc[0]} action items")
    elif features['num_action_verbs'].iloc[0] == 1:
        print("- Contains 1 action item")
    else:
        print("- No action items")
    
    # Emphasis analysis
    if features['num_uppercase_words_subject'].iloc[0] > 2:
        print("- Strong emphasis in subject (Multiple uppercase words)")
    elif features['num_uppercase_words_subject'].iloc[0] > 0:
        print(f"- Some emphasis in subject ({features['num_uppercase_words_subject'].iloc[0]} uppercase words)")
    
    # Question analysis
    if features['num_questions'].iloc[0] > 0:
        print(f"- Contains {features['num_questions'].iloc[0]} question(s)")
    
    # Deadline analysis
    if features['has_deadline'].iloc[0]:
        print("- Contains deadline or due date")
    
    # Priority indicators
    if features['num_medium_indicators'].iloc[0] > 0:
        print(f"- Contains {features['num_medium_indicators'].iloc[0]} medium priority indicators")
    if features['num_low_indicators'].iloc[0] > 0:
        print(f"- Contains {features['num_low_indicators'].iloc[0]} low priority indicators")
    
    # Final classification explanation
    print("\nThis email is classified as", end=" ")
    if predicted_priority == 'High':
        print("high priority because:")
        if features['urgency_and_risk'].iloc[0]:
            print("- Critical combination of urgency and risk")
        if features['urgency_flag'].iloc[0] or features['risk_flag'].iloc[0]:
            print("- Contains significant urgency/risk indicators")
        if features['has_deadline'].iloc[0]:
            print("- Has immediate deadline")
        if features['num_action_verbs'].iloc[0] > 2:
            print("- Multiple action items requiring attention")
    elif predicted_priority == 'Low':
        print("low priority because:")
        if features['num_low_indicators'].iloc[0] > 0:
            print("- Contains multiple informational/courtesy indicators")
        if features['num_action_verbs'].iloc[0] == 0:
            print("- No immediate actions required")
        if not any([features['urgency_flag'].iloc[0], features['risk_flag'].iloc[0], 
                   features['has_deadline'].iloc[0]]):
            print("- No urgency, risk, or deadline indicators")
    else:
        print("medium priority because:")
        if features['num_action_verbs'].iloc[0] in [1, 2]:
            print("- Contains moderate number of action items")
        if features['num_medium_indicators'].iloc[0] > 0:
            print("- Contains typical medium priority indicators")
        if features['has_question'].iloc[0]:
            print("- Requires response to questions")
        if not features['urgency_and_risk'].iloc[0]:
            print("- No critical urgency/risk combination")

def main():
    # Load the trained model
    print("Loading model...")
    model = joblib.load('C:/Users/User/OneDrive - Asia Pacific University/APU Final Year Project/FYP Email Project Documents/Email Dataset Python/FYP PART 2/Priority Modeling/Models/priority_model_v2.joblib')
    
    while True:
        print("\nEmail Priority Prediction")
        print("------------------------")
        print("Options:")
        print("1. Test with a sample high-priority email")
        print("2. Test with a sample medium-priority email")
        print("3. Test with a sample low-priority email")
        print("4. Enter a custom email")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '5':
            break
        
        if choice == '1':
            subject = "URGENT: Critical System Failure - Immediate Action Required"
            message = "The production database is down and affecting all users. Need immediate assistance to restore service. This is causing significant business impact. Please respond ASAP with your availability to help resolve this critical issue."
        
        elif choice == '2':
            subject = "Weekly Project Update - Action Items"
            message = "Here's the status update for Project X. We're on track but need your review of the following items: 1. Updated timeline 2. Resource allocation 3. Budget adjustments. Please provide your feedback by Friday."
        
        elif choice == '3':
            subject = "Office Party - Save the Date"
            message = "Just wanted to let you know that we're planning the annual office party for next month. More details will follow soon. Hope you can join us for some fun and relaxation!"
        
        elif choice == '4':
            subject = input("\nEnter email subject: ")
            message = input("Enter email message: ")
        
        else:
            print("Invalid choice. Please try again.")
            continue
        
        # Make prediction
        predicted_priority, confidence, class_probabilities, features = predict_priority(model, subject, message)
        
        # Print email content
        print("\nEmail Content:")
        print(f"Subject: {subject}")
        print(f"Message: {message}")
        
        # Explain prediction
        explain_prediction(predicted_priority, confidence, class_probabilities, features)

if __name__ == "__main__":
    main() 