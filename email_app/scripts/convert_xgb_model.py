"""
Script to convert an XGBoost model saved with an older version to a format
compatible with XGBoost 3.0.0.
"""

import os
import joblib
import xgboost as xgb
import logging
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings('ignore', category=UserWarning)

def convert_xgb_model(input_model_path, output_model_path):
    """
    Convert an XGBoost model to a format compatible with the current XGBoost version.
    
    Args:
        input_model_path (str): Path to the original model file
        output_model_path (str): Path where the converted model will be saved
    """
    logger.info(f"Converting model: {input_model_path} -> {output_model_path}")
    
    try:
        # Try to load the model using joblib
        logger.info("Attempting to load model with joblib...")
        model = joblib.load(input_model_path)
        
        # Check if it's an XGBoost model
        if hasattr(model, 'save_model'):
            # It's an XGBClassifier or similar
            logger.info("Model appears to be an XGBClassifier")
            model.save_model(output_model_path)
            logger.info(f"Successfully saved model to {output_model_path}")
            return True
        elif isinstance(model, xgb.Booster):
            # It's a Booster
            logger.info("Model appears to be a Booster")
            model.save_model(output_model_path)
            logger.info(f"Successfully saved model to {output_model_path}")
            return True
        else:
            logger.warning(f"Model is not an XGBoost model: {type(model)}")
            # Try to save it with joblib anyway
            joblib.dump(model, output_model_path)
            logger.info(f"Saved model with joblib to {output_model_path}")
            return True
    
    except Exception as e:
        logger.error(f"Error loading model with joblib: {str(e)}")
        
        try:
            # Try loading directly as a Booster
            logger.info("Attempting to load as XGBoost Booster...")
            model = xgb.Booster()
            model.load_model(input_model_path)
            model.save_model(output_model_path)
            logger.info(f"Successfully saved Booster to {output_model_path}")
            return True
        except Exception as e2:
            logger.error(f"Error loading as Booster: {str(e2)}")
            
            try:
                # Try loading as XGBClassifier
                logger.info("Attempting to load as XGBClassifier...")
                model = xgb.XGBClassifier()
                model.load_model(input_model_path)
                model.save_model(output_model_path)
                logger.info(f"Successfully saved XGBClassifier to {output_model_path}")
                return True
            except Exception as e3:
                logger.error(f"Error loading as XGBClassifier: {str(e3)}")
    
    logger.error("All conversion attempts failed.")
    return False

if __name__ == "__main__":
    # Input and output paths
    model_dir = "email_app/models/ml_models"
    input_path = os.path.join(model_dir, "bert_xgb_model.joblib")
    output_path = os.path.join(model_dir, "bert_xgb_model_converted.json")
    
    # Convert the model
    success = convert_xgb_model(input_path, output_path)
    
    if success:
        print(f"Model converted successfully to {output_path}")
        print("You can now update your code to use this converted model.")
    else:
        print("Failed to convert the model. Check logs for details.") 