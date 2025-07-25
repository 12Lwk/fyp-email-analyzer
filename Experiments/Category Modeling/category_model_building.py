import pandas as pd
from faker import Faker
import random
import uuid

fake = Faker()
Faker.seed(42)

email_categories = [
    "Finance & Transaction Email",
    "IT Alerts & System Notifications Email",
    "Internal Policies & HR Updates Email",
    "Legal & Contractual Email",
    "Meeting & Schedule Email",
    "Personal Email",
    "Promotions or Marketing Email",
    "Social Media Email",
    "Spam Email",
    "Utilities Bill Email",
    "Work or Business Email"
]


def generate_email(category):
    return {
        "Email_ID": str(uuid.uuid4()),
        "From": fake.email(),
        "To": fake.email(),
        "Subject": fake.sentence(nb_words=6),
        "Message": fake.paragraph(nb_sentences=5),
        "Category": category
    }

# Number of emails per category
emails_per_category = 1818  # Approximately 20,000 emails in total

# Generate emails
emails = []
for category in email_categories:
    for _ in range(emails_per_category):
        emails.append(generate_email(category))

# Create DataFrame
df_emails = pd.DataFrame(emails)

df_emails.to_csv("test_20k_synthetic_emails_dataset.csv", index=False)