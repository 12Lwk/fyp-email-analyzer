import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import classification_report, precision_score, recall_score, f1_score
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import VotingClassifier
from sklearn.calibration import CalibratedClassifierCV
import xgboost as xgb
from scipy.sparse import hstack, csr_matrix, vstack
import joblib
from tqdm import tqdm
import gc
import re
import warnings
import logging
from datetime import datetime
import os
from nltk.corpus import wordnet
import random
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import TruncatedSVD

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_categorization.log'),
        logging.StreamHandler()
    ]
)

warnings.filterwarnings('ignore')

class EmailCategorizationSystem:
    def __init__(self, config):
        self.config = config
        self.models = {}
        self.vectorizer = None
        self.scaler = None
        self.label_encoder = None
        self.monitoring = self.setup_monitoring()
        
    def clean_text(self, text):
        """Clean and preprocess text."""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        text = ' '.join(text.split())
        return text

    def extract_email_features(self, subject, message):
        """Extract enhanced email-specific features."""
        # Basic length features
        subject_words = subject.split()
        message_words = message.split()
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

    def extract_advanced_features(self, texts):
        """Extract advanced features using BERT embeddings."""
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(texts)
        
        # Reduce dimensionality
        svd = TruncatedSVD(n_components=50)
        reduced_embeddings = svd.fit_transform(embeddings)
        
        return reduced_embeddings

    def augment_data(self, X, y):
        """Augment the dataset using various techniques."""
        # SMOTE for oversampling
        over = SMOTE(sampling_strategy='minority')
        under = RandomUnderSampler(sampling_strategy='majority')
        steps = [('o', over), ('u', under)]
        pipeline = Pipeline(steps=steps)
        
        X_resampled, y_resampled = pipeline.fit_resample(X, y)
        return X_resampled, y_resampled

    def train_models(self, X, y):
        """Train and evaluate multiple models."""
        logging.info("Training models...")
        
        # Prepare models
        self.models = {
            'svm': LinearSVC(
                class_weight='balanced',
                dual=False,
                max_iter=2000,
                random_state=42,
                C=1.0
            ),
            'lr': LogisticRegression(
                class_weight='balanced',
                max_iter=2000,
                random_state=42,
                n_jobs=-1,
                C=1.0,
                solver='saga',
                multi_class='multinomial'
            ),
            'nb': MultinomialNB(
                alpha=0.5,
                fit_prior=True
            ),
            'xgb': xgb.XGBClassifier(
                tree_method='hist',
                max_depth=7,
                learning_rate=0.05,
                n_estimators=200,
                random_state=42,
                n_jobs=-1,
                enable_categorical=False,
                use_label_encoder=False,
                objective='multi:softmax',
                num_class=len(np.unique(y)),
                verbosity=2,
                max_bin=256,
                grow_policy='lossguide',
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=3,
                gamma=0.1,
                reg_alpha=0.1,
                reg_lambda=1
            )
        }
        
        # Train each model
        for name, model in self.models.items():
            logging.info(f"Training {name}...")
            model.fit(X, y)
            
        # Create ensemble
        calibrated_models = {
            name: CalibratedClassifierCV(base_estimator=model, cv=3)
            for name, model in self.models.items()
        }
        
        self.ensemble = VotingClassifier(
            estimators=[(name, model) for name, model in calibrated_models.items()],
            voting='soft',
            weights=[2, 1, 1, 2]  # Higher weights for XGBoost and SVM
        )
        
        self.ensemble.fit(X, y)
        logging.info("Model training completed")

    def evaluate_models(self, X_test, y_test):
        """Evaluate model performance."""
        logging.info("Evaluating models...")
        
        results = {}
        for name, model in self.models.items():
            y_pred = model.predict(X_test)
            results[name] = {
                'accuracy': (y_pred == y_test).mean(),
                'precision': precision_score(y_test, y_pred, average='macro'),
                'recall': recall_score(y_test, y_pred, average='macro'),
                'f1': f1_score(y_test, y_pred, average='macro')
            }
        
        # Evaluate ensemble
        y_pred_ensemble = self.ensemble.predict(X_test)
        results['ensemble'] = {
            'accuracy': (y_pred_ensemble == y_test).mean(),
            'precision': precision_score(y_test, y_pred_ensemble, average='macro'),
            'recall': recall_score(y_test, y_pred_ensemble, average='macro'),
            'f1': f1_score(y_test, y_pred_ensemble, average='macro')
        }
        
        return results

    def setup_monitoring(self):
        """Set up monitoring system."""
        return {
            'performance_dashboard': {
                'metrics': ['accuracy', 'precision', 'recall', 'f1'],
                'update_frequency': 'daily'
            },
            'alert_system': {
                'thresholds': {
                    'accuracy': 0.6,
                    'precision': 0.65,
                    'recall': 0.55,
                    'f1': 0.6
                },
                'notification_channels': ['email', 'log']
            },
            'retraining_schedule': {
                'frequency': 'weekly',
                'trigger_conditions': {
                    'performance_drop': 0.05,
                    'data_drift': 0.1,
                    'new_data_threshold': 1000
                }
            }
        }

    def save_model(self, path):
        """Save the model and related objects."""
        model_data = {
            'models': self.models,
            'ensemble': self.ensemble,
            'vectorizer': self.vectorizer,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'monitoring': self.monitoring
        }
        
        joblib.dump(model_data, path)
        logging.info(f"Model saved to {path}")

    def load_model(self, path):
        """Load a saved model."""
        model_data = joblib.load(path)
        self.models = model_data['models']
        self.ensemble = model_data['ensemble']
        self.vectorizer = model_data['vectorizer']
        self.scaler = model_data['scaler']
        self.label_encoder = model_data['label_encoder']
        self.monitoring = model_data['monitoring']
        logging.info(f"Model loaded from {path}")

def main():
    # Configuration
    config = {
        'data_path': 'FYP PART 2/Category Modeling/final_email_category_balanced.csv',
        'model_save_path': 'FYP PART 2/Category Modeling/Latest Category Models/enhanced_email_categorization_model.joblib',
        'batch_size': 500,
        'test_size': 0.2,
        'random_state': 42
    }
    
    # Initialize system
    system = EmailCategorizationSystem(config)
    
    # Load and preprocess data
    logging.info("Loading dataset...")
    email_data = pd.read_csv(config['data_path'])
    
    # Clean data
    email_data = email_data[
        (email_data['Cleaned_Subject'].str.len() >= 3) & 
        (email_data['Cleaned_Message'].str.len() >= 10)
    ].drop_duplicates(subset=['Cleaned_Subject', 'Cleaned_Message']).reset_index(drop=True)
    
    # Prepare text data
    email_data['cleaned_subject'] = email_data['Cleaned_Subject'].apply(system.clean_text)
    email_data['cleaned_message'] = email_data['Cleaned_Message'].apply(system.clean_text)
    email_data['combined_text'] = email_data['cleaned_subject'] + ' SUBJECT_END ' + email_data['cleaned_message']
    
    # Extract features
    logging.info("Extracting features...")
    basic_features = np.vstack([
        system.extract_email_features(row['Cleaned_Subject'], row['Cleaned_Message'])
        for _, row in email_data.iterrows()
    ])
    
    # Extract advanced features
    advanced_features = system.extract_advanced_features(email_data['combined_text'].values)
    
    # Scale features
    scaler = MinMaxScaler()
    basic_features_scaled = scaler.fit_transform(basic_features)
    
    # Combine features
    X = np.hstack([basic_features_scaled, advanced_features])
    y = email_data['Qwen2.5_Category']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config['test_size'], random_state=config['random_state']
    )
    
    # Augment data
    X_train_augmented, y_train_augmented = system.augment_data(X_train, y_train)
    
    # Train models
    system.train_models(X_train_augmented, y_train_augmented)
    
    # Evaluate models
    results = system.evaluate_models(X_test, y_test)
    
    # Print results
    logging.info("\nModel Performance Summary:")
    for model_name, metrics in results.items():
        logging.info(f"\n{model_name}:")
        for metric, value in metrics.items():
            logging.info(f"{metric}: {value:.4f}")
    
    # Save model
    system.save_model(config['model_save_path'])
    logging.info("Training completed successfully")

if __name__ == "__main__":
    main() 