import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Load environment variables
    load_dotenv()

    # Get API key
    api_key = os.getenv('GOOGLE_API_KEY', '').strip()
    if not api_key:
        logger.error("GOOGLE_API_KEY environment variable not set")
        return

    # Configure Gemini
    genai.configure(api_key=api_key)

    # List available models
    try:
        models = genai.list_models()
        logger.info("Available models:")
        for model in models:
            logger.info(f"- {model.name}")
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")

if __name__ == "__main__":
    main()