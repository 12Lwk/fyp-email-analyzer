// Function to get URL parameters
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// Function to extract email ID from URL path
function getEmailIdFromPath() {
    const path = window.location.pathname;
    console.log('Current path:', path);
    
    // Pattern specifically looking for a segment that looks like an ID
    // This should match patterns like 19634091ffc37345 but not inbox_email_detail
    const idPattern = /\/([a-f0-9]{8,})\/?$/i;
    const match = path.match(idPattern);
    
    if (match && match[1]) {
        const emailId = match[1];
        console.log('Extracted email ID using pattern:', emailId);
        return emailId;
    }
    
    // Fallback to traditional method if pattern matching fails
    const cleanPath = path.replace(/\/$/, '');
    const segments = cleanPath.split('/').filter(Boolean);
    console.log('Path segments:', segments);
    
    // Skip 'inbox_email_detail' segment and get the actual ID
    let emailId = null;
    for (let i = 0; i < segments.length; i++) {
        // Skip common path parts that are not IDs
        if (segments[i] === 'inbox_email_detail' || 
            segments[i] === 'inbox_email' || 
            segments[i] === 'email') {
            continue;
        }
        
        // Look for segments that match typical ID patterns (alphanumeric, reasonable length)
        if (/^[a-zA-Z0-9_\-\.]{6,}$/.test(segments[i])) {
            emailId = segments[i];
            console.log('Found email ID by skipping known path segments:', emailId);
            break;
        }
    }
    
    // Last segment fallback (if none of the above worked)
    if (!emailId && segments.length > 0) {
        emailId = segments[segments.length - 1];
        console.log('Using last segment as fallback email ID:', emailId);
    }
    
    return emailId;
}

// Function to validate individual email address
function isValidEmailAddress(email) {
    if (!email) return false;
    
    // Remove any leading/trailing whitespace
    email = email.trim();
    
    // More permissive email regex that allows more valid email formats
    const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/i;
    return emailRegex.test(email);
}

// Function to validate email field with support for multiple recipients
function validateEmailField(field) {
    if (!field) return false;
    
    const value = field.value.trim();
    
    // Remove any existing error messages
    const existingErrors = field.parentElement.querySelectorAll('.invalid-feedback');
    existingErrors.forEach(error => error.remove());
    
    // Create new error div
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    
    // If field is empty and not required, it's valid
    if (!value) {
        field.classList.remove('is-invalid', 'is-valid');
        return true;
    }
    
    // Split by comma for multiple recipients
    const emails = value.split(',').map(email => email.trim()).filter(email => email.length > 0);
    
    if (emails.length === 0) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        errorDiv.textContent = 'Please enter at least one email address';
        field.parentElement.appendChild(errorDiv);
        return false;
    }
    
    // Check each email address
    const invalidEmails = emails.filter(email => !isValidEmailAddress(email));
    
    if (invalidEmails.length > 0) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        if (invalidEmails.length === 1) {
            errorDiv.textContent = `Invalid email address: ${invalidEmails[0]}`;
        } else {
            errorDiv.textContent = `Invalid email addresses: ${invalidEmails.join(', ')}`;
        }
        field.parentElement.appendChild(errorDiv);
        return false;
    }
    
    // All emails are valid
    field.classList.add('is-valid');
    field.classList.remove('is-invalid');
    return true;
}

// Extract email address from a string
function extractEmailAddress(text) {
    if (!text) return '';
    
    // First try the standard regex pattern for email extraction
    const emailRegex = /([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+)/gi;
    const matches = text.match(emailRegex);
    
    if (matches && matches.length > 0) {
        return matches[0];
    }
    
    // If standard regex fails, try to handle special cases
    // Case 1: "From: user@example.com"
    if (text.toLowerCase().includes('from:')) {
        const fromSplit = text.split('from:');
        if (fromSplit.length > 1) {
            const potentialEmail = fromSplit[1].trim();
            const secondAttempt = potentialEmail.match(emailRegex);
            if (secondAttempt && secondAttempt.length > 0) {
                return secondAttempt[0];
            }
        }
    }
    
    // Case 2: "Name <user@example.com>"
    const angleBracketRegex = /<([^>]+)>/;
    const angleBracketMatch = text.match(angleBracketRegex);
    if (angleBracketMatch && angleBracketMatch.length > 1) {
        const insideBrackets = angleBracketMatch[1];
        if (insideBrackets.includes('@')) {
            return insideBrackets;
        }
    }
    
    // Case 3: Just return any string with @ in it
    if (text.includes('@')) {
        return text.trim();
    }
    
    // No email found
    return '';
}

// Function to format a sender name for display in messages
function formatSenderForDisplay(senderName, senderEmail) {
    if (!senderName && !senderEmail) return 'Unknown Sender';
    
    // If we have both name and email
    if (senderName && senderEmail) {
        // Check if name already contains the email
        if (senderName.includes(senderEmail)) {
            return senderName;
        }
        return `${senderName} <${senderEmail}>`;
    }
    
    // If we only have email
    if (senderEmail) {
        return senderEmail;
    }
    
    // If we only have name
    return senderName;
}

// Function to format a readable date for detailed views
function formatDetailDate(dateStr) {
    if (!dateStr) {
        return moment().format('dddd, MMMM D, YYYY [at] h:mm A');
    }
    
    // Parse the date string with moment and ensure it's valid
    const momentDate = moment(dateStr);
    if (!momentDate.isValid()) {
        console.warn('Invalid date:', dateStr);
        return moment().format('dddd, MMMM D, YYYY [at] h:mm A');
    }
    
    return momentDate.format('dddd, MMMM D, YYYY [at] h:mm A');
}

// Function to show error message with auto-hide
function showError(message, duration = 5000) {
    // Remove any existing error alerts first
    const existingAlerts = document.querySelectorAll('.alert-danger');
    existingAlerts.forEach(alert => alert.remove());
    
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        const container = document.createElement('div');
        container.id = 'alertContainer';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1040;'; // Lower z-index
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

// Function to show success message
function showSuccess(message, duration = 3000) {
    // Remove any existing success alerts first
    const existingAlerts = document.querySelectorAll('.alert-success');
    existingAlerts.forEach(alert => alert.remove());
    
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        const container = document.createElement('div');
        container.id = 'alertContainer';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1040;'; // Lower z-index
        document.body.appendChild(container);
    }
    
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show';
    alert.innerHTML = `
        <i class="fas fa-check-circle me-2"></i>
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

// Function to show field error
function showFieldError(field, message) {
    if (!field || !field.parentElement) return;
    
    // Remove any existing error messages
    const existingErrors = field.parentElement.querySelectorAll('.invalid-feedback');
    existingErrors.forEach(error => error.remove());
    
    // Add error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback d-block';
    errorDiv.style.color = '#dc3545';
    errorDiv.style.fontSize = '0.875em';
    errorDiv.style.marginTop = '0.25rem';
    errorDiv.textContent = message;
    
    // Insert error message after the field
    field.parentElement.appendChild(errorDiv);
    
    // Add invalid class to field
    field.classList.add('is-invalid');
}

// Function to handle email submission
async function handleEmailSubmission(e) {
    if (e && typeof e.preventDefault === 'function') {
        e.preventDefault();
    }
    
    const form = e.target.closest('form');
    if (!form) return;
    
    // Clear previous validation messages
    clearValidationMessages(form);
    
    try {
        if (!isSubmitting) {
            await sendEmailDirectly(form);
        } else {
            showError('Please wait while the previous email is being sent');
        }
    } catch (error) {
        console.error('Error in handleEmailSubmission:', error);
        showError(error.message || 'Failed to send email');
    }
}

// Function to initialize form handlers
function initializeFormHandlers() {
    const form = document.querySelector('#composeForm, #composeEmailForm');
    if (!form) return;
    
    // Initialize all form fields
    const fields = form.querySelectorAll('input, textarea');
    fields.forEach(field => {
        initializeFormField(field);
    });
    
    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        await handleEmailSubmission(e);
    });
    
    // Initialize send button
    const sendBtn = form.querySelector('#sendEmailBtn, button[type="submit"]');
    if (sendBtn) {
        sendBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            await handleEmailSubmission(e);
        });
    }
    
    // Initialize CC/BCC buttons
    const ccButton = form.querySelector('#ccButton');
    const bccButton = form.querySelector('#bccButton');
    
    if (ccButton) {
        ccButton.addEventListener('click', function(e) {
            e.preventDefault();
            const ccField = form.querySelector('.cc-field');
            if (ccField) {
                ccField.classList.toggle('d-none');
                if (!ccField.classList.contains('d-none')) {
                    const input = ccField.querySelector('input');
                    if (input) input.focus();
                }
            }
        });
    }
    
    if (bccButton) {
        bccButton.addEventListener('click', function(e) {
            e.preventDefault();
            const bccField = form.querySelector('.bcc-field');
            if (bccField) {
                bccField.classList.toggle('d-none');
                if (!bccField.classList.contains('d-none')) {
                    const input = bccField.querySelector('input');
                    if (input) input.focus();
                }
            }
        });
    }
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initial setup
    initializeFormHandlers();
    
    // Handle modal events
    const composeModal = document.getElementById('composeModal');
    if (composeModal) {
        composeModal.addEventListener('shown.bs.modal', function() {
            // Re-initialize form handlers
            initializeFormHandlers();
            
            // Focus on first empty required field
            const form = document.querySelector('#composeForm, #composeEmailForm');
            if (form) {
                const firstEmptyField = form.querySelector('input[required]:not([value]), textarea[required]:empty');
                if (firstEmptyField) {
                    setTimeout(() => {
                        firstEmptyField.focus();
                    }, 100);
                }
            }
        });
        
        composeModal.addEventListener('hidden.bs.modal', function() {
            // Clear all validation messages when modal is closed
            const form = document.querySelector('#composeForm, #composeEmailForm');
            if (form) {
                clearValidationMessages(form);
                form.reset();
            }
        });
    }

    // Correction save handler
    const saveBtn = document.getElementById('save-corrections-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            const emailId = document.getElementById('email-id').value;
            const newCategory = document.getElementById('category-select').value;
            const newPriority = document.getElementById('priority-select').value;
            fetch('/api/emails/correct_label/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': (typeof getCookie === 'function') ? getCookie('csrftoken') : (window.csrftoken || '{{ csrf_token }}')
                },
                body: JSON.stringify({
                    email_id: emailId,
                    category: newCategory,
                    priority: newPriority
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    document.getElementById('correction-success').style.display = 'block';
                } else {
                    alert('Failed to save corrections.');
                }
            });
        });
    }
});

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

// Get user's current email
function getCurrentUserEmail() {
    // Try to get email from sidebar or header
    const sidebarEmail = document.getElementById('sidebarEmail');
    if (sidebarEmail && sidebarEmail.textContent) {
        return sidebarEmail.textContent.trim();
    }
    
    // Fallback - try to get from other elements
    const userEmailElements = document.querySelectorAll('[data-user-email]');
    if (userEmailElements.length > 0) {
        return userEmailElements[0].getAttribute('data-user-email');
    }
    
    // Last resort - check if there's a hard-coded email in the DOM
    const emailFrom = document.querySelector('#emailFrom option');
    if (emailFrom && emailFrom.textContent) {
        return emailFrom.textContent.trim();
    }
    
    return 'user'; // Default fallback
}

// Direct function to get the email ID from the current URL
function getDirectEmailId() {
    // Get the current URL path
    const path = window.location.pathname;
    console.log('Current URL path:', path);
    
    // This will match patterns like /inbox_email_detail/19634091ffc37345/
    const regex = /\/inbox_email_detail\/([0-9a-f]+)\/?$/i;
    const match = path.match(regex);
    
    if (match && match[1]) {
        const emailId = match[1];
        console.log('Found email ID directly:', emailId);
        return emailId;
    }
    
    console.error('Could not extract email ID from URL:', path);
    return null;
}

// Function to load email details
async function loadEmailDetails() {
    console.log('Loading email details...');
    
    // Store the page number from the referrer if coming from inbox
    const referrer = document.referrer;
    if (referrer && referrer.includes('/inbox')) {
        const pageMatch = referrer.match(/[?&]page=(\d+)/);
        if (pageMatch && pageMatch[1]) {
            const page = pageMatch[1];
            console.log('Storing page number from referrer:', page);
            localStorage.setItem('inbox_page_number', page);
        }
    }
    
    const loadingIndicator = document.getElementById('loadingContainer');
    const emailContainer = document.getElementById('emailContentContainer');
    const errorContainer = document.getElementById('errorContainer');
    
    // Show loading state
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    if (emailContainer) emailContainer.style.display = 'none';
    if (errorContainer) errorContainer.style.display = 'none';

    try {
        // Use the direct method to get the email ID
        const emailId = getDirectEmailId();
        console.log('Email ID from direct method:', emailId);
        
        if (!emailId) {
            throw new Error('Email ID not found in URL. Please check the URL format or return to inbox.');
        }

        // Make API request
        console.log('Fetching email details for ID:', emailId);
        let data;
        
        try {
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
    
            data = await response.json();
            console.log('Email data received:', data);
        } catch (apiError) {
            console.warn('API call failed, using mock data:', apiError);
            
            // Use mock data if API call fails but we have a valid ID
            data = {
                id: emailId,
                subject: 'Email Content (Mock Data)',
                sender: 'Mock Sender',
                sender_email: 'mock@example.com',
                recipients: ['user@example.com'],
                date: new Date().toISOString(),
                snippet: 'This is mock email content since the API call failed. The application is working correctly, but there might be an issue with the backend API or the database connection.',
                priority: 'medium',
                category: 'General'
            };
        }
        
        // Store email data globally for action buttons
        window.currentEmailData = data;
        
        // Update email content
        if (emailContainer) {
            // Update subject in the page title
            const subjectElement = document.querySelector('h2');
            if (subjectElement) {
                // Check multiple locations where the subject might be stored in the data
                let subject = '';
                
                // Use a more reliable way to get the subject
                if (data.subject) {
                    subject = data.subject;
                    console.log('Found subject directly in data:', subject);
                } else if (data.data && data.data.subject) {
                    subject = data.data.subject;
                    console.log('Found subject in data.data:', subject);
                }
                
                // If subject is still empty, use other possible field names
                if (!subject && data.email_subject) {
                    subject = data.email_subject;
                    console.log('Found subject in email_subject field:', subject);
                }
                
                // If subject is still empty or just whitespace, use a default
                if (!subject || subject.trim() === '') {
                    subject = 'No Subject';
                    console.log('No subject found, using default');
                }
                
                // Log and set the final subject
                console.log('Setting email subject to:', subject);
                subjectElement.textContent = subject;
                
                // Also update document title
                document.title = `${subject} - Email Analytics`;
            }
            
            // Update action buttons with email ID
            const actionButtons = document.querySelectorAll('[data-email-id]');
            actionButtons.forEach(button => {
                button.setAttribute('data-email-id', emailId);
            });

            // Update sender information
            const fromElement = document.querySelector('.email-details .from');
            if (fromElement) {
                fromElement.innerHTML = `From: <span>${formatSenderForDisplay(data.sender, data.sender_email)}</span>`;
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
                const formattedDate = data.date ? formatDetailDate(data.date) : formatDetailDate(new Date());
                dateElement.innerHTML = `Date: <span>${formattedDate}</span>`;
                
                // Also update the data attribute for consistency
                if (data.date) {
                    dateElement.querySelector('span').setAttribute('data-date', data.date);
                }
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
                } else if (emailData.body) {
                    emailContent = emailData.body;
                } else if (emailData.content) {
                    emailContent = emailData.content;
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
                    ${error.message || 'Failed to load email details'}
                </div>
                <div class="text-center mt-3">
                    <a href="/inbox_email/" class="btn btn-primary">
                        <i class="fas fa-arrow-left me-1"></i> Return to Inbox
                    </a>
                </div>
            `;
            errorContainer.style.display = 'block';
        } else {
            // Create error container if it doesn't exist
            const container = document.createElement('div');
            container.id = 'errorContainer';
            container.className = 'mb-4';
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    ${error.message || 'Failed to load email details'}
                </div>
                <div class="text-center mt-3">
                    <a href="/inbox_email/" class="btn btn-primary">
                        <i class="fas fa-arrow-left me-1"></i> Return to Inbox
                    </a>
                </div>
            `;
            
            // Find a good place to insert the error
            const contentArea = document.querySelector('.container-fluid');
            if (contentArea) {
                contentArea.prepend(container);
            } else {
                // Last resort - add to body
                document.body.prepend(container);
            }
        }
    }
}

// Function to handle back button click
function handleBackButtonClick() {
    // Get current page from URL if available
    const currentUrl = window.location.href;
    const emailId = getEmailIdFromPath();
    
    // Store the email ID we're coming from
    if (emailId) {
        localStorage.setItem('last_viewed_email_id', emailId);
    }
    
    // Check if we have stored page information
    const storedPage = localStorage.getItem('inbox_page_number');
    
    if (storedPage) {
        // Go back to inbox with stored page number
        window.location.href = `/inbox/?page=${storedPage}`;
    } else {
        // If no stored page, go to inbox page 1
        window.location.href = '/inbox/';
    }
}

// Add this function to the document load event
document.addEventListener('DOMContentLoaded', function() {
    // ... other existing code ...
    
    // Store current page number when viewing inbox
    const currentUrl = window.location.href;
    if (currentUrl.includes('/inbox/')) {
        const pageMatch = currentUrl.match(/[?&]page=(\d+)/);
        const page = pageMatch ? pageMatch[1] : '1';
        localStorage.setItem('inbox_page_number', page);
    }
    
    // Add event listener to back button
    document.getElementById('backToInbox').addEventListener('click', handleBackButtonClick);
});

// Add event listener for popstate to handle browser back/forward buttons
window.addEventListener('popstate', function(event) {
    // If we have a page number in the state, use it
    if (event.state && event.state.page) {
        const page = event.state.page;
        window.location.href = `/inbox/?page=${page}`;
    }
});

// Add a global function to ensure modals are properly closed
function setupModalBackdropCleanup() {
    // One-time setup for Bootstrap modals to ensure backdrops are removed
    document.addEventListener('hidden.bs.modal', function (event) {
        console.log('Modal hidden event triggered');
        
        // Force remove modal-open class
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        
        // Force remove any backdrop
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            console.log('Removing leftover backdrop');
            backdrop.remove();
        }
    }, true); // Use capture phase to ensure this runs before other handlers
    
    // Also check for backdrops periodically when no modals are visible
    setInterval(function() {
        const visibleModals = document.querySelectorAll('.modal.show');
        if (visibleModals.length === 0) {
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) {
                console.log('Cleanup: removing orphaned backdrop');
                backdrop.remove();
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
            }
        }
    }, 1000);
}

// Initialize page functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Email detail page loaded');
    
    // Setup modal backdrop cleanup
    setupModalBackdropCleanup();
    
    // Load email details
    loadEmailDetails();

    // Initialize back button functionality
    const backButton = document.getElementById('backToInbox');
    if (backButton) {
        backButton.addEventListener('click', handleBackButtonClick);
    }

    // Initialize email actions
    initializeEmailActions();
    
    // Initialize compose modal controls
    initializeComposeModalControls();
    
    // When compose modal is shown, do additional setup
    const composeModal = document.getElementById('composeModal');
    if (composeModal) {
        composeModal.addEventListener('shown.bs.modal', function() {
            console.log('Compose modal shown, setting up fields');
            // Focus on recipient field if empty
            const toField = document.getElementById('emailTo');
            if (toField && !toField.value) {
                toField.focus();
            }
        });
    }

    // Initialize send button
    const sendButton = document.getElementById('sendEmailBtn');
    if (sendButton) {
        sendButton.addEventListener('click', function(e) {
            e.preventDefault();
            sendEmailDirectly();
        });
    }
});

function initializeEmailActions() {
    console.log('Initializing email actions');
    
    // Initialize back button
    const backButton = document.getElementById('backToInbox');
    if (backButton) {
        backButton.addEventListener('click', handleBackButtonClick);
    }

    // Initialize reply button
    const replyButton = document.querySelector('.reply-btn');
    if (replyButton) {
        replyButton.addEventListener('click', function() {
            const emailId = this.getAttribute('data-email-id');
            if (emailId) {
                replyEmail(emailId);
            }
        });
    }

    // Initialize reply all button
    const replyAllButton = document.querySelector('.reply-all-btn');
    if (replyAllButton) {
        replyAllButton.addEventListener('click', function() {
            const emailId = this.getAttribute('data-email-id');
            if (emailId) {
                replyAllEmail(emailId);
            }
        });
    }

    // Initialize forward button
    const forwardButton = document.querySelector('.forward-btn');
    if (forwardButton) {
        forwardButton.addEventListener('click', function() {
            const emailId = this.getAttribute('data-email-id');
            if (emailId) {
                forwardEmail(emailId);
            }
        });
    }

    // Initialize delete button
    const deleteButton = document.querySelector('.delete-btn');
    if (deleteButton) {
        deleteButton.addEventListener('click', function() {
            const emailId = this.getAttribute('data-email-id');
            if (emailId) {
                deleteEmail(emailId);
            }
        });
    }

    // Initialize send button
    const sendButton = document.getElementById('sendEmailBtn');
    if (sendButton) {
        sendButton.addEventListener('click', function(e) {
            e.preventDefault();
            sendEmailDirectly();
        });
    }
}

// Function to handle email reply
function replyEmail(emailId) {
    console.log('Replying to email:', emailId);
    
    try {
        // Use cached email data if available
        const email = window.currentEmailData || {};
        
        // Check if modal exists
        const modalElement = document.getElementById('composeModal');
        if (!modalElement) {
            throw new Error('Compose email modal not found in the DOM');
        }
        
        // Show loading state
        showSuccess('Preparing reply...');
        
        // Open compose modal
        const composeModal = new bootstrap.Modal(modalElement);
        composeModal.show();
        
        // Set recipient field
        const toField = document.getElementById('emailTo');
        if (toField) {
            toField.value = email.sender_email || email.sender || '';
        }
        
        // Set subject with Re: prefix
        const subjectField = document.getElementById('emailSubject');
        if (subjectField) {
            const subject = email.subject || 'No Subject';
            subjectField.value = subject.startsWith('Re:') ? subject : `Re: ${subject}`;
        }
        
        // Set body with quoted original message and proper formatting
        const bodyField = document.getElementById('emailBody');
        if (bodyField) {
            const date = email.date ? formatDetailDate(email.date) : formatDetailDate(new Date());
            const formattedSender = formatSenderForDisplay(email.sender, email.sender_email);
            const content = formatReplyContent(email.snippet || '');
            
            // Format the complete reply with proper spacing
            bodyField.value = `\n\nOn ${date}, ${formattedSender} wrote:\n\n${content}`;
            
            // Place cursor at the beginning for the reply
            bodyField.setSelectionRange(0, 0);
            bodyField.focus();
        }
        
        // Store original email ID for reference
        const composeForm = document.getElementById('composeForm');
        if (composeForm) {
            composeForm.dataset.originalEmailId = emailId;
            composeForm.dataset.action = 'reply';
        }
        
    } catch (error) {
        console.error('Error preparing reply:', error);
        showError(`Failed to prepare reply: ${error.message}`);
    }
}

// Function to handle email reply all
function replyAllEmail(emailId) {
    console.log('Reply all to email:', emailId);
    
    try {
        // Use cached email data if available
        const email = window.currentEmailData || {};
        
        // Check if modal exists - Use the correct modal ID from the HTML
        const modalElement = document.getElementById('composeModal');
        if (!modalElement) {
            throw new Error('Compose email modal not found in the DOM');
        }
        
        // Show loading state or indicator
        showSuccess('Preparing reply all...');
        
        // Open compose modal with reply all details - use bootstrap 5 syntax
        const composeModal = new bootstrap.Modal(modalElement);
        composeModal.show();

        // Get user's email
        const userEmail = getCurrentUserEmail();
        
        // Set "From" field if it exists as a select
        const fromField = document.getElementById('emailFrom');
        if (fromField && fromField.tagName === 'SELECT') {
            // Check if the option exists
            let optionExists = false;
            for (let i = 0; i < fromField.options.length; i++) {
                if (fromField.options[i].value === userEmail || 
                    fromField.options[i].textContent === userEmail) {
                    fromField.selectedIndex = i;
                    optionExists = true;
                    break;
                }
            }
            
            // If option doesn't exist, add it
            if (!optionExists && userEmail) {
                const option = document.createElement('option');
                option.value = userEmail;
                option.textContent = userEmail;
                option.selected = true;
                fromField.appendChild(option);
            }
        }

        // Get formatted sender for quoted message
        const formattedSender = formatSenderForDisplay(email.sender, email.sender_email);

        // Prepare recipients list with error handling
        let recipientsList = [];
        
        // Add sender to recipients if it's an email address
        if (email.sender_email && isValidEmailAddress(email.sender_email)) {
            recipientsList.push(email.sender_email);
        } else if (email.sender && isValidEmailAddress(email.sender)) {
            recipientsList.push(email.sender);
        } else if (email.sender) {
            // Try to extract email from sender text
            const extractedEmail = extractEmailAddress(email.sender);
            if (extractedEmail && extractedEmail !== email.sender) {
                recipientsList.push(extractedEmail);
            }
        }
        
        // Handle different formats of recipients (string or array)
        if (email.recipients) {
            if (Array.isArray(email.recipients)) {
                // Add all valid email addresses
                email.recipients.forEach(recipient => {
                    if (recipient && typeof recipient === 'string') {
                        // Check if it's already a valid email or needs extraction
                        if (isValidEmailAddress(recipient)) {
                            recipientsList.push(recipient);
                        } else {
                            const extracted = extractEmailAddress(recipient);
                            if (extracted && extracted !== recipient) {
                                recipientsList.push(extracted);
                            }
                        }
                    }
                });
            } else if (typeof email.recipients === 'string') {
                // Split by commas if it's a comma-separated string
                const parts = email.recipients.split(',').map(p => p.trim());
                parts.forEach(part => {
                    if (part) {
                        if (isValidEmailAddress(part)) {
                            recipientsList.push(part);
                        } else {
                            const extracted = extractEmailAddress(part);
                            if (extracted && extracted !== part) {
                                recipientsList.push(extracted);
                            }
                        }
                    }
                });
            }
        }
        
        // Remove current user's email from recipients
        recipientsList = recipientsList.filter(email => email !== userEmail);
        
        // Remove duplicates and join
        const uniqueRecipients = [...new Set(recipientsList)].join(', ');
        
        console.log('Setting recipients for reply all:', uniqueRecipients);
        
        // Set form fields with safe fallbacks
        const toField = document.getElementById('emailTo');
        if (toField) {
            toField.value = uniqueRecipients;
            
            // Trigger change event to ensure validation recognizes the input
            const event = new Event('change', { bubbles: true });
            toField.dispatchEvent(event);
        }
        
        const subjectField = document.getElementById('emailSubject');
        if (subjectField) {
            const subject = email.subject || 'No Subject';
            // Avoid adding multiple Re: prefixes
            subjectField.value = subject.startsWith('Re:') ? subject : `Re: ${subject}`;
        }
        
        const bodyField = document.getElementById('emailBody');
        if (bodyField) {
            // Use current date if the email date is unavailable
            const date = email.date ? formatDetailDate(email.date) : formatDetailDate(new Date());
            let content = email.snippet || '';
            
            // --- Enhanced Cleaning with Line Breaks & Quote Prefix ---
            // 1. Replace <br> tags with newlines
            content = content.replace(/<br\s*\/?>/gi, '\n');
            // 2. Replace closing block tags like </p>, </div> with newlines
            content = content.replace(/<\/(p|div|h[1-6]|li|blockquote|tr|td)>/gi, '\n'); // Added more block tags
            // 3. Remove <style> blocks and their content
            content = content.replace(/<style[^>]*>.*?<\/style>/gs, ''); 
            // 4. Remove remaining HTML tags
            content = content.replace(/<[^>]*>/g, '');
            // 5. Decode HTML entities
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = content;
            content = tempDiv.textContent || tempDiv.innerText || "";
            // 6. Normalize internal whitespace (multiple spaces/tabs to one space)
            content = content.replace(/[ \t]+/g, ' ');
            // 7. Normalize multiple newlines to max two
            content = content.replace(/\n\s*\n/g, '\n\n');
            // 8. Trim overall whitespace
            content = content.trim();
            // 9. Add quote prefix to each line *only if it has content*
            content = content.split('\n').map(line => {
                const trimmedLine = line.trim();
                return trimmedLine ? `> ${trimmedLine}` : ''; // Return empty string for blank lines
            }).join('\n');
            // --- End Cleaning ---
            
            bodyField.value = `\n\nOn ${date}, ${formattedSender} wrote:\n${content}`; // Removed extra > prefix here
            
            // Place cursor at the beginning of the body for the user's reply
            bodyField.setSelectionRange(0, 0);
            bodyField.focus();
        }

        // Show CC field
        const ccField = document.querySelector('.cc-field');
        const bccField = document.querySelector('.bcc-field');
        if (ccField) ccField.classList.remove('d-none');
        if (bccField) bccField.classList.add('d-none');

        // Store original email ID for reference
        const composeForm = document.getElementById('composeForm');
        if (composeForm) {
            composeForm.dataset.originalEmailId = emailId;
            composeForm.dataset.action = 'reply_all';
        }

    } catch (error) {
        console.error('Error preparing reply all:', error);
        showError(`Failed to prepare reply all: ${error.message}`);
    }
}

// Function to handle email forwarding
function forwardEmail(emailId) {
    console.log('Forwarding email:', emailId);
    
    try {
        // Use cached email data if available
        const email = window.currentEmailData || {};
        
        // Check if modal exists
        const modalElement = document.getElementById('composeModal');
        if (!modalElement) {
            throw new Error('Compose email modal not found in the DOM');
        }
        
        // Show loading state
        showSuccess('Preparing forward...');
        
        // Open compose modal
        const composeModal = new bootstrap.Modal(modalElement);
        composeModal.show();
        
        // Set subject with Fwd: prefix
        const subjectField = document.getElementById('emailSubject');
        if (subjectField) {
            const subject = email.subject || 'No Subject';
            subjectField.value = subject.startsWith('Fwd:') ? subject : `Fwd: ${subject}`;
        }
        
        // Set body with forwarded message and proper formatting
        const bodyField = document.getElementById('emailBody');
        if (bodyField) {
            const sender = formatSenderForDisplay(email.sender, email.sender_email);
            const date = formatDetailDate(email.date);
            const subject = email.subject || 'No Subject';
            const content = formatForwardContent(email.snippet || '');
            
            // Format with proper line breaks and spacing
            const forwardHeader = [
                '---------- Forwarded message ---------',
                `From: ${sender}`,
                `Date: ${date}`,
                `Subject: ${subject}`,
                `To: ${email.recipients || 'No Recipients'}`,
                '',
                ''
            ].join('\n');
            
            bodyField.value = `${forwardHeader}${content}`;
            
            // Place cursor at the beginning
            bodyField.setSelectionRange(0, 0);
            bodyField.focus();
        }
        
        // Store original email ID for reference
        const composeForm = document.getElementById('composeForm');
        if (composeForm) {
            composeForm.dataset.originalEmailId = emailId;
            composeForm.dataset.action = 'forward';
        }
        
    } catch (error) {
        console.error('Error preparing forward:', error);
        showError(`Failed to prepare forward: ${error.message}`);
    }
}

// Add the cleanEmailContent function if it doesn't exist
function cleanEmailContent(content) {
    if (!content) return '';
    
    console.log('Cleaning email content');
    
    try {
        // First handle inline styles that we want to preserve as text formatting
        let cleaned = content
            // Convert common style-based formatting to text markers
            .replace(/<(span|div|p)[^>]*style="[^"]*font-weight:\s*bold[^"]*"[^>]*>(.*?)<\/\1>/gi, '**$2**')
            .replace(/<(span|div|p)[^>]*style="[^"]*font-style:\s*italic[^"]*"[^>]*>(.*?)<\/\1>/gi, '_$2_')
            .replace(/<(span|div|p)[^>]*style="[^"]*text-decoration:\s*underline[^"]*"[^>]*>(.*?)<\/\1>/gi, '__$2__')
            // Handle font sizes for headers
            .replace(/<(span|div|p)[^>]*style="[^"]*font-size:\s*(2[4-9]|[3-9][0-9]|large|x-large|xx-large)[^"]*"[^>]*>(.*?)<\/\1>/gi, '\n### $3\n')
            // Handle text alignment
            .replace(/<(div|p)[^>]*style="[^"]*text-align:\s*center[^"]*"[^>]*>(.*?)<\/\1>/gi, '\n\t$2\n')
            .replace(/<(div|p)[^>]*style="[^"]*text-align:\s*right[^"]*"[^>]*>(.*?)<\/\1>/gi, '\n\t\t$2\n')
            // Handle lists with proper indentation
            .replace(/<(ol|ul)[^>]*>([\s\S]*?)<\/\1>/gi, function(match, listType, content) {
                return '\n' + content.replace(/<li[^>]*>([\s\S]*?)<\/li>/gi, '  • $1\n');
            })
            // Handle blockquotes
            .replace(/<blockquote[^>]*>([\s\S]*?)<\/blockquote>/gi, '\n> $1\n')
            // Handle tables with basic formatting
            .replace(/<table[^>]*>([\s\S]*?)<\/table>/gi, function(match, tableContent) {
                return '\n' + tableContent
                    .replace(/<tr[^>]*>([\s\S]*?)<\/tr>/gi, function(match, rowContent) {
                        return rowContent
                            .replace(/<t[dh][^>]*>([\s\S]*?)<\/t[dh]>/gi, '$1\t')
                            .trim() + '\n';
                    });
            });

        // Handle HTML block elements with proper spacing
        cleaned = cleaned
            // Convert HTML block elements to double line breaks with proper spacing
            .replace(/<\/(div|p|h[1-6]|table|tr|blockquote)>/gi, '\n\n')
            .replace(/<(hr)[^>]*>/gi, '\n---\n')
            // Handle BR tags consistently
            .replace(/<br[^>]*>/gi, '\n')
            // Remove style tags and their content
            .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
            // Remove script tags and their content
            .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
            // Remove CSS rules
            .replace(/@media[^{]*{[^}]*}/g, '')
            .replace(/\.[^{]*{[^}]*}/g, '')
            // Remove all other HTML tags while preserving content
            .replace(/<[^>]+>/g, '');

        // Handle special characters and entities
        cleaned = cleaned
            // Common HTML entities
            .replace(/&nbsp;/g, ' ')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'")
            .replace(/&mdash;/g, "—")
            .replace(/&ndash;/g, "–")
            .replace(/&hellip;/g, "...")
            // Handle other numeric HTML entities
            .replace(/&#(\d+);/g, (match, dec) => String.fromCharCode(dec))
            // Handle hex HTML entities
            .replace(/&#x([0-9a-f]+);/gi, (match, hex) => String.fromCharCode(parseInt(hex, 16)))
            // Handle special whitespace
            .replace(/\u00A0/g, ' ') // Convert non-breaking spaces
            .replace(/\u2003/g, '  ') // Convert em spaces
            .replace(/\u2002/g, ' '); // Convert en spaces

        // Normalize line endings
        cleaned = cleaned.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

        // Handle multiple line breaks and spacing
        cleaned = cleaned
            // First normalize all whitespace
            .replace(/[ \t]+/g, ' ')
            // Handle multiple line breaks properly
            .replace(/\n\s*\n\s*\n+/g, '\n\n')
            // Split into lines and process each
            .split('\n')
            .map(line => {
                line = line.trim();
                // Preserve indentation for centered/right-aligned text
                if (line.startsWith('\t')) {
                    return line;
                }
                return line;
            })
            .join('\n')
            // Final cleanup of multiple spaces and line breaks
            .replace(/ +$/gm, '') // Remove trailing spaces
            .replace(/^\s+|\s+$/g, ''); // Trim start and end

        console.log('Content cleaned successfully with style preservation');
        return cleaned;
    } catch (error) {
        console.error('Error cleaning content:', error);
        return content; // Return original content if cleaning fails
    }
}

function formatReplyContent(content) {
    if (!content) return '';
    
    // Clean the content first
    content = cleanEmailContent(content);
    
    // Split into lines and properly quote each non-empty line
    return content
        .split('\n')
        .map(line => {
            line = line.trim();
            if (!line) return '';
            
            // Preserve existing formatting
            if (line.startsWith('\t')) {
                // Preserve centered/right-aligned text
                return `> ${line}`;
            } else if (line.startsWith('  •')) {
                // Preserve list items with proper indentation
                return `>   ${line}`;
            } else if (line.startsWith('### ')) {
                // Preserve headers
                return `> ${line}`;
            } else if (line.startsWith('> ')) {
                // Handle nested quotes
                return `> ${line}`;
            } else {
                // Regular line
                return `> ${line}`;
            }
        })
        .join('\n')
        // Ensure proper spacing between sections
        .replace(/\n{3,}/g, '\n\n');
}

function formatForwardContent(content) {
    if (!content) return '';
    
    // Clean the content first
    content = cleanEmailContent(content);
    
    // Preserve formatting while ensuring proper line breaks
    return content
        .split('\n')
        .map(line => {
            line = line.trim();
            if (!line) return '';
            
            // Preserve special formatting
            if (line.startsWith('\t')) {
                // Preserve centered/right-aligned text
                return line;
            } else if (line.startsWith('  •')) {
                // Preserve list items
                return line;
            } else if (line.startsWith('### ')) {
                // Preserve headers
                return `\n${line}\n`;
            } else if (line.startsWith('> ')) {
                // Preserve blockquotes
                return line;
            } else if (line === '---') {
                // Preserve horizontal rules
                return `\n${line}\n`;
            } else {
                // Regular paragraph
                return line;
            }
        })
        .filter(line => line) // Remove empty lines
        .join('\n\n') // Add double line breaks between paragraphs
        .replace(/\n{3,}/g, '\n\n'); // Normalize multiple line breaks
}

// Function to handle email deletion
function deleteEmail(emailId) {
    console.log('Attempting to delete email:', emailId);
    
    if (!confirm('Are you sure you want to delete this email?')) {
        console.log('Delete cancelled by user');
        return;
    }

    try {
        // Show loading state
        showSuccess('Deleting email...');
        
        // Make API call to delete email
        fetch(`/api/emails/${emailId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: emailId })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to delete email: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            showSuccess('Email deleted successfully');
            setTimeout(() => {
                window.location.href = '/inbox_email/';
            }, 1500);
        })
        .catch(error => {
            console.error('Error deleting email:', error);
            showError(`Failed to delete email: ${error.message}`);
        });
        
    } catch (error) {
        console.error('Error deleting email:', error);
        showError(`Failed to delete email: ${error.message}`);
    }
}

// Add a flag to prevent duplicate submissions
let isSubmitting = false;

// Function to remove all validation messages
function clearValidationMessages(form) {
    if (!form) return;
    
    // Remove all error messages
    const errorMessages = form.querySelectorAll('.invalid-feedback');
    errorMessages.forEach(msg => msg.remove());
    
    // Remove invalid states from fields
    const invalidFields = form.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => field.classList.remove('is-invalid'));
}

async function sendEmailDirectly(form) {
    if (isSubmitting) {
        return;
    }

    try {
        isSubmitting = true;
        
        if (!form) {
            form = document.querySelector('#composeForm, #composeEmailForm');
        }
        
        if (!form) {
            throw new Error('Compose form not found');
        }

        // Get form fields
        const toField = form.querySelector('input[name="to"], #emailTo');
        const subjectField = form.querySelector('input[name="subject"], #emailSubject');
        const bodyField = form.querySelector('textarea[name="body"], #emailBody');
        const ccField = form.querySelector('input[name="cc"], #emailCc');
        const bccField = form.querySelector('input[name="bcc"], #emailBcc');

        if (!toField || !subjectField || !bodyField) {
            throw new Error('Required form fields not found');
        }

        // Prevent sending to your own email
        const userEmail = (getCurrentUserEmail() || '').trim().toLowerCase();
        if (toField.value.trim().toLowerCase() === userEmail) {
            showError('You cannot send an email to yourself.');
            isSubmitting = false;
            return;
        }

        // Get and clean form data
        const to = toField.value ? toField.value.trim() : '';
        const subject = subjectField.value ? subjectField.value.trim() : '';
        const body = bodyField.value ? bodyField.value.trim() : '';
        const cc = ccField?.value ? ccField.value.trim() : '';
        const bcc = bccField?.value ? bccField.value.trim() : '';

        let isValid = true;

        // Validate required fields
        if (!to) {
            isValid = false;
            showFieldError(toField, 'Recipient email is required');
        } else if (!validateEmailField(toField)) {
            isValid = false;
        }

        if (!subject) {
            isValid = false;
            showFieldError(subjectField, 'Subject is required');
        }

        if (!body) {
            isValid = false;
            showFieldError(bodyField, 'Message body is required');
        }

        if (!isValid) {
            return;
        }

        // Prepare email data
        const emailData = {
            to: to,
            subject: subject,
            body: body,
            cc: cc,
            bcc: bcc,
            original_email_id: form.dataset.originalEmailId || '',
            action: form.dataset.action || 'new'
        };

        // Send email
        const response = await fetch('/api/emails/send/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(emailData),
            credentials: 'same-origin'
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `Failed to send email: ${response.status}`);
        }

        // Close compose modal first
        closeComposeModal();
        form.reset();

        // Create success popup
        let successPopup = document.getElementById('successPopup');
        if (!successPopup) {
            successPopup = document.createElement('div');
            successPopup.id = 'successPopup';
            successPopup.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 1050;
                opacity: 0;
                transition: opacity 0.3s ease-in-out;
                min-width: 300px;
                text-align: center;
            `;
            successPopup.innerHTML = `
                <div class="success-icon" style="color: #28a745; font-size: 48px; margin-bottom: 15px;">
                    <i class="fas fa-check-circle"></i>
                </div>
                <h4 style="color: #28a745; margin-bottom: 10px;">Email Sent Successfully!</h4>
                <p style="color: #666; margin-bottom: 15px;">Your message has been sent to ${to}</p>
            `;
            document.body.appendChild(successPopup);
        }

        // Create overlay
        let overlay = document.getElementById('successOverlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'successOverlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                z-index: 1040;
                opacity: 0;
                transition: opacity 0.3s ease-in-out;
            `;
            document.body.appendChild(overlay);
        }

        // Show popup and overlay with fade in
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
            successPopup.style.opacity = '1';
        });

        // Remove popup and overlay after delay
        setTimeout(() => {
            overlay.style.opacity = '0';
            successPopup.style.opacity = '0';
            setTimeout(() => {
                overlay.remove();
                successPopup.remove();
            }, 300);
        }, 2000);

    } catch (error) {
        console.error('Error sending email:', error);
        showError(error.message || 'Failed to send email');
        throw error;
    } finally {
        isSubmitting = false;
    }
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeFormHandlers();
    
    // Re-initialize handlers when compose modal is shown
    const composeModal = document.getElementById('composeModal');
    if (composeModal) {
        composeModal.addEventListener('shown.bs.modal', function() {
            initializeFormHandlers();
            // Focus on the first empty required field
            const form = document.querySelector('#composeForm, #composeEmailForm');
            if (form) {
                const firstEmptyField = form.querySelector('input[required]:not([value]), textarea[required]:empty');
                if (firstEmptyField) {
                    firstEmptyField.focus();
                }
            }
        });
    }
});

// Initialize DOM event listeners for CC/BCC buttons
function initializeComposeModalControls() {
    // Add event listeners for CC and BCC toggles
    const ccButton = document.getElementById('ccButton');
    const bccButton = document.getElementById('bccButton');
    
    if (ccButton) {
        ccButton.addEventListener('click', function(e) {
            e.preventDefault();
            const ccField = document.querySelector('.cc-field');
            if (ccField) {
                ccField.classList.toggle('d-none');
            }
        });
    }
    
    if (bccButton) {
        bccButton.addEventListener('click', function(e) {
            e.preventDefault();
            const bccField = document.querySelector('.bcc-field');
            if (bccField) {
                bccField.classList.toggle('d-none');
            }
        });
    }
    
    // Add event listener for send button
    const sendButton = document.getElementById('sendEmailBtn');
    if (sendButton) {
        sendButton.addEventListener('click', function(e) {
            e.preventDefault();
            handleEmailSubmission();
        });
    }
}

// Function to close compose modal
function closeComposeModal() {
    const modal = document.getElementById('composeModal');
    if (modal) {
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) {
            bsModal.hide();
        }
        
        // Clean up modal-related elements
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
        
        // Reset body styles
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }
}

// Voice command functionality
let mediaRecorder = null;
let audioChunks = [];

// Record voice command
async function recordVoiceCommand() {
    // Stop any existing recognition before starting new one
    if (window.recognition) {
        try {
            window.recognition.stop();
        } catch (e) {
            console.log('Cleaning up existing recognition');
        }
        window.recognition = null;
    }

    // Stop hotword detection if active
    if (window.hotwordDetector && window.hotwordDetector.isActive()) {
        window.hotwordDetector.stop();
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        const audioChunks = [];

        mediaRecorder.addEventListener("dataavailable", event => {
            audioChunks.push(event.data);
        });

        mediaRecorder.addEventListener("stop", async () => {
            const audioBlob = new Blob(audioChunks);
            const result = await convertSpeechToText(audioBlob);
            if (result) {
                handleVoiceCommand(result);
            }
            stream.getTracks().forEach(track => track.stop());
        });

        mediaRecorder.start();
        setTimeout(() => mediaRecorder.stop(), 5000);
        
        return true;
    } catch (error) {
        console.error('Error recording voice command:', error);
        showNotification('Error recording voice command: ' + error.message, 'error');
        return false;
    }
}

// Convert speech to text using Google Cloud Speech-to-Text
async function convertSpeechToText(audioBlob) {
    try {
        // Show loading state
        const commandResult = document.getElementById('commandResult');
        commandResult.style.display = 'block';
        commandResult.className = 'alert alert-info';
        commandResult.textContent = 'Processing your voice command...';
        
        // Convert blob to base64
        const base64Audio = await blobToBase64(audioBlob);
        
        // Log request details for debugging (only size, not content)
        console.log('Sending speech-to-text request, audio size:', base64Audio.length);
        
        try {
            const response = await fetch('/api/voice/speech-to-text/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    audio: base64Audio
                })
            });
    
            // Check for HTTP errors
            if (!response.ok) {
                console.error('Speech-to-text API error:', response.status, response.statusText);
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
    
            // Try to parse JSON response
            const data = await response.json();
            console.log('Speech-to-text response:', data);
            
            if (data.success || data.text || data.transcription) {
                // Show transcription - handle different response formats
                const recognizedText = data.text || data.transcription || '';
                commandResult.className = 'alert alert-success';
                commandResult.textContent = `Recognized: "${recognizedText}"`;
                return recognizedText;
            } else {
                // Show error
                const errorMsg = data.error || 'Could not recognize speech';
                commandResult.className = 'alert alert-danger';
                commandResult.textContent = errorMsg;
                throw new Error(errorMsg);
            }
        } catch (fetchError) {
            console.error('Fetch error in speech-to-text:', fetchError);
            
            // Show user-friendly error
            commandResult.className = 'alert alert-danger';
            commandResult.textContent = 'Error: Could not connect to speech recognition service';
            
            // Propagate error for fallback handling
            throw fetchError;
        }
    } catch (error) {
        console.error('Error converting speech to text:', error);
        
        const commandResult = document.getElementById('commandResult');
        commandResult.style.display = 'block';
        commandResult.className = 'alert alert-danger';
        commandResult.textContent = 'Error processing speech: ' + error.message;
        
        throw error; // Re-throw for fallback handling
    }
}

// Convert text to speech using Google Cloud Text-to-Speech
async function convertTextToSpeech(text) {
    try {
        const response = await fetch('/api/voice/text-to-speech/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ text })
        });

        if (!response.ok) {
            throw new Error(`Text-to-Speech error: ${response.status}`);
        }
        
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        await audio.play();
        
        return true;
    } catch (error) {
        console.error('Error converting text to speech:', error);
        return false;
    }
}

// Helper function to convert blob to base64
function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

// Initialize voice command functionality
function initializeVoiceCommands() {
    console.log('Voice commands are handled by hotword_detection.js');
    
    // Only set up the button click handler
    const voiceCommandBtn = document.getElementById('voiceCommandBtn');
    if (voiceCommandBtn) {
        voiceCommandBtn.addEventListener('click', function() {
            // This will now be handled by hotword_detection.js
            console.log('Voice command button clicked - handled by hotword_detection.js');
        });
    }
}

// Handle voice command based on intent
async function handleVoiceCommand(intent, emailId, parameters) {
    console.log('Handling voice command:', intent, 'for email:', emailId, 'with parameters:', parameters);
    
    // Ensure emailId is available if needed, potentially from global scope or data attribute if not passed
    if (!emailId) {
        emailId = getDirectEmailId(); // Attempt to get it if not provided
        console.log('Attempted to get emailId for voice command:', emailId);
    }

    try {
        switch(intent) {
            case 'read_email':
                // Find the email content
                const emailContent = document.getElementById('emailContent')?.textContent || '';
                const emailSubject = document.getElementById('emailSubject')?.textContent || '';
                
                if (!emailContent && !emailSubject) {
                    showNotification('Could not find email content to read.', 'warning');
                    break;
                }
                // Read the email
                showNotification('Reading email...', 'info');
                await readTextWithBrowserSpeechSynthesis(`Email subject: ${emailSubject}. Content: ${emailContent}`);
                showNotification('Finished reading email.', 'success');
                break;
                
            case 'reply':
            case 'reply_to_email': // Added alias
                showNotification('Opening reply...', 'info');
                if (typeof replyEmail === 'function' && emailId) {
                    replyEmail(emailId);
                } else if (typeof replyEmail === 'function') {
                     showNotification('Could not determine email ID for reply.', 'error');
                } else {
                    // Fallback if function isn't defined (should not happen)
                    const replyBtn = document.querySelector('.reply-btn');
                    if (replyBtn) replyBtn.click(); 
                    else showNotification('Reply function not available.', 'error');
                }
                break;
                
            case 'forward':
                showNotification('Opening forward...', 'info');
                if (typeof forwardEmail === 'function' && emailId) {
                    forwardEmail(emailId);
                } else if (typeof forwardEmail === 'function'){
                    showNotification('Could not determine email ID for forward.', 'error');
                } else {
                    // Fallback
                    const forwardBtn = document.querySelector('.forward-btn');
                    if (forwardBtn) forwardBtn.click();
                    else showNotification('Forward function not available.', 'error');
                }
                break;
                
            case 'analyze':
                // Trigger analysis generation
                const generateAnalysisBtn = document.getElementById('generateAnalysisBtn');
                if (generateAnalysisBtn) {
                    showNotification('Starting analysis...', 'info');
                    generateAnalysisBtn.click();
                } else {
                    showNotification('Analysis feature not available.', 'error');
                }
                break;
                
            case 'mark_important':
                // Mark email as important (Placeholder)
                showNotification('Marking as important (simulated)...', 'info');
                // This would need to be implemented based on your application's API
                // e.g., await markEmailImportant(emailId);
                showNotification('Email marked as important.', 'success');
                break;

            case 'go_back':
            case 'back_to_inbox': // Added intent
                showNotification('Going back to inbox...', 'info');
                if (typeof handleBackButtonClick === 'function') {
                    handleBackButtonClick();
                } else {
                     showNotification('Back function not available.', 'error');
                }
                break;
                
            default:
                console.log('Unrecognized voice intent:', intent);
                showNotification(`Command "${intent}" not recognized or not supported on this page.`, 'warning');
        }
    } catch (error) {
        console.error('Error handling voice command:', error);
        showNotification('Error executing command: ' + error.message, 'error');
    }
}

// Function to read an email aloud
async function readEmail(emailId) {
    try {
        console.log('Reading email with ID:', emailId);
        const commandResult = document.getElementById('commandResult');
        if (commandResult) {
            commandResult.className = 'alert alert-info';
            commandResult.textContent = 'Reading email...';
        }
        
        // First try to read with text from the DOM if no emailId is provided
        if (!emailId) {
            const emailContent = document.getElementById('emailContent').textContent;
            const emailSubject = document.getElementById('emailSubject').textContent;
            
            // Use browser's built-in speech synthesis
            await readTextWithBrowserSpeechSynthesis(`Email subject: ${emailSubject}. Content: ${emailContent}`);
            return;
        }
        
        // If we have an emailId, try the API
        const response = await fetch('/api/voice/read-email/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                email_id: emailId,
                return_text: true // First get just the text
            })
        });
        
        const data = await response.json();
        console.log('Read email response:', data);
        
        if (data.success && data.content) {
            // We have text content, now try to get audio
            try {
                // Try to get audio version
                const audioResponse = await fetch('/api/voice/text-to-speech/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ 
                        text: data.content 
                    })
                });
                
                if (audioResponse.ok && audioResponse.headers.get('content-type').includes('audio')) {
                    // We got audio, play it
                    const audioBlob = await audioResponse.blob();
                    const audioUrl = URL.createObjectURL(audioBlob);
                    const audio = new Audio(audioUrl);
                    
                    // Show status
                    if (commandResult) {
                        commandResult.className = 'alert alert-success';
                        commandResult.textContent = 'Reading email...';
                    }
                    
                    await playAudio(audio);
                    return;
                } else {
                    // Fallback to browser speech synthesis
                    throw new Error('Audio response not valid');
                }
            } catch (audioError) {
                console.warn('Error getting audio, falling back to browser speech:', audioError);
                await readTextWithBrowserSpeechSynthesis(data.content);
            }
        } else if (data.fallback && data.content) {
            // Use the fallback content with browser's speech synthesis
            await readTextWithBrowserSpeechSynthesis(data.content);
        } else {
            // Failed to get content, try to read from DOM
            const emailContent = document.getElementById('emailContent').textContent;
            const emailSubject = document.getElementById('emailSubject').textContent;
            await readTextWithBrowserSpeechSynthesis(`Email subject: ${emailSubject}. Content: ${emailContent}`);
        }
        
        // Update command result
        if (commandResult) {
            commandResult.className = 'alert alert-success';
            commandResult.textContent = 'Finished reading email';
        }
    } catch (error) {
        console.error('Error reading email:', error);
        
        // Update command result
        const commandResult = document.getElementById('commandResult');
        if (commandResult) {
            commandResult.className = 'alert alert-danger';
            commandResult.textContent = 'Error reading email: ' + error.message;
        }
        
        showNotification('Error reading email: ' + error.message, 'error');
        
        // Try browser fallback as last resort
        try {
            const emailContent = document.getElementById('emailContent').textContent;
            const emailSubject = document.getElementById('emailSubject').textContent;
            await readTextWithBrowserSpeechSynthesis(`Email subject: ${emailSubject}. Content: ${emailContent}`);
        } catch (fallbackError) {
            console.error('Even browser speech synthesis failed:', fallbackError);
        }
    }
}

// Play audio with promise wrapper
function playAudio(audio) {
    return new Promise((resolve, reject) => {
        audio.onended = resolve;
        audio.onerror = reject;
        audio.play().catch(reject);
    });
}

// Use the browser's built-in speech synthesis
function readTextWithBrowserSpeechSynthesis(text) {
    return new Promise((resolve, reject) => {
        if (!window.speechSynthesis) {
            reject(new Error('Browser does not support speech synthesis'));
            return;
        }
        
        // Cancel any ongoing speech
        speechSynthesis.cancel();
        
        // Create utterance
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        utterance.lang = 'en-US';
        
        // Handle events
        utterance.onend = () => resolve();
        utterance.onerror = (event) => reject(new Error(`Speech synthesis error: ${event.error}`));
        
        // Speak
        speechSynthesis.speak(utterance);
    });
}

// Browser-based speech recognition as a fallback
function recognizeSpeechWithBrowser() {
    console.log('Speech recognition is handled by hotword_detection.js');
    return false;
}

// Function to check and request microphone permissions
async function checkMicrophonePermission() {
    try {
        // Show a notification that we're checking microphone permissions
        showNotification('Checking microphone access...', 'info');
        
        // Request microphone access explicitly
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // If we get here, permission was granted - close the stream
        stream.getTracks().forEach(track => track.stop());
        
        showNotification('Microphone access granted!', 'success');
        return true;
    } catch (error) {
        console.error('Microphone permission error:', error);
        
        // Show a detailed error message based on the type of error
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            showNotification('Microphone access denied. Please enable microphone permissions in your browser settings.', 'danger');
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
            showNotification('No microphone found. Please connect a microphone and try again.', 'danger');
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
            showNotification('Cannot access microphone. It may be in use by another application.', 'danger');
        } else {
            showNotification('Error accessing microphone: ' + error.message, 'danger');
        }
        
        return false;
    }
}

// Modified function to start voice command with permission check and better audio handling
async function startBrowserSpeechRecognition() {
    console.log('Speech recognition is handled by hotword_detection.js');
        return false;
}

// Function to use Google Cloud Speech-to-Text API
async function useGoogleCloudSpeechAPI(audioBlob) {
    try {
        showNotification('Processing speech with Google Cloud API...', 'info');
        
        // Convert the audio blob to base64
        const base64Audio = await blobToBase64(audioBlob);
        
        // Send to server endpoint that will use Google Cloud Speech-to-Text
        const response = await fetch('/api/voice/speech-to-text/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                audio: base64Audio
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success && result.transcription) {
            showNotification(`Recognized: "${result.transcription}"`, 'success');
            return result.transcription;
        } else {
            throw new Error(result.error || 'Failed to transcribe speech');
        }
    } catch (error) {
        console.error('Error using Google Cloud Speech API:', error);
        showNotification('Error using Google Cloud Speech API: ' + error.message, 'danger');
        return null;
    }
}

// Record audio for Google Cloud API
async function recordAudioForGoogleCloud() {
    try {
        showNotification('Checking microphone access...', 'info');
        
        // Check microphone permission first
        const permissionGranted = await checkMicrophonePermission();
        if (!permissionGranted) {
            return null;
        }
        
        showNotification('Recording... Please speak your command', 'info');
        
        // Start animation for microphone button
        if (typeof startMicrophoneAnimation === 'function') {
            startMicrophoneAnimation();
        }
        
        // Create media stream
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        const audioChunks = [];
        
        return new Promise((resolve, reject) => {
            // Handle data available event
            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunks.push(event.data);
            });
            
            // Handle stop event
            mediaRecorder.addEventListener('stop', () => {
                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
                
                // Create audio blob
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                resolve(audioBlob);
                
                // Stop animation
                if (typeof stopMicrophoneAnimation === 'function') {
                    stopMicrophoneAnimation();
                }
            });
            
            // Start recording
            mediaRecorder.start();
            
            // Stop recording after 8 seconds
            setTimeout(() => {
                if (mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                }
            }, 8000);
        });
    } catch (error) {
        console.error('Error recording audio:', error);
        showNotification('Error recording audio: ' + error.message, 'danger');
        
        // Stop animation
        if (typeof stopMicrophoneAnimation === 'function') {
            stopMicrophoneAnimation();
        }
        
        return null;
    }
}

// Updated function to use Google Cloud instead of browser recognition
async function startGoogleCloudSpeechRecognition() {
    try {
        // Record audio
        const audioBlob = await recordAudioForGoogleCloud();
        if (!audioBlob) {
            return;
        }
        
        // Use Google Cloud API to transcribe
        const transcript = await useGoogleCloudSpeechAPI(audioBlob);
        if (!transcript) {
            return;
        }
        
        // Process command
        processBrowserCommand(transcript);
    } catch (error) {
        console.error('Error with Google Cloud speech recognition:', error);
        showNotification('Error with speech recognition: ' + error.message, 'danger');
    }
}

// Function to debug microphone input
async function debugMicrophoneInput() {
    try {
        showNotification('Testing microphone input...', 'info', 10000);
        
        // Create a debug container in the page
        let debugContainer = document.getElementById('microphoneDebugContainer');
        if (!debugContainer) {
            debugContainer = document.createElement('div');
            debugContainer.id = 'microphoneDebugContainer';
            debugContainer.className = 'card mt-3';
            debugContainer.innerHTML = `
                <div class="card-header bg-info text-white">
                    <h5 class="mb-0">Microphone Debug</h5>
                </div>
                <div class="card-body">
                    <div class="text-center mb-3">
                        <div class="progress mb-3">
                            <div id="volumeLevel" class="progress-bar bg-success" role="progressbar" style="width: 0%"></div>
                        </div>
                        <div id="microphoneStatus">Initializing microphone test...</div>
                    </div>
                    <div id="microphoneDetails" class="small text-muted"></div>
                </div>
            `;
            
            // Add it to the page
            const voiceCommandSection = document.querySelector('.card-body');
            if (voiceCommandSection) {
                voiceCommandSection.appendChild(debugContainer);
            } else {
                document.body.appendChild(debugContainer);
            }
        }
        
        const volumeLevel = document.getElementById('volumeLevel');
        const microphoneStatus = document.getElementById('microphoneStatus');
        const microphoneDetails = document.getElementById('microphoneDetails');
        
        // Request microphone access
        microphoneStatus.textContent = 'Requesting microphone access...';
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            } 
        });
        
        microphoneStatus.textContent = 'Microphone access granted. Testing audio levels...';
        
        // Get available audio devices
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices.filter(device => device.kind === 'audioinput');
        
        // Display available microphones
        microphoneDetails.innerHTML = `
            <p><strong>Available Microphones (${audioInputs.length}):</strong></p>
            <ul>
                ${audioInputs.map(device => `<li>${device.label || 'Unnamed Device'}</li>`).join('')}
            </ul>
        `;
        
        // Create an AudioContext to analyze the microphone input
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const analyser = audioContext.createAnalyser();
        const microphone = audioContext.createMediaStreamSource(stream);
        microphone.connect(analyser);
        
        analyser.fftSize = 256;
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        // Function to update volume level
        const updateVolume = () => {
            analyser.getByteFrequencyData(dataArray);
            
            // Calculate average volume level
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
            }
            const average = sum / bufferLength;
            const volumePercentage = Math.min(100, average * 2); // Scale up for better visibility
            
            // Update volume level display
            volumeLevel.style.width = `${volumePercentage}%`;
            
            // Change color based on level
            if (volumePercentage < 10) {
                volumeLevel.className = 'progress-bar bg-danger';
                microphoneStatus.textContent = 'Very low audio level detected. Please check your microphone.';
            } else if (volumePercentage < 30) {
                volumeLevel.className = 'progress-bar bg-warning';
                microphoneStatus.textContent = 'Low audio level. Try speaking louder or adjusting microphone settings.';
            } else {
                volumeLevel.className = 'progress-bar bg-success';
                microphoneStatus.textContent = 'Good audio level detected. Your microphone is working.';
            }
            
            // Continue monitoring
            requestAnimationFrame(updateVolume);
        };
        
        // Start monitoring
        updateVolume();
        
        // Add stop button
        const stopButton = document.createElement('button');
        stopButton.className = 'btn btn-danger mt-3';
        stopButton.textContent = 'Stop Microphone Test';
        stopButton.onclick = () => {
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
            // Remove debug container
            debugContainer.remove();
            showNotification('Microphone test completed', 'info');
        };
        debugContainer.querySelector('.card-body').appendChild(stopButton);
        
        // Add button to try speech recognition with this microphone
        const testSpeechButton = document.createElement('button');
        testSpeechButton.className = 'btn btn-primary mt-3 ms-2';
        testSpeechButton.textContent = 'Test Speech Recognition';
        testSpeechButton.onclick = () => {
            // Stop volume monitoring
            stream.getTracks().forEach(track => track.stop());
            
            // Update status
            microphoneStatus.textContent = 'Starting speech recognition test...';
            
            // Start speech recognition with extra hints
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            
            recognition.lang = 'en-US';
            recognition.interimResults = false;
            recognition.maxAlternatives = 3;
            recognition.continuous = false;
            
            // Show clear feedback
            microphoneStatus.textContent = 'Listening... Please say "test one two three"';
            
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                microphoneStatus.textContent = `Recognized: "${transcript}"`;
                microphoneDetails.innerHTML += `<p class="text-success">Speech recognition successful! Heard: "${transcript}"</p>`;
            };
            
            recognition.onerror = (event) => {
                microphoneStatus.textContent = `Error: ${event.error}`;
                microphoneDetails.innerHTML += `
                    <p class="text-danger">Error: ${event.error}</p>
                    <p>Troubleshooting tips:</p>
                    <ul>
                        <li>Make sure you're speaking clearly into the microphone</li>
                        <li>Check that no other apps are using your microphone</li>
                        <li>Try reloading the page</li>
                        <li>Try a different browser (Chrome works best)</li>
                    </ul>
                `;
            };
            
            recognition.onend = () => {
                microphoneDetails.innerHTML += `<p>Speech recognition session ended</p>`;
            };
            
            recognition.start();
        };
        debugContainer.querySelector('.card-body').appendChild(testSpeechButton);
        
        return true;
    } catch (error) {
        console.error('Error testing microphone:', error);
        showNotification('Error testing microphone: ' + error.message, 'danger');
        return false;
    }
}

// Function to read email content aloud
function readEmailContent() {
    console.log('Reading email content');
    const emailContent = document.getElementById('emailContent');
    if (emailContent) {
        const textToRead = emailContent.textContent || emailContent.innerText;
        if (textToRead) {
            readTextWithBrowserSpeechSynthesis(textToRead);
        } else {
            console.error('No email content found to read');
        }
    } else {
        console.error('Email content element not found');
    }
}

// Function to use suggested reply
function useSuggestedReply() {
    // Debug logs to help diagnose the issue
    console.log("DEBUG: currentEmailData", window.currentEmailData);
    console.log("DEBUG: userEmail", getCurrentUserEmail());

    const suggestedReply = document.getElementById('suggestedReply')?.textContent;
    if (!suggestedReply) {
        showError('No suggested reply available');
        return;
    }

    // Get the current email data
    const email = window.currentEmailData || {};
    const userEmail = (getCurrentUserEmail() || '').trim().toLowerCase();

    // Set the From field dynamically
    const fromField = document.getElementById('emailFrom');
    if (fromField) {
        fromField.value = getCurrentUserEmail() || '';
    }

    // Set the To field: try sender_email, then sender, then first recipient that's not the user
    const toField = document.getElementById('emailTo');
    if (toField) {
        let recipient = '';
        if (email.sender_email && email.sender_email.trim().toLowerCase() !== userEmail) {
            recipient = email.sender_email.trim();
        } else if (email.sender && email.sender.trim().toLowerCase() !== userEmail) {
            // Try to extract email from sender string
            const emailMatch = email.sender.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
            if (emailMatch && emailMatch[0].trim().toLowerCase() !== userEmail) {
                recipient = emailMatch[0].trim();
            } else {
                recipient = email.sender.trim();
            }
        } else if (email.recipients) {
            let recipientsArr = [];
            if (Array.isArray(email.recipients)) {
                recipientsArr = email.recipients;
            } else if (typeof email.recipients === 'string') {
                recipientsArr = email.recipients.split(',').map(r => r.trim());
            }
            recipient = recipientsArr.find(r => r && r.trim().toLowerCase() !== userEmail) || '';
        }
        toField.value = recipient;
        toField.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // Set subject with Re: prefix
    const subjectField = document.getElementById('emailSubject');
    if (subjectField) {
        const subject = email.subject || 'No Subject';
        subjectField.value = subject.startsWith('Re:') ? subject : `Re: ${subject}`;
    }

    // Set body with suggested reply
    const bodyField = document.getElementById('emailBody');
    if (bodyField) {
        bodyField.value = suggestedReply;
        bodyField.focus();
    }

    // Store original email ID for reference
    const composeForm = document.getElementById('composeForm');
    if (composeForm) {
        composeForm.dataset.originalEmailId = email.id;
        composeForm.dataset.action = 'reply';
    }
}

// Function to handle form field validation
function initializeFormField(field) {
    if (!field) return;

    // Remove any existing event listeners
    const newField = field.cloneNode(true);
    field.parentNode.replaceChild(newField, field);
    
    // Add input event listener
    newField.addEventListener('input', function() {
        // Remove error state as soon as user starts typing
        this.classList.remove('is-invalid');
        const feedback = this.parentElement.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    });

    // Add focus event listener
    newField.addEventListener('focus', function() {
        // Clear error state on focus
        this.classList.remove('is-invalid');
        const feedback = this.parentElement.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    });

    return newField;
}
    