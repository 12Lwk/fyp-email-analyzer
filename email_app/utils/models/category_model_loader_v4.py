import re
import string
import numpy as np
import logging
from scipy.sparse import hstack
from sklearn.preprocessing import MinMaxScaler
from joblib import load
import os

class EmailCategoryModelV4:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmailCategoryModelV4, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.model = None
        self.vectorizer = None
        self.scaler = None
        
        # Load the model and its components
        self._load_model()
        
        # Category mapping with confidence thresholds
        self.category_mapping = {
            0: {"name": "Finance & Transactions", "threshold": 0.30},
            1: {"name": "General Business Communication", "threshold": 0.25},
            2: {"name": "IT Alerts & System Notifications", "threshold": 0.35},
            3: {"name": "Internal Policies & HR Updates", "threshold": 0.30},
            4: {"name": "Legal & Contractual", "threshold": 0.35},
            5: {"name": "Meetings & Scheduling", "threshold": 0.30},
            6: {"name": "Personal Communication & Purely Personal", "threshold": 0.20},
            7: {"name": "Project Management & Strategy", "threshold": 0.30},
            8: {"name": "Spam & Marketing", "threshold": 0.40}
        }
        
        # Category-specific keyword sets with weights
        self.category_terms = {
            'finance': {
                'invoice': 1.5, 'payment': 1.5, 'budget': 1.3, 'transaction': 1.4,
                'financial': 1.2, 'expense': 1.3, 'receipt': 1.2, 'cost': 1.1,
                'bank': 1.4, 'credit': 1.3, 'debit': 1.3, 'fund': 1.2,
                'purchase': 1.2, 'vendor': 1.1, 'bill': 1.3, 'tax': 1.3,
                'accounting': 1.4, 'fiscal': 1.3, 'payroll': 1.4, 'reimbursement': 1.3,
                'audit': 1.4, 'balance': 1.2, 'revenue': 1.3, 'refund': 1.2
            },
            'business': {
                'business': 1.3, 'company': 1.2, 'team': 1.2, 'organization': 1.2,
                'department': 1.2, 'office': 1.1, 'corporate': 1.2, 'strategy': 1.2,
                'process': 1.1, 'procedure': 1.1, 'report': 1.1, 'update': 1.1,
                'information': 1.0, 'data': 1.0, 'analysis': 1.1, 'review': 1.1,
                'customer': 1.2, 'client': 1.2, 'partner': 1.2, 'vendor': 1.2,
                'supplier': 1.2, 'stakeholder': 1.2, 'management': 1.1, 'director': 1.1
            },
            'it_alerts': {
                'alert': 1.5, 'outage': 1.5, 'server': 1.4, 'downtime': 1.5,
                'maintenance': 1.4, 'update': 1.3, 'upgrade': 1.3, 'system': 1.3,
                'incident': 1.4, 'backup': 1.4, 'security': 1.4, 'breach': 1.5,
                'password': 1.4, 'access': 1.3, 'login': 1.3, 'account': 1.2,
                'vpn': 1.4, 'network': 1.4, 'infrastructure': 1.3, 'database': 1.3,
                'software': 1.3, 'hardware': 1.3, 'application': 1.2, 'email': 1.1
            },
            'hr': {
                'policy': 1.5, 'hr': 1.6, 'human resources': 1.6, 'employee': 1.3,
                'benefits': 1.4, 'handbook': 1.5, 'personnel': 1.3, 'sick leave': 1.4,
                'vacation': 1.3, 'vacation day': 1.4, 'pto': 1.4, 'time off': 1.3,
                'holiday': 1.2, 'review': 1.2, 'performance': 1.2, 'appraisal': 1.3,
                'payroll': 1.3, 'salary': 1.3, 'compensation': 1.3, 'onboarding': 1.4
            },
            'legal': {
                'legal': 1.5, 'contract': 1.5, 'agreement': 1.4, 'nda': 1.5,
                'terms': 1.3, 'conditions': 1.3, 'clause': 1.4, 'compliance': 1.4,
                'sign': 1.2, 'signature': 1.3, 'party': 1.2, 'counsel': 1.4,
                'attorney': 1.4, 'law': 1.3, 'regulation': 1.3, 'policy': 1.2,
                'amendment': 1.4, 'liability': 1.4, 'confidential': 1.3, 'proprietary': 1.3
            },
            'meeting': {
                'meeting': 1.5, 'calendar': 1.4, 'schedule': 1.4, 'invite': 1.3,
                'agenda': 1.5, 'conference': 1.4, 'call': 1.1, 'appointment': 1.3,
                'event': 1.2, 'available': 1.1, 'reschedule': 1.4, 'attendee': 1.3,
                'zoom': 1.4, 'teams': 1.3, 'webex': 1.3, 'google meet': 1.3,
                'room': 1.2, 'booking': 1.3, 'slot': 1.2, 'availability': 1.3
            },
            'personal': {
                'friend': 1.4, 'family': 1.4, 'personal': 1.4, 'private': 1.3,
                'weekend': 1.3, 'dinner': 1.3, 'lunch': 1.3, 'movie': 1.3,
                'travel': 1.3, 'vacation': 1.3, 'photo': 1.2, 'picture': 1.2,
                'birthday': 1.4, 'gift': 1.3, 'party': 1.3, 'celebration': 1.3,
                'holiday': 1.2, 'congrats': 1.3, 'congratulations': 1.3, 'best wishes': 1.3
            },
            'project': {
                'project': 1.5, 'milestone': 1.5, 'deadline': 1.4, 'timeline': 1.4,
                'deliverable': 1.5, 'status': 1.3, 'plan': 1.3, 'roadmap': 1.4,
                'sprint': 1.4, 'task': 1.3, 'jira': 1.4, 'trello': 1.4,
                'progress': 1.3, 'tracking': 1.3, 'phase': 1.3, 'implementation': 1.2,
                'development': 1.2, 'testing': 1.2, 'kickoff': 1.4, 'launch': 1.3
            },
            'spam': {
                'offer': 1.4, 'free': 1.5, 'discount': 1.4, 'prize': 1.5,
                'winner': 1.5, 'lottery': 1.6, 'urgent': 1.4, 'attention': 1.3,
                'congratulation': 1.5, 'million': 1.4, 'dollar': 1.3, 'limited time': 1.4,
                'claim': 1.4, 'click': 1.3, 'link': 1.2, 'password': 1.3,
                'account': 1.2, 'verify': 1.3, 'verification': 1.3, 'bank': 1.3
            }
        }
        
        # Contextual term sets
        self.urgency_terms = ['urgent', 'asap', 'immediately', 'deadline', 'today', 'tomorrow', 'morning', 
                            'afternoon', 'evening', 'urgent', 'priority', 'important']
        self.action_terms = ['please', 'kindly', 'request', 'action', 'review', 'confirm', 'approve', 'respond',
                           'reply', 'send', 'forward', 'update', 'provide', 'complete', 'submit', 'perform']
        self.positive_terms = ['thank', 'thanks', 'good', 'great', 'excellent', 'appreciate', 'happy', 
                             'pleased', 'wonderful', 'congratulations', 'well done', 'success']
        self.negative_terms = ['issue', 'problem', 'error', 'mistake', 'fail', 'urgent', 'complaint', 
                             'concern', 'wrong', 'bad', 'sorry', 'unfortunately', 'regret']
        
        # Add rule-based keywords with confidence thresholds
        self.rule_based_categories = {
            "Finance & Transactions": {
                "keywords": [
                    "invoice", "payment", "budget", "transaction", "financial",
                    "expense", "receipt", "cost", "bank", "credit", "debit",
                    "fund", "purchase", "vendor", "bill", "tax", "accounting",
                    "fiscal", "payroll", "reimbursement"
                ],
                "threshold": 0.35
            },
            "IT Alerts & System Notifications": {
                "keywords": [
                    "server", "system", "alert", "notification", "maintenance",
                    "outage", "downtime", "update", "security", "password",
                    "access", "network", "IT", "infrastructure", "backup",
                    "database", "error", "incident", "undelivered mail",
                    "delivery failed", "mail system", "gateway", "bounce",
                    "mail returned", "delivery status", "delivery failure"
                ],
                "threshold": 0.40
            },
            "Internal Policies & HR Updates": {
                "keywords": [
                    "hr", "human resources", "policy", "policies", "update",
                    "training", "employee", "staff", "personnel", "benefits",
                    "leave", "holiday", "vacation", "sick", "attendance",
                    "workplace", "handbook"
                ],
                "threshold": 0.35
            },
            "Spam & Marketing": {
                "keywords": [
                    "offer", "free", "discount", "prize", "promotion",
                    "marketing", "subscribe", "unsubscribe", "featured",
                    "exclusive", "limited time", "opportunity", "welcome",
                    "get started", "submission", "rangeMe", "marketplace",
                    "platform", "buyer", "seller"
                ],
                "threshold": 0.35
            }
        }
    
    def _load_model(self):
        """Load the trained model and its components"""
        try:
            # Try the email_app/models directory first
            model_path = os.path.join('email_app', 'models', 'enhanced_email_categorization_model_v4.joblib')
            if not os.path.exists(model_path):
                # Try alternative paths if needed
                alternative_paths = [
                    os.path.join('FYP PART 2', 'Category Modeling', 'enhanced_email_categorization_model_v4.joblib'),
                    os.path.join('FYP PART 2', 'Category Modeling', 'models', 'enhanced_email_categorization_model_v4.joblib')
                ]
                
                for path in alternative_paths:
                    if os.path.exists(path):
                        model_path = path
                        break
                else:
                    raise FileNotFoundError(f"Model file not found in any of the following locations:\n" +
                                          f"1. {model_path}\n" +
                                          f"2. {alternative_paths[0]}\n" +
                                          f"3. {alternative_paths[1]}")
            
            model_data = load(model_path)
            
            self.model = model_data['ensemble']
            self.vectorizer = model_data['vectorizer']
            self.scaler = model_data['scaler']
            
            logging.info(f"Model loaded successfully from {model_path}")
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")
            raise
    
    def _clean_text(self, text):
        """Clean text for feature extraction"""
        if not isinstance(text, str):
            return ""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _calculate_category_scores(self, cleaned_subject, cleaned_message):
        """Calculate weighted scores for each category"""
        combined_text = cleaned_subject + ' ' + cleaned_message
        category_scores = {}
        
        for category, terms in self.category_terms.items():
            score = 0
            total_weight = 0
            for term, weight in terms.items():
                if re.search(r'\b' + re.escape(term) + r'\b', combined_text, re.IGNORECASE):
                    score += weight
                    total_weight += weight
            category_scores[category] = score / max(total_weight, 1)
        
        return category_scores
    
    def _extract_email_features(self, subject, message, cleaned_subject="", cleaned_message=""):
        """
        Extract comprehensive features from email subject and message
        Matches exactly with enhanced_email_categorization_v4.py
        """
        if not isinstance(subject, str):
            subject = ""
        if not isinstance(message, str):
            message = ""
            
        # If cleaned text not provided, clean it
        if not cleaned_subject:
            cleaned_subject = self._clean_text(subject)
        if not cleaned_message:
            cleaned_message = self._clean_text(message)
            
        features = []
        
        # PART 1: STRUCTURAL FEATURES
        # Length features
        features.append(len(subject))
        features.append(len(message))
        features.append(len(cleaned_subject.split()))
        features.append(len(cleaned_message.split()))
        
        # Case and punctuation ratios
        features.append(sum(1 for c in subject if c.isupper()) / max(len(subject), 1))
        features.append(sum(1 for c in message if c.isupper()) / max(len(message), 1))
        features.append(sum(1 for c in subject if c in string.punctuation) / max(len(subject), 1))
        features.append(sum(1 for c in message if c in string.punctuation) / max(len(message), 1))
        
        # Question features
        features.append(subject.count('?'))
        features.append(message.count('?'))
        
        # Special character ratios
        features.append(sum(1 for c in subject if not c.isalnum()) / max(len(subject), 1))
        features.append(sum(1 for c in message if not c.isalnum()) / max(len(message), 1))
        features.append(sum(1 for c in subject if c.isdigit()) / max(len(subject), 1))
        features.append(sum(1 for c in message if c.isdigit()) / max(len(message), 1))
        
        # URL and email presence
        features.append(1 if re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', 
                                     message) else 0)
        features.append(1 if re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message) else 0)
        
        # PART 2: EMAIL STRUCTURE FEATURES
        # CC/BCC detection
        features.append(1 if re.search(r'\bcc:|bcc:', message, re.IGNORECASE) else 0)
        
        # Forwarded email detection
        features.append(1 if re.search(r'forwarded message|^fw:', message, re.IGNORECASE) else 0)
        
        # Reply detection
        features.append(1 if re.search(r'^re:', subject, re.IGNORECASE) else 0)
        
        # Attachment detection
        features.append(1 if re.search(r'attach|enclosed|attached|\.pdf|\.doc|\.xls|\.zip|\.png|\.jpg', 
                                     message, re.IGNORECASE) else 0)
        
        # HTML content detection
        features.append(1 if any(pattern in message.lower() for pattern in ['<html', '<body', '<div', '<p>', '<table', '<a href']) else 0)
        
        # Thread length approximation
        thread_indicators = message.count('wrote:') + message.count('From:') + message.count('To:') + message.count('Sent:') + message.count('Date:')
        features.append(thread_indicators)
        
        # PART 3: SEMANTIC FEATURES FROM CLEANED TEXT
        # Calculate category-specific keyword scores (weighted approach)
        category_scores = self._calculate_category_scores(cleaned_subject, cleaned_message)
        features.extend(list(category_scores.values()))
        
        # PART 4: CONTEXTUAL FEATURES
        # Time urgency indicators
        urgency_score = sum(1 for term in self.urgency_terms 
                          if re.search(r'\b' + re.escape(term) + r'\b', subject + message, re.IGNORECASE))
        features.append(urgency_score / len(self.urgency_terms))
        
        # Action request indicators
        action_score = sum(1 for term in self.action_terms 
                         if re.search(r'\b' + re.escape(term) + r'\b', subject + message, re.IGNORECASE))
        features.append(action_score / len(self.action_terms))
        
        # Sentiment approximation (very basic)
        positive_score = sum(1 for term in self.positive_terms 
                           if re.search(r'\b' + re.escape(term) + r'\b', cleaned_subject + cleaned_message, re.IGNORECASE))
        negative_score = sum(1 for term in self.negative_terms 
                           if re.search(r'\b' + re.escape(term) + r'\b', cleaned_subject + cleaned_message, re.IGNORECASE))
        
        features.append(positive_score / len(self.positive_terms))
        features.append(negative_score / len(self.negative_terms))
        features.append((positive_score - negative_score) / (len(self.positive_terms) + len(self.negative_terms)))
        
        return np.array(features)
    
    def _apply_rule_based_classification(self, subject, message):
        """
        Apply rule-based classification using keyword matching
        Returns tuple of (category, confidence)
        """
        if not isinstance(subject, str):
            subject = ""
        if not isinstance(message, str):
            message = ""
            
        text = f"{subject} {message}".lower()
        
        category_scores = {}
        for category, config in self.rule_based_categories.items():
            matches = sum(1 for keyword in config["keywords"] 
                        if keyword.lower() in text)
            if matches > 0:
                # Calculate confidence based on number of matches and keyword count
                confidence = min(0.3 + (matches / len(config["keywords"]) * 0.4), 
                               config["threshold"])
                category_scores[category] = confidence
        
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            return best_category[0], best_category[1]
        
        return None, 0.0

    def predict_category(self, subject, message):
        """
        Enhanced prediction using both ML model and rule-based approach
        """
        try:
            # Get ML model prediction
            ml_prediction = self._predict_with_model(subject, message)
            
            # If ML confidence is high enough, use it
            if not ml_prediction.get('is_low_confidence', True):
                return ml_prediction
            
            # Try rule-based classification
            rule_category, rule_confidence = self._apply_rule_based_classification(
                subject, message
            )
            
            # If rule-based found a match with good confidence
            if rule_category and rule_confidence >= 0.3:
                return {
                    'category': rule_category,
                    'confidence': rule_confidence,
                    'method': 'rule_based',
                    'probabilities': {rule_category: rule_confidence},
                    'is_low_confidence': False
                }
            
            # If both methods have low confidence, return ML prediction
            return ml_prediction
            
        except Exception as e:
            logging.error(f"Error predicting email category: {str(e)}")
            return {
                'category': 'uncategorized',
                'confidence': 0.0,
                'probabilities': {},
                'error': str(e)
            }
    
    def _predict_with_model(self, subject, message):
        """Original ML model prediction logic"""
        # Move existing prediction code here
        cleaned_subject = self._clean_text(subject)
        cleaned_message = self._clean_text(message)
        
        features = self._extract_email_features(subject, message, 
                                             cleaned_subject, cleaned_message)
        
        combined_text = cleaned_subject + ' SUBJECT_END ' + cleaned_message
        text_features = self.vectorizer.transform([combined_text])
        
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        X = hstack([features_scaled, text_features]).tocsr()
        
        probabilities = self.model.predict_proba(X)[0]
        top_indices = probabilities.argsort()[-2:][::-1]
        confidence = probabilities[top_indices[0]]
        second_best_confidence = probabilities[top_indices[1]]
        
        prediction = self.category_mapping[top_indices[0]]["name"]
        threshold = self.category_mapping[top_indices[0]]["threshold"]
        
        category_scores = self._calculate_category_scores(cleaned_subject, 
                                                        cleaned_message)
        
        return {
            'category': prediction,
            'confidence': float(confidence),
            'method': 'ml_model',
            'probabilities': {self.category_mapping[i]["name"]: float(p) 
                            for i, p in enumerate(probabilities)},
            'is_low_confidence': confidence < threshold,
            'relative_confidence': float(confidence / second_best_confidence) 
                                 if second_best_confidence > 0 else float('inf'),
            'category_scores': category_scores
        }
    
    def standardize_categories_in_db(self):
        """Perform a one-time standardization of categories in the database"""
        try:
            import psycopg2
            from dotenv import load_dotenv
            import os
            
            # Load environment variables
            load_dotenv()
            
            # Connect using environment variables
            conn = psycopg2.connect(
                dbname=os.getenv('DB_NAME', 'email_db'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'email1234'),
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432')
            )
            cur = conn.cursor()
            
            # Update all numerical categories and variations in one go
            standardized_mapping = {
                # Map numerical categories and their string representations
                "0": "Finance & Transactions",
                "1": "General Business Communication",
                "2": "IT Alerts & System Notifications",
                "3": "Internal Policies & HR Updates",
                "4": "Legal & Contractual",
                "5": "Meetings & Scheduling",
                "6": "Personal Communication & Purely Personal",
                "7": "Project Management & Strategy",
                "8": "Spam & Marketing",
                # Map variations
                "Finance & Transaction": "Finance & Transactions",
                "Business Communication": "General Business Communication",
                "IT Alert": "IT Alerts & System Notifications",
                "Internal Policy": "Internal Policies & HR Updates",
                "HR Update": "Internal Policies & HR Updates",
                "Legal": "Legal & Contractual",
                "Meeting": "Meetings & Scheduling",
                "Personal": "Personal Communication & Purely Personal",
                "Project": "Project Management & Strategy",
                "Spam": "Spam & Marketing"
            }
            
            # Do the update in a single transaction
            for old_category, new_category in standardized_mapping.items():
                cur.execute(
                    "UPDATE emails SET category = %s WHERE category = %s",
                    (new_category, str(old_category))
                )
            
            conn.commit()
            cur.close()
            conn.close()
            logging.info("Category standardization completed successfully")
            
        except Exception as e:
            logging.error(f"Error standardizing categories: {str(e)}")
            raise 