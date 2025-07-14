# Smart Email Management System

*Final Year Project: Advancing Email Productivity with Hybrid AI and Data Analytics*

This project delivers a modern, intelligent email management platform built with Django, combining machine learning, rule-based logic, and generative AI to help users focus on what matters. The system automatically prioritizes, categorizes, and summarizes emails, supports hands-free voice commands, and provides actionable analytics—all while ensuring privacy and scalability.

---

## Contents
- [Motivation](#motivation)
- [System Overview](#system-overview)
- [Key Features](#key-features)
- [Data & Modeling](#data--modeling)
- [API Integrations](#api-integrations)
- [Setup](#setup)
- [How to Use](#how-to-use)
- [Database Schema](#database-schema)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

---

## Motivation
Email overload is a persistent challenge for professionals. This project aims to transform the inbox experience by leveraging a hybrid AI approach combining robust machine learning models, domain-specific rules, and Generative AI to deliver reliable, context-aware email organization and insights.

---

## System Overview
The platform is architected for modularity and extensibility, with clear separation between data ingestion, processing, AI services, and user interaction.

System Architecture:

```
User Interface
  ├── Web UI (Inbox, Analytics, Compose, etc.)
  └── Voice Commands (Web Speech API)
      ↓
REST API (Django Backend)
      ↓
Email Logic & Orchestration
  ├── ML Models (XGBoost for Priority, SVM for Category)
  ├── Rule Engine (Domain-specific heuristics)
  ├── Generative AI (Gemini for Summaries/Replies)
  └── Vector Search (pgvector for semantic similarity)
      ↓
Database (PostgreSQL with pgvector)
```

---

## Key Features
- **Hybrid Priority Scoring:** Merges Random Forest predictions with a transparent rule-based engine for robust, real-world prioritization.
- **Automated Categorization:** XGBoost model classifies emails into actionable categories (e.g., Primary, Social, Promotions).
- **Generative AI Summaries & Replies:** Uses Google Gemini for summarizing threads and suggesting context-aware replies.
- **Voice-Driven Inbox:** Browser-based voice commands (Web Speech API) for hands-free navigation and actions.
- **Analytics Dashboard:** Visualizes trends, response times, and sender/recipient activity.
- **Semantic Search:** Finds similar emails using vector embeddings and pgvector.
- **Secure Gmail Integration:** OAuth2-based access for reading, sending, and managing emails.

---

## Data & Modeling
- **Data Sources:**
  - Enron Email Dataset (public, business context)
  - Anonymized, consented personal inbox data
  - Synthetic data for class balancing and edge cases
- **Preprocessing Pipeline:**
  - HTML/text cleaning, tokenization, lemmatization
  - Custom stopword removal, TF-IDF vectorization
- **Modeling:**
  - **Priority:** XGBoost classifier + rule-based adjustment
  - **Category:** SVM (linear kernel)
  - **Evaluation:**

    | Task      | Model    | Accuracy | F1-Score |
    |-----------|----------|----------|----------|
    | Priority  | RF       | 99%      | 1.00     |
    | Category  | XGBoost  | 84%      | 0.87     |

- **Hybrid Approach:**
  - ML models provide baseline predictions
  - Rule engine refines output using sender history, keywords, and context
  - Generative AI augments with summaries and smart replies

### Email Category Labeling & Balancing

The Enron dataset used in this project did not include category or priority labels, which posed a challenge for supervised learning. To address this, we used the Qwen2.5 large language model (LLM) to automatically generate consistent, context-aware labels for both email category and priority. Each email was passed through a structured prompt, and the model assigned one of several workplace-relevant categories, such as:

- Work or Business Email
- Finance & Transactions Email
- Personal Email
- Meeting & Schedule Email
- Spam Email
- IT Alerts & System Notifications Email
- Internal Policies & HR Updates Email
- Social Media Email
- Utilities Bill Email
- Promotions or Marketing Email
- Legal & Contractual Email

This LLM-based approach ensured high-quality, context-sensitive labeling, reducing human error and making the dataset suitable for training robust machine learning models.

**Balancing the Dataset:**
- Categories with more than 15,000 samples were capped at 15,000 (randomly selected)
- Smaller categories were kept as-is
- No synthetic samples were added, preserving the quality of text embeddings

Remaining imbalance was handled by using class weights during model training, ensuring the model learned to recognize minority categories effectively.

### Model Interpretability & Hybrid Adjustment

Despite high accuracy and F1-scores, detailed analysis revealed a consistent bias toward the Medium priority class—especially for borderline or ambiguous emails. To address this, a post-training probability adjustment layer was developed, refining model predictions using domain-specific signals such as:
- Urgency or risk keywords (e.g., “urgent”, “critical”, “failure”)
- Action verbs and deadline phrases (“due today”, “immediately”)
- Uppercase emphasis in subject lines
- Informational/courtesy phrases for Low priority (“FYI”, “reminder”)

This adjustment applies:
- Weighted scoring based on detected context
- Nonlinear scaling to boost or reduce probabilities (e.g., cubic boost for strong urgency)
- Class threshold logic to avoid over-assigning Medium unless other classes lack strong signals

This hybrid approach ensures the system delivers more reliable, human-aligned prioritization—especially in edge cases where pure statistical models may fail. The result is a practical, interpretable solution for real-world email management.

---

## API Integrations
- **Gmail API:** Secure email access and management
- **Google Gemini (Generative AI):** Summarization, smart replies
- **Google Cloud AI Platform:** Model deployment and scaling
- **pgvector:** Semantic search in PostgreSQL

---

## Setup
1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <project-directory>
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows: venv\Scripts\activate
   # macOS/Linux: source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in your credentials (Gmail, Gemini, DB, etc.)
5. **Start Docker services:**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```
6. **Run migrations:**
   ```bash
   python manage.py migrate
   ```
7. **Launch the server:**
   ```bash
   python manage.py runserver
   ```

---

## How to Use
- **Login:** Use "Login with Google" (OAuth2) to connect your inbox.
- **Inbox:** View emails with AI-prioritized and categorized labels.
- **Voice Commands:** Click the mic icon and say commands like "Read the first email", "Reply", or "Compose".
- **Analytics:** Explore the dashboard for trends and insights.
- **Smart Replies:** Use AI-generated suggestions for quick responses.

---

## Database Schema
The main email table includes:
- id, user_email, subject, sender, recipients, date, snippet, has_attachments, attachments, star, label, folder, last_modified, priority, priority_score, priority_explanation, priority_last_updated, category, category_confidence, category_last_updated

---

## Roadmap
- [ ] On-demand summarization for long threads
- [ ] Sentiment analysis for emotional context
- [ ] One-click deployment scripts
- [ ] Enhanced analytics (e.g., cohort analysis)
- [ ] Real-time notifications for high-priority emails

---

## Contributing
Contributions are welcome! Please open an issue or submit a pull request. All features are tested on a mix of real and synthetic data for reliability and privacy.
