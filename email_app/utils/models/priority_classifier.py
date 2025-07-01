import re
from typing import Dict, Tuple, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailPriorityClassifier:
    """
    A classifier for determining email priority based on subject, body, and sender.
    Current implementation uses simple rule-based heuristics, can be replaced with ML model.
    """
    
    def __init__(self):
        """Initialize the classifier with priority keywords"""
        # Priority indication keywords
        self.high_priority_keywords = [
            'urgent', 'immediate', 'asap', 'important', 'critical', 'deadline',
            'emergency', 'priority', 'attention', 'required', 'action', 'needed',
            'alert', 'warning', 'high priority', 'time-sensitive', 'crucial',
            'vital', 'essential', 'mandatory', 'due today', 'due tomorrow',
            'overdue', 'escalation', 'expedite', 'rush', 'now', 'immediately',
            'security breach', 'system down', 'outage', 'failure', 'error'
        ]
        
        self.medium_priority_keywords = [
            'update', 'review', 'please', 'request', 'follow up', 'reminder',
            'meeting', 'status', 'report', 'question', 'feedback', 'respond',
            'information', 'confirm', 'schedule', 'approve', 'review needed',
            'pending', 'waiting', 'response needed', 'task', 'project update',
            'decision needed', 'input needed', 'discussion', 'coordination',
            'planning', 'preparation', 'upcoming', 'next week', 'soon'
        ]
        
        # Low priority categories
        self.low_priority_categories = [
            'Spam Email',
            'Promotions or Marketing Email',
            'Social Media Email'
        ]
        
        # Compile regex patterns for faster matching
        self.high_pattern = re.compile(r'\b(' + '|'.join(self.high_priority_keywords) + r')\b', re.IGNORECASE)
        self.medium_pattern = re.compile(r'\b(' + '|'.join(self.medium_priority_keywords) + r')\b', re.IGNORECASE)
    
    def predict_priority(self, subject: str, body: str, sender: str, category: str = None) -> Tuple[str, Dict[str, float], Optional[List[str]]]:
        """
        Predict email priority based on subject, body, and sender.
        
        Args:
            subject: Email subject
            body: Email body or snippet
            sender: Email sender
            category: Email category (e.g., 'Spam Email', 'Promotions or Marketing Email', 'Social Media Email')
            
        Returns:
            tuple: (priority label, confidence scores dict, matched keywords)
            
        Raises:
            ValueError: If inputs are invalid
        """
        try:
            # Check for low priority categories first
            if category and category in self.low_priority_categories:
                logger.info(f"Email categorized as {category}, setting priority to LOW")
                return "LOW", {"LOW": 1.0, "MEDIUM": 0.0, "HIGH": 0.0}, None
            
            # Convert inputs to strings and handle None values
            subject = str(subject) if subject else ""
            body = str(body) if body else ""
            sender = str(sender) if sender else ""
            
            if not subject and not body:
                logger.warning("Empty subject and body provided")
                return "LOW", {"LOW": 0.5}, None
            
            # Combine text for analysis with higher weight for subject
            text = f"{subject} {subject} {body}"  # Double weight for subject
            
            # Count keyword matches
            high_matches = len(self.high_pattern.findall(text))
            medium_matches = len(self.medium_pattern.findall(text))
            
            # Calculate priority scores with adjusted weights
            high_score = min(0.9, high_matches * 0.4)  # Increased from 0.3
            medium_score = min(0.7, medium_matches * 0.25)  # Increased from 0.2
            low_score = 0.3  # Reduced from 0.5 to make it easier for other priorities
            
            # Additional score for subject-line matches
            subject_high_matches = len(self.high_pattern.findall(subject))
            subject_medium_matches = len(self.medium_pattern.findall(subject))
            high_score += min(0.2, subject_high_matches * 0.1)  # Extra weight for subject matches
            medium_score += min(0.2, subject_medium_matches * 0.1)
            
            # Determine priority based on highest score
            scores = {
                "HIGH": high_score,
                "MEDIUM": medium_score,
                "LOW": low_score
            }
            
            # Get priority with highest score
            priority = max(scores, key=scores.get)
            
            # For debugging purposes, collect matched keywords
            matched_keywords = None
            if high_matches > 0 or medium_matches > 0:
                matched_keywords = []
                if high_matches > 0:
                    matched_keywords.extend(self.high_pattern.findall(text))
                if medium_matches > 0:
                    matched_keywords.extend(self.medium_pattern.findall(text))
            
            logger.debug(f"Priority prediction: {priority} with scores {scores}")
            return priority, scores, matched_keywords
            
        except Exception as e:
            logger.error(f"Error in priority prediction: {str(e)}")
            return "LOW", {"LOW": 0.5}, None
