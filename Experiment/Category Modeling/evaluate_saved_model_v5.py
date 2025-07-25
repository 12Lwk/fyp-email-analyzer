import joblib
import pandas as pd
import numpy as np
from scipy.sparse import hstack, csr_matrix
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support, precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from tqdm import tqdm
from enhanced_email_categorization_v5 import EnhancedEmailCategorizationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def plot_confusion_matrix(cm, classes, title, normalize=True, cmap=plt.cm.Blues, figsize=(15, 12)):
    """
    Plot confusion matrix with better visualization
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    plt.figure(figsize=figsize)
    sns.heatmap(
        cm, 
        annot=True, 
        fmt='.2f' if normalize else 'd',
        cmap=cmap,
        xticklabels=classes,
        yticklabels=classes
    )
    plt.title(title)
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()

def plot_category_distribution(data, category_col, title):
    """Plot distribution of categories in the dataset"""
    plt.figure(figsize=(15, 8))
    category_counts = data[category_col].value_counts()
    category_counts.plot(kind='bar')
    plt.title(title)
    plt.xlabel('Categories')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    return category_counts

def evaluate_model_on_dataset(model_data, test_data, system, dataset_name):
    """
    Evaluate model on a specific dataset
    """
    logging.info(f"\nEvaluating on {dataset_name}...")
    
    # Define possible column names
    subject_cols = ['Subject', 'subject', 'Email_Subject', 'email_subject', 'Cleaned_Subject', 'cleaned_subject']
    message_cols = ['Message', 'message', 'Email_Body', 'email_body', 'Body', 'body', 'Cleaned_Message', 'cleaned_message']
    category_cols = ['True_Category', 'true_category', 'Category', 'category', 'Label', 'label']
    
    # Find actual column names in the dataset
    subject_col = next((col for col in subject_cols if col in test_data.columns), None)
    message_col = next((col for col in message_cols if col in test_data.columns), None)
    category_col = next((col for col in category_cols if col in test_data.columns), None)
    
    if not all([subject_col, message_col, category_col]):
        missing_cols = []
        if not subject_col:
            missing_cols.append("subject")
        if not message_col:
            missing_cols.append("message")
        if not category_col:
            missing_cols.append("category")
        raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
    
    logging.info(f"Using columns: subject='{subject_col}', message='{message_col}', category='{category_col}'")
    
    # Clean data
    test_data = test_data[
        (test_data[subject_col].str.len() >= 3) & 
        (test_data[message_col].str.len() >= 10)
    ].drop_duplicates(subset=[subject_col, message_col]).reset_index(drop=True)
    
    # Map categories to standard format if needed
    category_mapping = model_data.get('category_mapping', {})
    if category_mapping:
        test_data[category_col] = test_data[category_col].map(category_mapping).fillna(test_data[category_col])
    
    # Filter unknown categories
    known_categories = set(model_data['vectorizer'].classes_)
    test_data = test_data[test_data[category_col].isin(known_categories)].reset_index(drop=True)
    
    # Plot category distribution
    plt.figure(figsize=(12, 6))
    test_data[category_col].value_counts().plot(kind='bar')
    plt.title(f'Category Distribution - {dataset_name}')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    # Extract features
    X_test = system.extract_features(
        test_data[subject_col],
        test_data[message_col],
        model_data['vectorizer']
    )
    y_test = test_data[category_col]
    
    # Make predictions
    y_pred = model_data['model'].predict(X_test)
    y_pred_proba = model_data['model'].predict_proba(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted')
    recall = recall_score(y_test, y_pred, average='weighted')
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    logging.info(f"\nResults for {dataset_name}:")
    logging.info(f"Accuracy: {accuracy:.4f}")
    logging.info(f"Precision: {precision:.4f}")
    logging.info(f"Recall: {recall:.4f}")
    logging.info(f"F1 Score: {f1:.4f}")
    
    # Print classification report
    print(f"\nDetailed Classification Report for {dataset_name}:")
    print(classification_report(y_test, y_pred))
    
    # Plot confusion matrix
    plt.figure(figsize=(12, 8))
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=model_data['vectorizer'].classes_,
                yticklabels=model_data['vectorizer'].classes_)
    plt.title(f'Confusion Matrix - {dataset_name}')
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'predictions': y_pred,
        'probabilities': y_pred_proba,
        'true_labels': y_test
    }

def evaluate_model(model_path='enhanced_email_categorization_model_v5.joblib',
                  test_datasets=None):
    """
    Comprehensive evaluation of the email categorization model v5
    """
    if test_datasets is None:
        test_datasets = {
            'Batch 1': 'rewritten_batch1_emails_polished_testing_data.csv',
            'Recent Data': 'emails_202504202357.csv'
        }
    
    # Load the model
    logging.info(f"Loading model from {model_path}...")
    model_data = joblib.load(model_path)
    
    # Initialize system
    system = EnhancedEmailCategorizationSystem({})
    
    results = {}
    
    # Evaluate on each dataset
    for dataset_name, data_path in test_datasets.items():
        try:
            # Load test data
            logging.info(f"Loading test data from {data_path}...")
            test_data = pd.read_csv(data_path)
            
            # Print available columns for debugging
            logging.info(f"Available columns in {dataset_name}: {list(test_data.columns)}")
            
            # Evaluate
            results[dataset_name] = evaluate_model_on_dataset(
                model_data, test_data, system, dataset_name
            )
            
        except Exception as e:
            logging.error(f"Error evaluating {dataset_name}: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            continue
    
    return results

if __name__ == "__main__":
    test_datasets = {
        'Batch 1': 'rewritten_batch1_emails_polished_testing_data.csv',
        'Recent Data': 'emails_202504202357.csv'
    }
    evaluate_model(test_datasets=test_datasets)