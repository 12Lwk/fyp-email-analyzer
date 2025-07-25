import os
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings
warnings.filterwarnings('ignore')
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

def count_action_verbs(text):
    action_verbs = [
        'need', 'require', 'request', 'submit', 'complete', 'finish', 'send',
        'provide', 'update', 'review', 'check', 'verify', 'confirm', 'approve',
        'respond', 'reply', 'answer', 'follow up', 'prepare', 'create', 'develop',
        'implement', 'test', 'deploy', 'fix', 'resolve', 'address', 'handle',
        'manage', 'coordinate', 'organize', 'schedule', 'arrange', 'plan',
        'discuss', 'meet', 'present', 'report', 'document', 'record', 'track',
        'monitor', 'evaluate', 'assess', 'analyze', 'investigate', 'research',
        'study', 'learn', 'understand', 'consider', 'decide', 'choose', 'select',
        'recommend', 'suggest', 'propose', 'advise', 'guide', 'help', 'support',
        'assist', 'collaborate', 'cooperate', 'work', 'contribute', 'participate',
        'join', 'attend', 'visit', 'travel', 'move', 'transfer', 'change',
        'modify', 'adjust', 'revise', 'edit', 'correct', 'improve', 'enhance',
        'optimize', 'streamline', 'simplify', 'clarify', 'explain', 'describe',
        'define', 'specify', 'detail', 'list', 'enumerate', 'count', 'calculate',
        'measure', 'quantify', 'evaluate', 'compare', 'contrast', 'differentiate',
        'distinguish', 'identify', 'recognize', 'detect', 'discover', 'find',
        'locate', 'search', 'seek', 'look', 'examine', 'inspect', 'check',
        'verify', 'validate', 'confirm', 'prove', 'demonstrate', 'show',
        'display', 'present', 'exhibit', 'illustrate', 'depict', 'represent',
        'portray', 'characterize', 'describe', 'narrate', 'tell', 'relate',
        'report', 'inform', 'notify', 'announce', 'declare', 'state', 'express',
        'communicate', 'convey', 'transmit', 'deliver', 'send', 'forward',
        'distribute', 'share', 'exchange', 'trade', 'swap', 'switch', 'replace',
        'substitute', 'alternate', 'rotate', 'cycle', 'circulate', 'flow',
        'move', 'transfer', 'transport', 'carry', 'bring', 'take', 'fetch',
        'get', 'obtain', 'acquire', 'gain', 'earn', 'win', 'achieve', 'attain',
        'reach', 'accomplish', 'complete', 'finish', 'end', 'stop', 'halt',
        'pause', 'wait', 'delay', 'postpone', 'defer', 'reschedule', 'cancel',
        'terminate', 'abort', 'quit', 'exit', 'leave', 'depart', 'go', 'come',
        'arrive', 'return', 'revert', 'restore', 'recover', 'regain', 'retrieve',
        'reclaim', 'repossess', 'recover', 'restore', 'repair', 'fix', 'mend',
        'heal', 'cure', 'treat', 'handle', 'manage', 'control', 'regulate',
        'govern', 'rule', 'lead', 'guide', 'direct', 'steer', 'navigate',
        'pilot', 'drive', 'operate', 'run', 'execute', 'perform', 'conduct',
        'carry out', 'implement', 'enforce', 'apply', 'use', 'utilize', 'employ',
        'exercise', 'practice', 'train', 'teach', 'instruct', 'educate', 'coach',
        'mentor', 'advise', 'counsel', 'consult', 'recommend', 'suggest', 'propose',
        'offer', 'present', 'provide', 'supply', 'furnish', 'equip', 'arm',
        'prepare', 'ready', 'set', 'arrange', 'organize', 'order', 'sort',
        'classify', 'categorize', 'group', 'cluster', 'bunch', 'gather',
        'collect', 'accumulate', 'amass', 'assemble', 'build', 'construct',
        'create', 'make', 'form', 'shape', 'mold', 'forge', 'craft', 'design',
        'develop', 'produce', 'generate', 'manufacture', 'fabricate', 'build',
        'erect', 'raise', 'lift', 'elevate', 'boost', 'increase', 'augment',
        'enhance', 'improve', 'better', 'upgrade', 'update', 'modernize',
        'renovate', 'refurbish', 'restore', 'repair', 'fix', 'mend', 'heal',
        'cure', 'treat', 'handle', 'manage', 'control', 'regulate', 'govern',
        'rule', 'lead', 'guide', 'direct', 'steer', 'navigate', 'pilot',
        'drive', 'operate', 'run', 'execute', 'perform', 'conduct', 'carry out',
        'implement', 'enforce', 'apply', 'use', 'utilize', 'employ', 'exercise',
        'practice', 'train', 'teach', 'instruct', 'educate', 'coach', 'mentor',
        'advise', 'counsel', 'consult', 'recommend', 'suggest', 'propose',
        'offer', 'present', 'provide', 'supply', 'furnish', 'equip', 'arm',
        'prepare', 'ready', 'set', 'arrange', 'organize', 'order', 'sort',
        'classify', 'categorize', 'group', 'cluster', 'bunch', 'gather',
        'collect', 'accumulate', 'amass', 'assemble', 'build', 'construct',
        'create', 'make', 'form', 'shape', 'mold', 'forge', 'craft', 'design',
        'develop', 'produce', 'generate', 'manufacture', 'fabricate'
    ]
    count = 0
    text_lower = text.lower()
    for verb in action_verbs:
        if verb in text_lower:
            count += 1
    return count

def extract_email_features(email_text):
    # Extract subject and body
    subject_match = re.search(r'Subject:\s*(.*?)(?:\n\n|\n$)', email_text, re.IGNORECASE)
    subject = subject_match.group(1).strip() if subject_match else ""
    body = email_text[email_text.find('\n\n')+2:].strip() if '\n\n' in email_text else email_text.strip()
    
    # Combine subject and body for processing
    combined_text = f"{subject} {body}"
    
    # Additional patterns for feature extraction
    time_sensitive_patterns = [
        r'\b(today|tomorrow|asap|urgent|immediate|now)\b',
        r'\b(by|before|until)\b.*\b(end of|eod|today|tomorrow)\b',
        r'\b(deadline|due|expires?)\b.*\b(today|tomorrow|soon)\b'
    ]
    
    action_required_patterns = [
        r'\b(need|require|must|should)\b.*\b(action|response|reply|review)\b',
        r'\b(please|kindly)\b.*\b(provide|send|review|approve)\b',
        r'\baction\s+required\b'
    ]
    
    importance_patterns = [
        r'\b(important|critical|crucial|essential|vital)\b',
        r'\b(high|top)\b.*\b(priority|importance)\b',
        r'\b(significant|major|key)\b.*\b(impact|issue|concern)\b'
    ]
    
    # Common low-priority patterns
    routine_patterns = [
        r'\b(weekly|daily|monthly|regular|routine)\b.*\b(meeting|update|report|reminder)\b',
        r'\b(reminder|fyi|for your information)\b',
        r'\b(newsletter|announcement|bulletin)\b',
        r'\b(scheduled|recurring)\b'
    ]
    
    # Casual conversation patterns
    casual_patterns = [
        r'\b(hi|hey|hello)\b.*\b(how are you|how\'s it going|what\'s up)\b',
        r'\b(thanks|thank you|thx)\b.*\b(regards|best|cheers)\b',
        r'\b(see you|catch up|talk to you|chat)\b.*\b(later|soon|tomorrow|next)\b',
        r'\b(have a|enjoy your)\b.*\b(day|weekend|holiday|break)\b',
        r'\b(congratulations|congrats|well done|great job)\b',
        r'\b(lunch|coffee|break)\b.*\b(together|with|join)\b'
    ]
    
    # Common high-priority patterns
    urgent_patterns = [
        r'\b(urgent|asap|immediate|emergency)\b',
        r'\b(critical|crucial|vital)\b.*\b(deadline|issue|problem)\b',
        r'\b(escalation|escalated)\b',
        r'\b(blocked|blocking)\b.*\b(progress|development)\b',
        r'\b(urgent)\b.*\b(attention|response|action)\b',
        r'\b(immediate)\b.*\b(review|approval|decision)\b'
    ]
    
    # Risk-related patterns with context
    risk_patterns = [
        r'\b(risk|issue|problem|error)\b.*\b(critical|severe|major)\b',
        r'\b(failure|outage|incident)\b',
        r'\b(security|breach|vulnerability)\b',
        r'\b(production|system)\b.*\b(down|issue|error)\b',
        r'\b(customer|client)\b.*\b(complaint|escalation|issue)\b',
        r'\b(deadline|milestone)\b.*\b(missed|risk|delayed)\b'
    ]
    
    # Extract features
    features = {
        'subject_len': len(subject),
        'body_len': len(body),
        'total_len': len(combined_text),
        'urgency_flag': 1 if any(re.search(pattern, combined_text.lower()) for pattern in urgent_patterns) else 0,
        'risk_flag': 1 if any(re.search(pattern, combined_text.lower()) for pattern in risk_patterns) else 0,
        'time_sensitive_flag': 1 if any(re.search(pattern, combined_text.lower()) for pattern in time_sensitive_patterns) else 0,
        'action_required_flag': 1 if any(re.search(pattern, combined_text.lower()) for pattern in action_required_patterns) else 0,
        'importance_flag': 1 if any(re.search(pattern, combined_text.lower()) for pattern in importance_patterns) else 0,
        'num_action_verbs': count_action_verbs(combined_text),
        'num_uppercase_words_subject': len([word for word in subject.split() if word.isupper()]),
        'num_uppercase_words_body': len([word for word in body.split() if word.isupper()]),
        'has_question': 1 if '?' in combined_text else 0,
        'num_questions': combined_text.count('?'),
        'routine_flag': 1 if any(re.search(pattern, combined_text.lower()) for pattern in routine_patterns) else 0,
        'casual_flag': 1 if any(re.search(pattern, combined_text.lower()) for pattern in casual_patterns) else 0,
        'urgency_and_risk': 1 if (any(re.search(pattern, combined_text.lower()) for pattern in urgent_patterns) and 
                                 any(re.search(pattern, combined_text.lower()) for pattern in risk_patterns)) else 0,
        'num_sentences': len(re.split(r'[.!?]+', combined_text)),
        'num_paragraphs': len([p for p in combined_text.split('\n\n') if p.strip()]),
        'Combined_Text': combined_text
    }
    
    return features

def load_model():
    print("\nLoading Random Forest model...")
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, 'Models', 'Old Models', 'rf_priority_model.joblib')
        preprocessor_path = os.path.join(current_dir, 'Models', 'Old Models', 'rf_priority_preprocessor.joblib')
        
        print(f"Looking for model at: {model_path}")
        print(f"Looking for preprocessor at: {preprocessor_path}")
        
        if not os.path.exists(model_path):
            print(f"Error: Model file not found at {model_path}")
            return None, None
            
        if not os.path.exists(preprocessor_path):
            print(f"Error: Preprocessor file not found at {preprocessor_path}")
            return None, None
            
        model = joblib.load(model_path)
        print("Successfully loaded model")
        
        preprocessor = joblib.load(preprocessor_path)
        print("Successfully loaded preprocessor")
        
        return model, preprocessor
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        print(f"Current working directory: {os.getcwd()}")
        return None, None

def predict_priority(email_text, model, preprocessor):
    print("\nExtracting features from email...")
    features = extract_email_features(email_text)
    print("Features extracted successfully")
    
    try:
        print("\nPreprocessing email...")
        # Create DataFrame with basic features
        df = pd.DataFrame({
            'text': [features['Combined_Text']],
            'subject_len': [features['subject_len']],
            'num_action_verbs': [features['num_action_verbs']],
            'urgency_flag': [features['urgency_flag']],
            'risk_flag': [features['risk_flag']],
            'has_question': [features['has_question']],
            'routine_flag': [features['routine_flag']],
            'casual_flag': [features['casual_flag']]
        })
        
        # Preprocess the text using the loaded preprocessor
        print("Transforming features...")
        processed_features = preprocessor.transform(df)
        print(f"Processed features shape: {processed_features.shape}")
        
        print("\nGenerating predictions...")
        # Get prediction probabilities
        probs = model.predict_proba(processed_features)[0]
        prediction = model.predict(processed_features)[0]
        print(f"Raw prediction: {prediction}")
        print(f"Probabilities: {probs}")
        
        # Map predictions to priority levels
        priority_map = {0: "Low", 1: "Medium", 2: "High"}
        predicted_priority = priority_map[prediction]
        confidence = max(probs)
        
        return {
            'prediction': predicted_priority,
            'probabilities': probs,
            'confidence': confidence,
            'features': features
        }
    except Exception as e:
        print(f"Error in prediction: {str(e)}")
        print("Feature values:")
        for key, value in features.items():
            if key != 'Combined_Text':  # Don't print the full text
                print(f"  {key}: {value}")
        return None

def explain_prediction(result):
    if not result:
        return "Could not generate prediction explanation."
    
    features = result['features']
    prediction = result['prediction']
    confidence = result['confidence']
    
    explanation = [
        f"\nPredicted Priority: {prediction}",
        f"Confidence: {confidence:.2%}",
        "\nKey Factors:"
    ]
    
    # Add feature explanations
    if features['urgency_flag'] or features['time_sensitive_flag']:
        explanation.append("- Urgency: Present")
        if features['time_sensitive_flag']:
            explanation.append("  * Contains time-sensitive indicators")
    
    if features['risk_flag']:
        explanation.append("- Risk: Present")
        if features['importance_flag']:
            explanation.append("  * Contains importance/criticality indicators")
    
    if features['action_required_flag']:
        explanation.append("- Action Required: Yes")
        explanation.append(f"  * Contains {features['num_action_verbs']} action verbs")
    
    if features['routine_flag']:
        explanation.append("- Routine: Yes")
        explanation.append("  * Contains patterns indicating routine/recurring items")
    
    if features['casual_flag']:
        explanation.append("- Casual: Yes")
        explanation.append("  * Contains casual conversation patterns")
    
    if features['has_question']:
        explanation.append(f"- Questions: {features['num_questions']} found")
    
    # Add structural analysis
    explanation.append("\nStructural Analysis:")
    explanation.append(f"- Subject Length: {features['subject_len']} characters")
    explanation.append(f"- Body Length: {features['body_len']} characters")
    explanation.append(f"- Paragraphs: {features['num_paragraphs']}")
    explanation.append(f"- Sentences: {features['num_sentences']}")
    
    # Add confidence level
    if confidence >= 0.9:
        explanation.append("\nVery high confidence in this prediction")
    elif confidence >= 0.7:
        explanation.append("\nHigh confidence in this prediction")
    else:
        explanation.append("\nModerate confidence in this prediction")
    
    return "\n".join(explanation)

def main():
    print("Email Priority Prediction System (Random Forest Model)")
    print("==============================================")
    
    # Load the model
    model, preprocessor = load_model()
    if not model or not preprocessor:
        print("Failed to load model. Exiting.")
        return
    
    while True:
        print("\nOptions:")
        print("1. Test with sample high-priority email")
        print("2. Test with sample medium-priority email")
        print("3. Test with sample low-priority email")
        print("4. Enter custom email")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '5':
            break
            
        email_text = ""
        if choice == '1':
            email_text = """Subject: URGENT: Critical System Outage - Immediate Action Required

Dear Team,

We are experiencing a critical system outage affecting our main production servers. This requires immediate attention and resolution.

Key Issues:
- Production system is down
- Customer services are affected
- Revenue impact is significant

Please respond ASAP with your availability to join an emergency response call.

Regards,
System Admin"""
        elif choice == '2':
            email_text = """Subject: Project Status Update Request

Hi Team,

Could you please provide an update on the current status of the project? We need to review the following items:

1. Timeline progress
2. Resource allocation
3. Budget status
4. Risk assessment

Please submit your updates by end of day.

Thanks,
Project Manager"""
        elif choice == '3':
            email_text = """Subject: Weekly Team Meeting Reminder

Hello everyone,

Just a friendly reminder about our regular weekly team meeting tomorrow at 10 AM.

Agenda:
- Team updates
- Ongoing projects
- Open discussion

See you all there!

Best regards,
Team Lead"""
        elif choice == '4':
            print("\nEnter your email text (press Enter twice to finish):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            email_text = "\n".join(lines)
        else:
            print("Invalid choice. Please try again.")
            continue
            
        if email_text:
            result = predict_priority(email_text, model, preprocessor)
            if result:
                explanation = explain_prediction(result)
                print(explanation)
            else:
                print("Failed to generate prediction.")

if __name__ == "__main__":
    main()