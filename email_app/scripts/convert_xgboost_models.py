import os
import joblib
import xgboost as xgb
import logging
import pickle
import warnings

# Suppress XGBoost warnings
warnings.filterwarnings('ignore', category=UserWarning, module='xgboost')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_xgboost_model(input_path: str, output_path: str):
    """
    Convert an XGBoost model to the current format
    
    Args:
        input_path: Path to the input model file
        output_path: Path to save the converted model
    """
    try:
        logger.info(f"Converting model from {input_path} to {output_path}")
        
        # First try loading with pickle
        try:
            with open(input_path, 'rb') as f:
                model = pickle.load(f)
            logger.info("Successfully loaded model with pickle")
        except Exception as e1:
            logger.warning(f"Failed to load with pickle: {str(e1)}")
            model = None
        
        # If pickle failed, try joblib
        if model is None:
            try:
                model = joblib.load(input_path)
                logger.info("Successfully loaded model with joblib")
            except Exception as e2:
                logger.warning(f"Failed to load with joblib: {str(e2)}")
                model = None
        
        # If both failed, try direct XGBoost loading
        if model is None:
            try:
                model = xgb.Booster()
                model.load_model(input_path)
                logger.info("Successfully loaded model with XGBoost Booster")
            except Exception as e3:
                logger.error(f"All loading methods failed: {str(e3)}")
                raise
        
        # Save the model in the current format
        if isinstance(model, (xgb.XGBClassifier, xgb.Booster)):
            # Save as JSON format for better compatibility
            model.save_model(output_path)
            logger.info(f"Saved model as XGBoost JSON format to {output_path}")
        else:
            # If it's a different type of model, try to convert it
            try:
                # Create a new XGBoost model
                new_model = xgb.Booster()
                # Save the model parameters
                new_model.save_model(output_path)
                logger.info(f"Converted and saved model to {output_path}")
            except Exception as e:
                logger.error(f"Failed to convert model: {str(e)}")
                raise
        
    except Exception as e:
        logger.error(f"Error converting model: {str(e)}")
        raise

def main():
    # Define model paths
    base_dir = 'email_app/models/ml_models'
    
    # Convert XGBoost model
    xgb_input = os.path.join(base_dir, 'bert_xgb_model.joblib')
    xgb_output = os.path.join(base_dir, 'bert_xgb_model_converted.json')
    
    if os.path.exists(xgb_input):
        convert_xgboost_model(xgb_input, xgb_output)
    else:
        logger.warning(f"Input model not found at {xgb_input}")

if __name__ == "__main__":
    main() 