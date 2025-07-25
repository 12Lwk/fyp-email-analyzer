import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os
from sklearn.impute import SimpleImputer

np.random.seed(42)

def load_data():
    """Load and prepare the dataset"""
    print("Loading dataset...")
    df = pd.read_csv('C:/Users/User/OneDrive - Asia Pacific University/APU Final Year Project/FYP Email Project Documents/Email Dataset Python/FYP PART 2/Priority Modeling/cleaned_priority_email_dataset.csv')
    
    print("\nDataset columns:")
    print(df.columns.tolist())
    
    print("\nInitial dataset shape:", df.shape)
    print("\nMissing values before cleaning:")
    print(df.isnull().sum())
    
    # Drop rows with missing values in key columns
    key_columns = ['Cleaned_Subject', 'Cleaned_Message', 'Email_Priority']
    df = df.dropna(subset=key_columns)
    
    print("\nDataset shape after dropping missing values:", df.shape)
    print("\nMissing values after cleaning:")
    print(df.isnull().sum())
    
    print("\nUnique Email_Priority values:", df['Email_Priority'].unique())
    print("Priority value counts:")
    print(df['Email_Priority'].value_counts())
    
    # Ensure Email_Priority is integer type
    df['Email_Priority'] = df['Email_Priority'].astype(int)
    
    return df

def create_preprocessor():
    """Create a preprocessing pipeline"""
    # Text features
    text_features = ['Cleaned_Subject', 'Cleaned_Message']
    
    # Numeric features - only include features that exist in the dataset
    numeric_features = [
        'urgency_flag', 'risk_flag', 'urgency_and_risk',
        'num_action_verbs', 'num_uppercase_words_subject',
        'subject_len', 'has_question'
    ]
    
    # Create preprocessing pipelines for text features
    subject_transformer = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.9,
            strip_accents='unicode',
            lowercase=True
        ))
    ])
    
    message_transformer = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=4000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.9,
            strip_accents='unicode',
            lowercase=True
        ))
    ])
    
    numeric_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    # Combine transformers with feature weights
    preprocessor = ColumnTransformer(
        transformers=[
            ('subject', subject_transformer, 'Cleaned_Subject'),
            ('message', message_transformer, 'Cleaned_Message'),
            ('num', numeric_transformer, numeric_features)
        ],
        remainder='drop',
        n_jobs=-1,
        transformer_weights={
            'subject': 1.5,    # Increase subject importance
            'message': 1.0,    # Base weight for message
            'num': 2.0         # Increase importance of numeric features
        }
    )
    
    return preprocessor

def train_model():
    """Train the priority prediction model"""
    # Load data
    df = load_data()
    
    # Split features and target
    X = df.drop('Email_Priority', axis=1)
    y = df['Email_Priority']
    
    # Calculate class weights to handle imbalance
    class_counts = y.value_counts()
    total_samples = len(y)
    class_weights = {
        0: total_samples / (3 * class_counts[0]) * 1.2,  # Boost low priority
        1: total_samples / (3 * class_counts[1]) * 0.8,  # Reduce medium priority
        2: total_samples / (3 * class_counts[2]) * 1.2   # Boost high priority
    }
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print("\nTraining set shape:", X_train.shape)
    print("Test set shape:", X_test.shape)
    
    # Create preprocessor
    preprocessor = create_preprocessor()
    
    # Create and train the model pipeline
    model = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(
            n_estimators=300,
            max_depth=25,
            min_samples_split=4,
            min_samples_leaf=2,
            class_weight=class_weights,
            criterion='entropy',
            max_features='sqrt',  # Use sqrt of features for better generalization
            bootstrap=True,       # Enable bootstrapping
            oob_score=True,       # Use out-of-bag score
            n_jobs=-1,
            random_state=42
        ))
    ])
    
    print("\nTraining model...")
    model.fit(X_train, y_train)
    
    # Evaluate the model
    print("\nEvaluating model...")
    y_pred = model.predict(X_test)
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Low', 'Medium', 'High']))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Save the model and preprocessor
    print("\nSaving model and preprocessor...")
    if not os.path.exists('Models'):
        os.makedirs('Models')
    
    joblib.dump(model, 'Models/priority_model_v2.joblib')
    print("Model saved successfully!")
    
    return model

if __name__ == "__main__":
    model = train_model() 