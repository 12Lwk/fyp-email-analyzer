import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import string
from faker import Faker
import os
from textblob import TextBlob

# Initialize Faker for realistic data
fake = Faker()

# Categories and their variations
CATEGORIES = {
    'Work or Business Email': {
        'subjects': [
            'Project Update: {project_name}',
            'Business Proposal: {company_name}',
            'Client Meeting Follow-up',
            'Quarterly Report Review',
            'Team Collaboration Request',
            'Business Development Opportunity',
            'Contract Review Needed',
            'Strategic Planning Session',
            'Market Analysis Report',
            'Business Partnership Discussion',
            'Urgent: Client Deliverable Due',
            'Project Timeline Update',
            'Budget Approval Required',
            'Team Performance Review',
            'Sales Pipeline Update',
            'Vendor Contract Renewal',
            'Important: Project Milestone',
            'Resource Allocation Request',
            'Client Feedback Summary',
            'Urgent: Project Deadline'
        ]
    },
    'Promotions or Marketing Email': {
        'subjects': [
            'Last Day: {discount}% Off Everything',
            'Flash Sale: Up to {discount}% Off',
            'Members Only: Early Access Sale',
            'Special Offer Just For You',
            'Don\'t Miss Out: {product_name} Launch',
            '🎉 Exclusive Deal Inside',
            'Your Special Discount Code Inside',
            'Last Chance: Sale Ends Tonight',
            'New Arrival: {product_name}',
            'Weekend Special: Extra {discount}% Off',
            'Black Friday Deals Start Now',
            'Cyber Monday: Biggest Sale Ever',
            'Prime Day Exclusive Offers',
            'Holiday Season Special Deals',
            'Birthday Reward: Special Gift Inside'
        ]
    },
    'Legal & Contractual Email': {
        'subjects': [
            'Contract Review: {contract_name}',
            'Legal Notice: {matter_name}',
            'Agreement Amendment Request',
            'Compliance Update Required',
            'Legal Documentation Request',
            'Important: Terms of Service Update',
            'Contract Termination Notice',
            'Legal Compliance Deadline',
            'Urgent: Legal Action Required',
            'Policy Update Confirmation',
            'Regulatory Compliance Alert',
            'Legal Document Submission',
            'Contract Renewal Notice',
            'Important: Legal Deadline',
            'Compliance Training Required'
        ]
    },
    'Personal Email': {
        'subjects': [
            'Family Gathering Plans',
            'Weekend Get-together',
            'Happy Birthday Wishes!',
            'Vacation Planning Details',
            'Personal Update',
            'Coffee Catch-up?',
            'Dinner Plans Tonight',
            'Holiday Celebration Details',
            'Thank You Note',
            'Congratulations!',
            'Get Well Soon Wishes',
            'Wedding Invitation',
            'Baby Shower Details',
            'Housewarming Party',
            'Graduation Celebration'
        ]
    },
    'Meeting & Schedule Email': {
        'subjects': [
            'Meeting Invitation: {meeting_topic}',
            'Schedule Update: {event_name}',
            'Team Meeting: {meeting_name}',
            'Urgent Meeting Request',
            'Meeting Rescheduled',
            'Calendar Invite: Project Review',
            'Quick Sync-up Required',
            'Workshop Schedule Update',
            'Training Session Details',
            'Conference Call Information',
            'Board Meeting Schedule',
            'Client Meeting Confirmation',
            'Team Building Event',
            'Quarterly Review Meeting',
            'Annual Planning Session'
        ]
    },
    'Internal Policies & HR Updates Email': {
        'subjects': [
            'Important: Policy Update',
            'HR Announcement: Benefits Change',
            'New Employee Guidelines',
            'Company Policy Revision',
            'Urgent: Safety Protocol Update',
            'Employee Handbook Updates',
            'Benefits Enrollment Period',
            'Important: Leave Policy Change',
            'Workplace Guidelines Update',
            'HR: Performance Review Process',
            'Company Holiday Schedule',
            'Training Requirement Update',
            'Office Closure Notice',
            'COVID-19 Protocol Update',
            'Workplace Safety Alert'
        ]
    },
    'Social Media Email': {
        'subjects': [
            'New LinkedIn Connection Requests',
            'Your Post is Trending!',
            'Instagram: New Followers Alert',
            'Twitter: Engagement Summary',
            'Facebook: Friend Request Update',
            'LinkedIn: Profile Views Update',
            'Your Content is Going Viral',
            'Weekly Social Media Summary',
            'Instagram Story Highlights',
            'Twitter: Trending in Your Network',
            'LinkedIn: Job Recommendations',
            'Facebook: Event Invitations',
            'Instagram: Live Stream Alert',
            'Social Media Milestone Reached',
            'Your Network is Growing!'
        ]
    },
    'Finance & Transaction Email': {
        'subjects': [
            'Transaction Alert: RM{amount}',
            'Payment Confirmation #{reference}',
            'Invoice Due Reminder',
            'Statement Available Online',
            'Urgent: Payment Required',
            'Credit Card Transaction Alert',
            'Bank Statement Available',
            'Investment Portfolio Update',
            'Tax Document Available',
            'Payment Overdue Notice',
            'Direct Debit Notification',
            'Suspicious Transaction Alert',
            'Account Balance Update',
            'Investment Opportunity',
            'Loan Payment Reminder'
        ]
    },
    'IT Alerts & System Notifications Email': {
        'subjects': [
            'Urgent: Security Update Required',
            'System Maintenance Notice',
            'Password Reset Required',
            'Account Security Alert',
            'Network Outage Notice',
            'Critical System Update',
            'Server Maintenance Schedule',
            'Software Update Available',
            'Security Breach Alert',
            'System Access Update',
            'Database Maintenance Alert',
            'Emergency System Shutdown',
            'Network Security Update',
            'System Upgrade Required',
            'IT Support Ticket Update'
        ]
    },
    'Spam Email': {
        'subjects': [
            'CONGRATULATIONS! You\'ve Won!',
            'Urgent: Account Verification',
            'Your Prize is Waiting',
            'Limited Time Offer!!!',
            'Make Money Fast!',
            'You\'re Our Lucky Winner',
            'Inheritance Claim Notice',
            'Account Access Required',
            'Investment Opportunity!!!',
            'Lottery Winner Alert!!!',
            'Unclaimed Money Waiting',
            'Your Account Will Be Suspended',
            'Special One-Time Offer',
            'Urgent Response Required!!!',
            'Your Payment is Pending'
        ]
    },
    'Utilities Bill Email': {
        'subjects': [
            'TNB: Your Monthly Bill',
            'Water Bill Payment Due',
            'TM UniFi: Bill Ready',
            'Maxis: Monthly Statement',
            'Gas Bill Payment Reminder',
            'Utility Service Notice',
            'Important: Service Update',
            'Billing Cycle Change Notice',
            'Service Interruption Alert',
            'Payment Confirmation',
            'Usage Statement Available',
            'Account Statement Ready',
            'Service Plan Update',
            'Urgent: Payment Required',
            'Important: Service Notice'
        ]
    }
}

# Priority levels and their weights
PRIORITIES = {
    'High': 0.2,
    'Medium': 0.5,
    'Low': 0.3
}

def generate_random_data():
    """Generate random data for email templates"""
    data = {
        'name': fake.name(),
        'sender_name': fake.name(),
        'project_name': fake.catch_phrase(),
        'company_name': fake.company(),
        'specific_area': fake.word(),
        'duration': f"{random.randint(15, 120)} minutes",
        'milestone1': fake.sentence(),
        'milestone2': fake.sentence(),
        'milestone3': fake.sentence(),
        'product_name': fake.word(),
        'discount': random.randint(10, 50),
        'feature1': fake.word(),
        'feature2': fake.word(),
        'feature3': fake.word(),
        'promo_code': ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
        'end_date': (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
        'benefit1': fake.word(),
        'benefit2': fake.word(),
        'benefit3': fake.word(),
        'contract_name': fake.word(),
        'matter_name': fake.word(),
        'deadline': (datetime.now() + timedelta(days=random.randint(1, 14))).strftime('%Y-%m-%d'),
        'point1': fake.sentence(),
        'point2': fake.sentence(),
        'point3': fake.sentence(),
        'phone': fake.phone_number(),
        'contract_type': fake.word(),
        'effective_date': (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
        'change1': fake.sentence(),
        'change2': fake.sentence(),
        'change3': fake.sentence(),
        'topic': fake.word(),
        'personal_update': fake.paragraph(),
        'personal_message': fake.paragraph(),
        'meeting_name': fake.word(),
        'meeting_topic': fake.word(),  # Added for meeting subjects
        'event_name': fake.word(),     # Added for schedule subjects
        'date': (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
        'time': f"{random.randint(9, 17)}:00",
        'agenda1': fake.sentence(),
        'agenda2': fake.sentence(),
        'agenda3': fake.sentence(),
        'location': fake.word(),
        'meeting_id': ''.join(random.choices(string.digits, k=10)),
        'password': ''.join(random.choices(string.ascii_letters + string.digits, k=8)),
        'meeting_link': fake.url(),
        'policy_name': fake.word(),
        'update1': fake.sentence(),
        'update2': fake.sentence(),
        'update3': fake.sentence(),
        'time_period': fake.word(),
        'engagement_rate': random.uniform(1, 10),
        'reach_count': random.randint(1000, 10000),
        'growth_rate': random.uniform(1, 5),
        'highlight1': fake.sentence(),
        'highlight2': fake.sentence(),
        'highlight3': fake.sentence(),
        'month': fake.month_name(),
        'theme1': fake.word(),
        'theme2': fake.word(),
        'theme3': fake.word(),
        'amount': random.uniform(10, 1000),
        'reference': ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
        'status': random.choice(['Completed', 'Pending', 'Failed']),
        'invoice_number': ''.join(random.choices(string.digits, k=8)),
        'due_date': (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
        'payment_method': random.choice(['Credit Card', 'Bank Transfer', 'PayPal']),
        'version': f"{random.randint(1, 10)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
        'size': f"{random.randint(10, 1000)}MB",
        'spam_link': fake.url(),
        'prize': random.choice(['$1000', 'iPhone', 'Laptop', 'Vacation Package']),
        'product': fake.word(),        # Added for spam subjects
        'utility': random.choice(['Electricity', 'Water', 'Gas', 'Internet']),
        'account_number': ''.join(random.choices(string.digits, k=10)),
        'usage': f"{random.randint(100, 1000)} {random.choice(['kWh', 'gallons', 'cubic feet', 'GB'])}",
        'product_category': fake.word() # Added for promotions
    }
    return data

def generate_random_paragraph():
    """Generate a random, natural-sounding paragraph"""
    templates = [
        f"As discussed in our previous conversation, {fake.sentence()} In light of this, {fake.sentence()} {fake.sentence()}",
        f"I hope you're doing well. {fake.sentence()} {fake.sentence()} Let me know your thoughts on this.",
        f"Following up on {fake.word()}, {fake.sentence()} {fake.sentence()} This means that {fake.sentence()}",
        f"I wanted to bring to your attention that {fake.sentence()} {fake.sentence()} As a result, {fake.sentence()}",
        f"Thank you for your {fake.word()}. {fake.sentence()} {fake.sentence()} Moving forward, {fake.sentence()}"
    ]
    return random.choice(templates)

def generate_email_body(category, data, style):
    """Generate unique email body based on category and writing style"""
    
    def add_typos(text, probability=0.1):
        """Add realistic typos to text"""
        common_typos = {
            'the': ['teh', 'th', 'thee'],
            'and': ['adn', 'andd', 'nad'],
            'your': ['youre', 'yur', 'yor'],
            'please': ['plz', 'pls', 'plese'],
            'would': ['woud', 'wuld', 'wld'],
            'could': ['coud', 'culd', 'cld'],
            'their': ['thier', 'ther', 'thir'],
            'receive': ['recieve', 'receve', 'receiv'],
            'business': ['busines', 'bussiness', 'bisness'],
            'immediately': ['immediatly', 'imediately', 'immedietly']
        }
        
        words = text.split()
        for i, word in enumerate(words):
            if random.random() < probability and word.lower() in common_typos:
                words[i] = random.choice(common_typos[word.lower()])
        return ' '.join(words)

    def generate_personal_content():
        contexts = [
            f"I've been meaning to tell you about {fake.sentence()} It's been quite an experience, and {fake.sentence()}",
            f"You won't believe what happened {fake.sentence()} The funny thing is, {fake.sentence()}",
            f"Remember when we talked about {fake.word()}? Well, {fake.sentence()} {fake.sentence()}",
            f"I was thinking about our last conversation about {fake.word()}, and {fake.sentence()}"
        ]
        return random.choice(contexts) + "\n\n" + generate_random_paragraph()

    def generate_business_content():
        project_contexts = [
            f"After reviewing the latest metrics for {data['project_name']}, {fake.sentence()} The key findings indicate that {fake.sentence()}",
            f"The team has made significant progress on {data['project_name']}. {fake.sentence()} However, we've identified some challenges: {fake.sentence()}",
            f"I wanted to provide a comprehensive update on {data['project_name']}. {fake.sentence()} Our next steps include {fake.sentence()}"
        ]
        return random.choice(project_contexts) + "\n\n" + generate_random_paragraph()

    def generate_marketing_content():
        marketing_hooks = [
            f"🌟 We've got something special just for you! {fake.sentence()} Don't miss out on this exclusive opportunity to {fake.sentence()}",
            f"As a valued customer, we're excited to share {fake.sentence()} Plus, {fake.sentence()}",
            f"Get ready for our biggest sale yet! {fake.sentence()} But that's not all - {fake.sentence()}"
        ]
        return random.choice(marketing_hooks) + "\n\n" + generate_random_paragraph()

    # Category-specific content templates with more natural variations
    templates = {
        'Work or Business Email': [
            lambda: f"{generate_business_content()}\n\nKey Action Items:\n1. {fake.sentence()}\n2. {fake.sentence()}\n3. {fake.sentence()}\n\nPlease review and provide your feedback by {data['deadline']}.",
            lambda: f"I hope this email finds you well.\n\n{generate_business_content()}\n\nCould we schedule a quick call to discuss these points in detail?",
            lambda: f"Following our discussion about {data['project_name']},\n\n{generate_business_content()}\n\nI've attached the relevant documents for your review."
        ],
        
        'Promotions or Marketing Email': [
            lambda: f"{generate_marketing_content()}\n\nHere's what's included:\n• {fake.sentence()}\n• {fake.sentence()}\n• {fake.sentence()}\n\nOffer ends {data['end_date']}!",
            lambda: f"🎉 Exclusive Offer Inside!\n\n{generate_marketing_content()}\n\nUse code {data['promo_code']} at checkout to claim your discount.",
            lambda: f"Don't miss out on this amazing deal!\n\n{generate_marketing_content()}\n\nLimited time offer - Act fast!"
        ],
        
        'Personal Email': [
            lambda: f"{generate_personal_content()}\n\nWould love to hear your thoughts on this.",
            lambda: f"Hey there!\n\n{generate_personal_content()}\n\nLet's catch up soon!",
            lambda: f"I've been meaning to write to you.\n\n{generate_personal_content()}\n\nHow have you been?"
        ],
        
        'Legal & Contractual Email': [
            lambda: f"This email serves as formal notice regarding the {data['contract_name']} agreement.\n\n{generate_random_paragraph()}\n\nPlease note the following critical points:\n\n1. {fake.sentence()}\n2. {fake.sentence()}\n3. {fake.sentence()}\n\nKindly acknowledge receipt and compliance with these terms.",
            lambda: f"Important Legal Update\n\n{generate_random_paragraph()}\n\nRequired Actions:\n1. {fake.sentence()}\n2. {fake.sentence()}\n\nPlease ensure completion by {data['deadline']}."
        ]
    }

    # Get template based on category
    category_templates = templates.get(category, [lambda: generate_random_paragraph()])
    content = random.choice(category_templates)()

    # Add some natural variation based on style
    if style['formality'] == 'casual':
        content = add_typos(content, probability=0.05)
    
    if style['length'] == 'long':
        content += f"\n\n{generate_random_paragraph()}"
    elif style['length'] == 'short':
        content = content.split('\n\n')[0]

    # Add contextual variations
    variations = [
        f"\n\nBy the way, {fake.sentence()}",
        f"\n\nOne more thing: {fake.sentence()}",
        f"\n\nP.S. {fake.sentence()}",
        f"\n\nAlso, {fake.sentence()}"
    ]
    
    if random.random() < 0.3:  # 30% chance to add a variation
        content += random.choice(variations)

    # Format the email
    email = f"{style['greeting']} {data['name']},\n\n{content}\n\n{style['closing']},\n{data['sender_name']}"
    
    # Add common email elements randomly
    if random.random() < 0.2:  # 20% chance to add a confidentiality notice
        email += "\n\nCONFIDENTIALITY NOTICE: This email and any attachments are confidential and may be privileged..."
    
    if random.random() < 0.15:  # 15% chance to add a signature
        email += f"\n\n--\n{data['sender_name']}\n{data['company_name']}\nPhone: {data['phone']}"
    
    return email

def generate_unique_writing_style():
    """Generate unique writing style variations"""
    return {
        'formality': random.choice(['formal', 'semi-formal', 'casual']),
        'tone': random.choice(['professional', 'friendly', 'urgent', 'informative', 'persuasive', 'concerned', 'enthusiastic']),
        'structure': random.choice(['direct', 'narrative', 'bullet-points', 'mixed']),
        'length': random.choices(['short', 'medium', 'long'], weights=[0.2, 0.5, 0.3])[0],
        'greeting': random.choice([
            'Dear', 'Hello', 'Hi', 'Greetings', 'Good morning', 'Good afternoon',
            'Hey', 'Hi there', 'Dear Mr.', 'Dear Ms.', 'Dear Dr.'
        ]),
        'closing': random.choice([
            'Best regards', 'Sincerely', 'Kind regards', 'Thanks', 'Cheers', 'Best wishes',
            'Warm regards', 'Regards', 'Thank you', 'Many thanks', 'Looking forward to hearing from you'
        ])
    }

def determine_priority(category, subject, content):
    """Determine email priority based on content analysis and rules"""
    subject_lower = subject.lower()
    content_lower = content.lower()
    
    # High Priority Triggers
    high_priority_words = {
        'urgent', 'immediate', 'asap', 'emergency', 'critical', 'important',
        'deadline', 'action required', 'urgent action', 'overdue', 'attention needed',
        'security alert', 'password', 'account suspended', 'suspicious activity',
        'payment overdue', 'service interruption', 'system down', 'maintenance alert'
    }
    
    # Category-specific priority rules
    category_priorities = {
        'Work or Business Email': {
            'high': {'contract', 'proposal', 'deadline', 'urgent meeting', 'client', 'project due'},
            'medium': {'update', 'review', 'meeting', 'report', 'status'},
            'low': {'newsletter', 'announcement', 'fyi', 'general'}
        },
        'Legal & Contractual Email': {
            'high': {'deadline', 'legal notice', 'immediate action', 'compliance', 'violation'},
            'medium': {'review', 'update', 'changes', 'terms'},
            'low': {'information', 'newsletter', 'announcement'}
        },
        'IT Alerts & System Notifications Email': {
            'high': {'security', 'breach', 'system down', 'urgent maintenance', 'critical update'},
            'medium': {'update available', 'maintenance', 'patch', 'scheduled'},
            'low': {'newsletter', 'tips', 'general'}
        },
        'Finance & Transaction Email': {
            'high': {'fraud', 'unauthorized', 'overdue', 'urgent payment', 'immediate action'},
            'medium': {'payment due', 'invoice', 'statement', 'transaction'},
            'low': {'receipt', 'confirmation', 'newsletter'}
        },
        'Utilities Bill Email': {
            'high': {'disconnection', 'overdue', 'urgent payment', 'service interruption'},
            'medium': {'payment due', 'bill ready', 'reminder'},
            'low': {'newsletter', 'usage report', 'general notice'}
        }
    }

    # Check for explicit high priority indicators
    if any(word in subject_lower or word in content_lower for word in high_priority_words):
        return 'High'

    # Category-specific priority check
    if category in category_priorities:
        rules = category_priorities[category]
        if any(word in subject_lower or word in content_lower for word in rules['high']):
            return 'High'
        elif any(word in subject_lower or word in content_lower for word in rules['medium']):
            return 'Medium'
        elif any(word in subject_lower or word in content_lower for word in rules['low']):
            return 'Low'

    # Default priorities for other categories
    default_priorities = {
        'Promotions or Marketing Email': 'Low',
        'Personal Email': 'Medium',
        'Meeting & Schedule Email': 'Medium',
        'Internal Policies & HR Updates Email': 'Medium',
        'Social Media Email': 'Low',
        'Spam Email': 'Low'
    }

    return default_priorities.get(category, 'Medium')

def generate_email():
    """Generate a single email with unique writing style"""
    # Use the same categories as defined in CATEGORIES
    category = random.choice(list(CATEGORIES.keys()))
    
    # Generate data and style
    data = generate_random_data()
    style = generate_unique_writing_style()
    
    # Generate subject from the predefined templates
    subject = random.choice(CATEGORIES[category]['subjects']).format(**data)
    
    # Generate body
    body = generate_email_body(category, data, style)
    
    # Determine priority based on content
    priority = determine_priority(category, subject, body)
    
    return {
        'Subject': subject,
        'Message': body,
        'Category': category,
        'Priority': priority,
        'Date': (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d %H:%M:%S')
    }

def generate_dataset(num_emails=10000):
    """Generate a dataset of emails"""
    print(f"Generating {num_emails} emails...")
    
    emails = []
    for i in range(num_emails):
        if (i + 1) % 1000 == 0:
            print(f"Generated {i + 1} emails...")
        emails.append(generate_email())
    
    df = pd.DataFrame(emails)
    
    # Save to CSV
    output_path = os.path.join(os.path.dirname(__file__), 'generated_email_dataset.csv')
    df.to_csv(output_path, index=False)
    print(f"\nDataset saved to {output_path}")
    
    # Print category distribution
    print("\nCategory Distribution:")
    print(df['Category'].value_counts(normalize=True).sort_values(ascending=False))
    
    # Print priority distribution
    print("\nPriority Distribution:")
    print(df['Priority'].value_counts(normalize=True).sort_values(ascending=False))
    
    # Print priority distribution per category
    print("\nPriority Distribution per Category:")
    print(pd.crosstab(df['Category'], df['Priority'], normalize='index'))

if __name__ == "__main__":
    generate_dataset(10000)
