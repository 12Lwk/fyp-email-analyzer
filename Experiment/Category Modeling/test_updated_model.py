import logging
from enhanced_email_categorization_v4 import EnhancedEmailCategorizationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_model():
    # Initialize the model
    config = {
        'model_save_path': 'FYP PART 2/Category Modeling/enhanced_email_categorization_model_v4.joblib'
    }
    
    system = EnhancedEmailCategorizationSystem(config)
    
    # Load the trained model
    system.load_model(config['model_save_path'])
    
    # Test emails with different characteristics
    test_emails = [
        {
            'subject': 'Meeting tomorrow at 2 PM',
            'message': 'Hi team, Let\'s meet tomorrow at 2 PM to discuss the project progress.'
        },
        {
            'subject': 'Urgent: Server downtime notification',
            'message': 'The production server will be down for maintenance tonight from 10 PM to 2 AM.'
        },
        {
            'subject': 'Updated company policies',
            'message': 'Please review the attached document containing updates to our HR policies.'
        },
        {
            'subject': 'Project status update needed',
            'message': 'Could you provide an update on the current project milestones and timeline?'
        },
        {
            'subject': 'Invoice for March services',
            'message': 'Please find attached the invoice for services rendered in March 2024.'
        }
    ]
    
    # Test each email
    for i, email in enumerate(test_emails, 1):
        result = system.predict(email['subject'], email['message'])
        
        print(f"\nTest Email {i}:")
        print(f"Subject: {email['subject']}")
        print(f"Message: {email['message']}")
        print(f"Predicted Category: {result['category']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Relative Confidence: {result['relative_confidence']:.2f}x")
        print("Alternative Categories:")
        for category, prob in result['alternatives']:
            print(f"  - {category}: {prob:.2%}")
        print("-" * 80)

if __name__ == "__main__":
    test_model() 
from enhanced_email_categorization_v4 import EnhancedEmailCategorizationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_model():
    # Initialize the model
    config = {
        'model_save_path': 'FYP PART 2/Category Modeling/enhanced_email_categorization_model_v4.joblib'
    }
    
    system = EnhancedEmailCategorizationSystem(config)
    
    # Load the trained model
    system.load_model(config['model_save_path'])
    
    # Test emails with different characteristics
    test_emails = [
        {
            'subject': 'Meeting tomorrow at 2 PM',
            'message': 'Hi team, Let\'s meet tomorrow at 2 PM to discuss the project progress.'
        },
        {
            'subject': 'Urgent: Server downtime notification',
            'message': 'The production server will be down for maintenance tonight from 10 PM to 2 AM.'
        },
        {
            'subject': 'Updated company policies',
            'message': 'Please review the attached document containing updates to our HR policies.'
        },
        {
            'subject': 'Project status update needed',
            'message': 'Could you provide an update on the current project milestones and timeline?'
        },
        {
            'subject': 'Invoice for March services',
            'message': 'Please find attached the invoice for services rendered in March 2024.'
        }
    ]
    
    # Test each email
    for i, email in enumerate(test_emails, 1):
        result = system.predict(email['subject'], email['message'])
        
        print(f"\nTest Email {i}:")
        print(f"Subject: {email['subject']}")
        print(f"Message: {email['message']}")
        print(f"Predicted Category: {result['category']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Relative Confidence: {result['relative_confidence']:.2f}x")
        print("Alternative Categories:")
        for category, prob in result['alternatives']:
            print(f"  - {category}: {prob:.2%}")
        print("-" * 80)

if __name__ == "__main__":
    test_model() 
 
 
 
 
from enhanced_email_categorization_v4 import EnhancedEmailCategorizationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_model():
    # Initialize the model
    config = {
        'model_save_path': 'FYP PART 2/Category Modeling/enhanced_email_categorization_model_v4.joblib'
    }
    
    system = EnhancedEmailCategorizationSystem(config)
    
    # Load the trained model
    system.load_model(config['model_save_path'])
    
    # Test emails with different characteristics
    test_emails = [
        {
            'subject': 'Meeting tomorrow at 2 PM',
            'message': 'Hi team, Let\'s meet tomorrow at 2 PM to discuss the project progress.'
        },
        {
            'subject': 'Urgent: Server downtime notification',
            'message': 'The production server will be down for maintenance tonight from 10 PM to 2 AM.'
        },
        {
            'subject': 'Updated company policies',
            'message': 'Please review the attached document containing updates to our HR policies.'
        },
        {
            'subject': 'Project status update needed',
            'message': 'Could you provide an update on the current project milestones and timeline?'
        },
        {
            'subject': 'Invoice for March services',
            'message': 'Please find attached the invoice for services rendered in March 2024.'
        }
    ]
    
    # Test each email
    for i, email in enumerate(test_emails, 1):
        result = system.predict(email['subject'], email['message'])
        
        print(f"\nTest Email {i}:")
        print(f"Subject: {email['subject']}")
        print(f"Message: {email['message']}")
        print(f"Predicted Category: {result['category']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Relative Confidence: {result['relative_confidence']:.2f}x")
        print("Alternative Categories:")
        for category, prob in result['alternatives']:
            print(f"  - {category}: {prob:.2%}")
        print("-" * 80)

if __name__ == "__main__":
    test_model() 
from enhanced_email_categorization_v4 import EnhancedEmailCategorizationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_model():
    # Initialize the model
    config = {
        'model_save_path': 'FYP PART 2/Category Modeling/enhanced_email_categorization_model_v4.joblib'
    }
    
    system = EnhancedEmailCategorizationSystem(config)
    
    # Load the trained model
    system.load_model(config['model_save_path'])
    
    # Test emails with different characteristics
    test_emails = [
        {
            'subject': 'Meeting tomorrow at 2 PM',
            'message': 'Hi team, Let\'s meet tomorrow at 2 PM to discuss the project progress.'
        },
        {
            'subject': 'Urgent: Server downtime notification',
            'message': 'The production server will be down for maintenance tonight from 10 PM to 2 AM.'
        },
        {
            'subject': 'Updated company policies',
            'message': 'Please review the attached document containing updates to our HR policies.'
        },
        {
            'subject': 'Project status update needed',
            'message': 'Could you provide an update on the current project milestones and timeline?'
        },
        {
            'subject': 'Invoice for March services',
            'message': 'Please find attached the invoice for services rendered in March 2024.'
        }
    ]
    
    # Test each email
    for i, email in enumerate(test_emails, 1):
        result = system.predict(email['subject'], email['message'])
        
        print(f"\nTest Email {i}:")
        print(f"Subject: {email['subject']}")
        print(f"Message: {email['message']}")
        print(f"Predicted Category: {result['category']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Relative Confidence: {result['relative_confidence']:.2f}x")
        print("Alternative Categories:")
        for category, prob in result['alternatives']:
            print(f"  - {category}: {prob:.2%}")
        print("-" * 80)

if __name__ == "__main__":
    test_model() 
 
 
 
 
from enhanced_email_categorization_v4 import EnhancedEmailCategorizationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_model():
    # Initialize the model
    config = {
        'model_save_path': 'FYP PART 2/Category Modeling/enhanced_email_categorization_model_v4.joblib'
    }
    
    system = EnhancedEmailCategorizationSystem(config)
    
    # Load the trained model
    system.load_model(config['model_save_path'])
    
    # Test emails with different characteristics
    test_emails = [
        {
            'subject': 'Meeting tomorrow at 2 PM',
            'message': 'Hi team, Let\'s meet tomorrow at 2 PM to discuss the project progress.'
        },
        {
            'subject': 'Urgent: Server downtime notification',
            'message': 'The production server will be down for maintenance tonight from 10 PM to 2 AM.'
        },
        {
            'subject': 'Updated company policies',
            'message': 'Please review the attached document containing updates to our HR policies.'
        },
        {
            'subject': 'Project status update needed',
            'message': 'Could you provide an update on the current project milestones and timeline?'
        },
        {
            'subject': 'Invoice for March services',
            'message': 'Please find attached the invoice for services rendered in March 2024.'
        }
    ]
    
    # Test each email
    for i, email in enumerate(test_emails, 1):
        result = system.predict(email['subject'], email['message'])
        
        print(f"\nTest Email {i}:")
        print(f"Subject: {email['subject']}")
        print(f"Message: {email['message']}")
        print(f"Predicted Category: {result['category']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Relative Confidence: {result['relative_confidence']:.2f}x")
        print("Alternative Categories:")
        for category, prob in result['alternatives']:
            print(f"  - {category}: {prob:.2%}")
        print("-" * 80)

if __name__ == "__main__":
    test_model() 
from enhanced_email_categorization_v4 import EnhancedEmailCategorizationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_model():
    # Initialize the model
    config = {
        'model_save_path': 'FYP PART 2/Category Modeling/enhanced_email_categorization_model_v4.joblib'
    }
    
    system = EnhancedEmailCategorizationSystem(config)
    
    # Load the trained model
    system.load_model(config['model_save_path'])
    
    # Test emails with different characteristics
    test_emails = [
        {
            'subject': 'Meeting tomorrow at 2 PM',
            'message': 'Hi team, Let\'s meet tomorrow at 2 PM to discuss the project progress.'
        },
        {
            'subject': 'Urgent: Server downtime notification',
            'message': 'The production server will be down for maintenance tonight from 10 PM to 2 AM.'
        },
        {
            'subject': 'Updated company policies',
            'message': 'Please review the attached document containing updates to our HR policies.'
        },
        {
            'subject': 'Project status update needed',
            'message': 'Could you provide an update on the current project milestones and timeline?'
        },
        {
            'subject': 'Invoice for March services',
            'message': 'Please find attached the invoice for services rendered in March 2024.'
        }
    ]
    
    # Test each email
    for i, email in enumerate(test_emails, 1):
        result = system.predict(email['subject'], email['message'])
        
        print(f"\nTest Email {i}:")
        print(f"Subject: {email['subject']}")
        print(f"Message: {email['message']}")
        print(f"Predicted Category: {result['category']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Relative Confidence: {result['relative_confidence']:.2f}x")
        print("Alternative Categories:")
        for category, prob in result['alternatives']:
            print(f"  - {category}: {prob:.2%}")
        print("-" * 80)

if __name__ == "__main__":
    test_model() 
 
 
 
 
from enhanced_email_categorization_v4 import EnhancedEmailCategorizationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_model():
    # Initialize the model
    config = {
        'model_save_path': 'FYP PART 2/Category Modeling/enhanced_email_categorization_model_v4.joblib'
    }
    
    system = EnhancedEmailCategorizationSystem(config)
    
    # Load the trained model
    system.load_model(config['model_save_path'])
    
    # Test emails with different characteristics
    test_emails = [
        {
            'subject': 'Meeting tomorrow at 2 PM',
            'message': 'Hi team, Let\'s meet tomorrow at 2 PM to discuss the project progress.'
        },
        {
            'subject': 'Urgent: Server downtime notification',
            'message': 'The production server will be down for maintenance tonight from 10 PM to 2 AM.'
        },
        {
            'subject': 'Updated company policies',
            'message': 'Please review the attached document containing updates to our HR policies.'
        },
        {
            'subject': 'Project status update needed',
            'message': 'Could you provide an update on the current project milestones and timeline?'
        },
        {
            'subject': 'Invoice for March services',
            'message': 'Please find attached the invoice for services rendered in March 2024.'
        }
    ]
    
    # Test each email
    for i, email in enumerate(test_emails, 1):
        result = system.predict(email['subject'], email['message'])
        
        print(f"\nTest Email {i}:")
        print(f"Subject: {email['subject']}")
        print(f"Message: {email['message']}")
        print(f"Predicted Category: {result['category']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Relative Confidence: {result['relative_confidence']:.2f}x")
        print("Alternative Categories:")
        for category, prob in result['alternatives']:
            print(f"  - {category}: {prob:.2%}")
        print("-" * 80)

if __name__ == "__main__":
    test_model() 
from enhanced_email_categorization_v4 import EnhancedEmailCategorizationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_model():
    # Initialize the model
    config = {
        'model_save_path': 'FYP PART 2/Category Modeling/enhanced_email_categorization_model_v4.joblib'
    }
    
    system = EnhancedEmailCategorizationSystem(config)
    
    # Load the trained model
    system.load_model(config['model_save_path'])
    
    # Test emails with different characteristics
    test_emails = [
        {
            'subject': 'Meeting tomorrow at 2 PM',
            'message': 'Hi team, Let\'s meet tomorrow at 2 PM to discuss the project progress.'
        },
        {
            'subject': 'Urgent: Server downtime notification',
            'message': 'The production server will be down for maintenance tonight from 10 PM to 2 AM.'
        },
        {
            'subject': 'Updated company policies',
            'message': 'Please review the attached document containing updates to our HR policies.'
        },
        {
            'subject': 'Project status update needed',
            'message': 'Could you provide an update on the current project milestones and timeline?'
        },
        {
            'subject': 'Invoice for March services',
            'message': 'Please find attached the invoice for services rendered in March 2024.'
        }
    ]
    
    # Test each email
    for i, email in enumerate(test_emails, 1):
        result = system.predict(email['subject'], email['message'])
        
        print(f"\nTest Email {i}:")
        print(f"Subject: {email['subject']}")
        print(f"Message: {email['message']}")
        print(f"Predicted Category: {result['category']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Relative Confidence: {result['relative_confidence']:.2f}x")
        print("Alternative Categories:")
        for category, prob in result['alternatives']:
            print(f"  - {category}: {prob:.2%}")
        print("-" * 80)

if __name__ == "__main__":
    test_model() 
 
 
 
 
 