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

def clean_text(text):
    """Clean text by removing special characters and extra spaces."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_email_features(subject, message):
    """Extract enhanced email-specific features."""
    # Basic length features
    subject_words = str(subject).split()
    message_words = str(message).split()
    subject_len = len(subject_words)
    message_len = len(message_words)
    
    # Question and exclamation features
    subject_questions = str(subject).count('?')
    message_questions = str(message).count('?')
    subject_exclamations = str(subject).count('!')
    message_exclamations = str(message).count('!')
    
    # Case features
    subject_upper = sum(1 for c in str(subject) if c.isupper())
    message_upper = sum(1 for c in str(message) if c.isupper())
    subject_upper_ratio = subject_upper / (len(str(subject)) + 1)
    message_upper_ratio = message_upper / (len(str(message)) + 1)
    
    # Digit features
    subject_digits = sum(1 for c in str(subject) if c.isdigit())
    message_digits = sum(1 for c in str(message) if c.isdigit())
    subject_digit_ratio = subject_digits / (len(str(subject)) + 1)
    message_digit_ratio = message_digits / (len(str(message)) + 1)
    
    # URL and email features
    has_url = int(bool(re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(message))))
    has_email = int(bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', str(message))))
    
    # Special character ratios
    subject_special = sum(not c.isalnum() and not c.isspace() for c in str(subject)) / (len(str(subject)) + 1)
    message_special = sum(not c.isalnum() and not c.isspace() for c in str(message)) / (len(str(message)) + 1)
    
    return np.array([
        subject_len,
        message_len,
        subject_questions,
        message_questions,
        subject_exclamations,
        message_exclamations,
        subject_upper_ratio,
        message_upper_ratio,
        subject_digit_ratio,
        message_digit_ratio,
        has_url,
        has_email,
        subject_special,
        message_special,
        subject_len / (message_len + 1),
        (subject_questions + message_questions) / (subject_len + message_len + 1),
        (subject_exclamations + message_exclamations) / (subject_len + message_len + 1)
    ])

def main():
    # Load the saved model components
    logging.info("Loading saved model components...")
    model_data = joblib.load('enhanced_email_categorization_model.joblib')
    
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