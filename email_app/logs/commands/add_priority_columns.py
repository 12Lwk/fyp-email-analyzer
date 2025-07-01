from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

class Command(BaseCommand):
    help = 'Add priority-related columns to the emails table'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                self.stdout.write("Adding priority columns...")
                
                # Add new columns
                cursor.execute("""
                    ALTER TABLE emails
                    ADD COLUMN IF NOT EXISTS priority VARCHAR(10) DEFAULT 'MEDIUM',
                    ADD COLUMN IF NOT EXISTS priority_score FLOAT DEFAULT 0.0,
                    ADD COLUMN IF NOT EXISTS priority_explanation TEXT,
                    ADD COLUMN IF NOT EXISTS priority_last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                """)
                
                # Create index on priority column
                self.stdout.write("Creating index on priority column...")
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_emails_priority 
                    ON emails(priority)
                """)
                
                # Verify columns were added
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'emails' 
                    AND column_name LIKE 'priority%'
                    ORDER BY ordinal_position;
                """)
                
                self.stdout.write("\nNew columns added:")
                for column in cursor.fetchall():
                    self.stdout.write(f"{column[0]}: {column[1]}")
                
                self.stdout.write(self.style.SUCCESS('\nSuccessfully added priority columns and index'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
                raise 