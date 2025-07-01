from django.urls import path
from django.shortcuts import redirect
from django.conf import settings
from .views import (
    auth_views, gmail_views, core_views, 
    email_views, voice_views, ai_views,
    dashboard_views
)

app_name = 'email_app'

# Root URL view function
def root_redirect(request):
    """Redirect root URL based on Gmail authentication status."""
    if request.session.get('is_gmail_authenticated'):
        return redirect('email_app:email_dashboard')
    return redirect('email_app:login')

urlpatterns = [
    # Root URL
    path('', root_redirect, name='root'),
    
    # Authentication URLs
    path('login/', auth_views.serve_login, name='login'),
    path('login/auth/', auth_views.login_view, name='login_auth'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('accounts/login/', auth_views.serve_login, name='accounts_login'),
    path('api/auth/check/', auth_views.check_auth, name='check_auth'),
    
    # Gmail Authentication URLs
    path('gmail/authenticate/', gmail_views.authenticate_gmail, name='authenticate_gmail'),
    path('gmail/callback/', gmail_views.gmail_callback, name='gmail_callback'),
    path('check_gmail_auth/', gmail_views.check_gmail_auth, name='check_gmail_auth'),
    
    # Email Sync URLs
    path('email/sync/initialize/', core_views.initialize_email_sync, name='initialize_sync'),
    path('email/sync/status/', core_views.check_sync_status, name='check_sync_status'),
    
    # Dashboard and Email Management URLs
    path('dashboard/', dashboard_views.email_dashboard, name='email_dashboard'),
    path('priority_dashboard/', dashboard_views.priority_dashboard, name='priority_dashboard'),
    path('inbox/', core_views.inbox_email, name='inbox_email'),
    path('inbox_email_detail/<str:email_id>/', email_views.inbox_email_detail, name='inbox_email_detail'),
    path('compose/', core_views.compose, name='compose'),
    path('send_email/', gmail_views.send_email, name='send_email'),
    path('delete_email/<int:email_id>/', email_views.delete_email, name='delete_email'),
    path('sent/', core_views.sent_email, name='sent_email'),
    path('sent_email_detail/<str:email_id>/', email_views.sent_email_detail, name='sent_email_detail'),
    path('spam/', core_views.spam_email, name='spam_email'),
    path('spam_email_detail/<str:email_id>/', core_views.spam_email_detail, name='spam_email_detail'),
    path('settings/', core_views.settings_view, name='settings'),

    # API routes
    path('api/gmail/sync/', gmail_views.sync_emails_view, name='sync_emails'),
    path('api/emails/send/', gmail_views.send_email_api, name='send_email_api'),
    path('api/emails/analyze/', ai_views.analyze_email, name='analyze_email'),
    path('api/emails/similar/<str:email_id>/', ai_views.similar_emails, name='similar_emails'),
    path('api/emails/suggest-reply/<str:email_id>/', ai_views.suggest_reply, name='suggest_reply'),
    path('api/emails/daily-summary/', ai_views.daily_summary, name='daily_summary'),
    path('api/emails/view/', email_views.view_emails, name='view_emails'),
    path('api/emails/spam/', email_views.get_spam_emails, name='get_spam_emails'),
    path('api/emails/correct_label/', email_views.correct_email_label, name='correct_email_label'),
    path('api/emails/<str:email_id>/', email_views.get_email_detail, name='get_email_detail'),
    path('api/dashboard-data/', dashboard_views.get_dashboard_data, name='dashboard_data'),
    path('upload_excel/', core_views.upload_excel, name='upload_excel'),
    
    # Voice command endpoints
    path('api/voice/process-command/', voice_views.process_voice_command, name='process_voice_command'),
    path('api/voice/read-email/', voice_views.read_email, name='read_email'),
    path('api/voice/reply/', voice_views.process_reply, name='process_reply'),
    path('api/voice/forward/', voice_views.process_forward, name='process_forward'),
    path('api/voice/compose/', voice_views.process_compose, name='process_compose'),
    
    # Google Cloud API endpoints
    path('api/voice/speech-to-text/', voice_views.speech_to_text, name='speech_to_text'),
    path('api/voice/text-to-speech/', voice_views.text_to_speech, name='text_to_speech'),
] 