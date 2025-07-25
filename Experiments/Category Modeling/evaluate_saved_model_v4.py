import joblib
import pandas as pd
import numpy as np
from scipy.sparse import hstack, csr_matrix
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from tqdm import tqdm
import os
from enhanced_email_categorization_v4 import EnhancedEmailCategorizationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def plot_confusion_matrix(cm, classes, title, normalize=True, cmap=plt.cm.Blues):
    """
    Plot confusion matrix with better visualization
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    plt.figure(figsize=(12, 10))
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

def plot_category_metrics(metrics_df, title):
    """
    Plot precision, recall, and F1-score for each category
    """
    plt.figure(figsize=(15, 8))
    x = np.arange(len(metrics_df.index) - 3)  # Exclude 'accuracy', 'macro avg', 'weighted avg'
    width = 0.25
    
    plt.bar(x - width, metrics_df['precision'][:-3], width, label='Precision')
    plt.bar(x, metrics_df['recall'][:-3], width, label='Recall')
    plt.bar(x + width, metrics_df['f1-score'][:-3], width, label='F1-score')
    
    plt.xlabel('Categories')
    plt.ylabel('Score')
    plt.title(title)
    plt.xticks(x, metrics_df.index[:-3], rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()

def evaluate_model(model_path='enhanced_email_categorization_model_v4.joblib',
                  prev_model_path='enhanced_email_categorization_model_v3.joblib',
                  data_path='final_email_category_balanced.csv',
                  test_size=0.2,
                  random_state=42):
    """
    Comprehensive evaluation of the email categorization model
    """
    # Load the model
    logging.info(f"Loading model from {model_path}...")
    model_data = joblib.load(model_path)
    
    # Initialize system
    system = EnhancedEmailCategorizationSystem({})
    
    # Load components
    vectorizer = model_data['vectorizer']
    scaler = model_data['scaler']
    label_encoder = model_data['label_encoder']
    ensemble = model_data['ensemble']
    
    # Load test data
    logging.info(f"Loading test data from {data_path}...")
    email_data = pd.read_csv(data_path)
    
    # Clean data
    email_data = email_data[
        (email_data['Cleaned_Subject'].str.len() >= 3) & 
        (email_data['Cleaned_Message'].str.len() >= 10)
    ].drop_duplicates(subset=['Cleaned_Subject', 'Cleaned_Message']).reset_index(drop=True)
    
    # Use same random state for consistent testing
    np.random.seed(random_state)
    test_indices = np.random.choice(
        email_data.index,
        size=int(len(email_data) * test_size),
        replace=False
    )
    test_data = email_data.loc[test_indices]
    
    logging.info(f"Test set size: {len(test_data)} emails")
    
    # Prepare text data
    test_data['cleaned_subject'] = test_data['Cleaned_Subject'].apply(system.clean_text)
    test_data['cleaned_message'] = test_data['Cleaned_Message'].apply(system.clean_text)
    test_data['combined_text'] = test_data['cleaned_subject'] + ' SUBJECT_END ' + test_data['cleaned_message']
    
    # Extract features
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
    
    # Scale features
    basic_features_scaled = scaler.transform(basic_features)
    basic_features_sparse = csr_matrix(basic_features_scaled)
    
    # Combine features
    X_test = hstack([text_features, basic_features_sparse]).tocsr()
    
    # Transform target labels
    y_test = label_encoder.transform(test_data['Qwen2.5_Category'])
    
    # Make predictions
    logging.info("Making predictions...")
    y_pred = ensemble.predict(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    classification_rep = classification_report(
        y_test,
        y_pred,
        target_names=label_encoder.classes_,
        output_dict=True
    )
    
    # Create confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    
    # Print results
    logging.info(f"\nModel Performance (v4):")
    logging.info(f"Overall Accuracy: {accuracy:.4f}")
    
    # Create and display classification report
    metrics_df = pd.DataFrame(classification_rep).T
    print("\nClassification Report:")
    print(metrics_df.round(3).to_string())
    
    # Compare with v3 if available
    if os.path.exists(prev_model_path):
        logging.info("\nComparing with v3 model...")
        prev_model_data = joblib.load(prev_model_path)
        prev_ensemble = prev_model_data['ensemble']
        prev_vectorizer = prev_model_data['vectorizer']
        prev_scaler = prev_model_data['scaler']
        
        # Extract features using v3's pipeline
        prev_text_features = prev_vectorizer.transform(test_data['combined_text'])
        prev_basic_features = np.vstack([
            system.extract_email_features(
                row['Subject'],
                row['Message'],
                row['cleaned_subject'],
                row['cleaned_message']
            )
            for _, row in tqdm(test_data.iterrows(), total=len(test_data))
        ])
        
        prev_basic_features_scaled = prev_scaler.transform(prev_basic_features)
        prev_basic_features_sparse = csr_matrix(prev_basic_features_scaled)
        prev_X_test = hstack([prev_text_features, prev_basic_features_sparse]).tocsr()
        
        # Predict with v3
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
        print(f"V3 Accuracy: {prev_accuracy:.4f}")
        print(f"V4 Accuracy: {accuracy:.4f}")
        print(f"Improvement: {(accuracy - prev_accuracy) * 100:.2f}%")
        
        # Compare per-category metrics
        v3_metrics = pd.DataFrame(prev_report).T
        v4_metrics = pd.DataFrame(classification_rep).T
        
        comparison = pd.DataFrame({
            'V3_precision': v3_metrics['precision'],
            'V4_precision': v4_metrics['precision'],
            'V3_recall': v3_metrics['recall'],
            'V4_recall': v4_metrics['recall'],
            'V3_f1': v3_metrics['f1-score'],
            'V4_f1': v4_metrics['f1-score'],
        })
        
        comparison['prec_diff'] = comparison['V4_precision'] - comparison['V3_precision']
        comparison['recall_diff'] = comparison['V4_recall'] - comparison['V3_recall']
        comparison['f1_diff'] = comparison['V4_f1'] - comparison['V3_f1']
        
        print("\nPer-Category Improvement:")
        print(comparison.round(3).to_string())
    
    # Plot confusion matrix
    plot_confusion_matrix(
        cm,
        classes=label_encoder.classes_,
        title=f'Normalized Confusion Matrix (Accuracy: {accuracy:.4f})'
    )
    plt.savefig('confusion_matrix_v4.png')
    logging.info("Confusion matrix saved to confusion_matrix_v4.png")
    
    # Plot category metrics
    plot_category_metrics(
        metrics_df,
        'Category-wise Performance Metrics (V4)'
    )
    plt.savefig('category_metrics_v4.png')
    logging.info("Category metrics plot saved to category_metrics_v4.png")
    
    # Generate error analysis
    error_indices = np.where(y_test != y_pred)[0]
    error_analysis = pd.DataFrame({
        'True_Category': label_encoder.inverse_transform(y_test[error_indices]),
        'Predicted_Category': label_encoder.inverse_transform(y_pred[error_indices]),
        'Subject': test_data.iloc[error_indices]['Subject'].values,
        'Message': test_data.iloc[error_indices]['Message'].values
    })
    
    error_analysis.to_csv('error_analysis_v4.csv', index=False)
    logging.info("Error analysis saved to error_analysis_v4.csv")
    
    return {
        'accuracy': accuracy,
        'classification_report': classification_rep,
        'confusion_matrix': cm,
        'metrics_df': metrics_df,
        'error_analysis': error_analysis
    }

if __name__ == "__main__":
    evaluate_model()
