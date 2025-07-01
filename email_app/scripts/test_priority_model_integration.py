import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path so we can import from email_app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from email_app.ai_services.prioritazation.prioritization_service import EmailPrioritizationService

def test_prioritization():
    """Test the prioritization service with sample emails"""
    
    # Initialize the service
    logger.info("Initializing EmailPrioritizationService")
    priority_service = EmailPrioritizationService()

    # Sample emails for testing
    test_emails = [
        {
            "subject": "URGENT: Critical System Failure - Immediate Action Required",
            "body": "The production database is down and affecting all users. Need immediate assistance to restore service. This is causing significant business impact. Please respond ASAP with your availability to help resolve this critical issue.",
            "sender": "admin@company.com",
            "category": "IT Alerts & System Notifications Email",
            "expected_priority": "medium"
        },
        {
            "subject": "Weekly Project Update - Action Items",
            "body": "Here's the status update for Project X. We're on track but need your review of the following items: 1. Updated timeline 2. Resource allocation 3. Budget adjustments. Please provide your feedback by Friday.",
            "sender": "manager@company.com",
            "category": "Work or Business Email",
            "expected_priority": "medium"
        },
        {
            "subject": "Office Party - Save the Date",
            "body": "Just wanted to let you know that we're planning the annual office party for next month. More details will follow soon. Hope you can join us for some fun and relaxation!",
            "sender": "events@company.com",
            "category": "Social Media Email",
            "expected_priority": "low"
        },
        {
            "subject": "Special offer just for you!",
            "body": "Check out these exclusive deals! Limited time only - shop now for great savings on your favorite brands.",
            "sender": "marketing@retailer.com",
            "category": "Promotions or Marketing Email",
            "expected_priority": "low"
        }
    ]

    # Test each email
    for i, email in enumerate(test_emails, 1):
        logger.info(f"\nTesting email #{i}: {email['subject']}")
        
        # Make prediction
        priority, scores, explanation = priority_service.predict_priority(
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"],
            category=email["category"]
        )
        
        # Print results
        logger.info(f"Predicted Priority: {priority}")
        logger.info(f"Expected Priority: {email['expected_priority']}")
        logger.info(f"Confidence Scores: {scores}")
        logger.info(f"Explanation: {explanation}")
        
        # Check if prediction matches expectation
        if priority == email["expected_priority"]:
            logger.info("✓ PASS: Prediction matches expected priority")
        else:
            logger.warning("✗ FAIL: Prediction does not match expected priority")

if __name__ == "__main__":
    test_prioritization() 