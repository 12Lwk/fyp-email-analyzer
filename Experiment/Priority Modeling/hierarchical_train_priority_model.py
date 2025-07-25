import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import xgboost as xgb
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

def clean_text(text):
    """Clean and preprocess text"""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    text = ' '.join(text.split())
    return text

def extract_features(df):
    """Extract features from email data"""
    # Clean text
    df['Cleaned_Subject'] = df['Subject'].apply(clean_text)
    df['Cleaned_Message'] = df['Message'].apply(clean_text)
    df['Combined_Text'] = df['Cleaned_Subject'] + ' ' + df['Cleaned_Message']
    
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
    features = []
    
    for idx, row in df.iterrows():
        subject_words = row['Cleaned_Subject'].split()
        message_words = row['Cleaned_Message'].split()
        combined_text = row['Combined_Text']
        
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
        
        # Uppercase words
        num_uppercase_words = sum(1 for word in row['Subject'].split() 
                                if word.isupper() and len(word) > 1)
        
        # Text length features
        subject_len = len(row['Subject'])
        message_len = len(row['Message'])
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
        
        # Add features to list
        features.append([
            urgency_flag,
            risk_flag,
            urgency_and_risk,
            num_action_verbs,
            num_uppercase_words,
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
            optional_flag
        ])
    
    # Convert to DataFrame
    feature_names = [
        'urgency_flag', 'risk_flag', 'urgency_and_risk',
        'num_action_verbs', 'num_uppercase_words',
        'subject_len', 'message_len', 'combined_len',
        'has_question', 'has_deadline', 'time_sensitive',
        'num_words_subject', 'num_words_message',
        'informational_flag', 'social_flag', 'optional_flag'
    ]
    
    return pd.DataFrame(features, columns=feature_names)

def train_high_vs_rest_model(X, y):
    """Train model to distinguish High priority from others"""
    # Create binary labels
    y_binary = (y == 2).astype(int)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_binary, test_size=0.2, random_state=42, stratify=y_binary
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Create DMatrix
    dtrain = xgb.DMatrix(X_train_scaled, label=y_train)
    dtest = xgb.DMatrix(X_test_scaled, label=y_test)
    
    # Set parameters
    params = {
        'objective': 'binary:logistic',
        'max_depth': 6,
        'eta': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 1,
        'gamma': 0.1,
        'eval_metric': 'logloss'
    }
    
    # Train model
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=200,
        evals=[(dtrain, 'train'), (dtest, 'test')],
        early_stopping_rounds=20,
        verbose_eval=10
    )
    
    return model, scaler

def train_medium_vs_low_model(X, y):
    """Train model to distinguish Medium from Low priority"""
    # Filter data for Medium and Low priority
    mask = (y == 0) | (y == 1)
    X_filtered = X[mask]
    y_filtered = y[mask]
    
    # Create binary labels (1 for Medium, 0 for Low)
    y_binary = (y_filtered == 1).astype(int)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_filtered, y_binary, test_size=0.2, random_state=42, stratify=y_binary
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Create DMatrix
    dtrain = xgb.DMatrix(X_train_scaled, label=y_train)
    dtest = xgb.DMatrix(X_test_scaled, label=y_test)
    
    # Set parameters
    params = {
        'objective': 'binary:logistic',
        'max_depth': 5,
        'eta': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 1,
        'gamma': 0.1,
        'eval_metric': 'logloss'
    }
    
    # Train model
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=200,
        evals=[(dtrain, 'train'), (dtest, 'test')],
        early_stopping_rounds=20,
        verbose_eval=10
    )
    
    return model, scaler

def train_models():
    """Train hierarchical classification models"""
    # Load data
    print("Loading data...")
    df = pd.read_csv('C:/Users/User/OneDrive - Asia Pacific University/APU Final Year Project/FYP Email Project Documents/Email Dataset Python/FYP PART 2/Priority Modeling/cleaned_priority_email_dataset.csv')
    
    # Extract features
    print("Extracting features...")
    X = extract_features(df)
    y = df['Email_Priority']
    
    # Train High vs Rest model
    print("\nTraining High vs Rest model...")
    high_model, high_scaler = train_high_vs_rest_model(X, y)
    
    # Train Medium vs Low model
    print("\nTraining Medium vs Low model...")
    medium_low_model, medium_low_scaler = train_medium_vs_low_model(X, y)
    
    # Save models and scalers
    print("\nSaving models and scalers...")
    high_model.save_model('C:/Users/User/OneDrive - Asia Pacific University/APU Final Year Project/FYP Email Project Documents/Email Dataset Python/FYP PART 2/Priority Modeling/Models/high_priority_model.json')
    medium_low_model.save_model('C:/Users/User/OneDrive - Asia Pacific University/APU Final Year Project/FYP Email Project Documents/Email Dataset Python/FYP PART 2/Priority Modeling/Models/medium_low_priority_model.json')
    joblib.dump(high_scaler, 'C:/Users/User/OneDrive - Asia Pacific University/APU Final Year Project/FYP Email Project Documents/Email Dataset Python/FYP PART 2/Priority Modeling/Models/high_priority_scaler.joblib')
    joblib.dump(medium_low_scaler, 'C:/Users/User/OneDrive - Asia Pacific University/APU Final Year Project/FYP Email Project Documents/Email Dataset Python/FYP PART 2/Priority Modeling/Models/medium_low_priority_scaler.joblib')
    
    print("Training completed successfully!")

if __name__ == "__main__":
    train_models() 