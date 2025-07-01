// Compose Email Modal Functionality
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing compose email functionality');
    
    const composeForm = document.getElementById('composeForm');
    const attachFileBtn = document.getElementById('attachFileBtn');
    const fileInput = document.getElementById('fileInput');
    const attachmentList = document.getElementById('attachmentList');
    const saveAsDraftBtn = document.getElementById('saveAsDraft');
    const composeModal = document.getElementById('composeModal');
    
    // Initialize compose modal
    let composeModalInstance = null;
    if (composeModal) {
        composeModalInstance = new bootstrap.Modal(composeModal);
    }
    
    // Function to show compose modal
    window.showComposeModal = function(subject = '', to = '', body = '') {
        console.log('Showing compose modal with:', { subject, to, body });
        
        if (composeModalInstance) {
            // Set form values if provided
            if (subject) document.getElementById('emailSubject').value = subject;
            if (to) document.getElementById('emailTo').value = to;
            if (body) document.getElementById('emailBody').value = body;
            
            // Show the modal
            composeModalInstance.show();
        } else {
            console.error('Compose modal instance not found');
        }
    };
    
    // Check Gmail authentication when compose modal is opened
    if (composeModal) {
        composeModal.addEventListener('show.bs.modal', async function() {
            try {
                const authStatus = await checkGmailAuth();
                if (!authStatus.authenticated) {
                    showNotification('Gmail authentication required. Please log in again.', 'warning');
                    // Redirect to Gmail auth page
                    window.location.href = '/gmail/authenticate/';
                    return false; // Prevent modal from opening
                }
            } catch (error) {
                console.error('Error checking Gmail auth:', error);
            }
        });
    }
    
    // Handle file attachment button click
    if (attachFileBtn) {
        attachFileBtn.addEventListener('click', () => {
            fileInput.click();
        });
    }
    
    // Handle file selection
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            updateAttachmentList(files);
        });
    }
    
    // Toggle CC and BCC fields
    const ccButton = document.getElementById('ccButton');
    const bccButton = document.getElementById('bccButton');
    const ccFieldContainer = document.getElementById('emailCcContainer');
    const bccFieldContainer = document.getElementById('emailBccContainer');

    if (ccButton && ccFieldContainer) {
        ccButton.addEventListener('click', () => {
            ccFieldContainer.classList.toggle('d-none');
            if (!ccFieldContainer.classList.contains('d-none')) {
                document.getElementById('emailCc').focus();
            }
        });
    }

    if (bccButton && bccFieldContainer) {
        bccButton.addEventListener('click', () => {
            bccFieldContainer.classList.toggle('d-none');
            if (!bccFieldContainer.classList.contains('d-none')) {
                document.getElementById('emailBcc').focus();
            }
        });
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const validateEmail = (email) => {
        if (!email) return true; // Empty is valid (for CC/BCC)
        
        // Split multiple emails by comma and validate each
        const emails = email.split(',').map(e => e.trim());
        return emails.every(e => !e || emailRegex.test(e));
    };

    // Add validation to email fields
    const toField = document.getElementById('emailTo');
    const ccField = document.getElementById('emailCc');
    const bccField = document.getElementById('emailBcc');

    // Add validation to To field
    if (toField) {
        toField.addEventListener('blur', () => {
            const value = toField.value.trim();
            
            if (!value || !validateEmail(value)) {
                toField.classList.add('is-invalid');
                addInvalidFeedback(toField, 'Please enter valid email address(es)');
            } else {
                toField.classList.remove('is-invalid');
                removeInvalidFeedback(toField);
            }
        });
    }

    // Add validation to CC field
    if (ccField) {
        ccField.addEventListener('blur', () => {
            const value = ccField.value.trim();
            
            if (value && !validateEmail(value)) {
                ccField.classList.add('is-invalid');
                addInvalidFeedback(ccField, 'Please enter valid email address(es)');
            } else {
                ccField.classList.remove('is-invalid');
                removeInvalidFeedback(ccField);
            }
        });
    }

    // Add validation to BCC field
    if (bccField) {
        bccField.addEventListener('blur', () => {
            const value = bccField.value.trim();
            
            if (value && !validateEmail(value)) {
                bccField.classList.add('is-invalid');
                addInvalidFeedback(bccField, 'Please enter valid email address(es)');
            } else {
                bccField.classList.remove('is-invalid');
                removeInvalidFeedback(bccField);
            }
        });
    }

    // Helper functions for validation feedback
    function addInvalidFeedback(field, message) {
        const formGroup = field.closest('.form-group') || field.closest('.mb-3');
        if (formGroup && !formGroup.querySelector('.invalid-feedback')) {
            const helperDiv = document.createElement('div');
            helperDiv.className = 'invalid-feedback';
            helperDiv.textContent = message;
            formGroup.appendChild(helperDiv);
        }
    }

    function removeInvalidFeedback(field) {
        const formGroup = field.closest('.form-group') || field.closest('.mb-3');
        if (formGroup) {
            const feedback = formGroup.querySelector('.invalid-feedback');
            if (feedback) {
                formGroup.removeChild(feedback);
            }
        }
    }
    
    // Handle form submission
    if (composeForm) {
        composeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            console.log('Compose form submitted');
            
            // Get and validate form values
            let to = toField ? toField.value.trim() : '';
            let cc = ccField ? ccField.value.trim() : '';
            let bcc = bccField ? bccField.value.trim() : '';
            
            // Validate all email fields
            let isValid = true;
            
            // To field is required and must be valid
            if (!to || !validateEmail(to)) {
                if (toField) {
                    toField.classList.add('is-invalid');
                    addInvalidFeedback(toField, 'A valid recipient email address is required');
                    toField.focus();
                }
                isValid = false;
            }
            
            // CC field is optional but must be valid if provided
            if (cc && !validateEmail(cc)) {
                if (ccField) {
                    ccField.classList.add('is-invalid');
                    addInvalidFeedback(ccField, 'Please enter valid email address(es)');
                    if (isValid) { // Only focus if To field was valid
                        ccField.focus();
                    }
                }
                isValid = false;
            }
            
            // BCC field is optional but must be valid if provided
            if (bcc && !validateEmail(bcc)) {
                if (bccField) {
                    bccField.classList.add('is-invalid');
                    addInvalidFeedback(bccField, 'Please enter valid email address(es)');
                    if (isValid) { // Only focus if previous fields were valid
                        bccField.focus();
                    }
                }
                isValid = false;
            }
            
            if (!isValid) {
                showNotification('Please correct the errors in the form', 'error');
                return; // Stop form submission
            }

            // Additional check for example.com
            if (to.includes('example.com')) {
                const confirm = window.confirm('The recipient appears to be a placeholder email (example.com domain). Are you sure you want to send to this address?');
                if (!confirm) {
                    return;
                }
            }

            // Show sending state
            const sendBtn = document.querySelector('button[type="submit"]');
            if (sendBtn) {
                sendBtn.disabled = true;
                sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Sending...';
            }

            try {
                // Collect form data
                const formData = {
                    to: to,
                    cc: cc,
                    bcc: bcc,
                    subject: document.getElementById('emailSubject').value.trim() || 'No Subject',
                    body: document.getElementById('emailBody').value || ''
                };

                // Process attachments if any
                if (fileInput && fileInput.files.length > 0) {
                    const attachments = await Promise.all(
                        Array.from(fileInput.files).map(fileToBase64)
                    );
                    formData.attachments = attachments;
                }

                // Send the email
                const response = await sendEmail(formData);
                
                if (response.success) {
                    // Success handling
                    if (composeModalInstance) {
                        composeModalInstance.hide();
                    }
                    showNotification(response.message || 'Email sent successfully!', 'success');
                    composeForm.reset();
                } else {
                    // Error handling
                    showNotification(response.error || 'Failed to send email', 'error');
                }
            } catch (error) {
                console.error('Error sending email:', error);
                showNotification('An error occurred while sending the email', 'error');
            } finally {
                // Reset button state
                if (sendBtn) {
                    sendBtn.disabled = false;
                    sendBtn.innerHTML = 'Send <i class="fas fa-paper-plane ms-1"></i>';
                }
            }
        });
    }
    
    // Reset form when modal is closed
    composeModal.addEventListener('hidden.bs.modal', resetComposeForm);

    // Function to update attachment list display
    function updateAttachmentList(files) {
        if (!attachmentList) return;

        attachmentList.innerHTML = files.map(file => `
            <div class="attachment-item d-flex align-items-center mb-2">
                <i class="fas fa-paperclip me-2"></i>
                <span class="me-2">${file.name}</span>
                <small class="text-muted">(${formatFileSize(file.size)})</small>
                <button type="button" class="btn btn-sm btn-link text-danger ms-auto remove-attachment">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');

        // Add remove attachment functionality
        attachmentList.querySelectorAll('.remove-attachment').forEach((btn, index) => {
            btn.addEventListener('click', () => {
                const newFiles = Array.from(fileInput.files).filter((_, i) => i !== index);
                updateAttachmentList(newFiles);
            });
        });
    }

    // Function to clear attachments
    function clearAttachments() {
        if (attachmentList) {
            attachmentList.innerHTML = '';
        }
        if (fileInput) {
            fileInput.value = '';
        }
    }

    // Function to format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
});

// MOVED OUTSIDE DOMContentLoaded - Function to send email
async function sendEmail(formData) {
    try {
        console.log('Attempting to send email with data:', formData);
        
        // Convert plain text to HTML for better email client compatibility
        formData.body_html = formatEmailHtml(formData.body);
        
        // Try to send using Gmail API first
        const gmailResponse = await fetch('/api/emails/send/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        // Handle the response
        try {
            const contentType = gmailResponse.headers.get('content-type');
            
            // Check if response is JSON
            if (contentType && contentType.includes('application/json')) {
                const data = await gmailResponse.json();
                
                if (gmailResponse.ok) {
                    console.log('Email sent successfully via Gmail API');
                    return { 
                        success: true, 
                        data, 
                        provider: 'gmail',
                        message: data.message || 'Email sent successfully!',
                        db_save_success: data.db_save_success
                    };
                } else {
                    console.error('Error response from Gmail API:', data);
                    
                    // Check if authentication redirect is needed
                    if (gmailResponse.status === 401 && data.redirect) {
                        console.log('Authentication required, redirecting...');
                        // Alert the user before redirecting
                        alert('Gmail authentication required. You will be redirected to authenticate.');
                        window.location.href = data.redirect;
                        return { success: false, error: 'Authentication required', requiresAuth: true };
                    }
                    
                    // Check for specific error messages
                    if (data.error && data.details) {
                        return { 
                            success: false, 
                            error: `${data.error}: ${data.details}`,
                            details: data.details
                        };
                    }
                    
                    // Fall back to Django endpoint if Gmail API failed
                    console.log('Gmail API unavailable, falling back to Django endpoint');
                    try {
                        const djangoResponse = await fetch('/send_email/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCookie('csrftoken')
                            },
                            body: JSON.stringify(formData)
                        });
                        
                        if (djangoResponse.ok) {
                            const djangoData = await djangoResponse.json();
                            console.log('Email sent successfully via Django API');
                            return { success: true, data: djangoData, provider: 'django' };
                        } else {
                            let errorData;
                            try {
                                errorData = await djangoResponse.json();
                            } catch (e) {
                                errorData = { message: 'Failed to send email (Invalid response)' };
                            }
                            
                            return { 
                                success: false, 
                                error: errorData.message || 'Failed to send email',
                                provider: 'all'
                            };
                        }
                    } catch (fallbackError) {
                        console.error('Error with fallback method:', fallbackError);
                        return {
                            success: false,
                            error: 'All sending methods failed',
                            details: fallbackError.message
                        };
                    }
                }
            } else {
                // Handle non-JSON response
                const text = await gmailResponse.text();
                console.error('Non-JSON response:', text.substring(0, 100));
                return {
                    success: false,
                    error: 'Server returned an invalid response'
                };
            }
        } catch (parseError) {
            console.error('Error parsing response:', parseError);
            return { 
                success: false, 
                error: 'Failed to process server response' 
            };
        }
    } catch (error) {
        console.error('Network error:', error);
        return { 
            success: false, 
            error: 'Network error: Could not connect to server' 
        };
    }
}

// MOVED OUTSIDE DOMContentLoaded - Function to format email body as HTML
function formatEmailHtml(text) {
    if (!text) return '';
    
    // Normalize line endings
    text = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    
    // Convert line breaks to proper HTML paragraphs
    let paragraphs = text.split(/\n\n+/);
    
    // Create HTML wrapper with styling
    let htmlContent = `
        <div style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
    `;
    
    // Format each paragraph with proper HTML
    htmlContent += paragraphs
        .map(para => {
            // Handle individual line breaks within paragraphs
            para = para.replace(/\n/g, '<br>');
            return `<p style="margin: 0 0 10px 0; line-height: 1.5;">${para}</p>`;
        })
        .join('');
    
    // Close HTML wrapper
    htmlContent += `
        </div>
    `;
    
    return htmlContent;
}

// MOVED OUTSIDE DOMContentLoaded - Helper function to get CSRF token
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

// Function to check Gmail authentication
async function checkGmailAuth() {
    try {
        const response = await fetch('/check_gmail_auth/');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return {
            authenticated: data.status === 'success' && data.authenticated,
            message: data.message || 'Authentication check completed'
        };
    } catch (error) {
        console.error('Error checking Gmail auth:', error);
        return { authenticated: false, message: 'Failed to check authentication' };
    }
}

// Function to convert file to base64
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            // Get base64 string (remove the data URL prefix)
            const base64String = reader.result.split(',')[1];
            resolve(base64String);
        };
        reader.onerror = error => reject(error);
        reader.readAsDataURL(file);
    });
}

// Reset compose form
function resetComposeForm() {
    document.getElementById('composeForm').reset();
    document.getElementById('attachmentList').innerHTML = '';
    document.getElementById('fileInput').value = '';
    
    // Reset validation state
    const emailFields = ['emailTo', 'emailCc', 'emailBcc'];
    emailFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.classList.remove('is-invalid');
            const formGroup = field.closest('.form-group') || field.closest('.mb-3');
            if (formGroup) {
                const feedback = formGroup.querySelector('.invalid-feedback');
                if (feedback) {
                    formGroup.removeChild(feedback);
                }
            }
        }
    });
    
    // Hide CC and BCC fields
    const ccFieldContainer = document.getElementById('emailCcContainer');
    const bccFieldContainer = document.getElementById('emailBccContainer');
    
    if (ccFieldContainer) ccFieldContainer.classList.add('d-none');
    if (bccFieldContainer) bccFieldContainer.classList.add('d-none');
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification div if it doesn't exist
    let notificationDiv = document.getElementById('emailNotification');
    if (!notificationDiv) {
        notificationDiv = document.createElement('div');
        notificationDiv.id = 'emailNotification';
        notificationDiv.className = 'position-fixed top-50 start-50 translate-middle p-3 rounded shadow-lg';
        notificationDiv.style.zIndex = '9999';
        notificationDiv.style.minWidth = '300px';
        notificationDiv.style.textAlign = 'center';
        document.body.appendChild(notificationDiv);
    }
    
    // Set color based on notification type
    let bgColor, textColor, icon;
    switch (type) {
        case 'success':
            bgColor = '#198754'; // Bootstrap success green
            textColor = '#fff';
            icon = '<i class="fas fa-check-circle me-2"></i>';
            break;
        case 'error':
            bgColor = '#dc3545'; // Bootstrap danger red
            textColor = '#fff';
            icon = '<i class="fas fa-exclamation-circle me-2"></i>';
            break;
        case 'warning':
            bgColor = '#ffc107'; // Bootstrap warning yellow
            textColor = '#212529';
            icon = '<i class="fas fa-exclamation-triangle me-2"></i>';
            break;
        default:
            bgColor = '#0dcaf0'; // Bootstrap info blue
            textColor = '#fff';
            icon = '<i class="fas fa-info-circle me-2"></i>';
    }
    
    // Set styles
    notificationDiv.style.backgroundColor = bgColor;
    notificationDiv.style.color = textColor;
    
    // Set content
    notificationDiv.innerHTML = `
        <div class="d-flex align-items-center">
            ${icon}
            <span>${message}</span>
        </div>
    `;
    
    // Show notification with fade-in effect
    notificationDiv.style.opacity = '0';
    notificationDiv.style.display = 'block';
    notificationDiv.style.transition = 'opacity 0.3s ease-in-out';
    
    setTimeout(() => {
        notificationDiv.style.opacity = '1';
    }, 10);
    
    // Auto-dismiss after 3 seconds
    setTimeout(() => {
        notificationDiv.style.opacity = '0';
        setTimeout(() => {
            notificationDiv.style.display = 'none';
        }, 300);
    }, 3000);
} 