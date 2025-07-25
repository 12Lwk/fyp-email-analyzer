import pandas as pd
import random
import uuid
from datetime import datetime, timedelta
import faker

# Initialize Faker for realistic names and emails
fake = faker.Faker()

# Email categories and priorities
categories = [
    ("Finance & Transaction", ["High", "Medium", "Low"]),  # Added Low Priority
    ("IT Alerts & System Notifications", ["High", "Medium", "Low"]),  # Added Low Priority
    ("Legal & Contractual", ["Medium", "High"]),
    ("Utilities Bill", ["High", "Medium", "Low"]),
    ("Work or Business", ["High", "Medium", "Low"]),
    ("Meeting & Schedule", ["High", "Medium", "Low"]),
    ("Internal Policies & HR Updates", ["Medium", "Low"]),
    ("Personal", ["Low", "Medium"]),
    ("Promotions or Marketing", ["Low"]),
    ("Social Media", ["Low"]),
    ("Spam", ["Low"])
]

# Informal phrases for Personal category
informal_phrases = ["hi hihiiii", "this is testing only", "bye", "test 123", "123", "yo what's good", "just checking lol", "hahaha what's up"]

# Emojis for marketing and social media
emojis = ["⏰", "🎉", "🚀", "🌟", "💬", "🎁"]

# Random value lists for placeholders
systems = ["FYP API", "Vertex AI", "Google Drive", "CRM"]
projects = ["Q3 Partnership", "Client Onboarding", "Thai Rice Export"]
terms = ["pricing", "liability", "delivery"]
issues = ["contract breach", "compliance issue", "billing dispute"]
utilities = ["Electricity", "Water", "Internet"]
roles = ["IT Specialist", "Travel Consultant", "Penetration Tester"]
companies = ["TechWave", "Singtel", "Scientex Berhad"]
topics = ["Sales Analytics", "Q3 Planning", "Data Modeling", "System Outage"]
reasons = ["client request", "scheduling conflict", "urgent update"]
policies = ["remote work", "leave", "expense"]
changes = ["2 extra days", "new approval process", "updated guidelines"]
greetings = ["Hey", "Hi", "Yo"]
actions = ["Wanna grab coffee?", "Let's hang soon!", "You free this week?"]
signoffs = ["Bye", "Cheers", "Later"]
events = ["Spring", "Summer", "Flash", "MongoDB 8.0"]
codes = ["SAVE", "DEAL", "SHOP"]
platforms = ["LinkSphere", "LinkedIn", "Instagram"]
posts = ["new job post", "project update", "diversity initiative"]
action_names = ["connection", "message", "search"]
settings = ["2-Step Verification", "Password", "Email Forwarding"]
statuses = ["Failed", "Partially Imported"]

# Message templates for each category (without placeholders)
templates = {
    "Finance & Transaction": [
        ("Action Required: Past Due Account", "High", lambda to_name, account, amount, date, website, phone: f"Dear {to_name}, Your account #{account} is past due by ${amount}. Settle by {date} to avoid suspension. Pay at {website} or call {phone}. Regards, Billing Team"),
        ("Payment Confirmation", "Medium", lambda to_name, amount, date, website, phone: f"Hi {to_name}, Your payment of ${amount} was received on {date}. View details at {website}. Questions? Call {phone}. Best, Finance Team"),
        ("Transaction Receipt", "Medium", lambda to_name, amount, date, website, phone: f"Hi {to_name}, Thank you for your ${amount} purchase on {date}. Review details at {website}. Contact {phone} for support. Best, Finance Team"),
        ("Monthly Account Summary", "Low", lambda to_name, month, website, phone: f"Hi {to_name}, Your {month} account statement is available. View details at {website}. Questions? Call {phone}. Regards, Finance Team")
    ],
    "IT Alerts & System Notifications": [
        ("Security Alert: System Access", "High", lambda to_name, system, website, ext, email: f"Team, {system} was granted access to your account. If this wasn't you, secure it at {website}/security. Check activity now. Contact ext. {ext}. IT Crew"),
        ("System Import Failure", "Medium", lambda to_name, system, dataset, status, website, email: f"Hello, {system} failed to import data into dataset {dataset}. Operation: {status}. Details at {website}. Email {email} for support. IT Team"),
        ("System Account Confirmation", "Medium", lambda to_name, system, setting, website, email: f"Hi {to_name}, Your {system} account setting ({setting}) was updated. Review at {website}/account. Questions? Email {email}. IT Team"),
        ("System Usage Update", "Low", lambda to_name, system, usage, website, email: f"Hi {to_name}, Your {system} usage is at {usage}% capacity. Monitor at {website}/usage. Questions? Email {email}. IT Team")
    ],
    "Legal & Contractual": [
        ("Review Agreement", "Medium", lambda to_name, project, date, terms, from_name: f"Dear {to_name}, Review the attached {project} agreement by {date}. Focus on {terms}. Schedule a call to discuss. Best, {from_name}, Legal"),
        ("Urgent: Legal Notice", "High", lambda to_name, issue, date, phone: f"Dear {to_name}, Immediate action required for {issue}. Review the notice by {date}. Contact {phone}. Regards, Legal Team")
    ],
    "Utilities Bill": [
        ("Urgent: Utility Overdue Notice", "High", lambda to_name, utility, amount, date, website, phone: f"Hi {to_name}, Your {utility} bill of ${amount} is overdue. Pay by {date} to avoid disconnection. Visit {website} or call {phone}. Thanks, Billing Team"),
        ("Your Utility Bill", "Medium", lambda to_name, utility, month, amount, date, website, phone: f"Hi {to_name}, Your {utility} bill for {month} is ${amount}, due by {date}. Pay at {website} or call {phone}. Late fees apply. Thanks, Billing Team"),
        ("Utility Usage Summary", "Low", lambda to_name, utility, month, usage, website, phone: f"Hi {to_name}, Your {month} {utility} usage was {usage} units. View details at {website}. Questions? Call {phone}. Thanks, Billing Team")
    ],
    "Work or Business": [
        ("Urgent: Proposal", "High", lambda to_name, project, date, website, from_name: f"Hi {to_name}, I'm {from_name} from Chim Doo Malaysia, HQ in Thailand. Our {project} proposal needs your approval by {date} to meet Q3 deadlines. View at {website}. Reply ASAP. Regards, {from_name}"),
        ("Proposal", "Medium", lambda to_name, project, date, website, from_name: f"Hi {to_name}, I'm {from_name} from Chim Doo Malaysia, HQ in Thailand. We're expanding overseas with ready-to-eat Thai Rice (7 flavors). View details at {website}. Interested? Reply by {date}. Regards, {from_name}"),
        ("Job Opening", "Medium", lambda to_name, role, date, website, email: f"Team, We're hiring a {role}. Apply by {date} at {website}/careers. Share with your network! Email {email} for queries. Cheers, HR"),
        ("Follow-Up: Proposal", "Low", lambda to_name, project, date, from_name: f"Hi {to_name}, Following up on the {project} proposal sent {date}. Any feedback? Let's schedule a call. Best, {from_name}"),
        ("Urgent: Job Application Deadline", "High", lambda to_name, role, company, date, website, email: f"Hi {to_name}, The {role} position at {company} closes tomorrow, {date}! Apply now at {website}/careers or email {email}. Don't miss out. HR Team")
    ],
    "Meeting & Schedule": [
        ("Urgent: Meeting Rescheduled", "High", lambda to_name, topic, date, time, reason, website, from_name: f"Team, The {topic} meeting is now {date} at {time} due to {reason}. Attendance mandatory. Confirm ASAP at {website}. Thanks, {from_name}"),
        ("Emergency: Briefing", "High", lambda to_name, topic, date, time, rsvp_date, website, from_name: f"All, Join an emergency {topic} briefing on {date} at {time}. Critical updates shared. RSVP by {rsvp_date} at {website}. Regards, {from_name}"),
        ("Meeting", "Medium", lambda to_name, topic, date, time, rsvp_date, website, from_name: f"All, Join us on {date} at {time} for {topic}. Materials attached. RSVP by {rsvp_date} at {website}. Regards, {from_name}"),
        ("Reminder: Discussion", "Low", lambda to_name, topic, date, time, website, from_name: f"Hi Team, Friendly reminder for the {topic} discussion on {date} at {time}. Prep materials at {website}. See you there! {from_name}")
    ],
    "Internal Policies & HR Updates": [
        ("New Policy", "Medium", lambda to_name, policy, date, change, website, q_date: f"Dear Staff, From {date}, our {policy} policy includes {change}. Review at {website}/hr. Questions by {q_date}. HR Team"),
        ("Policy Training Reminder", "Low", lambda to_name, policy, date, email: f"All, Complete {policy} training by {date}. It's quick! Email {email} for help. Thanks, HR")
    ],
    "Personal": [
        ("Test Email", "Low", lambda to_name, greeting, phrase, action, signoff, from_name: f"{greeting}, {to_name}! {phrase} Just a quick note. {action} {signoff}, {from_name}"),
        ("Testing Sent Email", "Low", lambda to_name, phrase, from_name: f"Dear {to_name}, How are you? {phrase} This is just a testing email. Thank you, {from_name}")
    ],
    "Promotions or Marketing": [
        ("Sale Offer", "Low", lambda to_name, emoji, percent, event, code, date, website, from_name: f"Hi {to_name}, Our {event} sale offers {percent}% off with code {code}! Shop at {website} before {date}. Happy shopping! {from_name} ͏ ͏ ͏"),
        ("Webinar Invite", "Low", lambda to_name, emoji, event, date, topic, website, from_name: f"Hi {to_name}, Don't miss our {event} webinar on {date}! Learn {topic} with experts. Register at {website}. {from_name} ͏ ͏ ͏")
    ],
    "Social Media": [
        ("Search Notification", "Low", lambda to_name, emoji, platform, website: f"{to_name}, You appeared in 1 search on {platform}! See who viewed your profile at {website}. Stay active! {platform} Team ͏ ͏ ͏"),
        ("New Post Notification", "Low", lambda to_name, emoji, platform, user, post, website: f"{to_name}, {user} posted on {platform}: {post}. Check it out at {website}. {platform} Team ͏ ͏ ͏")
    ],
    "Spam": [
        ("Prize Scam", "Low", lambda to_name, amount, website, phrase: f"Congrats, {to_name}! You've won ${amount}! Click {website} to claim. {phrase} Act fast! Unsubscribe below.")
    ]
}

# Generate email data
def generate_email():
    category, priorities = random.choice(categories)
    # Adjust priority weights for specific categories
    if category == "Utilities Bill":
        priority = random.choices(priorities, weights=[20, 70, 10])[0]  # 20% High, 70% Medium, 10% Low
    elif category == "Work or Business":
        priority = random.choices(priorities, weights=[20, 40, 40])[0]  # 20% High, 40% Medium, 40% Low
    elif category == "Meeting & Schedule":
        priority = random.choices(priorities, weights=[30, 50, 20])[0]  # 30% High, 50% Medium, 20% Low
    elif category == "IT Alerts & System Notifications":
        priority = random.choices(priorities, weights=[50, 40, 10])[0]  # 50% High, 40% Medium, 10% Low
    elif category == "Finance & Transaction":
        priority = random.choices(priorities, weights=[45, 45, 10])[0]  # 45% High, 45% Medium, 10% Low
    else:
        priority = random.choice(priorities)

    template = random.choice(templates[category])
    subject_template, template_priority, message_func = template
    if template_priority != priority:
        # Ensure template matches priority
        valid_templates = [t for t in templates[category] if t[1] == priority]
        if valid_templates:
            template = random.choice(valid_templates)
            subject_template, template_priority, message_func = template

    # Generate metadata
    email_id = f"E{str(uuid.uuid4())[:8].upper()}"
    from_email = fake.email()
    to_name = fake.name().split()[0]  # First name for message
    to_email = fake.email()
    date_time = fake.date_time_between(start_date="-7d", end_date="now").strftime("%Y-%m-%d %H:%M:%S")
    
    # Random values for message construction
    account = str(random.randint(1000, 9999))
    amount = f"{random.randint(100, 10000):.2f}"
    date = (datetime.now() + timedelta(days=random.randint(1, 15))).strftime("%B %d, %Y")
    phone = f"({random.randint(800, 999)}) 555-{random.randint(1000, 9999)}"
    website = fake.url()
    system = random.choice(systems)
    dataset = f"untitled_{random.randint(100000, 999999)}"
    status = random.choice(statuses)
    ext = random.randint(100, 999)
    email = fake.email()
    project = random.choice(projects)
    term = random.choice(terms)
    from_name = fake.first_name()
    issue = random.choice(issues)
    utility = random.choice(utilities)
    month = (datetime.now() - timedelta(days=30)).strftime("%B")
    usage = random.randint(100, 1000)
    role = random.choice(roles)
    company = random.choice(companies)
    topic = random.choice(topics)
    time = (datetime.now() + timedelta(hours=random.randint(1, 8))).strftime("%I %p")
    rsvp_date = (datetime.now() + timedelta(days=random.randint(1, 5))).strftime("%B %d")
    reason = random.choice(reasons)
    policy = random.choice(policies)
    change = random.choice(changes)
    q_date = (datetime.now() + timedelta(days=random.randint(1, 10))).strftime("%B %d")
    greeting = random.choice(greetings) if category == "Personal" else ""
    phrase = random.choice(informal_phrases) if category in ["Personal", "Spam"] else ""
    action = random.choice(actions) if category == "Personal" else ""
    signoff = random.choice(signoffs) if category == "Personal" else "Regards"
    emoji = random.choice(emojis) if category in ["Promotions or Marketing", "Social Media"] else ""
    percent = random.randint(10, 70)
    event = random.choice(events)
    code = f"{random.choice(codes)}{random.randint(10, 50)}"
    platform = random.choice(platforms)
    user = fake.name()
    post = random.choice(posts)
    setting = random.choice(settings)

    # Construct subject and message
    subject = subject_template.replace("System", system).replace("Utility", utility).replace("Proposal", project).replace("Meeting", topic).replace("Policy", policy).replace("Job", role)
    if category == "Social Media":
        if "Search Notification" in subject_template:
            message = message_func(to_name, emoji, platform, website)
        else:
            message = message_func(to_name, emoji, platform, user, post, website)
    elif category == "Promotions or Marketing":
        if "Sale" in subject_template:
            message = message_func(to_name, emoji, percent, event, code, date, website, from_name)
        else:
            message = message_func(to_name, emoji, event, date, topic, website, from_name)
    else:
        # Generate message using the lambda function
        if category == "Finance & Transaction":
            if "Action Required: Past Due Account" in subject_template:
                message = message_func(to_name, account, amount, date, website, phone)
            elif "Payment Confirmation" in subject_template:
                message = message_func(to_name, amount, date, website, phone)
            elif "Transaction Receipt" in subject_template:
                message = message_func(to_name, amount, date, website, phone)
            else:  # "Monthly Account Summary" template
                message = message_func(to_name, month, website, phone)  # Correct parameters for this template
        elif category == "IT Alerts & System Notifications":
            if "Security Alert: System Access" in subject_template:
                message = message_func(to_name, system, website, ext=ext, email=email)
            elif "System Import Failure" in subject_template:
                message = message_func(to_name, system, dataset, status, website, email)
            elif "System Account Confirmation" in subject_template:
                message = message_func(to_name, system, setting, website, email)
            else:  # "System Usage Update" template
                message = message_func(to_name, system, usage, website, email)
        elif category == "Legal & Contractual":
            if "Urgent: Legal Notice" in subject_template:
                message = message_func(to_name, issue, date, phone)
            else:
                message = message_func(to_name, project, date, term, from_name)
        elif category == "Utilities Bill":
            if "Utility Usage Summary" in subject_template:
                message = message_func(to_name, utility, month, usage, website, phone)
            elif "Urgent: Utility Overdue Notice" in subject_template:
                message = message_func(to_name, utility, amount, date, website, phone)
            else:  # "Your Utility Bill" template
                message = message_func(to_name, utility, month, amount, date, website, phone)
        elif category == "Work or Business":
            if "Job Opening" in subject_template:
                message = message_func(to_name, role, date, website, email)
            elif "Urgent: Job Application Deadline" in subject_template:
                message = message_func(to_name, role, company, date, website, email)
            elif "Follow-Up: Proposal" in subject_template:
                message = message_func(to_name, project, date, from_name)
            else:  # "Urgent: Proposal" or "Proposal" templates
                message = message_func(to_name, project, date, website, from_name)
        elif category == "Meeting & Schedule":
            if "Emergency: Briefing" in subject_template or "Meeting" in subject_template:
                message = message_func(to_name, topic, date, time, rsvp_date, website, from_name)
            elif "Urgent: Meeting Rescheduled" in subject_template:
                message = message_func(to_name, topic, date, time, reason, website, from_name)
            else:  # "Reminder: Discussion" template
                message = message_func(to_name, topic, date, time, website, from_name)
        elif category == "Internal Policies & HR Updates":
            if "Policy Training Reminder" in subject_template:
                message = message_func(to_name, policy, date, email)
            else:
                message = message_func(to_name, policy, date, change, website, q_date)
        elif category == "Personal":
            if "Test Email" in subject_template:
                message = message_func(to_name, greeting, phrase, action, signoff, from_name)
            elif "Testing Sent Email" in subject_template:
                message = message_func(to_name, phrase, from_name)
        elif category == "Promotions or Marketing":
            if "Sale" in subject_template:
                message = message_func(to_name, emoji, percent, event, code, date, website, from_name)
            else:
                message = message_func(to_name, emoji, event, date, topic, website, from_name)
        elif category == "Social Media":
            if "Search Notification" in subject_template:
                message = message_func(to_name, emoji, platform, website)
            else:  # "New Post Notification" template
                message = message_func(to_name, emoji, platform, user, post, website)
        elif category == "Spam":
            message = message_func(to_name, amount, website, phrase)
        else:
            # Add the default case or other conditions here
            message = ""

    return {
        "Email ID": email_id,
        "From": from_email,
        "To": to_email,
        "Date & Time": date_time,
        "Subject": subject,
        "Message": message,
        "Priority": priority
    }

# Generate 20,000 emails
emails = [generate_email() for _ in range(20000)]
df = pd.DataFrame(emails)

# Save to CSV
df.to_csv("emails_dataset_20k.csv", index=False)

print("Generated 20,000 emails. Saved to emails_dataset_20k.csv")