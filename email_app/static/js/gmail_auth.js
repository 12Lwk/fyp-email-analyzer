// Gmail Authentication Handler
class GmailAuthHandler {
    constructor() {
        this.authButton = document.querySelector('#gmail-auth-btn');
        this.errorMessage = document.querySelector('#error-message');
        this.setupEventListeners();
    }

    setupEventListeners() {
        if (this.authButton) {
            this.authButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleAuth();
            });
        }
    }

    async handleAuth() {
        try {
            // Show loading state
            this.authButton.disabled = true;
            this.authButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Connecting...';

            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            // Make request to backend
            const response = await fetch('/gmail/authenticate/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.status === 'success' && data.auth_url) {
                // Redirect to Google's auth page
                window.location.href = data.auth_url;
            } else {
                throw new Error(data.message || 'Failed to initialize Gmail authentication');
            }

        } catch (error) {
            console.error('Gmail auth error:', error);
            // Show error message
            if (this.errorMessage) {
                this.errorMessage.textContent = 'Failed to connect to Gmail. Please try again.';
                this.errorMessage.style.display = 'block';
            }
        } finally {
            // Reset button state
            if (this.authButton) {
                this.authButton.disabled = false;
                this.authButton.innerHTML = '<i class="fab fa-google"></i> Authenticate with Gmail';
            }
        }
    }

    // Handle auth callback
    static handleCallback(code, state) {
        // This will be called after returning from Google's auth page
        fetch('/gmail/callback/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ code, state }),
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                window.location.href = data.redirect_url || '/email/dashboard/';
            } else {
                throw new Error(data.message || 'Authentication failed');
            }
        })
        .catch(error => {
            console.error('Callback error:', error);
            // Redirect to login with error
            window.location.href = '/login/?error=' + encodeURIComponent('Failed to complete Gmail authentication');
        });
    }
}

// Initialize handler
document.addEventListener('DOMContentLoaded', () => {
    new GmailAuthHandler();
}); 