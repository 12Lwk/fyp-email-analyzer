import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
df = pd.read_csv('cleaned_priority_email_dataset.csv')

# Print class distribution
print("\nClass Distribution:")
print(df['Email_Priority'].value_counts(normalize=True).round(4)*100)

# Print basic statistics
print("\nBasic Statistics:")
print(df.describe())

# Create features
def preprocess_text(text):
    if pd.isna(text):
        return ""
    return str(text).lower()

# Combine subject and message
df['combined_text'] = df['Subject'].apply(preprocess_text) + " " + df['Message'].apply(preprocess_text)

# Create TF-IDF features
vectorizer = TfidfVectorizer(max_features=1000)
X_text = vectorizer.fit_transform(df['combined_text'])

# Create numeric features
numeric_features = ['urgency_flag', 'risk_flag', 'urgency_and_risk', 
                   'num_action_verbs', 'num_uppercase_words_subject', 
                   'subject_len', 'has_question']

# Scale numeric features
scaler = StandardScaler()
X_numeric = scaler.fit_transform(df[numeric_features])

# Combine features
X = np.hstack([X_text.toarray(), X_numeric])

# Train a logistic regression model
model = LogisticRegression(max_iter=1000, class_weight='balanced')
model.fit(X, df['Email_Priority'])

# Get feature importance
feature_importance = pd.DataFrame({
    'feature': vectorizer.get_feature_names_out().tolist() + numeric_features,
    'importance': np.abs(model.coef_[0])
})

# Sort by importance
feature_importance = feature_importance.sort_values('importance', ascending=False)

# Print top 20 features
print("\nTop 20 Most Important Features:")
print(feature_importance.head(20))

# Plot feature importance
plt.figure(figsize=(12, 6))
sns.barplot(x='importance', y='feature', data=feature_importance.head(20))
plt.title('Top 20 Most Important Features')
plt.tight_layout()
plt.savefig('feature_importance.png')
plt.close()

# Print correlation matrix
print("\nCorrelation Matrix:")
correlation_matrix = df[numeric_features + ['Email_Priority']].corr()
print(correlation_matrix)

# Plot correlation heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
plt.title('Correlation Matrix')
plt.tight_layout()
plt.savefig('correlation_matrix.png')
plt.close() 