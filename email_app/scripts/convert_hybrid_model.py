"""
Script to convert a hybrid soft model saved with an older version to a format
compatible with the current scikit-learn and XGBoost versions.
"""

import os
import joblib
import xgboost as xgb
import logging
import warnings
import pickle
import numpy as np
import tempfile
from sklearn.base import BaseEstimator

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

def convert_hybrid_model(input_model_path, output_model_path):
    """
    Convert a hybrid model to a format compatible with the current libraries.
    
    Args:
        input_model_path (str): Path to the original model file
        output_model_path (str): Path where the converted model will be saved
    """
    logger.info(f"Converting hybrid model: {input_model_path} -> {output_model_path}")
    
    try:
        # Try to load the model using joblib with different options
        try:
            logger.info("Attempting to load model with joblib (mmap_mode='r')...")
            model = joblib.load(input_model_path, mmap_mode='r')
            logger.info(f"Successfully loaded model: {type(model)}")
        except Exception as e1:
            logger.warning(f"Failed with mmap_mode='r': {str(e1)}")
            try:
                logger.info("Attempting to load model with regular joblib...")
                model = joblib.load(input_model_path)
                logger.info(f"Successfully loaded model: {type(model)}")
            except Exception as e2:
                logger.warning(f"Failed with regular joblib: {str(e2)}")
                try:
                    # Try with pickle
                    logger.info("Attempting to load model with pickle...")
                    with open(input_model_path, 'rb') as f:
                        model = pickle.load(f)
                    logger.info(f"Successfully loaded model with pickle: {type(model)}")
                except Exception as e3:
                    logger.error(f"All loading attempts failed: {str(e3)}")
                    return False
        
        # Save the model in a compatible format
        logger.info(f"Saving model as {output_model_path}")
        joblib.dump(model, output_model_path, compress=3)
        logger.info("Model saved successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in conversion process: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    # Input and output paths
    model_dir = "email_app/models/ml_models"
    input_path = os.path.join(model_dir, "bert_hybrid_soft_model_new.joblib")
    output_path = os.path.join(model_dir, "bert_hybrid_soft_model_converted.joblib")
    
    # Convert the model
    success = convert_hybrid_model(input_path, output_path)
    
    if success:
        print(f"Model converted successfully to {output_path}")
        print("You can now update your code to use this converted model.")
    else:
        print("Failed to convert the model. Check logs for details.") 