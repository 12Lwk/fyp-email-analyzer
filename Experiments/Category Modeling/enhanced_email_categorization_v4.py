import pandas as pd
import numpy as np
import re
import string
import nltk
import joblib
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from scipy.sparse import hstack, csr_matrix, vstack
from sklearn.metrics import classification_report, accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import VotingClassifier
from sklearn.calibration import CalibratedClassifierCV
import xgboost as xgb
from nltk.corpus import stopwords
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class EnhancedEmailCategorizationSystem:
    """
    Enhanced email categorization system using multiple models and extensive feature extraction.
    Version 4 with improvements focused on category-specific feature extraction and model tuning.
    """
    
    def __init__(self, config):
        self.config = config
        self.vectorizer = None
        self.scaler = None
        self.label_encoder = None
        self.models = {}
        self.ensemble = None
        
        # Download NLTK resources if not already downloaded
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
            
        # Load stopwords
        self.stop_words = set(stopwords.words('english'))
        
        # Category-specific keyword dictionaries with weighted terms
        self._init_category_dictionaries()
    
    def _init_category_dictionaries(self):
        """Initialize category-specific keyword dictionaries with weights"""
        # For better categorization using domain knowledge
        self.category_terms = {
            'finance': {
                'invoice': 1.5, 'payment': 1.5, 'budget': 1.3, 'transaction': 1.4,
                'financial': 1.2, 'expense': 1.3, 'receipt': 1.2, 'cost': 1.1,
                'bank': 1.4, 'credit': 1.3, 'debit': 1.3, 'fund': 1.2,
                'purchase': 1.2, 'vendor': 1.1, 'bill': 1.3, 'tax': 1.3,
                'accounting': 1.4, 'fiscal': 1.3, 'payroll': 1.4, 'reimbursement': 1.3,
                'audit': 1.4, 'balance': 1.2, 'revenue': 1.3, 'refund': 1.2
            },
            'meeting': {
                'meeting': 1.5, 'calendar': 1.4, 'schedule': 1.4, 'invite': 1.3,
                'agenda': 1.5, 'conference': 1.4, 'call': 1.1, 'appointment': 1.3,
                'event': 1.2, 'available': 1.1, 'reschedule': 1.4, 'attendee': 1.3,
                'zoom': 1.4, 'teams': 1.3, 'webex': 1.3, 'google meet': 1.3,
                'room': 1.2, 'booking': 1.3, 'slot': 1.2, 'availability': 1.3,
                'session': 1.2, 'calendar invite': 1.5, 'presentation': 1.1, 'discussion': 1.1
            },
            'project': {
                'project': 1.5, 'milestone': 1.5, 'deadline': 1.4, 'timeline': 1.4,
                'deliverable': 1.5, 'status': 1.3, 'plan': 1.3, 'roadmap': 1.4,
                'sprint': 1.4, 'task': 1.3, 'jira': 1.4, 'trello': 1.4,
                'progress': 1.3, 'tracking': 1.3, 'phase': 1.3, 'implementation': 1.2,
                'development': 1.2, 'testing': 1.2, 'kickoff': 1.4, 'launch': 1.3,
                'initiative': 1.3, 'objective': 1.2, 'goal': 1.2, 'stakeholder': 1.3,
                'gantt': 1.5, 'workflow': 1.3, 'backlog': 1.4, 'scrum': 1.4,
                'agile': 1.3, 'kanban': 1.3, 'priority': 1.2, 'requirement': 1.2
            },
            'hr': {
                'policy': 1.5, 'hr': 1.6, 'human resources': 1.6, 'employee': 1.3,
                'benefits': 1.4, 'handbook': 1.5, 'personnel': 1.3, 'sick leave': 1.4,
                'vacation': 1.3, 'vacation day': 1.4, 'pto': 1.4, 'time off': 1.3,
                'holiday': 1.2, 'review': 1.2, 'performance': 1.2, 'appraisal': 1.3,
                'payroll': 1.3, 'salary': 1.3, 'compensation': 1.3, 'onboarding': 1.4,
                'offboarding': 1.4, 'recruiting': 1.3, 'interview': 1.2, 'termination': 1.4,
                'resignation': 1.4, 'promotion': 1.3, 'training': 1.2, 'development': 1.1
            },
            'legal': {
                'legal': 1.5, 'contract': 1.5, 'agreement': 1.4, 'nda': 1.5,
                'terms': 1.3, 'conditions': 1.3, 'clause': 1.4, 'compliance': 1.4,
                'sign': 1.2, 'signature': 1.3, 'party': 1.2, 'counsel': 1.4,
                'attorney': 1.4, 'law': 1.3, 'regulation': 1.3, 'policy': 1.2,
                'amendment': 1.4, 'liability': 1.4, 'confidential': 1.3, 'proprietary': 1.3,
                'intellectual property': 1.5, 'trademark': 1.4, 'patent': 1.4, 'copyright': 1.4,
                'dispute': 1.3, 'settlement': 1.4, 'disclosure': 1.3, 'jurisdiction': 1.4
            },
            'it': {
                'alert': 1.5, 'outage': 1.5, 'server': 1.4, 'downtime': 1.5,
                'maintenance': 1.4, 'update': 1.3, 'upgrade': 1.3, 'system': 1.3,
                'incident': 1.4, 'backup': 1.4, 'security': 1.4, 'breach': 1.5,
                'password': 1.4, 'access': 1.3, 'login': 1.3, 'account': 1.2,
                'vpn': 1.4, 'network': 1.4, 'infrastructure': 1.3, 'database': 1.3,
                'software': 1.3, 'hardware': 1.3, 'application': 1.2, 'email': 1.1,
                'ticket': 1.4, 'bug': 1.4, 'error': 1.3, 'patch': 1.4,
                'authentication': 1.4, 'authorization': 1.4, 'phishing': 1.5, 'malware': 1.5
            },
            'spam': {
                'offer': 1.4, 'free': 1.5, 'discount': 1.4, 'prize': 1.5,
                'winner': 1.5, 'lottery': 1.6, 'urgent': 1.4, 'attention': 1.3,
                'congratulation': 1.5, 'million': 1.4, 'dollar': 1.3, 'limited time': 1.4,
                'claim': 1.4, 'click': 1.3, 'link': 1.2, 'password': 1.3,
                'account': 1.2, 'verify': 1.3, 'verification': 1.3, 'bank': 1.3,
                'credit card': 1.4, 'credit score': 1.4, 'investment': 1.3, 'pharmacy': 1.5,
                'medication': 1.5, 'weight loss': 1.5, 'diet': 1.4, 'miracle': 1.5,
                'dating': 1.4, 'singles': 1.4, 'cure': 1.5, 'viagra': 1.6
            },
            'personal': {
                'friend': 1.4, 'family': 1.4, 'personal': 1.4, 'private': 1.3,
                'weekend': 1.3, 'dinner': 1.3, 'lunch': 1.3, 'movie': 1.3,
                'travel': 1.3, 'vacation': 1.3, 'photo': 1.2, 'picture': 1.2,
                'birthday': 1.4, 'gift': 1.3, 'party': 1.3, 'celebration': 1.3,
                'holiday': 1.2, 'congrats': 1.3, 'congratulations': 1.3, 'best wishes': 1.3,
                'wedding': 1.4, 'baby': 1.3, 'graduation': 1.3, 'anniversary': 1.3,
                'trip': 1.2, 'visit': 1.2, 'hello': 1.2, 'hey': 1.3,
                'coffee': 1.2, 'catch up': 1.3, 'miss you': 1.4, 'love': 1.3
            },
            'general_business': {
                'business': 1.3, 'company': 1.2, 'team': 1.2, 'organization': 1.2,
                'department': 1.2, 'office': 1.1, 'corporate': 1.2, 'strategy': 1.2,
                'process': 1.1, 'procedure': 1.1, 'report': 1.1, 'update': 1.1,
                'information': 1.0, 'data': 1.0, 'analysis': 1.1, 'review': 1.1,
                'customer': 1.2, 'client': 1.2, 'partner': 1.2, 'vendor': 1.2,
                'supplier': 1.2, 'stakeholder': 1.2, 'management': 1.1, 'director': 1.1,
                'executive': 1.1, 'ceo': 1.2, 'cfo': 1.2, 'cto': 1.2,
                'operations': 1.1, 'service': 1.1, 'product': 1.1, 'market': 1.1
            }
        }

    def clean_text(self, text):
        """
        Clean and normalize text for better feature extraction
        """
        if not isinstance(text, str) or pd.isna(text):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', ' url ', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', ' email ', text)
        
        # Remove phone numbers
        text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', ' phone ', text)
        
        # Replace special characters with spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove digits (but keep alphanumeric identifiers)
        text = re.sub(r'\b\d+\b', ' num ', text)
        
        # Remove stopwords
        words = [word for word in text.split() if word not in self.stop_words]
        
        return ' '.join(words).strip()
    
    def extract_email_features(self, subject, message, cleaned_subject="", cleaned_message=""):
        """
        Extract comprehensive features from email subject and message
        Improved version with category-specific features and importance weighting
        """
        if not isinstance(subject, str):
            subject = ""
        if not isinstance(message, str):
            message = ""
            
        # If cleaned text not provided, clean it
        if not cleaned_subject:
            cleaned_subject = self.clean_text(subject)
        if not cleaned_message:
            cleaned_message = self.clean_text(message)
            
        features = []
        
        # PART 1: STRUCTURAL FEATURES (from raw text)
        # Length features
        features.append(len(subject))
        features.append(len(message))
        features.append(len(subject.split()) if subject else 0)
        features.append(len(message.split()) if message else 0)
        
        # Case features
        features.append(sum(1 for c in subject if c.isupper()) / max(len(subject), 1))
        features.append(sum(1 for c in message if c.isupper()) / max(len(message), 1))
        
        # Question features
        features.append(subject.count('?'))
        features.append(message.count('?'))
        
        # Special character ratios
        special_chars = set(string.punctuation)
        features.append(sum(1 for c in subject if c in special_chars) / max(len(subject), 1))
        features.append(sum(1 for c in message if c in special_chars) / max(len(message), 1))
        
        # Digit features
        features.append(sum(1 for c in subject if c.isdigit()) / max(len(subject), 1))
        features.append(sum(1 for c in message if c.isdigit()) / max(len(message), 1))
        
        # URL and email presence
        features.append(1 if re.search(r'https?://\S+|www\.\S+', subject + message) else 0)
        features.append(1 if re.search(r'\S+@\S+', subject + message) else 0)
        
        # PART 2: EMAIL STRUCTURE FEATURES
        # CC/BCC feature
        features.append(1 if re.search(r'\bcc:|bcc:', message, re.IGNORECASE) else 0)
        
        # Forwarded email feature
        features.append(1 if re.search(r'forwarded message|^fw:', message + subject, re.IGNORECASE) else 0)
        
        # Reply feature
        features.append(1 if re.search(r'^re:', subject, re.IGNORECASE) else 0)
        
        # Attachment feature
        features.append(1 if re.search(r'attach|attached|attachment|enclosed|herewith|pdf|doc|xls|ppt|file',
                                     message, re.IGNORECASE) else 0)
        
        # Signature detection
        features.append(1 if re.search(r'regards|sincerely|thank you|thanks|cheers|best|warm regards', 
                                     message, re.IGNORECASE) else 0)
        
        # Thread length approximation
        features.append(message.count('wrote:') + message.count('From:') + message.count('To:') + 
                      message.count('Sent:') + message.count('Date:'))
        
        # PART 3: SEMANTIC FEATURES FROM CLEANED TEXT
        # Calculate category-specific keyword scores (weighted approach)
        category_scores = self._calculate_category_scores(cleaned_subject, cleaned_message)
        features.extend(list(category_scores.values()))
        
        # PART 4: CONTEXTUAL FEATURES
        # Time urgency indicators
        urgency_terms = ['urgent', 'asap', 'immediately', 'deadline', 'today', 'tomorrow', 'morning', 
                        'afternoon', 'evening', 'urgent', 'priority', 'important']
        urgency_score = sum(1 for term in urgency_terms 
                          if re.search(r'\b' + re.escape(term) + r'\b', subject + message, re.IGNORECASE))
        features.append(urgency_score / len(urgency_terms))
        
        # Action request indicators
        action_terms = ['please', 'kindly', 'request', 'action', 'review', 'confirm', 'approve', 'respond',
                       'reply', 'send', 'forward', 'update', 'provide', 'complete', 'submit', 'perform']
        action_score = sum(1 for term in action_terms 
                         if re.search(r'\b' + re.escape(term) + r'\b', subject + message, re.IGNORECASE))
        features.append(action_score / len(action_terms))
        
        # Sentiment approximation (very basic)
        positive_terms = ['thank', 'thanks', 'good', 'great', 'excellent', 'appreciate', 'happy', 
                         'pleased', 'wonderful', 'congratulations', 'well done', 'success']
        negative_terms = ['issue', 'problem', 'error', 'mistake', 'fail', 'urgent', 'complaint', 
                         'concern', 'wrong', 'bad', 'sorry', 'unfortunately', 'regret']
        
        positive_score = sum(1 for term in positive_terms 
                           if re.search(r'\b' + re.escape(term) + r'\b', cleaned_subject + cleaned_message, re.IGNORECASE))
        negative_score = sum(1 for term in negative_terms 
                           if re.search(r'\b' + re.escape(term) + r'\b', cleaned_subject + cleaned_message, re.IGNORECASE))
        
        features.append(positive_score / len(positive_terms))
        features.append(negative_score / len(negative_terms))
        features.append((positive_score - negative_score) / (len(positive_terms) + len(negative_terms)))
        
        return np.array(features)
    
    def _calculate_category_scores(self, cleaned_subject, cleaned_message):
        """
        Calculate weighted scores for each category based on keyword presence
        """
        # Combine subject and message with subject having higher weight
        combined_text = cleaned_subject + " " + cleaned_subject + " " + cleaned_message
        combined_text = combined_text.lower()
        
        # Calculate score for each category
        category_scores = {}
        
        for category, terms in self.category_terms.items():
            score = 0
            total_weight = 0
            
            for term, weight in terms.items():
                # Count occurrences of the term
                # Use word boundary to ensure whole word matching
                count = len(re.findall(r'\b' + re.escape(term) + r'\b', combined_text))
                if count > 0:
                    score += count * weight
                    total_weight += weight
            
            # Normalize score by total possible weight
            if total_weight > 0:
                category_scores[category] = score / (total_weight * 3)  # Normalize to 0-1 range
            else:
                category_scores[category] = 0
                
        return category_scores

    def augment_data(self, X, y):
        """
        Augment training data to address class imbalance and improve model robustness
        V4: Enhanced with more targeted augmentation techniques for minority classes
        """
        logging.info("Augmenting training data...")
        # Count samples per class
        class_counts = np.bincount(y)
        max_count = np.max(class_counts)
        min_count = np.min(class_counts[class_counts > 0])
        median_count = np.median(class_counts)
        
        # Identify minority classes (less than 50% of median)
        minority_classes = [i for i, count in enumerate(class_counts) 
                           if count < 0.5 * median_count and count > 0]
        
        # Identify classes that need improvement based on the evaluation results
        # These are classes with low F1-scores from the v3 evaluation
        priority_classes = {
            # Format: class_index: (augmentation_factor, noise_factor)
            # Higher noise factor = more variation in augmented samples
            # The specific indices should be set based on label encoding
            # Using placeholder values - these should be adjusted based on actual label encoding
            2: (2.5, 0.1),  # IT Alerts (improved recall, need precision)
            3: (3.0, 0.05),  # Internal Policies (low precision and F1)
            7: (2.5, 0.1),  # Project Management (need precision)
        }
        
        # First convert to dense if needed for consistency
        is_sparse = isinstance(X, csr_matrix)
        
        # Prepare storage for new samples
        augmented_samples = []
        augmented_labels = []
        
        # Targeted augmentation for problematic classes
        for class_idx, (aug_factor, noise_factor) in priority_classes.items():
            if class_idx in range(len(class_counts)):
                # Get samples from this class
                class_indices = np.where(y == class_idx)[0]
                
                if len(class_indices) == 0:
                    continue
                
                # Calculate how many samples to add
                n_samples_to_add = int(len(class_indices) * aug_factor)
                
                if n_samples_to_add > 0:
                    # Get features of just this class
                    class_samples = X[class_indices]
                    
                    for _ in range(n_samples_to_add):
                        # Randomly select a sample from this class
                        idx = np.random.choice(len(class_indices))
                        
                        if is_sparse:
                            # For sparse matrices
                            sample = class_samples[idx].toarray().flatten()
                            # Add small noise to create a new, slightly different sample
                            non_zero_indices = np.nonzero(sample)[0]
                            for nz_idx in non_zero_indices:
                                if np.random.random() < 0.7:  # Only modify some features
                                    noise = np.random.normal(0, noise_factor)
                                    sample[nz_idx] = max(0, sample[nz_idx] + noise)
                        else:
                            # For numpy arrays
                            sample = class_samples[idx].copy()
                            # Add small noise to create a new, slightly different sample
                            noise = np.random.normal(0, noise_factor, size=sample.shape)
                            # Only add noise to some features
                            mask = np.random.random(size=sample.shape) < 0.7
                            noise = noise * mask
                            sample = np.maximum(0, sample + noise)  # Keep values non-negative
                        
                        augmented_samples.append(sample)
                        augmented_labels.append(class_idx)
        
        # General augmentation for severely underrepresented classes
        for class_idx in minority_classes:
            if class_idx in priority_classes:
                continue  # Already handled above
                
            # Get samples from this class
            class_indices = np.where(y == class_idx)[0]
            
            if len(class_indices) == 0:
                continue
                
            # Calculate augmentation to bring to at least 80% of median count
            target_count = int(0.8 * median_count)
            n_samples_to_add = max(0, target_count - len(class_indices))
            
            if n_samples_to_add > 0:
                # Get features of just this class
                class_samples = X[class_indices]
                
                for _ in range(n_samples_to_add):
                    # Randomly select a sample from this class
                    idx = np.random.choice(len(class_indices))
                    
                    if is_sparse:
                        # For sparse matrices
                        sample = class_samples[idx].toarray().flatten()
                        # Add small noise to create a new, slightly different sample
                        non_zero_indices = np.nonzero(sample)[0]
                        for nz_idx in non_zero_indices:
                            if np.random.random() < 0.5:  # Lower modification rate
                                noise = np.random.normal(0, 0.05)  # Smaller noise
                                sample[nz_idx] = max(0, sample[nz_idx] + noise)
                    else:
                        # For numpy arrays
                        sample = class_samples[idx].copy()
                        # Add small noise to create a new, slightly different sample
                        noise = np.random.normal(0, 0.05, size=sample.shape)
                        # Only add noise to some features
                        mask = np.random.random(size=sample.shape) < 0.5
                        noise = noise * mask
                        sample = np.maximum(0, sample + noise)  # Keep values non-negative
                    
                    augmented_samples.append(sample)
                    augmented_labels.append(class_idx)
        
        # Now combine with original data
        if len(augmented_samples) > 0:
            # Convert augmented samples to appropriate format
            if is_sparse:
                # Get shape from original data
                n_features = X.shape[1]
                # Convert to sparse and stack
                augmented_matrix = csr_matrix(np.vstack(augmented_samples))
                X_aug = vstack([X, augmented_matrix])
            else:
                augmented_array = np.vstack(augmented_samples)
                X_aug = np.vstack([X, augmented_array])
                
            y_aug = np.append(y, augmented_labels)
        else:
            X_aug = X
            y_aug = y
        
        logging.info(f"Data augmentation complete. Original size: {len(y)}, Augmented size: {len(y_aug)}")
        return X_aug, y_aug
    
    def train_models(self, X_train, y_train):
        """
        Train multiple models and create an ensemble for email categorization
        V4: Improved model tuning and ensemble weighting
        """
        logging.info("Training models...")
        
        # Get class distribution for class weights
        class_counts = np.bincount(y_train)
        # Create class weights (inverse of frequency)
        class_weight = {i: np.sum(class_counts) / (len(class_counts) * max(1, c)) 
                      for i, c in enumerate(class_counts)}
        
        # SVM with class weights and calibration
        logging.info("Training svm...")
        svm_base = LinearSVC(
            class_weight=class_weight,
            C=1.2,  # Increased regularization strength
            dual='auto',
            max_iter=2000
        )
        self.models['svm'] = CalibratedClassifierCV(
            svm_base,
            method='sigmoid',
            cv=3
        )
        self.models['svm'].fit(X_train, y_train)
        
        # Logistic Regression with improved parameters
        logging.info("Training lr...")
        self.models['lr'] = LogisticRegression(
            solver='liblinear',
            C=1.5,  # Adjusted regularization 
            class_weight=class_weight,
            max_iter=1000,
            n_jobs=-1,
            multi_class='ovr',  # One-vs-rest often works well for imbalanced data
            random_state=42
        )
        self.models['lr'].fit(X_train, y_train)
        
        # Naive Bayes
        logging.info("Training nb...")
        self.models['nb'] = MultinomialNB(
            alpha=0.3  # Higher alpha for more smoothing (helps with rare features)
        )
        self.models['nb'].fit(X_train, y_train)
        
        # XGBoost with better hyperparameters
        logging.info("Training xgb...")
        # Scale weights for XGBoost
        scale = 1.0 / np.sum(list(class_weight.values()))
        xgb_weights = {k: v * scale * len(class_weight) for k, v in class_weight.items()}
        
        self.models['xgb'] = xgb.XGBClassifier(
            n_estimators=200,  # More trees
            max_depth=7,       # Deeper trees for more complex patterns
            learning_rate=0.1, # Lower learning rate for better generalization
            subsample=0.8,     # Subsampling for robustness
            colsample_bytree=0.8, # Feature subsampling
            objective='multi:softprob',
            use_label_encoder=False,
            eval_metric='mlogloss',
            tree_method='hist',  # Faster histogram-based algorithm
            random_state=42
        )
        
        # Fit with sample weights based on class
        sample_weights = np.array([xgb_weights[y] for y in y_train])
        self.models['xgb'].fit(
            X_train, 
            y_train,
            sample_weight=sample_weights,
            verbose=False
        )
        
        # Create an ensemble with improved weights
        # Based on v3 performance, we strengthen XGBoost & LR, reduce NB weight
        self.ensemble = VotingClassifier(
            estimators=[
                ('xgb', self.models['xgb']),
                ('svm', self.models['svm']),
                ('nb', self.models['nb']),
                ('lr', self.models['lr'])
            ],
            voting='soft',
            weights=[3, 2, 1, 3]  # Increased weight on XGBoost and LR
        )
        
        # Fit the ensemble
        self.ensemble.fit(X_train, y_train)
        logging.info("Model training completed")

    def predict(self, subject, message):
        """
        Predict the category of an email
        """
        if not self.ensemble or not self.vectorizer or not self.scaler or not self.label_encoder:
            raise ValueError("Model not trained. Call train() first.")
        
        # Clean text
        cleaned_subject = self.clean_text(subject)
        cleaned_message = self.clean_text(message)
        combined_text = cleaned_subject + ' SUBJECT_END ' + cleaned_message
        
        # Extract features
        basic_features = self.extract_email_features(subject, message, cleaned_subject, cleaned_message)
        basic_features = basic_features.reshape(1, -1)
        basic_features_scaled = self.scaler.transform(basic_features)
        basic_features_sparse = csr_matrix(basic_features_scaled)
        
        # Extract text features
        text_features = self.vectorizer.transform([combined_text])
        
        # Combine features
        X = hstack([text_features, basic_features_sparse]).tocsr()
        
        # Make prediction
        y_pred = self.ensemble.predict(X)
        category = self.label_encoder.inverse_transform(y_pred)[0]
        
        # Get probabilities for all classes
        probas = self.ensemble.predict_proba(X)[0]
        confidence = np.max(probas)
        
        # Get top 3 predictions with probabilities
        top_indices = np.argsort(probas)[::-1][:3]
        top_categories = self.label_encoder.inverse_transform(top_indices)
        top_probas = probas[top_indices]
        
        alternatives = list(zip(top_categories[1:], top_probas[1:]))
        
        return {
            'category': category,
            'confidence': float(confidence),
            'alternatives': alternatives
        }
    
    def save_model(self, model_path):
        """
        Save the trained model to disk
        """
        model_data = {
            'vectorizer': self.vectorizer,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'models': self.models,
            'ensemble': self.ensemble
        }
        
        joblib.dump(model_data, model_path)
        logging.info(f"Model saved to {model_path}")
    
    def load_model(self, model_path):
        """
        Load a trained model from disk
        """
        model_data = joblib.load(model_path)
        
        self.vectorizer = model_data['vectorizer']
        self.scaler = model_data['scaler']
        self.label_encoder = model_data['label_encoder']
        self.models = model_data['models']
        self.ensemble = model_data['ensemble']
        
        logging.info(f"Model loaded from {model_path}")
        return self

def main():
    # Configuration
    config = {
        'data_path': 'final_email_category_balanced.csv',
        'model_save_path': 'enhanced_email_categorization_model_v4.joblib',
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
        max_features=2500,  # Increased from 2000
        ngram_range=(1, 3),
        min_df=10,          # Reduced from 15 to capture more rare but important terms
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
