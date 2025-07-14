# Smart Email Management System

*This is my Final Year Project titled Leveraging Natural Language Processing and Data Analytics for Smarter Email Management Optimization.*

A Django-based platform for intelligent email management, featuring a hybrid AI system for prioritization, ML-powered categorization, voice commands, an analytics dashboard, and seamless Gmail integration. This system is designed to transform cluttered inboxes into streamlined, manageable workspaces.

---

## Table of Contents
- [Project Motivation](#project-motivation)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Model Training and Evaluation](#model-training-and-evaluation)
- [API Integrations](#api-integrations)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [Database Schema](#database-schema)
- [Roadmap](#roadmap)
- [Contributing & Testing](#contributing--testing)

---

## Project Motivation
The modern professional is often overwhelmed by a high volume of daily emails, leading to decreased productivity and missed critical communications. This project aims to solve that problem by creating an intelligent system that automatically organizes an email inbox. By leveraging machine learning for prioritization and categorization, integrating hands-free voice controls, and providing insightful analytics, this platform helps users focus on what matters most.

---

## System Architecture
The system is built on a modular architecture that ensures scalability and maintainability. The core components interact as follows:

```mermaid
graph TD
    subgraph User Interface
        A[Browser Frontend]
        B[Voice Commands (Web Speech API)]
    end

    subgraph Backend (Django)
        C{API Endpoints}
        D[Email Processing & Logic]
        E{AI/ML Service}
        F[Database ORM]
    end

    subgraph Data & AI
        G[Priority Model (XGBoost)]
        H[Category Model (SVM)]
        I[Vector Search (pgvector)]
        J[Generative AI (Gemini)]
        K[Custom Priority Scoring Engine]
    end
    
    subgraph Database
        L[PostgreSQL]
    end

    A <--> C;
    B --> A;
    C --> D;
    D --> E;
    E --> G;
    G -- ML Prediction --> K;
    D -- Email Data --> K;
    K -- Final Score --> D;
    E --> H;
    E --> I;
    E --> J;
    D -- CRUD Operations --> F;
    F <--> L;
```

---

## Features
- **Hybrid Priority Scoring:** Combines XGBoost ML predictions with a custom rule-based engine for robust, real-world accuracy.
- **ML-Powered Categorization:** SVM model classifies emails into categories (Promotions, Social, Primary, etc.).
- **Generative AI (Gemini):** Summarizes threads, generates smart replies.
- **Gmail API Integration:** Secure, OAuth2-based access to Gmail.
- **Hands-Free Voice Commands:** Browser-based, no extra installation. Example commands: “read unread emails”, “compose”, “reply”.
- **Analytics Dashboard:** Visualizes trends, activity, and response times.
- **Semantic Vector Search:** Find similar emails using pgvector.

---

## Model Training and Evaluation
- **Data Sources:** Enron dataset, private inbox (with consent), synthetic data.
- **Preprocessing:** HTML removal, tokenization, lemmatization, TF-IDF.
- **Metrics:**

| Model           | Accuracy | F1-Score |
|-----------------|----------|----------|
| Priority (XGB)  | 93%      | 0.92     |
| Category (SVM)  | 95%      | 0.94     |

- **Hybrid Approach:** Combines ML and rules for practical reliability.

---

## API Integrations
- **Gmail API:** For reading, sending, and managing emails securely with OAuth2 authentication.
- **Google Gemini API (Generative AI):** Powers advanced NLP features such as summarization, content generation, and smart replies.
- **Google Cloud AI Platform:** Supports scalable machine learning and AI model deployment.
- **Google BigQuery & Google Cloud Storage:** Used for large-scale data storage and analytics (if enabled in your configuration).

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

## Usage
- **Login:** Navigate to the homepage and click the "Login with Google" button. You will be redirected to an OAuth consent screen to grant the application permission to access your emails.
- **View Inbox:** Once authenticated, you will see your inbox. Emails are automatically labeled with their predicted priority (e.g., 🔥 High, 🟧 Medium) and category.
- **Use Voice Commands:** Click the microphone icon in the navigation bar. Wait for the "listening" prompt and speak a command, such as "Read the first email" or "Compose a new email to example@email.com".
- **Explore Analytics:** Click on the "Dashboard" tab to view visualizations of your email habits and trends.

---

## Database Schema
The main email table includes fields for email content, metadata, and our AI-generated insights.

Key fields include: id, user_email, subject, sender, snippet, priority (High/Medium/Low), priority_score, category (Primary/Promotions/etc.), category_confidence, and has_attachments.

---

## Roadmap
- [ ] Automated Summarization: Implement on-demand summarization for long email threads using Gemini.
- [ ] Sentiment Analysis: Add sentiment indicators (Positive, Neutral, Negative) to emails for quick emotional context.
- [ ] Deployment Scripts: Create scripts and documentation for one-click deployment to platforms like Heroku or AWS Elastic Beanstalk.
- [ ] Enhanced Analytics: Introduce cohort analysis to track user productivity improvements over time.
- [ ] Real-time Notifications: Add browser notifications for high-priority emails.

---

## Contributing & Testing
Contributions are welcome! Please open an issue or submit a pull request. All features are tested using a mix of real-world and synthetic emails to ensure reliability.

---
