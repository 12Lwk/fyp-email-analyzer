import re
import logging
import numpy as np
from typing import Dict, Any, List, Tuple, IO, Union
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import warnings
import xgboost as xgb
import os
import tempfile
import pickle
import sklearn
import json

logger = logging.getLogger(__name__)

#warnings.filterwarnings('ignore', category=UserWarning, module='xgboost')
warnings.filterwarnings('ignore', category=sklearn.exceptions.InconsistentVersionWarning)

TORCH_AVAILABLE = False

try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    TORCH_AVAILABLE = True
    logger.info("Torch and transformers available for categorization")
except Exception as e:
    logger.warning(f"Could not import torch/transformers: {str(e)}")
    logger.warning("Using fallback EmailCategorizationService")

class EmailCategorizationService:

    def __init__(self):
        logger.info("Initializing EmailCategorizationService")
        
        # Set torch availability flag
        self.torch_available = TORCH_AVAILABLE
        self.model = None
        self.tokenizer = None
        self.xgb_model = None
        self.label_encoder = None
        
        try:
            self.label_encoder = joblib.load('email_app/models/ml_models/label_encoder.joblib')
            logger.info("Label encoder loaded successfully")
        except Exception as e:
            logger.error(f"Error loading label encoder: {str(e)}", exc_info=True)
            self.label_encoder = None
            
        # Load XGBoost model
        try:
            # Check if converted XGBoost model exists
            xgb_converted_path = 'email_app/models/ml_models/bert_xgb_model_converted.json'
            xgb_original_path = 'email_app/models/ml_models/bert_xgb_model.joblib'
            
            if os.path.exists(xgb_converted_path):
                logger.info(f"Found converted XGBoost model at {xgb_converted_path}")
                self.xgb_model = self._load_xgb_model_direct(xgb_converted_path)
            else:
                logger.info(f"Trying original XGBoost model at {xgb_original_path}")
                self.xgb_model = self._load_xgb_model(xgb_original_path)
                
            logger.info("XGBoost model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading XGBoost model: {str(e)}", exc_info=True)
            self.xgb_model = None
        
        if self.torch_available:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained('email_app/models/ml_models/bert_embedder_model')
                self.model = AutoModel.from_pretrained('email_app/models/ml_models/bert_embedder_model')
                self.model.eval()  
                logger.info("BERT model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading BERT model: {str(e)}", exc_info=True)
                self.model = None
                self.tokenizer = None
                self.torch_available = False
                logger.warning("BERT model not available")
        else:
            logger.warning("BERT model not available")
        
        self.categories = [
            "Work or Business Email",
            "Finance & Transaction Email",
            "Personal Email", 
            "Meeting & Schedule Email",
            "Legal & Contractual Email",
            "Spam Email",
            "IT Alerts & System Notifications Email",
            "Internal Policies & HR Updates Email",
            "Social Media Email",
            "Promotions or Marketing Email",
            "Utilities Bill Email"
        ]
        
        self.category_embeddings = {}
        if self.model and self.tokenizer:
            for category in self.categories:
                self.category_embeddings[category] = self._get_bert_embedding(category)
                logger.info(f"Pre-computed embedding for category: {category}")

    def _load_xgb_model_direct(self, model_path: str):
        """Load an XGBoost model directly from a saved model file"""
        try:
            logger.info(f"Loading model directly from {model_path}")
            
            # Try loading with XGBoost directly first
            try:
                model = xgb.Booster()
                model.load_model(model_path)
                logger.info("Successfully loaded model with XGBoost Booster")
                return model
            except Exception as e1:
                logger.warning(f"Failed to load with XGBoost Booster: {str(e1)}")
            
            # Try loading with XGBClassifier
            try:
                model = xgb.XGBClassifier()
                model.load_model(model_path)
                logger.info("Successfully loaded model with XGBClassifier")
                return model
            except Exception as e2:
                logger.warning(f"Failed to load with XGBClassifier: {str(e2)}")
            
            # Try loading with joblib
            try:
                model = joblib.load(model_path)
                logger.info("Successfully loaded model with joblib")
                return model
            except Exception as e3:
                logger.warning(f"Failed to load with joblib: {str(e3)}")
            
            # If all methods fail, try to load as JSON
            try:
                with open(model_path, 'r') as f:
                    model_json = json.load(f)
                model = xgb.Booster()
                model.load_model(model_path)
                logger.info("Successfully loaded model from JSON")
                return model
            except Exception as e4:
                logger.error(f"All loading methods failed: {str(e4)}")
                raise
                
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise

    def _load_xgb_model(self, model_path: str):
        """Load XGBoost model with fallbacks"""
        try:
            logger.info(f"Attempting to load XGBoost model from {model_path}")
            
            # Try loading with XGBoost directly first
            try:
                model = xgb.Booster()
                model.load_model(model_path)
                logger.info("Successfully loaded model with XGBoost Booster")
                return model
            except Exception as e1:
                logger.warning(f"Failed to load with XGBoost Booster: {str(e1)}")
            
            # Try loading with XGBClassifier
            try:
                model = xgb.XGBClassifier()
                model.load_model(model_path)
                logger.info("Successfully loaded model with XGBClassifier")
                return model
            except Exception as e2:
                logger.warning(f"Failed to load with XGBClassifier: {str(e2)}")
            
            # Try loading with joblib
            try:
                model = joblib.load(model_path)
                logger.info("Successfully loaded model with joblib")
                return model
            except Exception as e3:
                logger.warning(f"Failed to load with joblib: {str(e3)}")
            
            # If all methods fail, try to load as JSON
            try:
                with open(model_path, 'r') as f:
                    model_json = json.load(f)
                model = xgb.Booster()
                model.load_model(model_path)
                logger.info("Successfully loaded model from JSON")
                return model
            except Exception as e4:
                logger.error(f"All loading methods failed: {str(e4)}")
                raise
                
        except Exception as e:
            logger.error(f"Failed to load XGBoost model: {str(e)}")
            raise

    def _get_bert_embedding(self, text: str) -> np.ndarray:
        if not self.model or not self.tokenizer:
            return None
            
        try:
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            
            return embeddings
        except Exception as e:
            logger.error(f"Error getting BERT embedding: {str(e)}", exc_info=True)
            return None

    def _get_semantic_similarity(self, text: str, category: str) -> float:
        if not self.model or not self.tokenizer:
            return 0.0
            
        try:
            text_embedding = self._get_bert_embedding(text)
            category_embedding = self.category_embeddings.get(category)
            
            if text_embedding is None or category_embedding is None:
                return 0.0
            
            similarity = cosine_similarity([text_embedding], [category_embedding])[0][0]
            return float(max(0.0, min(1.0, similarity)))
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {str(e)}", exc_info=True)
            return 0.0

    def categorize_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            combined_text = (
                (email_data.get('subject', '') or '') + ' ' +
                (email_data.get('content', '') or '') + ' ' 
            ).lower()
            
            logger.info(f"Processing email with subject: {email_data.get('subject', '')}")
            
            # Get BERT embedding for the text
            text_embedding = self._get_bert_embedding(combined_text)
            if text_embedding is None:
                logger.warning("Could not generate BERT embedding")
                return {
                    'category': "Personal Email",
                    'confidence': 0.1,
                    'explanation': "Default category due to embedding error"
                }
            
            # Use XGBoost model for prediction
            if self.xgb_model and self.label_encoder:
                try:
                    # Predict using XGBoost model
                    prediction = None
                    confidence = 0.0
                    
                    # Handle different types of XGBoost models
                    if hasattr(self.xgb_model, 'predict') and hasattr(self.xgb_model, 'predict_proba'):
                        # It's an XGBClassifier
                        prediction = self.xgb_model.predict([text_embedding])[0]
                        confidence = max(self.xgb_model.predict_proba([text_embedding])[0])
                    elif isinstance(self.xgb_model, xgb.Booster):
                        # It's a Booster
                        dmatrix = xgb.DMatrix([text_embedding])
                        pred_probs = self.xgb_model.predict(dmatrix)
                        prediction = pred_probs.argmax()
                        confidence = pred_probs.max()
                    
                    if prediction is not None:
                        # Convert numerical prediction to category name
                        category = self.label_encoder.inverse_transform([prediction])[0]
                        
                        logger.info(f"XGBoost model prediction: {category} with confidence {confidence:.3f}")
                        return {
                            'category': category,
                            'confidence': float(confidence),
                            'explanation': self._generate_explanation(category, float(confidence), "XGBoost")
                        }
                except Exception as e:
                    logger.error(f"Error in XGBoost model prediction: {str(e)}", exc_info=True)
            
            # Fallback to semantic similarity if XGBoost fails
            semantic_scores = {}
            if self.model and self.tokenizer:
                for category in self.categories:
                    semantic_scores[category] = self._get_semantic_similarity(combined_text, category)
                    logger.info(f"Category {category} similarity score: {semantic_scores[category]:.3f}")
            
            if not semantic_scores:
                best_category = "Personal Email"  
                confidence = 0.1
                logger.warning("No semantic scores available, using default category")
            else:
                best_category = max(semantic_scores, key=semantic_scores.get)
                confidence = float(semantic_scores[best_category])  
                logger.info(f"Selected category: {best_category} with confidence: {confidence:.3f}")
            
            confidence = max(confidence, 0.1)
            
            explanation = self._generate_explanation(best_category, confidence, "Semantic")
            
            return {
                'category': best_category,
                'confidence': confidence,  
                'explanation': explanation
            }
            
        except Exception as e:
            logger.error(f"Error in categorize_email: {str(e)}", exc_info=True)
            return {
                'category': "Personal Email",
                'confidence': 0.1,
                'explanation': "Default category due to processing error"
            }

    def _generate_explanation(self, category: str, confidence: float, method: str = "AI") -> str:
        confidence_percent = round(confidence * 100)
        
        if confidence < 0.3:
            confidence_text = "low"
        elif confidence < 0.7:
            confidence_text = "moderate"
        else:
            confidence_text = "high"
            
        return f"Classified as {category} with {confidence_text} confidence ({confidence_percent}%) using {method} model." 