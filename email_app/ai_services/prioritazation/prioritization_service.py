import os
import joblib
import numpy as np
import re
import pandas as pd
from typing import Dict, Tuple, List
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

logger = logging.getLogger(__name__)

class EmailPrioritizationService:
    def __init__(self):
        # Load the trained model and encoder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, '..', '..', 'models', 'pr_models', 'priority_model_v2.joblib')
        encoder_path = os.path.join(current_dir, '..', '..', 'models', 'pr_models', 'label_priority_encoder.joblib')
        
        logger.info(f"Loading priority model from {model_path}")
        self.model = joblib.load(model_path)
        logger.info(f"Loading priority label encoder from {encoder_path}")
        self.label_encoder = joblib.load(encoder_path)
    
    def _preprocess_email(self, subject: str, body: str) -> pd.DataFrame:
        """Clean and preprocess email text for the RandomForest model"""
        # Basic cleaning
        def clean_text(text):
            # Convert to lowercase
            text = text.lower()
            # Remove special characters and extra whitespace
            text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
            text = ' '.join(text.split())
            return text
        
        cleaned_subject = clean_text(subject)
        cleaned_message = clean_text(body)
        
        # Enhanced feature sets
        urgency_words = {
            'urgent', 'asap', 'emergency', 'immediate', 'critical', 'important',
            'priority', 'urgent priority', 'high priority', 'deadline', 'due',
            'escalation', 'escalated', 'time sensitive', 'action required'
        }
        
        risk_words = {
            'risk', 'warning', 'alert', 'danger', 'critical', 'serious',
            'issue', 'problem', 'failure', 'error', 'outage', 'breach',
            'security', 'compliance', 'violation', 'incident'
        }
        
        action_verbs = {
            'review', 'approve', 'confirm', 'update', 'respond', 'complete',
            'submit', 'verify', 'check', 'investigate', 'resolve', 'fix',
            'implement', 'test', 'deploy', 'analyze', 'assess', 'evaluate'
        }
        
        medium_indicators = {
            'review', 'update', 'feedback', 'status', 'progress', 'weekly',
            'monthly', 'report', 'meeting', 'discuss', 'follow up', 'schedule',
            'plan', 'proposal', 'suggestion', 'recommendation'
        }
        
        low_indicators = {
            'fyi', 'newsletter', 'announcement', 'info', 'thanks', 'thank you',
            'sharing', 'heads up', 'reminder', 'optional', 'when convenient',
            'no rush', 'take your time', 'for reference', 'just letting you know'
        }
        
        # Calculate flags with word context
        message_words = cleaned_message.split()
        subject_words = cleaned_subject.split()
        combined_text = cleaned_subject + ' ' + cleaned_message
        
        # Enhanced urgency detection
        urgency_flag = int(
            any(word in combined_text.split() for word in urgency_words) or
            ('asap' in combined_text) or
            ('as soon as possible' in combined_text) or
            ('right away' in combined_text) or
            ('immediately' in combined_text)
        )
        
        # Enhanced risk detection
        risk_flag = int(
            any(word in combined_text.split() for word in risk_words) or
            ('high impact' in combined_text) or
            ('affected' in combined_text and ('user' in combined_text or 'system' in combined_text)) or
            ('down' in combined_text and ('system' in combined_text or 'service' in combined_text))
        )
        
        urgency_and_risk = int(urgency_flag and risk_flag)
        
        # Enhanced action verb counting
        num_action_verbs = sum(1 for word in action_verbs if word in combined_text.split())
        
        # Count medium and low priority indicators
        num_medium_indicators = sum(1 for word in medium_indicators if word in combined_text.split())
        num_low_indicators = sum(1 for word in low_indicators if word in combined_text.split())
        
        # Enhanced uppercase analysis
        num_uppercase_words_subject = sum(1 for word in subject.split() if word.isupper() and len(word) > 1)
        num_uppercase_words_message = sum(1 for word in body.split() if word.isupper() and len(word) > 1)
        
        # Time sensitivity detection
        has_deadline = int(
            any(word in combined_text for word in ['deadline', 'due', 'by']) and
            any(word in combined_text for word in ['today', 'tomorrow', 'asap', 'immediate'])
        )
        
        # Question analysis
        num_questions = body.count('?')
        has_question = int(num_questions > 0)
        
        # Create a DataFrame with enhanced features
        features = pd.DataFrame({
            'Cleaned_Subject': [cleaned_subject],
            'Cleaned_Message': [cleaned_message],
            'urgency_flag': [urgency_flag],
            'risk_flag': [risk_flag],
            'urgency_and_risk': [urgency_and_risk],
            'num_action_verbs': [num_action_verbs],
            'num_medium_indicators': [num_medium_indicators],
            'num_low_indicators': [num_low_indicators],
            'num_uppercase_words_subject': [num_uppercase_words_subject],
            'num_uppercase_words_message': [num_uppercase_words_message],
            'subject_len': [len(subject)],
            'has_question': [has_question],
            'num_questions': [num_questions],
            'has_deadline': [has_deadline]
        })
        
        return features
        
    def predict_priority(self, subject: str, body: str, sender: str, category: str = None) -> Tuple[str, Dict[str, float], str]:
        """
        Predict email priority using the RandomForest model.
        
        Args:
            subject: Email subject
            body: Email body/snippet
            sender: Email sender
            category: Email category (e.g., 'Spam Email', 'Promotions or Marketing Email', 'Social Media Email')
            
        Returns:
            Tuple containing:
            - Predicted priority label (str)
            - Priority scores for each class (Dict[str, float])
            - Explanation of the prediction (str)
        """
        # Check for low priority categories (keeping this rule-based approach)
        low_priority_categories = ['Spam Email', 'Promotions or Marketing Email', 'Social Media Email']
        
        # Log the category for debugging
        logger.info(f"Received category: {category}")
        
        if category and category in low_priority_categories:
            logger.info(f"Category {category} is in low priority categories, setting priority to LOW")
            # Create a dictionary with all priorities set to 0 except 'low'
            scores = {label.lower(): 0.0 for label in self.label_encoder.classes_}
            scores['low'] = 1.0
            
            explanation = (
                f"The email has been automatically set to low priority "
                f"because it is categorized as {category}. "
                f"This is a system rule to ensure proper handling of {category.lower()} emails."
            )
            
            return 'low', scores, explanation
            
        # Preprocess the email
        logger.info("Using RandomForest model for prediction")
        features = self._preprocess_email(subject, body)
        
        try:
            # Make prediction with the model
            logger.info("Making prediction with model")
            priority_idx = self.model.predict(features)[0]
            probabilities = self.model.predict_proba(features)[0]
            
            # Convert numerical prediction to category
            if hasattr(self.model, 'classes_'):
                class_labels = self.model.classes_
            else:
                class_labels = self.label_encoder.classes_
                
            priority_label = str(class_labels[priority_idx])
            
            # Convert to low/medium/high if numerical
            if priority_label.isdigit():
                priority_map = {0: 'low', 1: 'medium', 2: 'high'}
                priority_label = priority_map.get(int(priority_label), 'medium')
            else:
                priority_label = priority_label.lower()
                
            # Create scores dictionary with enhanced score calculation
            scores = {}
            for i, label in enumerate(class_labels):
                label_str = str(label)
                if label_str.isdigit():
                    # Map numerical labels to string labels
                    label_str = {0: 'low', 1: 'medium', 2: 'high'}.get(int(label_str), 'medium')
                else:
                    label_str = label_str.lower()
                scores[label_str] = float(probabilities[i])
            
            # Apply rule-based adjustments to scores based on features
            high_score = 0
            medium_score = 0
            low_score = 0
            
            # High priority scoring
            if features['urgency_and_risk'].iloc[0]:
                high_score += 15  # Critical combination
            if features['urgency_flag'].iloc[0]:
                high_score += 10  # Strong urgency
            if features['risk_flag'].iloc[0]:
                high_score += 10  # Strong risk
            if features['has_deadline'].iloc[0]:
                high_score += 8   # Immediate deadline
            
            # Action-based scoring
            if features['num_action_verbs'].iloc[0] > 3:
                high_score += 8   # Multiple critical actions
            elif features['num_action_verbs'].iloc[0] > 1:
                medium_score += 6 # Several actions
            elif features['num_action_verbs'].iloc[0] == 1:
                medium_score += 4 # Single action
            else:
                low_score += 5    # No actions
            
            # Medium priority indicators
            if features['num_medium_indicators'].iloc[0] > 2:
                medium_score += 8 # Strong medium signals
            elif features['num_medium_indicators'].iloc[0] > 0:
                medium_score += 5 # Some medium signals
            
            # Low priority indicators
            if features['num_low_indicators'].iloc[0] > 2:
                low_score += 10   # Strong low signals
            elif features['num_low_indicators'].iloc[0] > 0:
                low_score += 6    # Some low signals
                
            # Emphasis scoring
            if features['num_uppercase_words_subject'].iloc[0] > 2:
                high_score += 6   # Strong emphasis
            elif features['num_uppercase_words_subject'].iloc[0] > 0:
                high_score += 3   # Some emphasis
            
            if features['num_uppercase_words_message'].iloc[0] > 2:
                high_score += 4   # Message emphasis
                
            # Question analysis
            if features['has_question'].iloc[0]:
                if features['num_questions'].iloc[0] > 2:
                    medium_score += 6 # Multiple questions
                else:
                    medium_score += 4 # Some questions
                    
            # Missing urgency indicators suggests low priority
            if not any([features['urgency_flag'].iloc[0], features['risk_flag'].iloc[0], 
                      features['has_deadline'].iloc[0], features['has_question'].iloc[0]]):
                low_score += 8    # No urgency indicators
            
            # Calculate total and weights
            total_score = high_score + medium_score + low_score
            if total_score == 0:
                total_score = 1  # Prevent division by zero
                
            high_weight = high_score / total_score
            medium_weight = medium_score / total_score
            low_weight = low_score / total_score
            
            # Apply rule-based adjustments with non-linear scaling (matching test implementation)
            adjusted_probabilities = probabilities.copy()
            
            # Apply non-linear scaling with stronger bias reduction (from test model)
            adjusted_probabilities[2] *= (1 + high_weight) ** 3    # High priority (stronger boost)
            adjusted_probabilities[1] *= (1 + medium_weight)       # Medium priority (no boost)
            adjusted_probabilities[0] *= (1 + low_weight) ** 3     # Low priority (stronger boost)
            
            # Apply score-based adjustments for stronger classification
            if high_score >= 20:
                adjusted_probabilities[2] *= 4.0  # Very strong high boost
            elif high_score >= 15:
                adjusted_probabilities[2] *= 3.0  # Strong high boost
                
            if low_score >= 15:
                adjusted_probabilities[0] *= 4.0  # Very strong low boost
            elif low_score >= 10:
                adjusted_probabilities[0] *= 3.0  # Strong low boost
                
            # Aggressive medium priority reduction (from test model)
            if high_score > 0 or low_score > 0:
                reduction_factor = min(0.5, max(0.1, 1.0 - (high_score + low_score) / 40))
                adjusted_probabilities[1] *= reduction_factor
                
            # Additional adjustments for clear signals (from test model)
            if high_score >= 15 and high_score > (medium_score + low_score):
                adjusted_probabilities[2] *= 2.0  # Clear high priority
                adjusted_probabilities[1] *= 0.5  # Reduce medium
                
            if low_score >= 15 and low_score > (medium_score + high_score):
                adjusted_probabilities[0] *= 2.0  # Clear low priority
                adjusted_probabilities[1] *= 0.5  # Reduce medium
            
            # Normalize probabilities
            adjusted_probabilities = adjusted_probabilities / adjusted_probabilities.sum()
            
            # Dynamic thresholds
            high_threshold = 0.25 if high_score >= 15 else 0.30
            low_threshold = 0.25 if low_score >= 15 else 0.30
            
            # Determine priority with confidence-based classification (matching test model)
            max_prob = max(adjusted_probabilities)
            max_index = list(adjusted_probabilities).index(max_prob)
            
            # More aggressive classification rules (from test model)
            if adjusted_probabilities[2] >= high_threshold or (max_index == 2 and high_score >= 12):
                priority_label = 'high'
            elif adjusted_probabilities[0] >= low_threshold or (max_index == 0 and low_score >= 12):
                priority_label = 'low'
            else:
                # Only classify as medium if neither high nor low conditions are met
                priority_label = 'medium'
                
            # Update scores with adjusted probabilities
            for i, label in enumerate(['low', 'medium', 'high']):
                scores[label] = float(adjusted_probabilities[i])
                
            explanation = self._generate_explanation(priority_label, scores, features)
            return priority_label, scores, explanation
            
        except Exception as e:
            logger.error(f"Error in model prediction: {str(e)}", exc_info=True)
            # Fallback to medium priority
            scores = {label: 0.33 for label in ['low', 'medium', 'high']}
            scores['medium'] = 0.34
            explanation = f"Default medium priority due to prediction error: {str(e)}"
            return 'medium', scores, explanation
    
    def _generate_explanation(self, predicted_label: str, scores: Dict[str, float], features: pd.DataFrame) -> str:
        """
        Generate a human-readable explanation for the priority prediction.
        
        Args:
            predicted_label: The predicted priority label
            scores: Dictionary of scores for each priority class
            features: The extracted features used for prediction
            
        Returns:
            Explanation string
        """
        confidence = scores[predicted_label]
        
        # Build detailed explanation
        explanation_parts = []
        
        # Add confidence level
        if confidence > 0.8:
            confidence_level = "high"
        elif confidence > 0.6:
            confidence_level = "moderate"
        else:
            confidence_level = "low"
            
        explanation_parts.append(
            f"The email has been classified as {predicted_label} priority "
            f"with {confidence_level} confidence ({confidence:.2%})."
        )
        
        # Add key factors based on features
        key_factors = []
        
        # Urgency and risk analysis
        if features['urgency_and_risk'].iloc[0]:
            key_factors.append("Contains both urgency and risk indicators (critical importance)")
        elif features['urgency_flag'].iloc[0]:
            key_factors.append("Contains urgency indicators")
        elif features['risk_flag'].iloc[0]:
            key_factors.append("Contains risk indicators")
        
        # Action verbs analysis
        if features['num_action_verbs'].iloc[0] > 3:
            key_factors.append(f"Contains multiple action items ({features['num_action_verbs'].iloc[0]} actions)")
        elif features['num_action_verbs'].iloc[0] > 1:
            key_factors.append(f"Contains {features['num_action_verbs'].iloc[0]} action items")
        elif features['num_action_verbs'].iloc[0] == 1:
            key_factors.append("Contains 1 action item")
        else:
            key_factors.append("No action items detected")
            
        # Emphasis analysis (uppercase)
        if features['num_uppercase_words_subject'].iloc[0] > 2:
            key_factors.append("Strong emphasis in subject (multiple uppercase words)")
        elif features['num_uppercase_words_subject'].iloc[0] > 0:
            key_factors.append(f"Some emphasis in subject ({features['num_uppercase_words_subject'].iloc[0]} uppercase words)")
        
        # Question analysis
        if features['num_questions'].iloc[0] > 0:
            key_factors.append(f"Contains {features['num_questions'].iloc[0]} question(s)")
        
        # Deadline analysis
        if features['has_deadline'].iloc[0]:
            key_factors.append("Contains deadline or due date")
            
        # Priority indicators
        if features['num_medium_indicators'].iloc[0] > 0:
            key_factors.append(f"Contains {features['num_medium_indicators'].iloc[0]} medium priority indicators")
        if features['num_low_indicators'].iloc[0] > 0:
            key_factors.append(f"Contains {features['num_low_indicators'].iloc[0]} low priority indicators")
            
        # Add key factors to explanation
        if key_factors:
            explanation_parts.append("Key factors: " + "; ".join(key_factors) + ".")
            
        # Add priority-specific reasoning
        if predicted_label == 'high':
            priority_reasons = []
            if features['urgency_and_risk'].iloc[0]:
                priority_reasons.append("critical combination of urgency and risk")
            if features['urgency_flag'].iloc[0] or features['risk_flag'].iloc[0]:
                priority_reasons.append("significant urgency/risk indicators")
            if features['has_deadline'].iloc[0]:
                priority_reasons.append("immediate deadline")
            if features['num_action_verbs'].iloc[0] > 2:
                priority_reasons.append("multiple action items requiring attention")
                
            if priority_reasons:
                explanation_parts.append(f"This email is classified as high priority because: {', '.join(priority_reasons)}.")
                
        elif predicted_label == 'low':
            priority_reasons = []
            if features['num_low_indicators'].iloc[0] > 0:
                priority_reasons.append("contains informational/courtesy indicators")
            if features['num_action_verbs'].iloc[0] == 0:
                priority_reasons.append("no immediate actions required")
            if not any([features['urgency_flag'].iloc[0], features['risk_flag'].iloc[0], features['has_deadline'].iloc[0]]):
                priority_reasons.append("no urgency, risk, or deadline indicators")
                
            if priority_reasons:
                explanation_parts.append(f"This email is classified as low priority because: {', '.join(priority_reasons)}.")
                
        else:  # medium priority
            priority_reasons = []
            if features['num_action_verbs'].iloc[0] in [1, 2]:
                priority_reasons.append("contains moderate number of action items")
            if features['num_medium_indicators'].iloc[0] > 0:
                priority_reasons.append("contains typical medium priority indicators")
            if features['has_question'].iloc[0]:
                priority_reasons.append("requires response to questions")
            if not features['urgency_and_risk'].iloc[0]:
                priority_reasons.append("no critical urgency/risk combination")
                
            if priority_reasons:
                explanation_parts.append(f"This email is classified as medium priority because: {', '.join(priority_reasons)}.")
                
        return " ".join(explanation_parts)
