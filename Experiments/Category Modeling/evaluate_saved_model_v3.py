import joblib
import pandas as pd
import numpy as np
from scipy.sparse import hstack, csr_matrix
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from tqdm import tqdm
import sys
import os
from enhanced_email_categorization_v3 import EnhancedEmailCategorizationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def evaluate_model(model_path='enhanced_email_categorization_model_v3.joblib', 
                  data_path='final_email_category_balanced.csv',
                  test_size=0.2, 
                  random_state=42):
    """
    Evaluate the performance of a saved email categorization model
    """
    # Load the saved model and components
    logging.info(f"Loading model from {model_path}...")
    model_data = joblib.load(model_path)
    
    ensemble_model = model_data['ensemble']
    vectorizer = model_data['vectorizer']
    scaler = model_data['scaler']
    label_encoder = model_data['label_encoder']
    
    # Initialize the categorization system
    system = EnhancedEmailCategorizationSystem({})
    
    # Load test data
    logging.info(f"Loading test data from {data_path}...")
    email_data = pd.read_csv(data_path)
    
    # Clean data
    email_data = email_data[
        (email_data['Cleaned_Subject'].str.len() >= 3) & 
        (email_data['Cleaned_Message'].str.len() >= 10)
    ].drop_duplicates(subset=['Cleaned_Subject', 'Cleaned_Message']).reset_index(drop=True)
    
    # Prepare text data
    email_data['cleaned_subject'] = email_data['Cleaned_Subject'].apply(system.clean_text)
    email_data['cleaned_message'] = email_data['Cleaned_Message'].apply(system.clean_text)
    email_data['combined_text'] = email_data['cleaned_subject'] + ' SUBJECT_END ' + email_data['cleaned_message']
    
    # Use same random state for consistent testing
    np.random.seed(random_state)
    test_indices = np.random.choice(
        email_data.index, 
        size=int(len(email_data) * test_size), 
        replace=False
    )
    test_data = email_data.loc[test_indices]
    
    logging.info(f"Test set size: {len(test_data)} emails")
    
    # Extract features from test data
    logging.info("Extracting features from test data...")
    basic_features = np.vstack([
        system.extract_email_features(
            row['Subject'], 
            row['Message'],
            row['cleaned_subject'],
            row['cleaned_message']
        )
        for _, row in tqdm(test_data.iterrows(), total=len(test_data))
    ])
    
    # Transform text with the fitted vectorizer
    text_features = vectorizer.transform(test_data['combined_text'])
    
    # Scale features with the fitted scaler
    basic_features_scaled = scaler.transform(basic_features)
    basic_features_sparse = csr_matrix(basic_features_scaled)
    
    # Combine features
    X_test = hstack([text_features, basic_features_sparse]).tocsr()
    
    # Transform target labels
    y_test = label_encoder.transform(test_data['Qwen2.5_Category'])
    
    # Predict with the ensemble model
    logging.info("Making predictions with the ensemble model...")
    y_pred = ensemble_model.predict(X_test)
    
    # Calculate category frequencies
    category_counts = pd.Series(label_encoder.inverse_transform(y_test)).value_counts()
    
    # Calculate performance metrics
    accuracy = accuracy_score(y_test, y_pred)
    classification_rep = classification_report(
        y_test, 
        y_pred, 
        target_names=label_encoder.classes_,
        output_dict=True
    )
    
    # Create a dataframe from the classification report for better display
    metrics_df = pd.DataFrame(classification_rep).T
    metrics_df = metrics_df.round(2)
    
    # Log overall performance
    logging.info(f"Overall accuracy: {accuracy:.4f}")
    
    # Print classification report
    print("\nClassification Report:")
    print(pd.DataFrame(classification_rep).T.to_string())
    
    # Compare with previous model if requested
    if "--compare" in sys.argv:
        prev_model_path = "enhanced_email_categorization_model_v2.joblib"
        if os.path.exists(prev_model_path):
            logging.info(f"Comparing with previous model: {prev_model_path}")
            try:
                prev_model_data = joblib.load(prev_model_path)
                
                # Load the original v2 system for feature extraction
                logging.info("Loading original v2 system for compatibility...")
                # Import the v2 class if available, or use a simpler comparison approach
                try:
                    from enhanced_email_categorization_v2 import EnhancedEmailCategorizationSystem as V2System
                    v2_system = V2System({})
                    
                    # Extract features using the v2 system's method
                    logging.info("Extracting features using v2 system...")
                    prev_basic_features = np.vstack([
                        v2_system.extract_email_features(row['Subject'], row['Message'])
                        for _, row in tqdm(test_data.iterrows(), total=len(test_data))
                    ])
                    
                    prev_ensemble = prev_model_data['ensemble']
                    prev_vectorizer = prev_model_data['vectorizer']
                    prev_scaler = prev_model_data['scaler']
                    
                    # Transform text with the v2 vectorizer
                    prev_text_features = prev_vectorizer.transform(test_data['combined_text'])
                    
                    # Scale features with the v2 scaler
                    prev_basic_features_scaled = prev_scaler.transform(prev_basic_features)
                    prev_basic_features_sparse = csr_matrix(prev_basic_features_scaled)
                    
                    # Combine features
                    prev_X_test = hstack([prev_text_features, prev_basic_features_sparse]).tocsr()
                    
                    # Predict with v2 model
                    prev_y_pred = prev_ensemble.predict(prev_X_test)
                    prev_accuracy = accuracy_score(y_test, prev_y_pred)
                    prev_report = classification_report(
                        y_test, 
                        prev_y_pred, 
                        target_names=label_encoder.classes_,
                        output_dict=True
                    )
                    
                    # Compare metrics
                    print("\nModel Comparison:")
                    print(f"V2 Accuracy: {prev_accuracy:.4f}")
                    print(f"V3 Accuracy: {accuracy:.4f}")
                    print(f"Improvement: {(accuracy - prev_accuracy) * 100:.2f}%")
                    
                    # Compare per-category metrics
                    v2_metrics = pd.DataFrame(prev_report).T
                    v3_metrics = pd.DataFrame(classification_rep).T
                    
                    comparison = pd.DataFrame({
                        'V2_precision': v2_metrics['precision'],
                        'V3_precision': v3_metrics['precision'],
                        'V2_recall': v2_metrics['recall'],
                        'V3_recall': v3_metrics['recall'],
                        'V2_f1': v2_metrics['f1-score'],
                        'V3_f1': v3_metrics['f1-score'],
                    })
                    
                    comparison['prec_diff'] = comparison['V3_precision'] - comparison['V2_precision']
                    comparison['recall_diff'] = comparison['V3_recall'] - comparison['V2_recall']
                    comparison['f1_diff'] = comparison['V3_f1'] - comparison['V2_f1']
                    
                    print("\nPer-Category Improvement:")
                    print(comparison.round(2).to_string())
                
                except (ImportError, ValueError) as e:
                    logging.warning(f"Cannot directly compare with v2 due to feature compatibility: {e}")
                    logging.info("Using reference values for comparison instead...")
                    
                    # Use reference values from v2 performance metrics
                    v2_reference = {
                        'accuracy': 0.67,
                        'macro_avg_recall': 0.72,
                        'macro_avg_precision': 0.58,
                        'macro_avg_f1': 0.63,
                        'category_f1': {
                            'Spam': 0.75,
                            'Meeting & Scheduling': 0.77,
                            'Personal Communication & Purely Personal': 0.72,
                            'Finance & Transactions': 0.67,
                            'General Business Communication': 0.64,
                            'Legal & Contractual': 0.61,
                            'IT Alerts & System Notifications': 0.57,
                            'Project Management & Strategy': 0.45,
                            'Internal Policies & HR Updates': 0.39
                        }
                    }
                    
                    print("\nModel Comparison with Reference Values:")
                    print(f"V2 Reference Accuracy: {v2_reference['accuracy']:.4f}")
                    print(f"V3 Measured Accuracy: {accuracy:.4f}")
                    print(f"Difference: {(accuracy - v2_reference['accuracy']) * 100:.2f}%")
                    
                    # Create comparison dataframe using reference values
                    v3_metrics = pd.DataFrame(classification_rep).T
                    v3_category_f1 = v3_metrics.loc[label_encoder.classes_, 'f1-score']
                    
                    comparison = pd.DataFrame({
                        'V2_Reference_F1': pd.Series(v2_reference['category_f1']),
                        'V3_Measured_F1': v3_category_f1
                    })
                    
                    comparison['F1_diff'] = comparison['V3_Measured_F1'] - comparison['V2_Reference_F1']
                    
                    print("\nPer-Category F1-Score Comparison:")
                    print(comparison.round(2).to_string())
                    
            except Exception as e:
                logging.error(f"Error during model comparison: {e}")
                logging.info("Continuing without comparison...")
    
    # Plot confusion matrix
    plt.figure(figsize=(12, 10))
    cm = confusion_matrix(y_test, y_pred)
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    # Create confusion matrix heatmap
    sns.heatmap(
        cm_norm, 
        annot=True, 
        fmt='.2f', 
        cmap='Blues',
        xticklabels=label_encoder.classes_,
        yticklabels=label_encoder.classes_
    )
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title(f'Normalized Confusion Matrix (Accuracy: {accuracy:.4f})')
    plt.tight_layout()
    
    # Save the confusion matrix plot
    plt.savefig('confusion_matrix_v3.png')
    logging.info("Confusion matrix saved to confusion_matrix_v3.png")
    
    # Return metrics for potential further analysis
    return {
        'accuracy': accuracy,
        'classification_report': classification_rep,
        'confusion_matrix': cm,
        'metrics_df': metrics_df
    }

if __name__ == "__main__":
    evaluate_model()
