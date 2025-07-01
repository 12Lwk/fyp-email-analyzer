"""
Email app ML models package.
"""

from .priority_classifier import EmailPriorityClassifier
from .category_model_loader_v4 import EmailCategoryModelV4

__all__ = ['EmailPriorityClassifier', 'EmailCategoryModelV4'] 