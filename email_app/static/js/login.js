document.addEventListener('DOMContentLoaded', function() {
    const googleLoginBtn = document.getElementById('gmail-auth-btn');
    const errorContainer = document.getElementById('error-container');
    const loadingOverlay = document.getElementById('loading-overlay');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');

    // Function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Function to show error message
    function showError(message) {
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
        setTimeout(() => {
            errorContainer.style.display = 'none';
        }, 5000);
    }

    // Handle URL parameters for error messages
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    if (error) {
        showError(decodeURIComponent(error));
    } else {
        errorContainer.style.display = 'none';
    }

    // Simulate progress for loading overlay
    function simulateProgress() {
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 100) progress = 100;
            
            progressBar.style.width = `${progress}%`;
            
            if (progress < 30) {
                progressText.textContent = 'Connecting to Gmail...';
            } else if (progress < 60) {
                progressText.textContent = 'Authenticating...';
            } else if (progress < 90) {
                progressText.textContent = 'Finalizing connection...';
            } else {
                progressText.textContent = 'Almost done!';
            }
            
            if (progress === 100) {
                clearInterval(interval);
            }
        }, 300);
        return interval;
    }

    // Handle Gmail login
    googleLoginBtn.addEventListener('click', async function(e) {
        e.preventDefault();
        
        try {
            // Show loading overlay
            loadingOverlay.style.display = 'flex';
            const progressInterval = simulateProgress();
            
            console.log('Attempting to authenticate with Gmail...');
            
            // Step 1: Authenticate with Gmail - using the correct endpoint
            const authResponse = await fetch('/gmail/authenticate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                credentials: 'same-origin'
            });
            
            clearInterval(progressInterval);
            progressBar.style.width = '100%';
            progressText.textContent = 'Authentication complete!';
            
            if (!authResponse.ok) {
                let errorMsg = 'Failed to authenticate with Gmail';
                try {
                    const errorData = await authResponse.json();
                    errorMsg = errorData.message || errorData.error || errorMsg;
                } catch (parseError) {
                    console.error('Error parsing response:', parseError);
                }
                throw new Error(errorMsg);
            }

            const authData = await authResponse.json();
            console.log('Auth response:', authData);
            
            if (authData.status === 'success') {
                // Redirect to the auth URL if provided
                if (authData.auth_url) {
                    window.location.href = authData.auth_url;
                } else {
                    throw new Error('No authentication URL provided');
                }
            } else {
                throw new Error(authData.message || 'Gmail authentication failed');
            }
        } catch (error) {
            console.error('Error:', error);
            loadingOverlay.style.display = 'none';
            showError(error.message || 'An error occurred during Gmail authentication');
        }
    });
});
