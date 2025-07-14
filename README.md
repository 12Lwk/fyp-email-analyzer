# Smart Email Management System
This is my Final Year Project titled Leveraging Natural Language Processing and Data Analytics for Smarter Email Management Optimization. A Django-based platform for intelligent email management, featuring AI-powered prioritization, categorization, voice commands, analytics, and seamless Gmail integration.

---

## Project Structure

```
email_app/           # Main Django application (AI, Gmail API, voice, templates)
email_project/       # Django project settings
datasets/            # Email datasets (priority, category)
docker/              # Docker configuration (PostgreSQL, pgvector)
requirements.txt     # Python dependencies
manage.py            # Django management script
.env                 # Environment variables
```

---

## Features

- **AI-Powered Email Classification**: Real-time priority (high/medium/low) and category detection using SVM, XGBoost, and contextual NLP.
- **Gmail API Integration**: Securely read, send, and manage emails with OAuth2.
- **Voice Commands**: Control your inbox hands-free using browser-based voice recognition (no extra installation required).
- **Analytics Dashboard**: Visualize trends, response times, and top senders.
- **Vector Search**: Find similar emails using pgvector.
- **Dockerized Databases**: PostgreSQL and pgvector for robust storage.

---

## Setup Instructions

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   - Copy `.env.example` to `.env` and update as needed.

4. **Start Docker containers:**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

---

## Voice Feature: Browser-Based Voice Commands

This project uses browser-based voice recognition and text-to-speech for hands-free email management. No additional installation is required.

- **Technology Used:** Web Speech API (SpeechRecognition and SpeechSynthesis)
- **Supported Browsers:** Google Chrome, Microsoft Edge (desktop)
- **How it works:**
  - Click the voice command button in the UI to start listening.
  - Speak commands such as "read this email", "reply", "send email", "use suggested reply", etc.
  - The system will process your command and perform the corresponding action in the web app.
- **Note:** Voice features may not work in all browsers. For best results, use the latest version of Chrome or Edge on desktop.

---

## Database Schema

The main email table includes:
- `id`, `user_email`, `subject`, `sender`, `recipients`, `date`, `snippet`, `has_attachments`, `attachments`, `star`, `label`, `folder`, `last_modified`, `priority`, `priority_score`, `priority_explanation`, `priority_last_updated`, `category`, `category_confidence`, `category_last_updated`

---

## Frontend Templates

- Inbox: `inbox_email.html`, `inbox_email_detail.html`
- Sent: `sent_email.html`, `sent_email_detail.html`
- Draft: `draft_email.html`
- Spam: `spam_email.html`, `spam_email_detail.html`
- Compose: `compose.html`
- Login: `login.html`
- Settings: `settings.html`
- Dashboard: `email_dashboard.html`

---

## Contributing & Testing

- All features are tested using a mix of real-world and synthetic emails, including data from the Enron email dataset, a personal inbox dataset (with consent), and carefully generated synthetic data.
- All data used is anonymized to ensure privacy and GDPR compliance.

---
