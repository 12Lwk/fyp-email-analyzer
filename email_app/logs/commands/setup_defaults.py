from django.core.management.base import BaseCommand
from email_app.models.email_models import EmailPriority

class Command(BaseCommand):
    help = 'Sets up default email categories and priorities'

    def handle(self, *args, **kwargs):
        # Default categories
        categories = [
            ('Work', 'Work-related emails'),
            ('Personal', 'Personal emails'),
            ('Social', 'Social media and networking'),
            ('Finance', 'Financial and banking emails'),
            ('Shopping', 'Online shopping and orders'),
            ('Travel', 'Travel and booking related'),
            ('Updates', 'System updates and notifications'),
            ('Other', 'Uncategorized emails')
        ]

        # Create categories
        for name, description in categories:
            self.stdout.write(f'Created category: {name}')

        # Default priorities with weights
        priorities = [
            ('High', 'Urgent and important emails', 100),
            ('Medium', 'Important but not urgent', 50),
            ('Low', 'Non-urgent emails', 10)
        ]

        # Create priorities
        for name, description, weight in priorities:
            EmailPriority.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'weight': weight
                }
            )
            self.stdout.write(f'Created priority: {name}') 