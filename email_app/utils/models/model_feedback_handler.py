import logging
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import os
from joblib import dump, load

class ModelFeedbackHandler:
    def __init__(self, model_path, min_samples=100, retrain_interval=7):
        self.model_path = model_path
        self.min_samples = min_samples
        self.retrain_interval = retrain_interval
        self.feedback_data = []
        self.last_retrain_time = None
        
    def add_feedback(self, email_id, subject, message, predicted_category, actual_category, confidence):
        """Add feedback for a prediction"""
        self.feedback_data.append({
            'email_id': email_id,
            'subject': subject,
            'message': message,
            'predicted_category': predicted_category,
            'actual_category': actual_category,
            'confidence': confidence,
            'timestamp': datetime.now()
        })
        
        # Check if we should retrain
        self._check_retraining()
        
    def _check_retraining(self):
        """Check if we should retrain the model"""
        if len(self.feedback_data) < self.min_samples:
            return
            
        if self.last_retrain_time is None:
            self._retrain_model()
            return
            
        days_since_last_retrain = (datetime.now() - self.last_retrain_time).days
        if days_since_last_retrain >= self.retrain_interval:
            self._retrain_model()
            
    def _retrain_model(self):
        """Retrain the model with feedback data"""
        try:
            if len(self.feedback_data) < self.min_samples:
                logging.info("Not enough feedback data for retraining")
                return
                
            # Convert feedback data to DataFrame
            df = pd.DataFrame(self.feedback_data)
            
            # Prepare features
            X = df['subject'] + ' SUBJECT_END ' + df['message']
            y = df['actual_category']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Load current model
            model_data = load(self.model_path)
            vectorizer = model_data['vectorizer']
            
            # Vectorize text
            X_train_vec = vectorizer.transform(X_train)
            X_test_vec = vectorizer.transform(X_test)
            
            # Train new model
            new_model = RandomForestClassifier(n_estimators=100, random_state=42)
            new_model.fit(X_train_vec, y_train)
            
            # Evaluate new model
            train_score = new_model.score(X_train_vec, y_train)
            test_score = new_model.score(X_test_vec, y_test)
            
            logging.info(f"New model trained - Train score: {train_score:.3f}, Test score: {test_score:.3f}")
            
            # Update model if performance is good
            if test_score > 0.7:  # Only update if test score is good
                model_data['ensemble'] = new_model
                model_data['last_training_time'] = datetime.now()
                
                # Save the updated model
                new_model_path = self.model_path.replace('.joblib', '_v5.joblib')
                dump(model_data, new_model_path)
                
                # Clear feedback data
                self.feedback_data = []
                self.last_retrain_time = datetime.now()
                
                logging.info(f"Model updated successfully and saved to {new_model_path}")
            else:
                logging.warning("New model performance not good enough, keeping old model")
                
        except Exception as e:
            logging.error(f"Error retraining model: {str(e)}")
            
    def get_feedback_stats(self):
        """Get statistics about feedback data"""
        if not self.feedback_data:
            return None
            
        df = pd.DataFrame(self.feedback_data)
        
        stats = {
            'total_feedback': len(df),
            'accuracy': (df['predicted_category'] == df['actual_category']).mean(),
            'avg_confidence': df['confidence'].mean(),
            'category_distribution': df['actual_category'].value_counts().to_dict(),
            'last_retrain_time': self.last_retrain_time
        }
        
        return stats 
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import os
from joblib import dump, load

class ModelFeedbackHandler:
    def __init__(self, model_path, min_samples=100, retrain_interval=7):
        self.model_path = model_path
        self.min_samples = min_samples
        self.retrain_interval = retrain_interval
        self.feedback_data = []
        self.last_retrain_time = None
        
    def add_feedback(self, email_id, subject, message, predicted_category, actual_category, confidence):
        """Add feedback for a prediction"""
        self.feedback_data.append({
            'email_id': email_id,
            'subject': subject,
            'message': message,
            'predicted_category': predicted_category,
            'actual_category': actual_category,
            'confidence': confidence,
            'timestamp': datetime.now()
        })
        
        # Check if we should retrain
        self._check_retraining()
        
    def _check_retraining(self):
        """Check if we should retrain the model"""
        if len(self.feedback_data) < self.min_samples:
            return
            
        if self.last_retrain_time is None:
            self._retrain_model()
            return
            
        days_since_last_retrain = (datetime.now() - self.last_retrain_time).days
        if days_since_last_retrain >= self.retrain_interval:
            self._retrain_model()
            
    def _retrain_model(self):
        """Retrain the model with feedback data"""
        try:
            if len(self.feedback_data) < self.min_samples:
                logging.info("Not enough feedback data for retraining")
                return
                
            # Convert feedback data to DataFrame
            df = pd.DataFrame(self.feedback_data)
            
            # Prepare features
            X = df['subject'] + ' SUBJECT_END ' + df['message']
            y = df['actual_category']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Load current model
            model_data = load(self.model_path)
            vectorizer = model_data['vectorizer']
            
            # Vectorize text
            X_train_vec = vectorizer.transform(X_train)
            X_test_vec = vectorizer.transform(X_test)
            
            # Train new model
            new_model = RandomForestClassifier(n_estimators=100, random_state=42)
            new_model.fit(X_train_vec, y_train)
            
            # Evaluate new model
            train_score = new_model.score(X_train_vec, y_train)
            test_score = new_model.score(X_test_vec, y_test)
            
            logging.info(f"New model trained - Train score: {train_score:.3f}, Test score: {test_score:.3f}")
            
            # Update model if performance is good
            if test_score > 0.7:  # Only update if test score is good
                model_data['ensemble'] = new_model
                model_data['last_training_time'] = datetime.now()
                
                # Save the updated model
                new_model_path = self.model_path.replace('.joblib', '_v5.joblib')
                dump(model_data, new_model_path)
                
                # Clear feedback data
                self.feedback_data = []
                self.last_retrain_time = datetime.now()
                
                logging.info(f"Model updated successfully and saved to {new_model_path}")
            else:
                logging.warning("New model performance not good enough, keeping old model")
                
        except Exception as e:
            logging.error(f"Error retraining model: {str(e)}")
            
    def get_feedback_stats(self):
        """Get statistics about feedback data"""
        if not self.feedback_data:
            return None
            
        df = pd.DataFrame(self.feedback_data)
        
        stats = {
            'total_feedback': len(df),
            'accuracy': (df['predicted_category'] == df['actual_category']).mean(),
            'avg_confidence': df['confidence'].mean(),
            'category_distribution': df['actual_category'].value_counts().to_dict(),
            'last_retrain_time': self.last_retrain_time
        }
        
        return stats 
 
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import os
from joblib import dump, load

class ModelFeedbackHandler:
    def __init__(self, model_path, min_samples=100, retrain_interval=7):
        self.model_path = model_path
        self.min_samples = min_samples
        self.retrain_interval = retrain_interval
        self.feedback_data = []
        self.last_retrain_time = None
        
    def add_feedback(self, email_id, subject, message, predicted_category, actual_category, confidence):
        """Add feedback for a prediction"""
        self.feedback_data.append({
            'email_id': email_id,
            'subject': subject,
            'message': message,
            'predicted_category': predicted_category,
            'actual_category': actual_category,
            'confidence': confidence,
            'timestamp': datetime.now()
        })
        
        # Check if we should retrain
        self._check_retraining()
        
    def _check_retraining(self):
        """Check if we should retrain the model"""
        if len(self.feedback_data) < self.min_samples:
            return
            
        if self.last_retrain_time is None:
            self._retrain_model()
            return
            
        days_since_last_retrain = (datetime.now() - self.last_retrain_time).days
        if days_since_last_retrain >= self.retrain_interval:
            self._retrain_model()
            
    def _retrain_model(self):
        """Retrain the model with feedback data"""
        try:
            if len(self.feedback_data) < self.min_samples:
                logging.info("Not enough feedback data for retraining")
                return
                
            # Convert feedback data to DataFrame
            df = pd.DataFrame(self.feedback_data)
            
            # Prepare features
            X = df['subject'] + ' SUBJECT_END ' + df['message']
            y = df['actual_category']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Load current model
            model_data = load(self.model_path)
            vectorizer = model_data['vectorizer']
            
            # Vectorize text
            X_train_vec = vectorizer.transform(X_train)
            X_test_vec = vectorizer.transform(X_test)
            
            # Train new model
            new_model = RandomForestClassifier(n_estimators=100, random_state=42)
            new_model.fit(X_train_vec, y_train)
            
            # Evaluate new model
            train_score = new_model.score(X_train_vec, y_train)
            test_score = new_model.score(X_test_vec, y_test)
            
            logging.info(f"New model trained - Train score: {train_score:.3f}, Test score: {test_score:.3f}")
            
            # Update model if performance is good
            if test_score > 0.7:  # Only update if test score is good
                model_data['ensemble'] = new_model
                model_data['last_training_time'] = datetime.now()
                
                # Save the updated model
                new_model_path = self.model_path.replace('.joblib', '_v5.joblib')
                dump(model_data, new_model_path)
                
                # Clear feedback data
                self.feedback_data = []
                self.last_retrain_time = datetime.now()
                
                logging.info(f"Model updated successfully and saved to {new_model_path}")
            else:
                logging.warning("New model performance not good enough, keeping old model")
                
        except Exception as e:
            logging.error(f"Error retraining model: {str(e)}")
            
    def get_feedback_stats(self):
        """Get statistics about feedback data"""
        if not self.feedback_data:
            return None
            
        df = pd.DataFrame(self.feedback_data)
        
        stats = {
            'total_feedback': len(df),
            'accuracy': (df['predicted_category'] == df['actual_category']).mean(),
            'avg_confidence': df['confidence'].mean(),
            'category_distribution': df['actual_category'].value_counts().to_dict(),
            'last_retrain_time': self.last_retrain_time
        }
        
        return stats 
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import os
from joblib import dump, load

class ModelFeedbackHandler:
    def __init__(self, model_path, min_samples=100, retrain_interval=7):
        self.model_path = model_path
        self.min_samples = min_samples
        self.retrain_interval = retrain_interval
        self.feedback_data = []
        self.last_retrain_time = None
        
    def add_feedback(self, email_id, subject, message, predicted_category, actual_category, confidence):
        """Add feedback for a prediction"""
        self.feedback_data.append({
            'email_id': email_id,
            'subject': subject,
            'message': message,
            'predicted_category': predicted_category,
            'actual_category': actual_category,
            'confidence': confidence,
            'timestamp': datetime.now()
        })
        
        # Check if we should retrain
        self._check_retraining()
        
    def _check_retraining(self):
        """Check if we should retrain the model"""
        if len(self.feedback_data) < self.min_samples:
            return
            
        if self.last_retrain_time is None:
            self._retrain_model()
            return
            
        days_since_last_retrain = (datetime.now() - self.last_retrain_time).days
        if days_since_last_retrain >= self.retrain_interval:
            self._retrain_model()
            
    def _retrain_model(self):
        """Retrain the model with feedback data"""
        try:
            if len(self.feedback_data) < self.min_samples:
                logging.info("Not enough feedback data for retraining")
                return
                
            # Convert feedback data to DataFrame
            df = pd.DataFrame(self.feedback_data)
            
            # Prepare features
            X = df['subject'] + ' SUBJECT_END ' + df['message']
            y = df['actual_category']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Load current model
            model_data = load(self.model_path)
            vectorizer = model_data['vectorizer']
            
            # Vectorize text
            X_train_vec = vectorizer.transform(X_train)
            X_test_vec = vectorizer.transform(X_test)
            
            # Train new model
            new_model = RandomForestClassifier(n_estimators=100, random_state=42)
            new_model.fit(X_train_vec, y_train)
            
            # Evaluate new model
            train_score = new_model.score(X_train_vec, y_train)
            test_score = new_model.score(X_test_vec, y_test)
            
            logging.info(f"New model trained - Train score: {train_score:.3f}, Test score: {test_score:.3f}")
            
            # Update model if performance is good
            if test_score > 0.7:  # Only update if test score is good
                model_data['ensemble'] = new_model
                model_data['last_training_time'] = datetime.now()
                
                # Save the updated model
                new_model_path = self.model_path.replace('.joblib', '_v5.joblib')
                dump(model_data, new_model_path)
                
                # Clear feedback data
                self.feedback_data = []
                self.last_retrain_time = datetime.now()
                
                logging.info(f"Model updated successfully and saved to {new_model_path}")
            else:
                logging.warning("New model performance not good enough, keeping old model")
                
        except Exception as e:
            logging.error(f"Error retraining model: {str(e)}")
            
    def get_feedback_stats(self):
        """Get statistics about feedback data"""
        if not self.feedback_data:
            return None
            
        df = pd.DataFrame(self.feedback_data)
        
        stats = {
            'total_feedback': len(df),
            'accuracy': (df['predicted_category'] == df['actual_category']).mean(),
            'avg_confidence': df['confidence'].mean(),
            'category_distribution': df['actual_category'].value_counts().to_dict(),
            'last_retrain_time': self.last_retrain_time
        }
        
        return stats 
 
 