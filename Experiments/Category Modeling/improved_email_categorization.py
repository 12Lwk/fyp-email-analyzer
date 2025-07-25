import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import classification_report
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
import xgboost as xgb
from scipy.sparse import hstack, csr_matrix, vstack
import joblib
from tqdm import tqdm
import gc
import re
import warnings
warnings.filterwarnings('ignore')

def clean_text(text):
    """Clean and preprocess text."""
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def extract_email_features(subject, message):
    """Extract enhanced email-specific features."""
    # Basic length features
    subject_words = subject.split()
    message_words = message.split()
    subject_len = len(subject_words)
    message_len = len(message_words)
    
    # Question and exclamation features
    subject_questions = subject.count('?')
    message_questions = message.count('?')
    subject_exclamations = subject.count('!')
    message_exclamations = message.count('!')
    
    # Case features
    subject_upper = sum(1 for c in subject if c.isupper())
    message_upper = sum(1 for c in message if c.isupper())
    subject_upper_ratio = subject_upper / (len(subject) + 1)
    message_upper_ratio = message_upper / (len(message) + 1)
    
    # Digit features
    subject_digits = sum(1 for c in subject if c.isdigit())
    message_digits = sum(1 for c in message if c.isdigit())
    subject_digit_ratio = subject_digits / (len(subject) + 1)
    message_digit_ratio = message_digits / (len(message) + 1)
    
    # URL and email features
    has_url = int(bool(re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message)))
    has_email = int(bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message)))
    
    # Special character ratios
    subject_special = sum(not c.isalnum() and not c.isspace() for c in subject) / (len(subject) + 1)
    message_special = sum(not c.isalnum() and not c.isspace() for c in message) / (len(message) + 1)
    
    return np.array([
        subject_len,
        message_len,
        subject_questions,
        message_questions,
        subject_exclamations,
        message_exclamations,
        subject_upper_ratio,
        message_upper_ratio,
        subject_digit_ratio,
        message_digit_ratio,
        has_url,
        has_email,
        subject_special,
        message_special,
        subject_len / (message_len + 1),  # Subject-message length ratio
        (subject_questions + message_questions) / (subject_len + message_len + 1),  # Question density
        (subject_exclamations + message_exclamations) / (subject_len + message_len + 1)  # Exclamation density
    ])

def batch_process_features(df, batch_size=500):
    """Process features in batches to save memory."""
    features_list = []
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        batch_features = np.vstack([
            extract_email_features(row['Cleaned_Subject'], row['Cleaned_Message'])
            for _, row in batch.iterrows()
        ])
        features_list.append(batch_features)
    return np.vstack(features_list)

# Load and preprocess data
print("Loading dataset...")
email_data = pd.read_csv("FYP PART 2/Category Modeling/final_email_category_balanced.csv")
print(f"Initial dataset size: {len(email_data)}")

# Remove duplicates and very short texts
print("Cleaning data...")
email_data = email_data[
    (email_data['Cleaned_Subject'].str.len() >= 3) & 
    (email_data['Cleaned_Message'].str.len() >= 10)
].drop_duplicates(subset=['Cleaned_Subject', 'Cleaned_Message']).reset_index(drop=True)
print(f"Final dataset size: {len(email_data)}")

# Print class distribution
print("\nClass distribution:")
print(email_data['Qwen2.5_Category'].value_counts(normalize=True))

# Clean and prepare text data
print("\nPreparing text features...")
email_data['cleaned_subject'] = email_data['Cleaned_Subject'].apply(clean_text)
email_data['cleaned_message'] = email_data['Cleaned_Message'].apply(clean_text)
email_data['combined_text'] = email_data['cleaned_subject'] + ' SUBJECT_END ' + email_data['cleaned_message']

# Extract numerical features in smaller batches
print("Extracting numerical features...")
additional_features = batch_process_features(email_data, batch_size=500)

# Scale features
print("Scaling features...")
minmax_scaler = MinMaxScaler()
additional_features_scaled = minmax_scaler.fit_transform(additional_features)
del additional_features
gc.collect()

# Prepare text vectorizer with optimized parameters
print("Preparing vectorizer...")
vectorizer = TfidfVectorizer(
    max_features=2000,
    ngram_range=(1, 3),  # Include trigrams
    min_df=15,
    max_df=0.85,
    stop_words='english',
    sublinear_tf=True,  # Apply sublinear scaling
    norm='l2',
    use_idf=True,
    smooth_idf=True
)

# Initial vectorization
print("Vectorizing text...")
X_text = vectorizer.fit_transform(email_data['combined_text'])
del email_data['combined_text'], email_data['cleaned_subject'], email_data['cleaned_message']
gc.collect()

# Convert to sparse matrix and combine features
print("Combining features...")
additional_features_sparse = csr_matrix(additional_features_scaled)
X = hstack([X_text, additional_features_sparse]).tocsr()
del X_text, additional_features_sparse, additional_features_scaled
gc.collect()

# Prepare target variables
y = email_data['Qwen2.5_Category']
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Define models with optimized parameters
models = {
    'svm': LinearSVC(
        class_weight='balanced',
        dual=False,
        max_iter=2000,
        random_state=42,
        C=1.0
    ),
    'lr': LogisticRegression(
        class_weight='balanced',
        max_iter=2000,
        random_state=42,
        n_jobs=-1,
        C=1.0,
        solver='saga',
        multi_class='multinomial'
    ),
    'nb': MultinomialNB(
        alpha=0.5,
        fit_prior=True
    ),
    'xgb': xgb.XGBClassifier(
        tree_method='hist',
        max_depth=7,
        learning_rate=0.05,
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
        enable_categorical=False,
        use_label_encoder=False,
        objective='multi:softmax',
        num_class=len(np.unique(y_encoded)),
        verbosity=2,
        max_bin=256,
        grow_policy='lossguide',
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1
    )
}

# Train and evaluate models
print("\nTraining models...")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
trained_models = {}

for name, model in models.items():
    print(f"\nTraining {name}...")
    try:
        scores = []
        y_train_data = y_encoded if name == 'xgb' else y
        
        for fold, (train_idx, val_idx) in enumerate(cv.split(X, y_encoded), 1):
            print(f"Fold {fold}/5")
            
            # Handle data based on model type
            if name == 'xgb':
                # Convert to DMatrix format for XGBoost with CPU parameters
                X_train = X[train_idx]
                X_val = X[val_idx]
                y_train = y_train_data[train_idx]
                y_val = y_train_data[val_idx]
                
                dtrain = xgb.DMatrix(X_train, label=y_train, enable_categorical=False)
                dval = xgb.DMatrix(X_val, label=y_val, enable_categorical=False)
                
                # Get parameters from model
                params = model.get_params()
                params.update({
                    'tree_method': 'hist',
                    'objective': 'multi:softmax',
                    'num_class': len(np.unique(y_encoded)),
                    'max_bin': 256,
                    'grow_policy': 'lossguide',
                    'subsample': 0.8,
                    'colsample_bytree': 0.8
                })
                
                # Train using native API with early stopping
                bst = xgb.train(
                    params,
                    dtrain,
                    num_boost_round=100,
                    evals=[(dtrain, 'train'), (dval, 'val')],
                    early_stopping_rounds=10,
                    verbose_eval=True
                )
                
                # Predict
                y_pred = bst.predict(dval)
                
                # Convert predictions to original labels
                y_val_display = label_encoder.inverse_transform(y_val)
                y_pred_display = label_encoder.inverse_transform(y_pred.astype(int))
                score = (y_val_display == y_pred_display).mean()
                
            elif name == 'nb':
                # Ensure features are non-negative for Naive Bayes
                X_train = X[train_idx]
                X_val = X[val_idx]
                if X_train.min() < 0:
                    print("Warning: Negative values found, using absolute values for Naive Bayes")
                    X_train = abs(X_train)
                    X_val = abs(X_val)
                y_train = y_train_data[train_idx]
                y_val = y_train_data[val_idx]
                model.fit(X_train, y_train)
                y_pred = model.predict(X_val)
                score = (y_val == y_pred).mean()
            
            else:
                X_train = X[train_idx]
                X_val = X[val_idx]
                y_train = y_train_data[train_idx]
                y_val = y_train_data[val_idx]
                model.fit(X_train, y_train)
                y_pred = model.predict(X_val)
                score = (y_val == y_pred).mean()
            
            scores.append(score)
            print(f"Accuracy: {score:.4f}")
            
            if name == 'xgb':
                print("\nClassification Report:")
                print(classification_report(y_val_display, y_pred_display))
            else:
                print("\nClassification Report:")
                print(classification_report(y_val, y_pred))
            
            # Clear memory
            del X_train, X_val, y_train, y_val, y_pred
            if name == 'xgb':
                del y_val_display, y_pred_display, dtrain, dval, bst
            gc.collect()
        
        print(f"\nAverage CV score: {np.mean(scores):.4f} (+/- {np.std(scores) * 2:.4f})")
        
        # Train final model
        print(f"Training final {name} model...")
        if name == 'xgb':
            # Train final model using native API
            dtrain = xgb.DMatrix(X, label=y_encoded)
            params = model.get_params()
            params['objective'] = 'multi:softmax'
            params['num_class'] = len(np.unique(y_encoded))
            
            bst = xgb.train(
                params,
                dtrain,
                num_boost_round=100,
                verbose_eval=10
            )
            
            # Create a wrapper model that uses the trained booster
            model = xgb.XGBClassifier()
            model._Booster = bst
            model.n_classes_ = len(np.unique(y_encoded))
            
            del dtrain, bst
            gc.collect()
            
        elif name == 'nb':
            if X.min() < 0:
                X_final = abs(X)
            else:
                X_final = X
            model.fit(X_final, y)
        else:
            model.fit(X, y)
        
        # Save model
        model_path = f"FYP PART 2/Category Modeling/Category Models/Current Models/{name}_category_model.joblib"
        model_data = {
            'model': model,
            'vectorizer': vectorizer,
            'scaler': minmax_scaler,
            'label_encoder': label_encoder if name == 'xgb' else None
        }
        joblib.dump(model_data, model_path)
        print(f"Model saved to {model_path}")
        
        trained_models[name] = model
        gc.collect()
        
    except Exception as e:
        print(f"Error training {name}: {str(e)}")
        continue

# Modify ensemble to include XGBoost and use soft voting
print("\nTraining ensemble model...")
try:
    estimators = [
        ('svm', trained_models['svm']),
        ('lr', trained_models['lr']),
        ('nb', trained_models['nb']),
        ('xgb', trained_models['xgb'])
    ]
    
    from sklearn.ensemble import VotingClassifier
    ensemble = VotingClassifier(estimators=estimators, voting='soft')
    ensemble.fit(X, y)
    
    ensemble_path = "FYP PART 2/Category Modeling/Category Models/Current Models/ensemble_category_model.joblib"
    ensemble_data = {
        'model': ensemble,
        'vectorizer': vectorizer,
        'scaler': minmax_scaler
    }
    joblib.dump(ensemble_data, ensemble_path)
    print(f"Ensemble model saved to {ensemble_path}")
    
except Exception as e:
    print(f"Error training ensemble: {str(e)}")

print("\nTraining completed!") 