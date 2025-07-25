import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from scipy.sparse import csr_matrix, hstack
import joblib

# Load the dataset
print("Loading dataset...")
email_data = pd.read_csv("FYP PART 2/Category Modeling/final_email_category_balanced.csv")

# Prepare text features
print("Preparing text features...")
vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    stop_words='english'
)
X_tfidf = vectorizer.fit_transform(email_data['Combined_Text'])

# Prepare numeric features
print("Preparing numeric features...")
numeric_features = email_data[['Log_Body_Length', 'avg_url_category']]

# Use MinMaxScaler for MultinomialNB (ensures non-negative values)
minmax_scaler = MinMaxScaler()
X_numeric_nb = minmax_scaler.fit_transform(numeric_features)
X_numeric_nb_sparse = csr_matrix(X_numeric_nb)

# Use StandardScaler for other models
standard_scaler = StandardScaler()
X_numeric_std = standard_scaler.fit_transform(numeric_features)
X_numeric_std_sparse = csr_matrix(X_numeric_std)

# Combine features
print("Combining features...")
X_final_nb = hstack([X_tfidf, X_numeric_nb_sparse])
X_final_std = hstack([X_tfidf, X_numeric_std_sparse])

# Prepare target variable
print("Preparing target variable...")
le = LabelEncoder()
y = le.fit_transform(email_data['Qwen2.5_Category'])

# Split the data
print("Splitting data into train and test sets...")
X_train_nb, X_test_nb, X_train_std, X_test_std, y_train, y_test = train_test_split(
    X_final_nb, X_final_std, y, test_size=0.2, random_state=42, stratify=y
)

# Initialize models
print("Initializing models...")
models = {
    "naive_bayes": (MultinomialNB(), True),  # True means use MinMaxScaler features
    "logistic_regression": (LogisticRegression(max_iter=1000, random_state=42), False),
    "svm": (LinearSVC(random_state=42), False),
    "random_forest": (RandomForestClassifier(n_estimators=100, random_state=42), False),
    "xgboost": (XGBClassifier(random_state=42), False)
}

# Train and evaluate models
print("\nTraining and evaluating models...")
for name, (model, use_minmax) in models.items():
    print(f"\nTraining {name}...")
    
    # Select appropriate feature matrix
    X_train = X_train_nb if use_minmax else X_train_std
    X_test = X_test_nb if use_minmax else X_test_std
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    print(f"Train accuracy: {train_score:.4f}")
    print(f"Test accuracy: {test_score:.4f}")
    
    # Save model
    model_path = f"FYP PART 2/Category Modeling/Category Models/Current Models/{name}_category_model.joblib"
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")

# Save feature transformers
print("\nSaving feature transformers...")
joblib.dump(vectorizer, "FYP PART 2/Category Modeling/Category Models/Current Models/tfidf_vectorizer.joblib")
joblib.dump(minmax_scaler, "FYP PART 2/Category Modeling/Category Models/Current Models/minmax_scaler.joblib")
joblib.dump(standard_scaler, "FYP PART 2/Category Modeling/Category Models/Current Models/standard_scaler.joblib")
joblib.dump(le, "FYP PART 2/Category Modeling/Category Models/Current Models/label_encoder.joblib")

print("\nTraining completed!") 