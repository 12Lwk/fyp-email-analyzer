import pandas as pd
import numpy as np
from test_ensemble_models import predict_priority, explain_prediction
import time
from tqdm import tqdm

def load_gmail_data(file_path):
    """Load and preprocess Gmail dataset"""
    print("Loading Gmail dataset...")
    
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Map column names to expected format
        column_mapping = {
            'Subject': 'subject',
            'Message': 'body',
            'From': 'from',
            'Date': 'date'
        }
        
        # Rename columns if they exist
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_columns = ['subject', 'body']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in dataset")
        
        # Remove any rows with missing values in required columns
        df = df.dropna(subset=required_columns)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['subject', 'body'])
        
        print(f"Loaded {len(df)} emails")
        print("\nDataset columns:", df.columns.tolist())
        print(f"Sample email:\n{df.iloc[0]}\n")
        
        return df
        
    except Exception as e:
        print(f"Error loading dataset: {str(e)}")
        return pd.DataFrame()

def test_gmail_emails(df):
    """Test priority classification on Gmail dataset"""
    print("\nTesting Priority Classification on Gmail Emails")
    print("=" * 50)

    # Initialize counters and timers
    total_emails = 0
    correct_predictions = 0
    start_time = time.time()
    
    # Initialize results dictionary
    results = {
        'HIGH': {'correct': 0, 'total': 0},
        'MEDIUM': {'correct': 0, 'total': 0},
        'LOW': {'correct': 0, 'total': 0}
    }
    
    # Track statistics
    automated_count = 0
    promotional_count = 0
    notification_count = 0
    urgent_count = 0
    processing_times = []

    # Sample size for testing
    sample_size = 50
    test_emails = df.sample(n=min(sample_size, len(df)))

    print("Processing emails:", flush=True)
    for idx, email in tqdm(test_emails.iterrows(), total=len(test_emails)):
        try:
            email_start_time = time.time()
            
            # Extract email components
            subject = str(email['subject'])
            message = str(email['body'])
            sender = str(email['from']) if 'from' in email else None
            
            print(f"\nEmail {total_emails + 1}:")
            print("=" * 30)
            print(f"From: {sender}")
            print(f"Subject: {subject}")
            print(f"Message Preview: {message[:100]}...")
            print("-" * 30)
            
            # Predict priority
            priority, confidence_scores = predict_priority(subject, message, sender)
            explanation = explain_prediction(subject, message, priority, confidence_scores, sender)
            
            # Update statistics
            total_emails += 1
            if priority == 'HIGH':
                results['HIGH']['total'] += 1
            elif priority == 'MEDIUM':
                results['MEDIUM']['total'] += 1
            else:
                results['LOW']['total'] += 1
                
            # Track processing time
            email_time = time.time() - email_start_time
            processing_times.append(email_time)
            
            # Print prediction results
            print(f"Predicted Priority: {priority}")
            print(f"Confidence Scores:")
            print(f"  Low: {confidence_scores['low']:.0%}")
            print(f"  Medium: {confidence_scores['medium']:.0%}")
            print(f"  High: {confidence_scores['high']:.0%}")
            print(f"Explanation: {explanation}")
            
        except Exception as e:
            print(f"Error processing email {total_emails + 1}: {str(e)}")
            continue

    # Calculate statistics
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\nTest Results Summary")
    print("=" * 50)
    
    if total_emails > 0:
        print(f"Total Emails Tested: {total_emails}")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Average Time per Email: {total_time/total_emails:.2f} seconds")
        
        # Print priority distribution
        print("\nPriority Distribution:")
        for priority in ['HIGH', 'MEDIUM', 'LOW']:
            count = results[priority]['total']
            percentage = (count / total_emails) * 100 if total_emails > 0 else 0
            print(f"{priority}: {count} ({percentage:.1f}%)")
    else:
        print("No emails were successfully processed.")

def main():
    # Path to Gmail dataset
    gmail_file = '../gmail_data_leetakasocc_at_gmail_com_20250406_142204.csv'
    
    # Load and test
    df = load_gmail_data(gmail_file)
    if df is not None:
        test_gmail_emails(df)

if __name__ == "__main__":
    main() 