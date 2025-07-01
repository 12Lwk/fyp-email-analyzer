import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'test-key-not-for-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'email_app',
]

# LLM Settings
HF_API_KEY = os.environ.get("HF_API_KEY", "")
LLM_PROVIDER = "huggingface"
LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "mistral" 