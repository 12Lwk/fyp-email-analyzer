// Function to get URL parameters
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// Function to extract email ID from URL path
function getEmailIdFromPath() {
    const path = window.location.pathname;
    console.log('Current path:', path);
    
    // Remove trailing slash if present
    const cleanPath = path.replace(/\/$/, '');
    console.log('Clean path:', cleanPath);
    
    // Split path and get the last segment
    const segments = cleanPath.split('/').filter(Boolean);
    console.log('Path segments:', segments);
    
    // Get the last segment as email ID
    const emailId = segments[segments.length - 1];
    console.log('Raw email ID:', emailId);
    
    if (emailId) {
        // Accept any alphanumeric characters and common special characters
        if (/^[a-zA-Z0-9-_]+$/.test(emailId)) {
            console.log('Valid email ID found:', emailId);
            return emailId;
        }
        console.error('Email ID contains invalid characters:', emailId);
    } else {
        console.error('No email ID found in path');
    }
    
    return emailId;
}

// Function to format date for email detail
function formatDetailDate(dateStr) {
    if (!dateStr) return 'Unknown Date';
    try {
    const date = new Date(dateStr);
        if (isNaN(date.getTime())) return 'Invalid Date';
    return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        hour12: true
    });
    } catch (error) {
        console.error('Error formatting date:', error);
        return 'Date Format Error';
    }
}

// Function to show error message with auto-hide
function showError(message, duration = 5000) {
    console.error('Error:', message);
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        console.warn('Alert container not found, creating one');
        const container = document.createElement('div');
        container.id = 'alertContainer';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1050;';
        document.body.appendChild(container);
    }
    
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show';
    alert.innerHTML = `
        <i class="fas fa-exclamation-circle me-2"></i>
        ${escapeHtml(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-hide after duration
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 150);
    }, duration);
}

// Function to escape HTML
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// Function to get label class based on label text
function getLabelClass(label) {
    if (!label) return 'default';
    const labelLower = label.toLowerCase();
    if (labelLower.includes('inbox')) return 'inbox';
    if (labelLower.includes('important')) return 'important';
    if (labelLower.includes('unread')) return 'unread';
    if (labelLower.includes('personal')) return 'personal';
    if (labelLower.includes('category_updates')) return 'updates';
    if (labelLower.includes('category_personal')) return 'personal';
    return 'default';
}

// Function to get CSRF token from cookies
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

// Function to load email details
async function loadEmailDetails() {
    console.log('Loading email details...');
    
    const loadingIndicator = document.getElementById('loadingContainer');
    const emailContainer = document.getElementById('emailContentContainer');
    const errorContainer = document.getElementById('errorContainer');
    
    // Show loading state
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    if (emailContainer) emailContainer.style.display = 'none';
    if (errorContainer) errorContainer.style.display = 'none';

    try {
        // Get email ID from URL path
        const pathSegments = window.location.pathname.split('/').filter(Boolean);
        const emailId = pathSegments[pathSegments.length - 1];
        
        if (!emailId) {
            throw new Error('Email ID not found in URL');
        }

        // Make API request
        const response = await fetch(`/api/emails/${emailId}/`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Email data received:', data);
        
        // Update email content
        if (emailContainer) {
            // Update subject in the page title
            const subjectElement = document.querySelector('h1');
            if (subjectElement) {
                subjectElement.textContent = data.subject || 'No Subject';
            }

            // Update sender information
            const fromElement = document.querySelector('.email-details .from');
            if (fromElement) {
                fromElement.innerHTML = `From: <span>${data.sender || 'Unknown Sender'}</span> ${data.sender_email || ''}`;
            }

            // Update recipients
            const toElement = document.querySelector('.email-details .to');
            if (toElement) {
                const recipients = Array.isArray(data.recipients) ? data.recipients.join(', ') : data.recipients;
                toElement.innerHTML = `To: <span>${recipients || 'No Recipients'}</span>`;
            }

            // Update date with proper formatting
            const dateElement = document.querySelector('.email-details .date');
            if (dateElement) {
                const formattedDate = data.date ? formatDetailDate(data.date) : 'Unknown Date';
                dateElement.innerHTML = `Date: <span>${formattedDate}</span>`;
            }

            // Update content/snippet
            const contentElement = document.querySelector('.email-content');
            if (contentElement) {
                // Get the email content from the data
                let emailContent = 'No Content';
                
                // Check data.data for nested response structure
                const emailData = data.data || data;
                
                if (emailData.snippet) {
                    emailContent = emailData.snippet;
                }

                // If content is an array, join it
                if (Array.isArray(emailContent)) {
                    emailContent = emailContent.join('\n');
                }

                // Replace newlines with <br> tags for proper HTML display
                emailContent = emailContent.replace(/\n/g, '<br>');

                contentElement.innerHTML = `
                    <div class="content-text">
                        ${emailContent}
                    </div>
                `;
            }

            // Update priority badge if it exists
            const priorityElement = document.querySelector('.priority-badge');
            if (priorityElement && data.priority) {
                priorityElement.textContent = data.priority.toUpperCase();
                priorityElement.className = `priority-badge ${data.priority.toLowerCase()}`;
            }

            // Update category badge if it exists
            const categoryElement = document.querySelector('.category-badge');
            if (categoryElement && data.category) {
                categoryElement.textContent = data.category;
                categoryElement.className = `category-badge ${data.category.toLowerCase().replace(/\s+/g, '-')}`;
            }

            // Show email container
            emailContainer.style.display = 'block';
        }

        // Hide loading indicator
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }

    } catch (error) {
        console.error('Error loading email:', error);
        
        // Hide loading indicator
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }

        // Show error message
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Failed to load email details: ${error.message}
                </div>
                <div class="text-center mt-3">
                    <a href="/inbox_email/" class="btn btn-primary">
                        <i class="fas fa-arrow-left me-1"></i> Return to Inbox
                    </a>
                </div>
            `;
            errorContainer.style.display = 'block';
        }
    }
}

// Function to handle back button click
function handleBackButtonClick() {
    // Check if there's a history state to go back to
    if (document.referrer && document.referrer.includes('/inbox')) {
        // If user came from inbox page, go back to previous page
        window.history.back();
    } else {
        // If no referrer or didn't come from inbox, redirect to inbox page
        window.location.href = '/inbox_email/';
    }
}

// Initialize page functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Email detail page loaded');
    
    // Load email details
    loadEmailDetails();

    // Initialize back button functionality
    const backButton = document.getElementById('backToInbox');
    if (backButton) {
        backButton.addEventListener('click', handleBackButtonClick);
    }

    // Initialize email actions
    initializeEmailActions();
});

function initializeEmailActions() {
    // Add event listeners for email actions (reply, delete, etc.)
    const replyBtn = document.querySelector('[onclick^="replyEmail"]');
    const replyAllBtn = document.querySelector('[onclick^="replyAllEmail"]');
    const forwardBtn = document.querySelector('[onclick^="forwardEmail"]');
    const deleteBtn = document.querySelector('[onclick^="deleteEmail"]');

    if (replyBtn) replyBtn.addEventListener('click', function(e) {
        e.preventDefault();
        const emailId = this.getAttribute('onclick').match(/'([^']+)'/)[1];
        replyEmail(emailId);
    });

    if (replyAllBtn) replyAllBtn.addEventListener('click', function(e) {
        e.preventDefault();
        const emailId = this.getAttribute('onclick').match(/'([^']+)'/)[1];
        replyAllEmail(emailId);
    });

    if (forwardBtn) forwardBtn.addEventListener('click', function(e) {
        e.preventDefault();
        const emailId = this.getAttribute('onclick').match(/'([^']+)'/)[1];
        forwardEmail(emailId);
    });

    if (deleteBtn) deleteBtn.addEventListener('click', function(e) {
        e.preventDefault();
        const emailId = this.getAttribute('onclick').match(/'([^']+)'/)[1];
        deleteEmail(emailId);
    });
}

// Show success message
function showSuccess(message) {
    // Create success alert if it doesn't exist
    let successAlert = document.getElementById('successAlert');
    if (!successAlert) {
        successAlert = document.createElement('div');
        successAlert.id = 'successAlert';
        successAlert.className = 'alert alert-success alert-dismissible fade show';
        successAlert.innerHTML = `
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            <i class="fas fa-check-circle me-2"></i>
            <span></span>
        `;
        document.querySelector('.container-fluid').insertBefore(successAlert, document.querySelector('.email-header'));
    }
    
    // Update message and show alert
    successAlert.querySelector('span').textContent = message;
    successAlert.style.display = 'block';
    
    // Auto hide after 3 seconds
    setTimeout(() => {
        successAlert.style.display = 'none';
    }, 3000);
} 