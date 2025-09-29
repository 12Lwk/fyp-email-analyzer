# Smart Email Management System

[![Project Status: Complete](https://img.shields.io/badge/Status-Complete-brightgreen.svg?style=for-the-badge)](https://www.repostatus.org/#inactive)
[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/downloads/)
[![Framework: Django](https://img.shields.io/badge/Framework-Django-092E20.svg?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![Database: PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791.svg?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/)
[![Gmail API](https://img.shields.io/badge/Gmail%20API-EA4335.svg?style=for-the-badge&logo=gmail&logoColor=white)](https://developers.google.com/gmail/api)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2.svg?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Machine Learning](https://img.shields.io/badge/ML-scikit--learn-F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-FF6600.svg?style=for-the-badge&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io/)
[![pgvector](https://img.shields.io/badge/pgvector-336791.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)

*Final Year Project: Leveraging Natural Language Processing and Data Analytics for Smarter Email Management Optimization or Advancing Email Productivity with Hybrid AI and Data Analytics*

This project delivers a modern, intelligent email management platform built with Django, combining machine learning, rule-based logic, and generative AI to help users focus on what matters. The system automatically prioritizes, categorizes, and summarizes emails, supports hands-free voice commands, and provides actionable analytics—all while ensuring privacy and scalability.

Link: [Read the project announcement on LinkedIn](https://www.linkedin.com/posts/lee-wen-kang-3b76b6188_fyp-finalyearproject-dataanalytics-activity-7331114077303345154-X-ZT?utm_source=share&utm_medium=member_desktop&rcm=ACoAACw97bsBncCETOMLZpB9FULMPgOBgDW6iBs) & [Watch a demo of the project on LinkedIn](https://www.linkedin.com/posts/lee-wen-kang-3b76b6188_fyp-finalyearproject-dataanalytics-activity-7331114077303345154-X-ZT?utm_source=share&utm_medium=member_desktop&rcm=ACoAACw97bsBncCETOMLZpB9FULMPgOBgDW6iBs)

---

## Contents
- [Motivation](#motivation)
- [Objectives](#objectives)
- [Project Structure](#project-structure)
- [System Overview](#system-overview)
- [Key Features](#key-features)
- [Data & Modeling](#data--modeling)
- [API Integrations](#api-integrations)
- [Setup](#setup)
- [How to Use](#how-to-use)
- [Database Schema](#database-schema)
- [Roadmap](#roadmap)
- [System Screenshots](#system-screenshots)
- [Contributing](#contributing)

---

## Motivation
Email overload is a persistent challenge for professionals. This project aims to transform the inbox experience by leveraging a hybrid AI approach combining robust machine learning models, domain-specific rules, and Generative AI to deliver reliable, context-aware email organization and insights.

---

## Objectives
1.	To conduct a comprehensive analysis of existing email management systems and user challenges through literature review and user surveys, and to prepare a structured email dataset for model development.
2.	To analyze and design an intelligent unified data architecture incorporating natural language processing, machine learning algorithms, and security protocols.
3.	To develop an intelligent multi-modal data assistant that integrates API integrations, automated visualization generation, and voice-enabled analytics
4.	To evaluate the effectiveness and performance of the developed system through controlled testing and user acceptance in enterprise environments.

---

## Project Structure
```
email_app/                    # Main Django application
├── ai_services/             # AI/ML services (categorization, prioritization, LLM)
├── Gmail_API/               # Gmail API integration
├── voice_services/          # Voice command functionality
├── views/                   # Django views (auth, email, dashboard, AI)
├── models/                  # Database models
├── templates/               # HTML templates
├── static/                  # CSS, JavaScript, assets
├── utils/                   # Utility functions
└── management/              # Django management commands

email_project/               # Django project settings
Data Preprocessing and EDA/  # Jupyter notebooks for data analysis
├── FYPEnronEmail_NLP1.ipynb        # Initial data loading and cleaning
├── FYP_Trans_Feature_NLP2.ipynb    # Feature transformation
├── FYP_Message_Text_Cleaning_NLP3.ipynb # Text preprocessing
└── FYP_Visualization4.ipynb         # Data visualization and EDA

Data Labeling Solutions/     # Automated labeling approaches
├── Large Language Model/   # LLM-based labeling (Qwen2.5)
└── Unsupervised Learning/   # Clustering-based labeling

Model Building/              # ML model development
├── Prioritization Model/    # Random Forest priority classification
└── Categorization Model/    # XGBoost category classification

Experiments/                 # Model experiments and iterations
├── Category Modeling/       # Category model experiments
├── Priority Modeling/       # Priority model experiments
├── Data Labeling GC/        # Google Cloud labeling experiments
└── Spam Data Preparation/   # Spam detection data prep

requirements.txt            # Python dependencies
manage.py                   # Django management script
.env                        # Environment variables
```

## System Overview
The platform is architected for modularity and extensibility, with clear separation between data ingestion, processing, AI services, and user interaction.

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
├─────────────────────────────────────────────────────────────┤
│  Web UI (Django Templates)    │  Voice Commands (Web Speech) │
│  • Inbox Management           │  • Voice Navigation          │
│  • Analytics Dashboard        │  • Hands-free Email Actions  │
│  • Email Composition          │  • Voice-to-Text Input       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Django REST API Layer                     │
├─────────────────────────────────────────────────────────────┤
│  Authentication (OAuth2)      │  Email Management Views      │
│  • Gmail OAuth Integration    │  • CRUD Operations           │
│  • Session Management         │  • Bulk Actions              │
│  • User Profile Management    │  • Search & Filtering        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    AI Services Layer                        │
├─────────────────────────────────────────────────────────────┤
│  ML Models                    │  Generative AI Services      │
│  • Random Forest (Priority)   │  • Google Gemini Integration │
│  • XGBoost (Categorization)   │  • Email Summarization       │
│  • Rule-based Enhancement     │  • Smart Reply Generation    │
│  • Vector Embeddings          │  • Context-aware Responses   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Data & Integration Layer                   │
├─────────────────────────────────────────────────────────────┤
│  Gmail API Integration        │  Database (PostgreSQL)       │
│  • Email Fetching             │  • Email Storage             │
│  • Send/Reply Operations      │  • User Profiles             │
│  • Real-time Sync            │  • Vector Search (pgvector)  │
│  • Attachment Handling        │  • Analytics Data            │
└─────────────────────────────────────────────────────────────┘
```

### Technical Stack
- **Backend:** Django 5.2, Python 3.9+
- **Database:** PostgreSQL with pgvector extension
- **ML/AI:** scikit-learn, XGBoost, Google Gemini API
- **Frontend:** HTML5, CSS3, JavaScript (Web Speech API)
- **APIs:** Gmail API, Google Cloud AI Platform
- **Authentication:** OAuth2 (Google)
- **Data Processing:** pandas, numpy, BeautifulSoup4

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

## Data & Modeling Pipeline

### Data Collection & Preparation
- **Primary Dataset:** Enron Email Dataset (517,401 emails from 150+ users)
- **Data Processing:** Multi-stage pipeline implemented in Jupyter notebooks:
  - `FYPEnronEmail_NLP1.ipynb`: Data loading, initial cleaning, and exploration
  - `FYP_Trans_Feature_NLP2.ipynb`: Feature engineering and transformation
  - `FYP_Message_Text_Cleaning_NLP3.ipynb`: Advanced text preprocessing (HTML cleaning, tokenization, lemmatization)
  - `FYP_Visualization4.ipynb`: Comprehensive EDA and data visualization

### Automated Data Labeling
- **LLM-Based Labeling:** Used Qwen2.5 large language model for consistent, context-aware labeling
- **Category Labels:** 11 workplace-relevant categories (Work/Business, Finance, Personal, Meeting, Spam, IT Alerts, HR Updates, Social Media, Utilities, Promotions, Legal)
- **Priority Labels:** 3-tier priority system (High, Medium, Low) based on urgency and importance
- **Quality Assurance:** Structured prompts ensure consistent labeling across 500K+ emails

### Machine Learning Models
- **Priority Classification:**
  - **Model:** Random Forest with 100 estimators
  - **Features:** TF-IDF vectors, sender patterns, temporal features
  - **Performance:** 99% accuracy, 1.00 F1-score
  - **Hybrid Enhancement:** Rule-based post-processing for edge cases

- **Category Classification:**
  - **Model:** XGBoost with optimized hyperparameters
  - **Features:** TF-IDF vectors, email metadata, content patterns
  - **Performance:** 84% accuracy, 0.87 F1-score
  - **Class Balancing:** Weighted training to handle imbalanced categories

### Model Implementation
- **AI Services Architecture:** Modular design in `email_app/ai_services/`
  - `categorization/`: Email category prediction service
  - `prioritazation/`: Email priority scoring service
  - `llm/`: Generative AI integration (Google Gemini)
  - `embeddings/`: Vector embeddings for semantic search
  - `summarization/`: Email thread summarization
  - `recommendations/`: Smart reply suggestions

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

## Setup Instructions

### Prerequisites
- Python 3.9 or higher
- PostgreSQL 12+ with pgvector extension
- Gmail API credentials
- Google Gemini API key

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd fyp-email-analyzer
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup:**
   - Install PostgreSQL and create a database named `email_db`
   - Install pgvector extension:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector;
     ```
   - Update database credentials in `email_project/settings.py` or use environment variables

5. **Configure environment variables:**
   Create a `.env` file in the root directory with:
   ```env
   # Gmail API
   GMAIL_CLIENT_ID=your_gmail_client_id
   GMAIL_CLIENT_SECRET=your_gmail_client_secret
   
   # Google Gemini API
   GEMINI_API_KEY=your_gemini_api_key
   
   # Database (if using environment variables)
   DB_NAME=email_db
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

6. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

7. **Create a superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

8. **Launch the development server:**
   ```bash
   python manage.py runserver
   ```

9. **Access the application:**
   - Open your browser and navigate to `http://localhost:8000`
   - Use "Login with Google" to authenticate and connect your Gmail account

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

## Future Work
Based on the findings and limitations of this project, several recommendations are proposed for future improvements:

1. **Improve OAuth Token Handling for Continuous Data Fetching:**
   - Enhance OAuth token management to reduce the need for frequent user reauthentication. Implement more efficient token refresh mechanisms or extend session handling for uninterrupted, real-time email fetching.

2. **Enhance AI-Generated Suggested Reply Quality:**
   - Improve the contextual relevance and accuracy of AI-generated replies by fine-tuning Gemini API models with domain-specific data or integrating multi-turn dialogue capabilities for more sophisticated responses.

3. **Strengthen Model Robustness for Ambiguous Emails:**
   - Expand the training dataset with more complex, real-world emails and collect user feedback to improve model learning. Explore advanced feature engineering (e.g., context-aware embeddings, hierarchical classification) to better handle challenging or borderline emails.

4. **Expand Voice Command Functionalities:**
   - Enable users to edit email content verbally and extend voice commands to other pages (e.g., Analytics Dashboard) for tasks like reading aloud key insights. Incorporate advanced speech-to-text features for improved accessibility and user experience.

5. **Optimize Data Preprocessing Using More Advanced LLMs:**
   - Use more powerful LLMs for dataset labeling, assuming improved computational resources, to produce higher-quality labeled data and improve model performance.

6. **Upgrade Deployment Infrastructure for Larger Models:**
   - Upgrade server hardware, expand storage, and ensure environment compatibility to support the deployment of more advanced machine learning models and realize their full potential.

---

## System Screenshots
1. **Login Page**
![login_page](./assets/login_page.png)   
2. **Dashboard Page**
![dashboard_Page_1](./assets/dashboard_Page_1.png)
![dashboard_Page_2](./assets/dashboard_Page_2.png)
3. **Inbox Page**
![inbox_page](./assets/inbox_page.png)
3. **Inbox Detail Page**
![inbox_detail_page_1](./assets/inbox_detail_page_1.png)
![inbox_detail_page_2](./assets/inbox_detail_page_2.png)
4. **Sent Page**
![sent_page](./assets/sent_page.png)
5. **Sent Detail Page**
![sent_detail_page_1](./assets/sent_detail_page_1.png)
6. **Compose Window**
![compose_window](./assets/compose_window.png)
7. **Spam Page**
![spam_page](./assets/spam_page.png)
8. **Spam Detail Page**
![spam_detail_page_1](./assets/spam_detail_page_1.png)
9. **Setting Page**
![setting_page](./assets/setting_page.png)


   

---

## Contributing
Contributions are welcome! Please open an issue or submit a pull request. All features are tested on a mix of real and synthetic data for reliability and privacy.

---

## Project Author

* **Lee Wen Kang**
* [Connect on LinkedIn](https://www.linkedin.com/in/leewenkang12/)
