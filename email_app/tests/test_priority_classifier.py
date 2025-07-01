import unittest
from email_app.utils.models.priority_classifier import EmailPriorityClassifier

class TestEmailPriorityClassifier(unittest.TestCase):
    def setUp(self):
        """Set up the classifier instance before each test"""
        self.classifier = EmailPriorityClassifier()

    def test_basic_classification(self):
        """Test basic email classification with different priorities"""
        
        # Test Case 1: High Priority Email
        subject_high = "URGENT: Critical Security Issue Needs Immediate Attention"
        body_high = "There has been a security breach that requires immediate action. Please review and respond ASAP. This is a critical issue that needs to be addressed by end of day."
        sender_high = "security@company.com"
        
        priority_high, scores_high, explanation_high = self.classifier.predict_priority(subject_high, body_high, sender_high)
        print("\nTest Case 1 - High Priority:")
        print(f"Priority: {priority_high}")
        print(f"Confidence Scores: {scores_high}")
        print(f"Explanation: {explanation_high}")

        # Test Case 2: Medium Priority Email
        subject_medium = "Project Update: Review Needed by Friday"
        body_medium = "Please review the attached project documents when you have a chance. We need your feedback before the team meeting on Friday."
        sender_medium = "project.manager@company.com"
        
        priority_medium, scores_medium, explanation_medium = self.classifier.predict_priority(subject_medium, body_medium, sender_medium)
        print("\nTest Case 2 - Medium Priority:")
        print(f"Priority: {priority_medium}")
        print(f"Confidence Scores: {scores_medium}")
        print(f"Explanation: {explanation_medium}")

        # Test Case 3: Low Priority Email
        subject_low = "Newsletter: Weekly Company Updates"
        body_low = "Here's your weekly digest of company news and updates. This week's highlights include team building activities and upcoming events."
        sender_low = "newsletter@company.com"
        
        priority_low, scores_low, explanation_low = self.classifier.predict_priority(subject_low, body_low, sender_low)
        print("\nTest Case 3 - Low Priority:")
        print(f"Priority: {priority_low}")
        print(f"Confidence Scores: {scores_low}")
        print(f"Explanation: {explanation_low}")

    def test_edge_cases(self):
        """Test edge cases and potential problematic inputs"""
        
        # Test Case 4: Empty Content
        subject_empty = ""
        body_empty = ""
        sender_empty = "test@company.com"
        
        priority_empty, scores_empty, explanation_empty = self.classifier.predict_priority(subject_empty, body_empty, sender_empty)
        print("\nTest Case 4 - Empty Content:")
        print(f"Priority: {priority_empty}")
        print(f"Confidence Scores: {scores_empty}")
        print(f"Explanation: {explanation_empty}")

        # Test Case 5: Mixed Signals
        subject_mixed = "URGENT: Optional Team Lunch Tomorrow"
        body_mixed = "When you have time, please let us know if you'd like to join the team lunch tomorrow. While not mandatory, it would be great to have everyone there!"
        sender_mixed = "social@company.com"
        
        priority_mixed, scores_mixed, explanation_mixed = self.classifier.predict_priority(subject_mixed, body_mixed, sender_mixed)
        print("\nTest Case 5 - Mixed Signals:")
        print(f"Priority: {priority_mixed}")
        print(f"Confidence Scores: {scores_mixed}")
        print(f"Explanation: {explanation_mixed}")

        # Test Case 6: Automated Sender
        subject_auto = "System Alert: Backup Completed"
        body_auto = "The system backup has been completed successfully. No action required."
        sender_auto = "no-reply@system.com"
        
        priority_auto, scores_auto, explanation_auto = self.classifier.predict_priority(subject_auto, body_auto, sender_auto)
        print("\nTest Case 6 - Automated Sender:")
        print(f"Priority: {priority_auto}")
        print(f"Confidence Scores: {scores_auto}")
        print(f"Explanation: {explanation_auto}")

    def test_feature_extraction(self):
        """Test feature extraction functionality"""
        
        # Test Case 7: Feature Extraction
        subject_test = "URGENT: Project Deadline Tomorrow"
        body_test = "Please review and approve the project deliverables by tomorrow. This is critical for our client meeting."
        
        features = self.classifier.extract_features(subject_test, body_test)
        print("\nTest Case 7 - Feature Extraction:")
        print("Extracted Features:")
        feature_names = [
            "urgency_flag", "risk_flag", "urgency_and_risk",
            "num_action_verbs", "num_uppercase_words", "subject_len",
            "message_len", "combined_len", "has_question",
            "has_deadline", "time_sensitive", "num_words_subject",
            "num_words_message", "informational_flag", "social_flag",
            "optional_flag"
        ]
        for i, name in enumerate(feature_names):
            print(f"{name}: {features[0][i]}")

if __name__ == '__main__':
    unittest.main() 