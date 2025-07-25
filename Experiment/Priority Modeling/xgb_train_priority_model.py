import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
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
    
    # New feature sets for Low priority detection
    informational_words = {
        'newsletter', 'digest', 'update', 'roundup', 'summary', 'weekly',
        'monthly', 'quarterly', 'announcement', 'news', 'introduction',
        'welcome', 'fyi', 'info', 'information'
    }
    
    social_words = {
        'social', 'event', 'party', 'celebration', 'lunch', 'dinner',
        'game', 'fun', 'activity', 'survey', 'poll', 'feedback',
        'rsvp', 'invitation', 'celebrate', 'join'
    }
    
    optional_phrases = {
        'when you have time', 'at your convenience', 'if you want',
        'feel free', 'optional', 'if you would like', 'if you wish',
        'no action required', 'for your information'
    }
    
    # Calculate features
    features = []
    
    for idx, row in df.iterrows():
        subject_words = row['Cleaned_Subject'].split()
        message_words = row['Cleaned_Message'].split()
        combined_text = row['Combined_Text']
        
        # Original feature calculations
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
        
        # New feature calculations
        informational_score = sum(1 for word in informational_words if word in combined_text.split())
        social_score = sum(1 for word in social_words if word in combined_text.split())
        optional_score = sum(1 for phrase in optional_phrases if phrase in combined_text)
        
        # Normalize new scores
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

def train_model():
    """Train XGBoost model for email priority classification"""
    # Load data
    print("Loading data...")
    df = pd.read_csv('cleaned_priority_email_dataset.csv')
    
    # Extract features
    print("Extracting features...")
    X = extract_features(df)
    y = df['Email_Priority']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Create DMatrix for XGBoost
    dtrain = xgb.DMatrix(X_train_scaled, label=y_train)
    dtest = xgb.DMatrix(X_test_scaled, label=y_test)
    
    # Calculate class weights
    class_weights = {
        0: 2.5,  # Low priority (increased from 1.5)
        1: 1.0,  # Medium priority
        2: 1.0   # High priority
    }
    
    # Set parameters
    params = {
        'objective': 'multi:softprob',
        'num_class': 3,
        'max_depth': 5,  # Increased from 4
        'eta': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 1,  # Decreased from 2
        'gamma': 0.1,  # Decreased from 0.2
        'eval_metric': 'mlogloss',
        'scale_pos_weight': 1.0
    }
    
    # Train model
    print("Training model...")
    num_rounds = 200  # Increased from 100
    model = xgb.train(
        params,
        dtrain,
        num_rounds,
        evals=[(dtrain, 'train'), (dtest, 'test')],
        early_stopping_rounds=20,  # Increased from 10
        verbose_eval=10
    )
    
    # Make predictions
    y_pred = model.predict(dtest)
    y_pred_labels = np.argmax(y_pred, axis=1)
    
    # Print evaluation metrics
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred_labels))
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred_labels)
    print(cm)
    
    # Plot feature importance
    importance = model.get_score(importance_type='gain')
    importance = {k: v for k, v in sorted(importance.items(), key=lambda item: item[1], reverse=True)}
    
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(importance)), list(importance.values()))
    plt.xticks(range(len(importance)), list(importance.keys()), rotation=45, ha='right')
    plt.title('Feature Importance (Gain)')
    plt.tight_layout()
    plt.savefig('xgb_feature_importance.png')
    plt.close()
    
    # Save model and scaler
    print("\nSaving model and scaler...")
    model.save_model('Models/xgb_priority_model.json')
    joblib.dump(scaler, 'Models/xgb_scaler.joblib')
    
    print("Training completed successfully!")

if __name__ == "__main__":
    train_model() 