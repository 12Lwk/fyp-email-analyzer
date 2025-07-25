import pandas as pd
import numpy as np
import re
import logging
import joblib
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
import xgboost as xgb
from sklearn.ensemble import VotingClassifier
from sklearn.calibration import CalibratedClassifierCV
from imblearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class EnhancedEmailCategorizationSystem:
    def __init__(self, config):
        self.config = config
        self.models = {}
        self.vectorizer = None
        self.scaler = None
        self.label_encoder = None
        
        # Initialize keyword sets
        self.initialize_keywords()
    
    def initialize_keywords(self):
        """Initialize various keyword sets for feature extraction."""
        # Business communication keywords
        self.business_keywords = {
            'report', 'update', 'business', 'project', 'status',
            'review', 'process', 'procedure', 'policy', 'department',
            'team', 'organization', 'company', 'corporate', 'strategy'
        }
        
        self.formal_phrases = {
            'please find', 'kindly', 'regarding', 'with respect to',
            'as per', 'pursuant to', 'in reference to', 'concerning'
        }
        
        # Project management keywords
        self.pm_keywords = {
            'milestone', 'deadline', 'timeline', 'roadmap', 'sprint',
            'deliverable', 'stakeholder', 'resource', 'scope', 'budget',
            'planning', 'implementation', 'phase', 'progress', 'target'
        }
        
        self.strategy_keywords = {
            'strategic', 'objective', 'goal', 'initiative', 'vision',
            'mission', 'growth', 'development', 'plan', 'forecast',
            'analysis', 'market', 'competitive', 'opportunity'
        }
        
        # HR and policy keywords
        self.hr_keywords = {
            'policy', 'procedure', 'compliance', 'regulation', 'guideline',
            'employee', 'staff', 'personnel', 'benefit', 'leave',
            'holiday', 'payroll', 'training', 'development', 'hr'
        }
        
        self.internal_markers = {
            'all staff', 'all employees', 'company-wide',
            'internal use', 'confidential', 'do not forward'
        }
        
        # Policy update patterns
        self.policy_patterns = [
            r'policy\s+update',
            r'new\s+policy',
            r'revised\s+policy',
            r'effective\s+(?:from|date)',
            r'please\s+note\s+(?:the|this)\s+change'
        ]
    
    def clean_text(self, text):
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
    
    def extract_contextual_features(self, subject, message):
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
    
    def extract_email_features(self, subject, message, cleaned_subject=None, cleaned_message=None):
        """Extract enhanced email-specific features from both raw and cleaned text."""
        # Basic text preparation
        subject = str(subject)
        message = str(message)
        cleaned_subject = str(cleaned_subject) if cleaned_subject is not None else subject
        cleaned_message = str(cleaned_message) if cleaned_message is not None else message
        
        subject_words = cleaned_subject.split()
        message_words = cleaned_message.split()
        
        # Basic length features
        subject_len = len(subject_words)
        message_len = len(message_words)
        
        # Question and exclamation features (from raw text)
        subject_questions = subject.count('?')
        message_questions = message.count('?')
        subject_exclamations = subject.count('!')
        message_exclamations = message.count('!')
        
        # Case features (from raw text)
        subject_upper = sum(1 for c in subject if c.isupper())
        message_upper = sum(1 for c in message if c.isupper())
        subject_upper_ratio = subject_upper / (len(subject) + 1)
        message_upper_ratio = message_upper / (len(message) + 1)
        
        # Digit features (from raw text)
        subject_digits = sum(1 for c in subject if c.isdigit())
        message_digits = sum(1 for c in message if c.isdigit())
        subject_digit_ratio = subject_digits / (len(subject) + 1)
        message_digit_ratio = message_digits / (len(message) + 1)
        
        # URL and email features (from raw text)
        has_url = int(bool(re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message)))
        has_email = int(bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message)))
        
        # Special character ratios (from raw text)
        subject_special = sum(not c.isalnum() and not c.isspace() for c in subject) / (len(subject) + 1)
        message_special = sum(not c.isalnum() and not c.isspace() for c in message) / (len(message) + 1)
        
        # Email structure features (from raw text)
        has_cc = int(bool(re.search(r'cc:|cc :', message.lower())))
        has_bcc = int(bool(re.search(r'bcc:|bcc :', message.lower())))
        has_forward = int(bool(re.search(r'forwarded|fwd:|fw:', message.lower())))
        has_reply = int(bool(re.search(r're:|reply:|replied', message.lower())))
        has_attachment = int(bool(re.search(r'attachment|attached|enclosed', message.lower())))
        
        # Business communication features (from cleaned text)
        business_keyword_count = sum(1 for word in message_words if word in self.business_keywords)
        business_keyword_ratio = business_keyword_count / (len(message_words) + 1)
        formality_score = sum(1 for phrase in self.formal_phrases if phrase in cleaned_message.lower())
        has_document_ref = int(bool(re.search(r'ref|reference|document|doc|attachment|attached', cleaned_message.lower())))
        
        # Project management features (from cleaned text)
        pm_keyword_count = sum(1 for word in message_words if word in self.pm_keywords)
        strategy_score = sum(1 for word in message_words if word in self.strategy_keywords)
        has_timeline = int(bool(re.search(r'q[1-4]|quarter|fy\d{2,4}|20\d{2}|fiscal', cleaned_message.lower())))
        
        # HR and policy features (from cleaned text)
        hr_keyword_count = sum(1 for word in message_words if word in self.hr_keywords)
        has_policy_update = int(any(re.search(pattern, cleaned_message.lower()) for pattern in self.policy_patterns))
        is_internal = sum(1 for marker in self.internal_markers if marker in cleaned_message.lower())
        
        # Contextual features (from both raw and cleaned text)
        contextual_features = self.extract_contextual_features(cleaned_subject, cleaned_message)
        
        # Email thread features (from raw text)
        has_thread = int(bool(re.search(r'thread|conversation|discussion', message.lower())))
        has_urgent = int(bool(re.search(r'urgent|important|asap|immediate', message.lower())))
        has_meeting = int(bool(re.search(r'meeting|schedule|calendar|appointment', message.lower())))
        
        # Combine all features
        features = [
            # Basic features
            subject_len, message_len,
            subject_questions, message_questions,
            subject_exclamations, message_exclamations,
            subject_upper_ratio, message_upper_ratio,
            subject_digit_ratio, message_digit_ratio,
            
            # Email structure features
            has_url, has_email,
            has_cc, has_bcc,
            has_forward, has_reply,
            has_attachment,
            
            # Content features
            subject_special, message_special,
            subject_len / (message_len + 1),
            (subject_questions + message_questions) / (subject_len + message_len + 1),
            (subject_exclamations + message_exclamations) / (subject_len + message_len + 1),
            
            # Business features
            business_keyword_ratio,
            formality_score / (len(message_words) + 1),
            has_document_ref,
            pm_keyword_count / (len(message_words) + 1),
            strategy_score / (len(message_words) + 1),
            has_timeline,
            hr_keyword_count / (len(message_words) + 1),
            has_policy_update,
            is_internal / (len(message_words) + 1),
            
            # Contextual features
            *contextual_features,
            
            # Email thread features
            has_thread,
            has_urgent,
            has_meeting
        ]
        
        return np.array(features)
    
    def augment_data(self, X, y):
        """Augment the dataset using SMOTE and undersampling."""
        over = SMOTE(sampling_strategy='auto')
        under = RandomUnderSampler(sampling_strategy='auto')
        steps = [('o', over), ('u', under)]
        pipeline = Pipeline(steps=steps)
        
        X_resampled, y_resampled = pipeline.fit_resample(X, y)
        return X_resampled, y_resampled
    
    def train_models(self, X, y):
        """Train multiple models with optimized parameters."""
        logging.info("Training models...")
        
        # Initialize models with optimized parameters
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
        
        # Create calibrated models for ensemble
        calibrated_models = {
            name: CalibratedClassifierCV(estimator=model, cv=3)
            for name, model in self.models.items()
        }
        
        # Train ensemble with weighted voting
        self.ensemble = VotingClassifier(
            estimators=[(name, model) for name, model in calibrated_models.items()],
            voting='soft',
            weights=[2, 2, 1, 3]  # Higher weights for XGBoost and SVM
        )
        
        self.ensemble.fit(X, y)
        logging.info("Model training completed")
    
    def save_model(self, path):
        """Save the trained model and its components."""
        model_data = {
            'vectorizer': self.vectorizer,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'models': self.models,
            'ensemble': self.ensemble
        }
        joblib.dump(model_data, path)
        logging.info(f"Model saved to {path}")

def main():
    # Configuration
    config = {
        'data_path': 'final_email_category_balanced.csv',
        'model_save_path': 'enhanced_email_categorization_model_v3.joblib',
        'batch_size': 500,
        'test_size': 0.2,
        'random_state': 42
    }
    
    # Initialize system
    system = EnhancedEmailCategorizationSystem(config)
    
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
        system.extract_email_features(
            row['Subject'], 
            row['Message'],
            row['cleaned_subject'],
            row['cleaned_message']
        )
        for _, row in tqdm(email_data.iterrows(), total=len(email_data))
    ])
    
    # Prepare text features
    system.vectorizer = TfidfVectorizer(
        max_features=2000,
        ngram_range=(1, 3),
        min_df=15,
        max_df=0.85,
        stop_words='english',
        sublinear_tf=True,
        norm='l2',
        use_idf=True,
        smooth_idf=True
    )
    
    text_features = system.vectorizer.fit_transform(email_data['combined_text'])
    
    # Scale features
    system.scaler = MinMaxScaler()
    basic_features_scaled = system.scaler.fit_transform(basic_features)
    basic_features_sparse = csr_matrix(basic_features_scaled)
    
    # Combine features
    X = hstack([text_features, basic_features_sparse]).tocsr()
    
    # Encode target variable
    system.label_encoder = LabelEncoder()
    y = system.label_encoder.fit_transform(email_data['Qwen2.5_Category'])
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config['test_size'], random_state=config['random_state']
    )
    
    # Augment data
    X_train_augmented, y_train_augmented = system.augment_data(X_train, y_train)
    
    # Train models
    system.train_models(X_train_augmented, y_train_augmented)
    
    # Save model
    system.save_model(config['model_save_path'])
    logging.info("Training completed successfully")

if __name__ == "__main__":
    main() 