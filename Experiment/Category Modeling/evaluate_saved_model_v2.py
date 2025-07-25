import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import logging
import re
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler, LabelEncoder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize keyword sets
business_keywords = {
    'report', 'update', 'business', 'project', 'status',
    'review', 'process', 'procedure', 'policy', 'department',
    'team', 'organization', 'company', 'corporate', 'strategy'
}

formal_phrases = {
    'please find', 'kindly', 'regarding', 'with respect to',
    'as per', 'pursuant to', 'in reference to', 'concerning'
}

pm_keywords = {
    'milestone', 'deadline', 'timeline', 'roadmap', 'sprint',
    'deliverable', 'stakeholder', 'resource', 'scope', 'budget',
    'planning', 'implementation', 'phase', 'progress', 'target'
}

strategy_keywords = {
    'strategic', 'objective', 'goal', 'initiative', 'vision',
    'mission', 'growth', 'development', 'plan', 'forecast',
    'analysis', 'market', 'competitive', 'opportunity'
}

hr_keywords = {
    'policy', 'procedure', 'compliance', 'regulation', 'guideline',
    'employee', 'staff', 'personnel', 'benefit', 'leave',
    'holiday', 'payroll', 'training', 'development', 'hr'
}

internal_markers = {
    'all staff', 'all employees', 'company-wide',
    'internal use', 'confidential', 'do not forward'
}

policy_patterns = [
    r'policy\s+update',
    r'new\s+policy',
    r'revised\s+policy',
    r'effective\s+(?:from|date)',
    r'please\s+note\s+(?:the|this)\s+change'
]

def clean_text(text):
    """Enhanced text cleaning with pattern preservation."""
    if not isinstance(text, str):
        return ""
    
    text = text.lower()
    
    # Preserve important patterns before cleaning
    text = re.sub(r'(?<=[a-z])\.(?=[a-z])', '. ', text)  # Fix merged sentences
    text = re.sub(r'(?<=\d)\.(?=\d)', 'DOT', text)  # Preserve version numbers
    text = re.sub(r'(?<=\w)-(?=\w)', 'HYPHEN', text)  # Preserve hyphenated words
    
    # Clean special characters while preserving spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Restore preserved patterns
    text = text.replace('DOT', '.')
    text = text.replace('HYPHEN', '-')
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def extract_contextual_features(subject, message):
    """Extract contextual relationships between subject and message."""
    subject_words = set(str(subject).lower().split())
    message_words = set(str(message).lower().split())
    
    # Subject-message overlap
    word_overlap = len(subject_words & message_words)
    overlap_ratio = word_overlap / (len(subject_words | message_words) + 1)
    
    # Key phrase continuation
    subject_bigrams = set(' '.join(pair) for pair in zip(str(subject).lower().split()[:-1], 
                                                        str(subject).lower().split()[1:]))
    message_bigrams = set(' '.join(pair) for pair in zip(str(message).lower().split()[:-1], 
                                                        str(message).lower().split()[1:]))
    phrase_continuation = len(subject_bigrams & message_bigrams)
    
    return [overlap_ratio, phrase_continuation]

def extract_email_features(subject, message):
    """Extract enhanced email-specific features."""
    # Basic text preparation
    subject = str(subject)
    message = str(message)
    subject_words = subject.split()
    message_words = message.split()
    
    # Basic length features
    subject_len = len(subject_words)
    message_len = len(message_words)
    
    # Question and exclamation features
    subject_questions = subject.count('?')
    message_questions = message.count('?')
    subject_exclamations = subject.count('!')
    message_exclamations = message.count('!')
    
    # Case features
    subject_upper = sum(1 for c in subject if c.isupper())
    message_upper = sum(1 for c in message if c.isupper())
    subject_upper_ratio = subject_upper / (len(subject) + 1)
    message_upper_ratio = message_upper / (len(message) + 1)
    
    # Digit features
    subject_digits = sum(1 for c in subject if c.isdigit())
    message_digits = sum(1 for c in message if c.isdigit())
    subject_digit_ratio = subject_digits / (len(subject) + 1)
    message_digit_ratio = message_digits / (len(message) + 1)
    
    # URL and email features
    has_url = int(bool(re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message)))
    has_email = int(bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message)))
    
    # Special character ratios
    subject_special = sum(not c.isalnum() and not c.isspace() for c in subject) / (len(subject) + 1)
    message_special = sum(not c.isalnum() and not c.isspace() for c in message) / (len(message) + 1)
    
    # Business communication features
    business_keyword_count = sum(1 for word in message_words if word in business_keywords)
    business_keyword_ratio = business_keyword_count / (len(message_words) + 1)
    formality_score = sum(1 for phrase in formal_phrases if phrase in message.lower())
    has_document_ref = int(bool(re.search(r'ref|reference|document|doc|attachment|attached', message.lower())))
    
    # Project management features
    pm_keyword_count = sum(1 for word in message_words if word in pm_keywords)
    strategy_score = sum(1 for word in message_words if word in strategy_keywords)
    has_timeline = int(bool(re.search(r'q[1-4]|quarter|fy\d{2,4}|20\d{2}|fiscal', message.lower())))
    
    # HR and policy features
    hr_keyword_count = sum(1 for word in message_words if word in hr_keywords)
    has_policy_update = int(any(re.search(pattern, message.lower()) for pattern in policy_patterns))
    is_internal = sum(1 for marker in internal_markers if marker in message.lower())
    
    # Contextual features
    contextual_features = extract_contextual_features(subject, message)
    
    # Combine all features
    features = [
        subject_len, message_len,
        subject_questions, message_questions,
        subject_exclamations, message_exclamations,
        subject_upper_ratio, message_upper_ratio,
        subject_digit_ratio, message_digit_ratio,
        has_url, has_email,
        subject_special, message_special,
        subject_len / (message_len + 1),
        (subject_questions + message_questions) / (subject_len + message_len + 1),
        (subject_exclamations + message_exclamations) / (subject_len + message_len + 1),
        business_keyword_ratio,
        formality_score / (len(message_words) + 1),
        has_document_ref,
        pm_keyword_count / (len(message_words) + 1),
        strategy_score / (len(message_words) + 1),
        has_timeline,
        hr_keyword_count / (len(message_words) + 1),
        has_policy_update,
        is_internal / (len(message_words) + 1)
    ] + contextual_features
    
    return np.array(features)

def main():
    # Load the saved model components
    logging.info("Loading saved model components...")
    model_path = 'enhanced_email_categorization_model_v2.joblib'
    
    # Check if model path is provided as command line argument
    import sys
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    
    model_data = joblib.load(model_path)
    
    # Extract components
    vectorizer = model_data['vectorizer']
    scaler = model_data['scaler']
    label_encoder = model_data['label_encoder']
    models = model_data['models']
    ensemble = model_data['ensemble']
    
    # Load test data
    logging.info("Loading test data...")
    test_data = pd.read_csv('final_email_category_balanced.csv')
    
    # Clean and prepare test data
    test_data = test_data[
        (test_data['Cleaned_Subject'].str.len() >= 3) & 
        (test_data['Cleaned_Message'].str.len() >= 10)
    ].drop_duplicates(subset=['Cleaned_Subject', 'Cleaned_Message']).reset_index(drop=True)
    
    # Prepare text data
    test_data['cleaned_subject'] = test_data['Cleaned_Subject'].apply(clean_text)
    test_data['cleaned_message'] = test_data['Cleaned_Message'].apply(clean_text)
    test_data['combined_text'] = test_data['cleaned_subject'] + ' SUBJECT_END ' + test_data['cleaned_message']
    
    # Extract features
    logging.info("Extracting features...")
    basic_features = np.vstack([
        extract_email_features(row['Cleaned_Subject'], row['Cleaned_Message'])
        for _, row in test_data.iterrows()
    ])
    
    # Transform text features
    text_features = vectorizer.transform(test_data['combined_text'])
    
    # Scale features
    basic_features_scaled = scaler.transform(basic_features)
    basic_features_sparse = csr_matrix(basic_features_scaled)
    
    # Combine features
    X_test = hstack([text_features, basic_features_sparse]).tocsr()
    
    # Encode target variable
    y_test = label_encoder.transform(test_data['Qwen2.5_Category'])
    
    # Evaluate each model
    logging.info("\nEvaluating individual models...")
    for name, model in models.items():
        logging.info(f"\nEvaluating {name}...")
        y_pred = model.predict(X_test)
        
        # Print detailed classification report
        logging.info(f"\nDetailed Classification Report for {name}:")
        logging.info(classification_report(y_test, y_pred, 
                                         target_names=label_encoder.classes_))
        
        # Print confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        logging.info(f"\nConfusion Matrix for {name}:")
        logging.info(cm)
        
        # Calculate per-class metrics
        per_class_metrics = {}
        for i, class_name in enumerate(label_encoder.classes_):
            per_class_metrics[class_name] = {
                'precision': precision_score(y_test, y_pred, labels=[i], average='micro'),
                'recall': recall_score(y_test, y_pred, labels=[i], average='micro'),
                'f1': f1_score(y_test, y_pred, labels=[i], average='micro')
            }
        
        logging.info(f"\nPer-class metrics for {name}:")
        for class_name, metrics in per_class_metrics.items():
            logging.info(f"{class_name}:")
            for metric, value in metrics.items():
                logging.info(f"  {metric}: {value:.4f}")
    
    # Evaluate ensemble
    logging.info("\nEvaluating ensemble model...")
    y_pred_ensemble = ensemble.predict(X_test)
    
    # Print detailed classification report for ensemble
    logging.info("\nDetailed Classification Report for Ensemble:")
    logging.info(classification_report(y_test, y_pred_ensemble, 
                                     target_names=label_encoder.classes_))
    
    # Print confusion matrix for ensemble
    cm_ensemble = confusion_matrix(y_test, y_pred_ensemble)
    logging.info("\nConfusion Matrix for Ensemble:")
    logging.info(cm_ensemble)
    
    # Calculate per-class metrics for ensemble
    per_class_metrics_ensemble = {}
    for i, class_name in enumerate(label_encoder.classes_):
        per_class_metrics_ensemble[class_name] = {
            'precision': precision_score(y_test, y_pred_ensemble, labels=[i], average='micro'),
            'recall': recall_score(y_test, y_pred_ensemble, labels=[i], average='micro'),
            'f1': f1_score(y_test, y_pred_ensemble, labels=[i], average='micro')
        }
    
    logging.info("\nPer-class metrics for Ensemble:")
    for class_name, metrics in per_class_metrics_ensemble.items():
        logging.info(f"{class_name}:")
        for metric, value in metrics.items():
            logging.info(f"  {metric}: {value:.4f}")

if __name__ == "__main__":
    main() 