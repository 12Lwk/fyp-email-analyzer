from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from email_app.ai_services.prioritazation.prioritization_service import EmailPrioritizationService
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Update priorities for all emails in the database'

    def add_arguments(self, parser):
        parser.add_argument('--user_email', type=str, help='Email address to update priorities for. If not provided, updates all emails.')

    def handle(self, *args, **options):
        # Initialize priority service
        priority_service = EmailPrioritizationService()
        user_email = options.get('user_email')
        
        with connection.cursor() as cursor:
            try:
                # Get total count of emails
                if user_email:
                    cursor.execute("SELECT COUNT(*) FROM emails WHERE user_email = %s", [user_email])
                else:
                    cursor.execute("SELECT COUNT(*) FROM emails")
                total_emails = cursor.fetchone()[0]
                self.stdout.write(f"\nFound {total_emails} emails to process")
                
                # Fetch emails in batches
                batch_size = 100
                processed = 0
                updated = 0
                
                while processed < total_emails:
                    # Fetch batch of emails
                    if user_email:
                        cursor.execute("""
                            SELECT id, subject, snippet, sender, category 
                            FROM emails 
                            WHERE user_email = %s
                            ORDER BY id 
                            LIMIT %s OFFSET %s
                        """, [user_email, batch_size, processed])
                    else:
                        cursor.execute("""
                            SELECT id, subject, snippet, sender, category 
                            FROM emails 
                            ORDER BY id 
                            LIMIT %s OFFSET %s
                        """, [batch_size, processed])
                    
                    emails = cursor.fetchall()
                    if not emails:
                        break
                    
                    # Process each email in the batch
                    for email in tqdm(emails, desc=f"Processing batch {processed//batch_size + 1}"):
                        email_id, subject, snippet, sender, category = email
                        
                        # Get priority prediction
                        priority, confidence_scores, explanation = priority_service.predict_priority(
                            subject=subject or '',
                            body=snippet or '',
                            sender=sender or '',
                            category=category
                        )
                        
                        # Update database
                        cursor.execute("""
                            UPDATE emails 
                            SET 
                                priority = %s,
                                priority_score = %s,
                                priority_explanation = %s,
                                priority_last_updated = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, [
                            priority,
                            confidence_scores[priority],
                            explanation,
                            email_id
                        ])
                        
                        updated += 1
                    
                    # Commit batch
                    connection.commit()
                    processed += len(emails)
                    self.stdout.write(f"\nProcessed {processed}/{total_emails} emails ({(processed/total_emails*100):.1f}%)")
                
                self.stdout.write(self.style.SUCCESS(f'\nSuccessfully updated priorities for {updated} emails'))
                
                # Print statistics
                if user_email:
                    cursor.execute("""
                        SELECT priority, COUNT(*) 
                        FROM emails 
                        WHERE user_email = %s
                        GROUP BY priority 
                        ORDER BY priority
                    """, [user_email])
                else:
                    cursor.execute("""
                        SELECT priority, COUNT(*) 
                        FROM emails 
                        GROUP BY priority 
                        ORDER BY priority
                    """)
                stats = cursor.fetchall()
                
                self.stdout.write("\nPriority Distribution:")
                for priority, count in stats:
                    percentage = (count / total_emails) * 100
                    self.stdout.write(f"{priority}: {count} emails ({percentage:.1f}%)")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error updating priorities: {str(e)}'))
                connection.rollback()
                raise 