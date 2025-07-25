import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier

# Load the dataset
print("Loading dataset...")
email_data = pd.read_csv("FYP PART 2/Category Modeling/final_email_category_balanced.csv")

# Remove duplicates
print("\nRemoving duplicates...")
email_data = email_data.drop_duplicates(subset=['Combined_Text'])
print(f"Dataset size after removing duplicates: {len(email_data)}")

# Check class distribution
print("\nClass distribution in the dataset:")
print(email_data['Qwen2.5_Category'].value_counts(normalize=True))

# Analyze text length distribution
print("\nAnalyzing text length distribution:")
email_data['text_length'] = email_data['Combined_Text'].str.len()
print(email_data['text_length'].describe())

# Check for potential data leakage
print("\nChecking for potential data leakage...")
category_words = set()
for category in email_data['Qwen2.5_Category'].unique():
    category_words.update(category.lower().split())

text_contains_category = email_data['Combined_Text'].str.lower().apply(
    lambda x: any(word in x for word in category_words)
)
print(f"Number of texts containing category words: {text_contains_category.sum()}")
print(f"Percentage: {text_contains_category.mean():.2%}")

# Sample some examples where category words appear in text
if text_contains_category.sum() > 0:
    print("\nSample of texts containing category words:")
    samples = email_data[text_contains_category].sample(5)
    for _, row in samples.iterrows():
        print(f"\nCategory: {row['Qwen2.5_Category']}")
        print(f"Text: {row['Combined_Text'][:200]}...")

# Analyze feature importance with a smaller sample
print("\nAnalyzing feature importance with a sample...")
sample_size = min(10000, len(email_data))
sample_data = email_data.sample(sample_size, random_state=42)

vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X_tfidf = vectorizer.fit_transform(sample_data['Combined_Text'])

numeric_features = sample_data[['Log_Body_Length', 'avg_url_category']]
scaler = StandardScaler()
X_numeric = scaler.fit_transform(numeric_features)
X_final = np.hstack([X_tfidf.toarray(), X_numeric])

# Train RF to get feature importance
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_final, sample_data['Qwen2.5_Category'])

# Get top 20 most important features
feature_names = vectorizer.get_feature_names_out()
feature_importance = pd.DataFrame({
    'feature': list(feature_names) + ['Log_Body_Length', 'avg_url_category'],
    'importance': rf.feature_importances_
})
feature_importance = feature_importance.sort_values('importance', ascending=False)
print("\nTop 20 most important features:")
print(feature_importance.head(20))

# Check for potential overfitting
print("\nAnalyzing potential overfitting...")
X_train, X_test, y_train, y_test = train_test_split(
    X_final, sample_data['Qwen2.5_Category'], 
    test_size=0.2, random_state=42, 
    stratify=sample_data['Qwen2.5_Category']
)

# Train and evaluate on different sample sizes
sample_sizes = [0.1, 0.2, 0.5, 1.0]
results = []

for size in sample_sizes:
    n_samples = int(len(X_train) * size)
    X_subset = X_train[:n_samples]
    y_subset = y_train[:n_samples]
    
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_subset, y_subset)
    
    train_score = rf.score(X_subset, y_subset)
    test_score = rf.score(X_test, y_test)
    results.append((size, train_score, test_score))

print("\nLearning curve analysis:")
for size, train_score, test_score in results:
    print(f"Training size: {size:.1%}, Train accuracy: {train_score:.4f}, Test accuracy: {test_score:.4f}")

# Check for potential issues in the dataset
print("\nChecking for potential dataset issues...")
print("\nSample of very short texts:")
short_texts = email_data[email_data['Combined_Text'].str.len() < 10]
print(short_texts[['Combined_Text', 'Qwen2.5_Category']].head())

print("\nSample of very long texts:")
long_texts = email_data[email_data['Combined_Text'].str.len() > 10000]
print(long_texts[['Combined_Text', 'Qwen2.5_Category']].head()) 