import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
import matplotlib.pyplot as plt
import seaborn as sns
from imblearn.over_sampling import SMOTE
import joblib
import os
import json
from datetime import datetime
import string
from collections import Counter

# Set random seed for reproducibility
np.random.seed(42)

# Define the base directory for saving results
BASE_DIR = r"C:/Users/User/OneDrive - Asia Pacific University/APU Final Year Project/FYP Email Project Documents/Email Dataset Python/Model Building/Categorization"
RESULTS_DIR = os.path.join(BASE_DIR, "Model Results")

# Create results directory if it doesn't exist
os.makedirs(RESULTS_DIR, exist_ok=True)

# Function to save run history
def save_run_history(model_name, status, accuracy=None, error=None):
    history_file = os.path.join(RESULTS_DIR, "run_history.json")
    
    # Load existing history or create new
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            history = json.load(f)
    else:
        history = []
    
    # Create new entry
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": model_name,
        "status": status,
        "accuracy": accuracy,
        "error": str(error) if error else None
    }
    
    # Add to history
    history.append(entry)
    
    # Save updated history
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=4)

def clean_text(text, category_words=None):
    """More aggressive text cleaning function that removes category words"""
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove category words if provided
    if category_words:
        for word in category_words:
            text = re.sub(r'\b' + re.escape(word) + r'\b', ' ', text)
    
    # Remove URLs and replace with placeholder
    text = re.sub(r'https?://\S+|www\.\S+', ' url ', text)
    
    # Remove email addresses and replace with placeholder
    text = re.sub(r'\S+@\S+', ' email ', text)
    
    # Remove phone numbers
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', ' phone ', text)
    
    # Remove dates
    text = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', ' date ', text)
    
    # Remove times
    text = re.sub(r'\b\d{1,2}:\d{2}\s*(?:AM|PM)?\b', ' time ', text)
    
    # Remove numbers
    text = re.sub(r'\b\d+\b', ' number ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?]', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_features(df):
    """Extract structural and content features with noise"""
    features = pd.DataFrame()
    
    # Text length features with noise
    features['subject_length'] = df['Subject'].apply(len) + np.random.normal(0, 1, len(df))
    features['message_length'] = df['Message'].apply(len) + np.random.normal(0, 1, len(df))
    
    # Word count features with noise
    features['subject_word_count'] = df['Subject'].apply(lambda x: len(x.split())) + np.random.normal(0, 0.5, len(df))
    features['message_word_count'] = df['Message'].apply(lambda x: len(x.split())) + np.random.normal(0, 0.5, len(df))
    
    # Case features with noise
    features['subject_upper_ratio'] = df['Subject'].apply(lambda x: sum(1 for c in x if c.isupper()) / max(len(x), 1)) + np.random.normal(0, 0.01, len(df))
    features['message_upper_ratio'] = df['Message'].apply(lambda x: sum(1 for c in x if c.isupper()) / max(len(x), 1)) + np.random.normal(0, 0.01, len(df))
    
    # URL features
    features['url_count'] = df['Message'].apply(lambda x: len(re.findall(r'https?://\S+|www\.\S+', x)))
    features['has_url'] = (features['url_count'] > 0).astype(int)
    
    # Question features
    features['subject_has_question'] = df['Subject'].apply(lambda x: '?' in x).astype(int)
    features['message_has_question'] = df['Message'].apply(lambda x: '?' in x).astype(int)
    
    # Special character features with noise
    features['subject_special_char_ratio'] = df['Subject'].apply(lambda x: sum(1 for c in x if not c.isalnum() and c != ' ') / max(len(x), 1)) + np.random.normal(0, 0.01, len(df))
    features['message_special_char_ratio'] = df['Message'].apply(lambda x: sum(1 for c in x if not c.isalnum() and c != ' ') / max(len(x), 1)) + np.random.normal(0, 0.01, len(df))
    
    # Add some random noise to all features
    for col in features.columns:
        if col not in ['has_url', 'subject_has_question', 'message_has_question']:
            features[col] = features[col] + np.random.normal(0, 0.01, len(df))
    
    return features

def check_data_leakage(df):
    """Check for potential data leakage"""
    print("\nChecking for data leakage...")
    
    # 1. Check if category words appear in subject/message
    category_words = set()
    for category in df['Category'].unique():
        words = category.lower().split()
        category_words.update(words)
    
    # Check subject leakage
    subject_leakage = df['Subject'].str.lower().apply(
        lambda x: any(word in x for word in category_words)
    ).mean()
    print(f"Category words found in {subject_leakage:.2%} of subjects")
    
    # Check message leakage
    message_leakage = df['Message'].str.lower().apply(
        lambda x: any(word in x for word in category_words)
    ).mean()
    print(f"Category words found in {message_leakage:.2%} of messages")
    
    # 2. Check for duplicate records
    duplicates = df.duplicated(subset=['Subject', 'Message']).sum()
    print(f"\nFound {duplicates} duplicate records")
    
    # 3. Check class distribution
    class_dist = df['Category'].value_counts(normalize=True)
    print("\nClass distribution:")
    print(class_dist)
    
    # 4. Check for exact matches between train and test
    return {
        'subject_leakage': subject_leakage,
        'message_leakage': message_leakage,
        'duplicates': duplicates,
        'class_dist': class_dist
    }

def validate_train_test_split(X_train, X_test, y_train, y_test):
    """Validate the train-test split"""
    print("\nValidating train-test split...")
    
    # Check for common subjects/messages
    train_subjects = set(X_train['Subject'])
    test_subjects = set(X_test['Subject'])
    common_subjects = train_subjects.intersection(test_subjects)
    print(f"Found {len(common_subjects)} common subjects between train and test")
    
    # Check class distribution in train and test
    train_dist = pd.Series(y_train).value_counts(normalize=True)
    test_dist = pd.Series(y_test).value_counts(normalize=True)
    print("\nClass distribution in train set:")
    print(train_dist)
    print("\nClass distribution in test set:")
    print(test_dist)
    
    return {
        'common_subjects': len(common_subjects),
        'train_dist': train_dist,
        'test_dist': test_dist
    }

# Load the dataset
file_path = os.path.join(BASE_DIR, "cleaned_category_email_dataset.csv")
df = pd.read_csv(file_path)

# Get category words for cleaning
category_words = set()
for category in df['Category'].unique():
    words = category.lower().split()
    category_words.update(words)

# Remove duplicates before any processing
df = df.drop_duplicates(subset=['Subject', 'Message'])

# Clean text with category word removal
df['Subject'] = df['Subject'].apply(lambda x: clean_text(x, category_words))
df['Message'] = df['Message'].apply(lambda x: clean_text(x, category_words))

# Combine text features
df['Combined_Text'] = df['Subject'] + ' ' + df['Message']

# Initialize TF-IDF vectorizer
tfidf_vectorizer = TfidfVectorizer(
    max_features=2000,
    ngram_range=(1, 2),
    min_df=10,
    max_df=0.8,
    stop_words='english',
    sublinear_tf=True
)

# Vectorize the text
X = tfidf_vectorizer.fit_transform(df['Combined_Text'])
y = df['Category']

# Use KFold for more robust validation
kf = KFold(n_splits=5, shuffle=True, random_state=42)

# Initialize models with more conservative parameters
models = {
    'Random Forest': RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42
    ),
    'SVM': SVC(
        kernel='linear',
        C=0.1,
        probability=True,
        random_state=42
    ),
    'Naive Bayes': MultinomialNB(
        alpha=1.0
    ),
    'Logistic Regression': LogisticRegression(
        max_iter=1000,
        C=0.1,
        random_state=42
    )
}

# Cross-validation results
cv_results = {}
for name, model in models.items():
    print(f"\nTraining {name} with cross-validation...")
    try:
        # Perform cross-validation
        scores = cross_val_score(
            model, 
            X, 
            y,
            cv=kf,
            scoring='accuracy'
        )
        
        cv_results[name] = {
            'mean_accuracy': scores.mean(),
            'std_accuracy': scores.std(),
            'scores': scores
        }
        
        print(f"Mean CV Accuracy: {scores.mean():.4f} (±{scores.std():.4f})")
        
    except Exception as e:
        print(f"Error in cross-validation for {name}: {str(e)}")
        save_run_history(name, "error", error=str(e))

# Save cross-validation results
with open(os.path.join(RESULTS_DIR, 'cross_validation_results.txt'), 'w') as f:
    f.write("Cross-Validation Results:\n")
    f.write("=" * 50 + "\n")
    for name, result in cv_results.items():
        f.write(f"\n{name}:\n")
        f.write(f"Mean Accuracy: {result['mean_accuracy']:.4f}\n")
        f.write(f"Standard Deviation: {result['std_accuracy']:.4f}\n")
        f.write(f"Individual Fold Scores: {result['scores']}\n")

# Save the vectorizer
joblib.dump(tfidf_vectorizer, os.path.join(RESULTS_DIR, 'tfidf_vectorizer.joblib'))

# Initial data validation
leakage_info = check_data_leakage(df)

# Clean text
df['Subject'] = df['Subject'].apply(clean_text)
df['Message'] = df['Message'].apply(clean_text)

# Split data first to prevent leakage
X = df[['Subject', 'Message']]
y = df['Category']

# Validate split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.2, 
    random_state=42, 
    stratify=y
)
split_info = validate_train_test_split(X_train, X_test, y_train, y_test)

# Save validation results
with open(os.path.join(RESULTS_DIR, 'data_validation.txt'), 'w') as f:
    f.write("Data Leakage Analysis:\n")
    f.write("=" * 50 + "\n")
    f.write(f"Category words in subjects: {leakage_info['subject_leakage']:.2%}\n")
    f.write(f"Category words in messages: {leakage_info['message_leakage']:.2%}\n")
    f.write(f"Duplicate records: {leakage_info['duplicates']}\n")
    f.write("\nClass Distribution:\n")
    f.write(str(leakage_info['class_dist']))
    
    f.write("\n\nTrain-Test Split Analysis:\n")
    f.write("=" * 50 + "\n")
    f.write(f"Common subjects between train and test: {split_info['common_subjects']}\n")
    f.write("\nTrain set distribution:\n")
    f.write(str(split_info['train_dist']))
    f.write("\nTest set distribution:\n")
    f.write(str(split_info['test_dist']))

# Extract features separately for train and test
train_features = extract_features(X_train)
test_features = extract_features(X_test)

# Scale numeric features
scaler = StandardScaler()
X_train_numeric = scaler.fit_transform(train_features)
X_test_numeric = scaler.transform(test_features)

# Combine features
X_train_combined = np.hstack([X_train_numeric, X_train_numeric])
X_test_combined = np.hstack([X_test_numeric, X_test_numeric])

# Encode target variable
label_encoder = LabelEncoder()
y_train_encoded = label_encoder.fit_transform(y_train)
y_test_encoded = label_encoder.transform(y_test)

# Balance the training data using SMOTE
smote = SMOTE(random_state=42)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train_combined, y_train_encoded)

# Train and evaluate models
results = {}
for name, model in models.items():
    print(f"\nTraining {name}...")
    try:
        # Train the model
        model.fit(X_train_balanced, y_train_balanced)
        
        # Make predictions
        y_pred = model.predict(X_test_combined)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test_encoded, y_pred)
        report = classification_report(y_test_encoded, y_pred, target_names=label_encoder.classes_)
        
        # Store results
        results[name] = {
            'model': model,
            'accuracy': accuracy,
            'report': report
        }
        
        # Save the model
        model_path = os.path.join(RESULTS_DIR, f'{name.lower().replace(" ", "_")}_model.joblib')
        joblib.dump(model, model_path)
        
        # Save run history
        save_run_history(name, "success", accuracy=accuracy)
        
        print(f"Accuracy: {accuracy:.4f}")
        print("Classification Report:")
        print(report)
        
    except Exception as e:
        print(f"Error training {name}: {str(e)}")
        save_run_history(name, "error", error=str(e))

# Create and train ensemble with more conservative weights
ensemble = VotingClassifier(
    estimators=[
        ('rf', results['Random Forest']['model']),
        ('svm', results['SVM']['model']),
        ('lr', results['Logistic Regression']['model'])
    ],
    voting='soft',
    weights=[1, 1, 1]  # Equal weights
)

ensemble.fit(X_train_balanced, y_train_balanced)
y_pred_ensemble = ensemble.predict(X_test_combined)
ensemble_accuracy = accuracy_score(y_test_encoded, y_pred_ensemble)
ensemble_report = classification_report(y_test_encoded, y_pred_ensemble, target_names=label_encoder.classes_)

# Save ensemble results
results['Ensemble'] = {
    'model': ensemble,
    'accuracy': ensemble_accuracy,
    'report': ensemble_report
}

# Save the ensemble model
joblib.dump(ensemble, os.path.join(RESULTS_DIR, 'ensemble_model.joblib'))

# Save vectorizer and scaler
joblib.dump(tfidf_vectorizer, os.path.join(RESULTS_DIR, 'tfidf_vectorizer.joblib'))
joblib.dump(scaler, os.path.join(RESULTS_DIR, 'scaler.joblib'))

# Visualization
plt.figure(figsize=(12, 6))
accuracies = [results[name]['accuracy'] for name in results.keys()]
plt.bar(results.keys(), accuracies)
plt.title('Model Comparison - Accuracy Scores')
plt.xlabel('Models')
plt.ylabel('Accuracy')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(RESULTS_DIR, 'model_comparison.png'))
plt.close()

# Save final results to a text file
with open(os.path.join(RESULTS_DIR, 'model_results.txt'), 'w') as f:
    for name, result in results.items():
        f.write(f"\n{name}\n")
        f.write("=" * 50 + "\n")
        f.write(f"Accuracy: {result['accuracy']:.4f}\n")
        f.write("\nClassification Report:\n")
        f.write(result['report'])
        f.write("\n" + "=" * 50 + "\n")

print("\nAll models have been trained and evaluated. Results and visualizations have been saved to the Model Results directory.") 