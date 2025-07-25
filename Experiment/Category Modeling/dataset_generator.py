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
            'Business Partnership Discussion'
        ],
        'templates': [
            """Dear {name},

I hope this email finds you well. I wanted to provide an update on the {project_name} project. We've made significant progress in the {specific_area} phase, and I'd like to schedule a review meeting to discuss the next steps.

Current Status:
- {milestone1}
- {milestone2}
- {milestone3}

Please let me know your availability for a {duration} meeting next week.

Best regards,
{sender_name}""",
            """Hi {name},

Quick update on the {project_name} initiative. The team has completed the {specific_task} ahead of schedule, and we're ready to move forward with {next_step}.

Key Points:
• {point1}
• {point2}
• {point3}

Let me know if you need any clarification.

Regards,
{sender_name}"""
        ]
    },
    'Promotions or Marketing Email': {
        'subjects': [
            'Exclusive Offer: {product_name}',
            'Limited Time Deal: {discount}% Off',
            'New Product Launch: {product_name}',
            'Special Promotion Alert',
            'Member-Only Discount',
            'Flash Sale: {product_category}',
            'Seasonal Special: {product_name}',
            'Loyalty Rewards Update',
            'Product Bundle Deal',
            'Clearance Sale Announcement'
        ],
        'templates': [
            """Hello {name},

We're excited to announce our latest promotion! For a limited time, you can get {product_name} at {discount}% off the regular price.

Features:
✓ {feature1}
✓ {feature2}
✓ {feature3}

Use code {promo_code} at checkout to claim your discount. Offer valid until {end_date}.

Best,
{sender_name}""",
            """Hi {name},

Great news! We're running a special promotion on {product_name} this week. Don't miss out on this amazing opportunity to save {discount}%.

Why you'll love it:
• {benefit1}
• {benefit2}
• {benefit3}

Shop now and use code {promo_code} to save!

Cheers,
{sender_name}"""
        ]
    },
    'Legal & Contractual Email': {
        'subjects': [
            'Contract Review: {contract_name}',
            'Legal Notice: {matter_name}',
            'Agreement Amendment Request',
            'Compliance Update',
            'Legal Consultation Required',
            'Contract Renewal Notice',
            'Terms of Service Update',
            'Legal Documentation Request',
            'Regulatory Compliance Alert',
            'Contract Termination Notice'
        ],
        'templates': [
            """Dear {name},

This email serves as formal notice regarding the {contract_name} agreement. Please review the attached documents and provide your response by {deadline}.

Key Points:
1. {point1}
2. {point2}
3. {point3}

Please contact our legal department at {phone} if you have any questions.

Sincerely,
{sender_name}""",
            """Hello {name},

I am writing to inform you about important updates to our {contract_type} agreement. The changes will take effect on {effective_date}.

Changes include:
• {change1}
• {change2}
• {change3}

Please acknowledge receipt of this notice.

Regards,
{sender_name}"""
        ]
    },
    'Personal Email': {
        'subjects': [
            'Catching Up',
            'Family Update',
            'Weekend Plans',
            'Birthday Wishes',
            'Holiday Greetings',
            'Personal News',
            'Friend Check-in',
            'Life Update',
            'Special Occasion',
            'Thoughts and Updates'
        ],
        'templates': [
            """Hey {name},

How have you been? It's been a while since we last caught up. I wanted to share some updates about {topic}.

{personal_update}

Let me know when you're free to chat!

Take care,
{sender_name}""",
            """Hi {name},

Hope you're doing well! Just wanted to check in and see how things are going with {topic}.

{personal_message}

Looking forward to hearing from you!

Best,
{sender_name}"""
        ]
    },
    'Meeting & Schedule Email': {
        'subjects': [
            'Meeting Invitation: {meeting_topic}',
            'Schedule Update: {event_name}',
            'Calendar Invite: {meeting_name}',
            'Team Meeting Reminder',
            'Conference Call Details',
            'Workshop Schedule',
            'Training Session Update',
            'Project Review Meeting',
            'Client Presentation',
            'Team Sync Meeting'
        ],
        'templates': [
            """Dear {name},

You are invited to attend the {meeting_name} meeting scheduled for {date} at {time}.

Agenda:
1. {agenda1}
2. {agenda2}
3. {agenda3}

Location: {location}
Meeting ID: {meeting_id}
Password: {password}

Please confirm your attendance.

Best regards,
{sender_name}""",
            """Hi {name},

Just a reminder about our {meeting_name} meeting tomorrow at {time}.

Key points to discuss:
• {point1}
• {point2}
• {point3}

Join via: {meeting_link}

See you there!
{sender_name}"""
        ]
    },
    'Internal Policies & HR Updates Email': {
        'subjects': [
            'HR Policy Update: {policy_name}',
            'New Company Guidelines',
            'Employee Handbook Revision',
            'Workplace Policy Change',
            'HR Announcement',
            'Company Policy Update',
            'Employee Benefits Update',
            'Workplace Guidelines',
            'HR Procedure Change',
            'Company Policy Review'
        ],
        'templates': [
            """Dear Team,

I am writing to inform you about important updates to our {policy_name} policy, effective {effective_date}.

Key Changes:
1. {change1}
2. {change2}
3. {change3}

Please review the attached document and complete the acknowledgment form by {deadline}.

Best regards,
{sender_name}""",
            """Hello Everyone,

We're updating our {policy_name} guidelines to better serve our team. The new policy will take effect on {effective_date}.

Updates include:
• {update1}
• {update2}
• {update3}

Please direct any questions to HR.

Regards,
{sender_name}"""
        ]
    },
    'Social Media Email': {
        'subjects': [
            'Social Media Update',
            'Platform Announcement',
            'Content Schedule',
            'Social Media Strategy',
            'Engagement Report',
            'Content Calendar',
            'Social Media Metrics',
            'Platform Changes',
            'Content Guidelines',
            'Social Media Policy'
        ],
        'templates': [
            """Hi {name},

Here's our social media update for {time_period}:

Performance Metrics:
- Engagement: {engagement_rate}%
- Reach: {reach_count}
- Growth: {growth_rate}%

Key Highlights:
1. {highlight1}
2. {highlight2}
3. {highlight3}

Let's discuss the strategy for next month.

Best,
{sender_name}""",
            """Hello {name},

I'm sharing our social media content calendar for {month}:

Content Themes:
• {theme1}
• {theme2}
• {theme3}

Please review and provide feedback by {deadline}.

Regards,
{sender_name}"""
        ]
    },
    'Finance & Transaction Email': {
        'subjects': [
            'Transaction Confirmation: {amount}',
            'Payment Receipt',
            'Invoice {invoice_number}',
            'Financial Statement',
            'Payment Reminder',
            'Account Statement',
            'Transaction Alert',
            'Payment Confirmation',
            'Invoice Update',
            'Financial Report'
        ],
        'templates': [
            """Dear {name},

This email confirms your recent transaction:

Transaction Details:
Amount: ${amount}
Date: {date}
Reference: {reference}
Status: {status}

If you have any questions, please contact our support team.

Best regards,
{sender_name}""",
            """Hello {name},

Your invoice #{invoice_number} for ${amount} is due on {due_date}.

Payment Details:
• Amount: ${amount}
• Due Date: {due_date}
• Payment Method: {payment_method}

Please process the payment before the due date.

Regards,
{sender_name}"""
        ]
    },
    'IT Alerts & System Notifications Email': {
        'subjects': [
            'System Maintenance Alert',
            'Security Update Required',
            'IT Service Notice',
            'System Upgrade Notification',
            'Network Maintenance',
            'Security Alert',
            'System Update',
            'IT Service Interruption',
            'Maintenance Schedule',
            'Security Patch Update'
        ],
        'templates': [
            """Dear {name},

This is to inform you about scheduled system maintenance:

Maintenance Details:
Date: {date}
Time: {time}
Duration: {duration}
Impact: {impact}

Please save your work before the maintenance window.

Best regards,
{sender_name}""",
            """Hello {name},

Important security update required for your system:

Update Details:
• Version: {version}
• Size: {size}
• Required By: {deadline}

Please install the update at your earliest convenience.

Regards,
{sender_name}"""
        ]
    },
    'Spam Email': {
        'subjects': [
            'Urgent: Your Account Needs Verification',
            'Congratulations! You Won {prize}',
            'Limited Time Offer: {product}',
            'Your Payment is Overdue',
            'Security Alert: Unusual Activity',
            'Account Suspension Notice',
            'Payment Confirmation Required',
            'Important: Account Update Needed',
            'Your Subscription is Expiring',
            'Action Required: Account Verification'
        ],
        'templates': [
            """Dear Valued Customer,

Your account has been flagged for unusual activity. Please verify your information immediately to avoid account suspension.

Click here to verify: {spam_link}

Best regards,
{sender_name}""",
            """Hello,

Congratulations! You've been selected to receive {prize}. Claim your prize now!

Click here to claim: {spam_link}

Regards,
{sender_name}"""
        ]
    },
    'Utilities Bill Email': {
        'subjects': [
            'Your {utility} Bill: ${amount}',
            'Monthly Statement: {utility}',
            'Bill Payment Reminder',
            'Utility Service Update',
            'Billing Statement',
            'Payment Due Notice',
            'Account Statement',
            'Service Charge Update',
            'Monthly Usage Report',
            'Billing Cycle Update'
        ],
        'templates': [
            """Dear {name},

Your {utility} bill for {month} is now available:

Account: {account_number}
Amount Due: ${amount}
Due Date: {due_date}
Usage: {usage}

Please make your payment by the due date.

Best regards,
{sender_name}""",
            """Hello {name},

Here's your {utility} statement for {month}:

Statement Details:
• Amount: ${amount}
• Due Date: {due_date}
• Usage: {usage}

Payment can be made through our online portal.

Regards,
{sender_name}"""
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
    return {
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
        'utility': random.choice(['Electricity', 'Water', 'Gas', 'Internet']),
        'account_number': ''.join(random.choices(string.digits, k=10)),
        'usage': f"{random.randint(100, 1000)} {random.choice(['kWh', 'gallons', 'cubic feet', 'GB'])}"
    }

def generate_unique_writing_style():
    """Generate unique writing style variations"""
    styles = {
        'formality': random.choice(['formal', 'semi-formal', 'casual']),
        'tone': random.choice(['professional', 'friendly', 'urgent', 'informative', 'persuasive']),
        'structure': random.choice(['direct', 'narrative', 'bullet-points', 'mixed']),
        'length': random.choice(['short', 'medium', 'long']),
        'emphasis': random.choice(['bold', 'italic', 'underline', 'none']),
        'greeting': random.choice(['Dear', 'Hello', 'Hi', 'Greetings', 'Good day']),
        'closing': random.choice(['Best regards', 'Sincerely', 'Regards', 'Thanks', 'Cheers', 'Best', 'Warm regards'])
    }
    return styles

def apply_writing_style(text, style):
    """Apply writing style variations to text"""
    # Adjust formality
    if style['formality'] == 'formal':
        text = text.replace('Hi', 'Dear')
        text = text.replace('Hey', 'Dear')
    elif style['formality'] == 'casual':
        text = text.replace('Dear', random.choice(['Hi', 'Hey']))
    
    # Adjust structure
    if style['structure'] == 'bullet-points':
        # Convert paragraphs to bullet points
        sentences = TextBlob(text).sentences
        text = '\n• ' + '\n• '.join(str(s) for s in sentences)
    elif style['structure'] == 'direct':
        # Make text more direct
        text = text.replace('I would like to', 'I want to')
        text = text.replace('Please let me know', 'Let me know')
    
    # Adjust length
    if style['length'] == 'short':
        # Keep only first two sentences
        sentences = TextBlob(text).sentences
        text = ' '.join(str(s) for s in sentences[:2])
    elif style['length'] == 'long':
        # Add more details
        text += '\n\nAdditional Information:\n' + fake.paragraph()
    
    # Add emphasis
    if style['emphasis'] == 'bold':
        text = f"**{text}**"
    elif style['emphasis'] == 'italic':
        text = f"*{text}*"
    
    return text

def generate_email_body(category, data):
    """Generate unique email body based on category and writing style"""
    style = generate_unique_writing_style()
    
    # Base templates with more variations
    templates = {
        'Work or Business Email': [
            f"{style['greeting']} {{name}},\n\n{{content}}\n\n{style['closing']},\n{{sender_name}}",
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nLooking forward to your response.\n{style['closing']},\n{{sender_name}}"
        ],
        'Promotions or Marketing Email': [
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nDon't miss out!\n{style['closing']},\n{{sender_name}}",
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nLimited time offer!\n{style['closing']},\n{{sender_name}}"
        ],
        'Legal & Contractual Email': [
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nPlease review carefully.\n{style['closing']},\n{{sender_name}}",
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nYour prompt attention is appreciated.\n{style['closing']},\n{{sender_name}}"
        ],
        'Personal Email': [
            f"{style['greeting']} {{name}},\n\n{{content}}\n\n{style['closing']},\n{{sender_name}}",
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nTake care!\n{style['closing']},\n{{sender_name}}"
        ],
        'Meeting & Schedule Email': [
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nPlease confirm your attendance.\n{style['closing']},\n{{sender_name}}",
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nLooking forward to seeing you there.\n{style['closing']},\n{{sender_name}}"
        ],
        'Internal Policies & HR Updates Email': [
            f"{style['greeting']} Team,\n\n{{content}}\n\nPlease review and acknowledge.\n{style['closing']},\n{{sender_name}}",
            f"{style['greeting']} Everyone,\n\n{{content}}\n\nYour compliance is required.\n{style['closing']},\n{{sender_name}}"
        ],
        'Social Media Email': [
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nLet's discuss the strategy.\n{style['closing']},\n{{sender_name}}",
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nYour feedback is valuable.\n{style['closing']},\n{{sender_name}}"
        ],
        'Finance & Transaction Email': [
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nPlease review the details.\n{style['closing']},\n{{sender_name}}",
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nPayment is required.\n{style['closing']},\n{{sender_name}}"
        ],
        'IT Alerts & System Notifications Email': [
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nPlease take necessary action.\n{style['closing']},\n{{sender_name}}",
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nYour attention is required.\n{style['closing']},\n{{sender_name}}"
        ],
        'Spam Email': [
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nAct now!\n{style['closing']},\n{{sender_name}}",
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nLimited time offer!\n{style['closing']},\n{{sender_name}}"
        ],
        'Utilities Bill Email': [
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nPayment is due.\n{style['closing']},\n{{sender_name}}",
            f"{style['greeting']} {{name}},\n\n{{content}}\n\nPlease make payment.\n{style['closing']},\n{{sender_name}}"
        ]
    }
    
    # Generate unique content based on category
    content_generators = {
        'Work or Business Email': lambda: f"I'm writing to update you on the {data['project_name']} project. We've made progress in {data['specific_area']} and need to discuss next steps.\n\nKey Updates:\n• {data['milestone1']}\n• {data['milestone2']}\n• {data['milestone3']}",
        'Promotions or Marketing Email': lambda: f"We're excited to offer you {data['discount']}% off {data['product_name']}!\n\nFeatures:\n• {data['feature1']}\n• {data['feature2']}\n• {data['feature3']}\n\nUse code {data['promo_code']} before {data['end_date']}",
        'Legal & Contractual Email': lambda: f"This notice concerns the {data['contract_name']} agreement. Please review the changes by {data['deadline']}.\n\nChanges:\n1. {data['change1']}\n2. {data['change2']}\n3. {data['change3']}",
        'Personal Email': lambda: f"How have you been? I wanted to share some updates about {data['topic']}.\n\n{data['personal_update']}",
        'Meeting & Schedule Email': lambda: f"Please join us for the {data['meeting_name']} meeting on {data['date']} at {data['time']}.\n\nAgenda:\n• {data['agenda1']}\n• {data['agenda2']}\n• {data['agenda3']}",
        'Internal Policies & HR Updates Email': lambda: f"The {data['policy_name']} policy has been updated, effective {data['effective_date']}.\n\nKey Changes:\n• {data['update1']}\n• {data['update2']}\n• {data['update3']}",
        'Social Media Email': lambda: f"Here's our social media update for {data['time_period']}:\n\nMetrics:\n• Engagement: {data['engagement_rate']}%\n• Reach: {data['reach_count']}\n• Growth: {data['growth_rate']}%",
        'Finance & Transaction Email': lambda: f"Transaction Details:\nAmount: ${data['amount']}\nDate: {data['date']}\nReference: {data['reference']}\nStatus: {data['status']}",
        'IT Alerts & System Notifications Email': lambda: f"System maintenance scheduled:\nDate: {data['date']}\nTime: {data['time']}\nDuration: {data['duration']}\nImpact: {data['impact']}",
        'Spam Email': lambda: f"Your account needs verification. Click here: {data['spam_link']}",
        'Utilities Bill Email': lambda: f"Your {data['utility']} bill for {data['month']}:\nAccount: {data['account_number']}\nAmount: ${data['amount']}\nDue: {data['due_date']}\nUsage: {data['usage']}"
    }
    
    # Generate content
    content = content_generators[category]()
    
    # Apply writing style
    content = apply_writing_style(content, style)
    
    # Format with template
    template = random.choice(templates[category])
    return template.format(**data, content=content)

def generate_email():
    """Generate a single email with unique writing style"""
    category = random.choice(list(CATEGORIES.keys()))
    priority = random.choices(
        list(PRIORITIES.keys()),
        weights=list(PRIORITIES.values())
    )[0]
    
    # Generate data
    data = generate_random_data()
    
    # Generate subject with variations
    subject_template = random.choice(CATEGORIES[category]['subjects'])
    subject = subject_template.format(**data)
    
    # Generate unique writing style
    style = {
        'greeting': random.choice(['Dear', 'Hello', 'Hi', 'Greetings', 'Good day']),
        'tone': random.choice(['formal', 'casual', 'urgent', 'friendly']),
        'structure': random.choice(['paragraph', 'bullet-points', 'mixed']),
        'length': random.choice(['short', 'medium', 'long']),
        'closing': random.choice(['Best regards', 'Sincerely', 'Regards', 'Thanks', 'Cheers'])
    }
    
    # Generate content based on style
    if style['structure'] == 'paragraph':
        content = fake.paragraph(nb_sentences=random.randint(3, 7))
    elif style['structure'] == 'bullet-points':
        content = f"• {fake.sentence()}\n• {fake.sentence()}\n• {fake.sentence()}"
    else:  # mixed
        content = f"{fake.paragraph(nb_sentences=2)}\n\nKey Points:\n• {fake.sentence()}\n• {fake.sentence()}\n• {fake.sentence()}"
    
    # Adjust length
    if style['length'] == 'short':
        content = content.split('\n')[0]
    elif style['length'] == 'long':
        content += f"\n\nAdditional Information:\n{fake.paragraph()}"
    
    # Adjust tone
    if style['tone'] == 'formal':
        content = content.replace('Hi', 'Dear')
        content = content.replace('Hey', 'Dear')
    elif style['tone'] == 'casual':
        content = content.replace('Dear', random.choice(['Hi', 'Hey']))
    elif style['tone'] == 'urgent':
        content = f"URGENT: {content}"
    
    # Add random variations
    variations = [
        "\n\nP.S. " + fake.sentence(),
        "\n\nLooking forward to your response.",
        "\n\nPlease let me know if you have any questions.",
        "\n\nThank you for your attention to this matter.",
        "\n\nYour prompt response is appreciated."
    ]
    
    # Combine everything
    body = f"{style['greeting']} {data['name']},\n\n{content}{random.choice(variations)}\n\n{style['closing']},\n{data['sender_name']}"
    
    return {
        'Subject': subject,
        'Message': body,
        'Category': category,
        'Priority': priority,
        'Date': (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d %H:%M:%S')
    }

def generate_dataset(num_emails=1000):
    """Generate a dataset of emails"""
    print(f"Generating {num_emails} emails...")
    
    emails = []
    for i in range(num_emails):
        if (i + 1) % 100 == 0:
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

if __name__ == "__main__":
    generate_dataset(1000)
