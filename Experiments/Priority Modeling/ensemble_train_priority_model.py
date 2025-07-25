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
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from nltk import word_tokenize

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

def extract_features(df):
    """Extract features from email data"""
    features = []
    
    # Initialize sentiment analyzer
    sia = SentimentIntensityAnalyzer()
    
    for _, row in df.iterrows():
        # Clean text
        subject = clean_text(row['Subject'])
        message = clean_text(row['Message'])
        
        # Basic text features
        subject_len = len(subject)
        message_len = len(message)
        total_len = subject_len + message_len
        
        # Word counts
        subject_words = word_tokenize(subject)
        message_words = word_tokenize(message)
        num_words_subject = len(subject_words)
        num_words_message = len(message_words)
        total_words = num_words_subject + num_words_message
        
        # Uppercase words
        num_uppercase_words_subject = sum(1 for word in subject_words if word.isupper())
        num_uppercase_words_message = sum(1 for word in message_words if word.isupper())
        
        # Question marks
        has_question_subject = '?' in subject
        has_question_message = '?' in message
        
        # Exclamation marks
        has_exclamation_subject = '!' in subject
        has_exclamation_message = '!' in message
        
        # Sentiment analysis
        subject_sentiment = sia.polarity_scores(subject)
        message_sentiment = sia.polarity_scores(message)
        
        # Action words
        action_words = {'urgent', 'important', 'asap', 'deadline', 'reminder', 'request', 'need', 'required', 'critical'}
        num_action_words_subject = sum(1 for word in subject_words if word in action_words)
        num_action_words_message = sum(1 for word in message_words if word in action_words)
        
        # Time-related words
        time_words = {'today', 'tomorrow', 'week', 'month', 'year', 'hour', 'minute', 'second', 'deadline', 'due'}
        num_time_words_subject = sum(1 for word in subject_words if word in time_words)
        num_time_words_message = sum(1 for word in message_words if word in time_words)
        
        # Risk-related words
        risk_words = {'security', 'breach', 'critical', 'emergency', 'alert', 'warning', 'issue', 'problem'}
        num_risk_words_subject = sum(1 for word in subject_words if word in risk_words)
        num_risk_words_message = sum(1 for word in message_words if word in risk_words)
        
        # Additional features
        has_urgency = any(word in action_words for word in subject_words + message_words)
        has_risk = any(word in risk_words for word in subject_words + message_words)
        urgency_and_risk = has_urgency and has_risk
        
        # Combine features
        feature_vector = [
            subject_len, message_len, total_len,
            num_words_subject, num_words_message, total_words,
            num_uppercase_words_subject, num_uppercase_words_message,
            int(has_question_subject), int(has_question_message),
            int(has_exclamation_subject), int(has_exclamation_message),
            subject_sentiment['compound'], message_sentiment['compound'],
            num_action_words_subject, num_action_words_message,
            num_time_words_subject, num_time_words_message,
            num_risk_words_subject, num_risk_words_message,
            subject_sentiment['pos'], subject_sentiment['neg'],
            message_sentiment['pos'], message_sentiment['neg'],
            int(has_urgency), int(has_risk), int(urgency_and_risk)
        ]
        
        features.append(feature_vector)
    
    return np.array(features)

def train_priority_model(X_train, y_train, priority_level):
    """Train a model for a specific priority level"""
    # Convert labels to binary (1 for target priority, 0 for others)
    y_binary = (y_train == priority_level).astype(int)
    
    # Calculate class weights safely
    n_pos = sum(y_binary)
    n_neg = len(y_binary) - n_pos
    
    if n_pos == 0:
        print(f"Warning: No {priority_level} priority examples in training set")
        return None
    
    # Set class weights to handle imbalance
    scale_pos_weight = n_neg / n_pos if n_pos > 0 else 1.0
    
    # Adjust parameters based on priority level
    if priority_level == 'Low':
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'eta': 0.05,  # Reduced learning rate
            'max_depth': 6,  # Increased depth
            'min_child_weight': 1,
            'scale_pos_weight': scale_pos_weight * 2.0,  # Increased weight for low priority
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'lambda': 1.0,  # L2 regularization
            'alpha': 0.5,   # L1 regularization
            'seed': 42
        }
    elif priority_level == 'High':
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'eta': 0.05,
            'max_depth': 7,  # Increased depth for high priority
            'min_child_weight': 1,
            'scale_pos_weight': scale_pos_weight * 1.5,  # Increased weight for high priority
            'subsample': 0.9,
            'colsample_bytree': 0.9,
            'lambda': 1.0,
            'alpha': 0.5,
            'seed': 42
        }
    else:  # Medium
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'eta': 0.05,
            'max_depth': 6,
            'min_child_weight': 1,
            'scale_pos_weight': scale_pos_weight,
            'subsample': 0.85,
            'colsample_bytree': 0.85,
            'lambda': 1.0,
            'alpha': 0.5,
            'seed': 42
        }
    
    # Create DMatrix
    dtrain = xgb.DMatrix(X_train, label=y_binary)
    
    # Train with early stopping
    num_rounds = 200  # Increased number of rounds
    watchlist = [(dtrain, 'train')]
    model = xgb.train(
        params,
        dtrain,
        num_rounds,
        watchlist,
        early_stopping_rounds=20,
        verbose_eval=False
    )
    
    return model

def train_models():
    """Train models for each priority level"""
    # Load and preprocess data
    df = pd.read_csv('cleaned_priority_email_dataset.csv')
    
    # Map numeric priorities to string labels
    priority_map = {0: 'Low', 1: 'Medium', 2: 'High'}
    df['Priority_Label'] = df['Email_Priority'].map(priority_map)
    
    # Print class distribution
    print("\nClass Distribution:")
    print(df['Priority_Label'].value_counts())
    
    # Extract features
    X = extract_features(df)
    y = df['Priority_Label'].values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Create Models directory if it doesn't exist
    import os
    os.makedirs('Models', exist_ok=True)
    
    # Train models for each priority level
    for priority in ['Low', 'Medium', 'High']:
        print(f"\nTraining {priority} Priority Model...")
        
        # Train model
        model = train_priority_model(X_train_scaled, y_train, priority)
        
        if model is None:
            print(f"Skipping {priority} priority model due to insufficient data")
            continue
        
        # Save model and scaler
        model.save_model(f'Models/{priority.lower()}_priority_model.json')
        joblib.dump(scaler, f'Models/{priority.lower()}_priority_scaler.joblib')
        
        # Evaluate on test set
        dtest = xgb.DMatrix(X_test_scaled)
        y_pred = model.predict(dtest)
        y_binary = (y_test == priority).astype(int)
        
        # Calculate metrics
        threshold = 0.5
        predictions = (y_pred >= threshold).astype(int)
        accuracy = np.mean(predictions == y_binary)
        precision = np.sum((predictions == 1) & (y_binary == 1)) / (np.sum(predictions == 1) + 1e-10)
        recall = np.sum((predictions == 1) & (y_binary == 1)) / (np.sum(y_binary == 1) + 1e-10)
        f1 = 2 * (precision * recall) / (precision + recall + 1e-10)
        
        print(f"{priority} Priority Model Performance:")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1-Score: {f1:.4f}")
        
        # Print feature importance
        importance = model.get_score(importance_type='gain')
        print("\nTop 5 Important Features:")
        for feature, score in sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {feature}: {score:.4f}")

if __name__ == "__main__":
    train_models() 