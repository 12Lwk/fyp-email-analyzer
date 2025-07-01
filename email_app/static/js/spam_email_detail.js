// Function to get URL parameters
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// Function to get direct email ID from URL path
function getDirectEmailId() {
    const pathSegments = window.location.pathname.split('/').filter(Boolean);
    const emailId = pathSegments[pathSegments.length - 1];
    console.log('Direct email ID from path:', emailId);
    return emailId;
}

// Function to extract or format an email address from various formats
function extractFormattedEmail(input) {
    console.log('Extracting formatted email from:', input);
    
    // If input is null or undefined, return empty string
    if (input == null) {
        return '';
    }
    
    // If input is already a string, check if it contains @
    if (typeof input === 'string') {
        if (input.includes('@')) {
            return input.trim();
        }
        
        // Try to extract email using regex
        const emailMatch = input.match(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+)/);
        return emailMatch ? emailMatch[1] : input.trim();
    }
    
    // If input is an object
    if (typeof input === 'object' && input !== null) {
        // Check for common email properties
        if (input.email) return input.email;
        if (input.address) return input.address;
        if (input.mail) return input.mail;
        
        // Try to convert to string
        try {
            const objString = JSON.stringify(input);
            const emailMatch = objString.match(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+)/);
            return emailMatch ? emailMatch[1] : '';
        } catch (e) {
            console.error('Error extracting email from object:', e);
    return '';
        }
    }
    
    // For other types, convert to string
    return String(input).trim();
}

// Function to extract the primary recipient email address
function extractPrimaryRecipient(recipientsData) {
    console.log('Extracting primary recipient from:', recipientsData);
    if (!recipientsData) return '';

    let firstEmail = '';

    try {
        let parsedRecipients = recipientsData;

        // If it's a string that looks like JSON, parse it
        if (typeof recipientsData === 'string' && (recipientsData.startsWith('[') || recipientsData.startsWith('{'))) {
            try {
                parsedRecipients = JSON.parse(recipientsData);
            } catch (e) {
                console.warn('Could not parse recipients string as JSON:', e);
                // If parsing fails, treat it as a plain string
                parsedRecipients = recipientsData;
            }
        }

        if (Array.isArray(parsedRecipients)) {
            // Find the first valid email in the array
            for (const recipient of parsedRecipients) {
                if (typeof recipient === 'string') {
                    firstEmail = extractFormattedEmail(recipient);
                } else if (typeof recipient === 'object' && recipient !== null) {
                    firstEmail = extractFormattedEmail(recipient.email || recipient.address || recipient.name);
                }
                if (firstEmail && firstEmail.includes('@')) break; // Found a valid email
            }
        } else if (typeof parsedRecipients === 'object' && parsedRecipients !== null) {
            // Handle single recipient object
            firstEmail = extractFormattedEmail(parsedRecipients.email || parsedRecipients.address || parsedRecipients.name);
        } else if (typeof parsedRecipients === 'string') {
            // Handle plain string (might contain multiple emails, take the first)
            const emails = parsedRecipients.split(/[,;]/).map(e => e.trim());
            if (emails.length > 0) {
                firstEmail = extractFormattedEmail(emails[0]);
            }
        }
    } catch (error) {
        console.error("Error extracting primary recipient:", error);
        // Fallback to treating the original data as a string if complex parsing fails
        if (typeof recipientsData === 'string') {
             firstEmail = extractFormattedEmail(recipientsData.split(/[,;]/)[0]);
        }
    }

    // Final cleanup
    firstEmail = firstEmail.replace(/[<>]/g, '').trim(); // Remove potential angle brackets
    console.log('Extracted primary recipient:', firstEmail);
    return firstEmail && firstEmail.includes('@') ? firstEmail : '';
}

// Function to format sender for display
function formatSenderForDisplay(senderName, senderEmail) {
    if (!senderName && !senderEmail) return 'Unknown Sender';
    
    if (senderName && senderEmail) {
        if (senderName.includes(senderEmail)) {
            return senderName;
        }
        return `${senderName} <${senderEmail}>`;
    }
    
    return senderEmail || senderName;
}

// Function to format date for email detail
function formatDetailDate(dateStr) {
    if (!dateStr) {
        return moment().format('dddd, MMMM D, YYYY [at] h:mm A');
    }
    
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

// Function to escape HTML
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// Function to show field error
function showFieldError(field, message) {
    if (!field) return;
    
    field.classList.add('is-invalid');
    field.classList.remove('is-valid');
    
    // Find the parent container
    const parentNode = field.closest('.position-relative') || field.parentElement;
    
    // Remove any existing error messages
    const existingErrors = parentNode.querySelectorAll('.invalid-feedback');
    existingErrors.forEach(error => error.remove());
    
    // Create and append the error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    parentNode.appendChild(errorDiv);
    
    // Scroll field into view if not visible
    if (!isElementInViewport(field)) {
        field.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Check if element is in viewport
function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// Function to load email details
async function loadEmailDetails() {
    console.log('Loading email details...');
    
    // Store the page number from referrer if coming from sent folder
    const referrer = document.referrer;
    if (referrer && referrer.includes('/sent')) {
        const pageMatch = referrer.match(/[?&]page=(\d+)/);
        if (pageMatch && pageMatch[1]) {
            localStorage.setItem('sent_page_number', pageMatch[1]);
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
        // Get email ID from URL
        const emailId = getDirectEmailId();
        console.log('Email ID:', emailId);
        
        if (!emailId) {
            throw new Error('Email ID not found in URL. Please check the URL format or return to sent folder.');
        }

        // Make API request
        console.log('Fetching email details for ID:', emailId);
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

        // Store email data globally for use in reply/forward functionality
        window.currentEmailData = data.data || data;
        console.log('Stored current email data:', window.currentEmailData);

        // Update page title
        document.title = `${data.subject || 'Sent Email'} - Email Analytics`;

        // Update email details in the UI
        const emailData = window.currentEmailData;
        
        // Update subject
        const subjectElement = document.getElementById('emailSubject');
        if (subjectElement) {
            subjectElement.textContent = emailData.subject || 'No Subject';
        }

        // Update metadata
        const fromElement = document.querySelector('.email-meta .from span');
        if (fromElement) {
            fromElement.textContent = formatSenderForDisplay(emailData.sender, emailData.sender_email);
        }

        const toElement = document.querySelector('.email-meta .to span');
        if (toElement) {
            let recipientsText = '';
            
            // Handle different recipient formats
            if (emailData.recipients) {
                // If recipients is a string but looks like JSON, try to parse it
                if (typeof emailData.recipients === 'string' && 
                    (emailData.recipients.startsWith('[') || emailData.recipients.startsWith('{'))) {
                    try {
                        const parsedRecipients = JSON.parse(emailData.recipients);
                        
                        if (Array.isArray(parsedRecipients)) {
                            // Handle array of recipient objects or strings
                            recipientsText = parsedRecipients.map(recipient => {
                                if (typeof recipient === 'object' && recipient !== null) {
                                    return recipient.email || recipient.name || JSON.stringify(recipient);
                                }
                                return recipient;
                            }).join(', ');
                        } else if (typeof parsedRecipients === 'object' && parsedRecipients !== null) {
                            // Handle single recipient object
                            recipientsText = parsedRecipients.email || parsedRecipients.name || JSON.stringify(parsedRecipients);
                        } else {
                            recipientsText = String(parsedRecipients);
                        }
                    } catch (e) {
                        console.warn('Error parsing recipients JSON:', e);
                        recipientsText = emailData.recipients; // Use as-is if parsing fails
                    }
                } else if (typeof emailData.recipients === 'object' && emailData.recipients !== null) {
                    // Handle direct object
                    if (Array.isArray(emailData.recipients)) {
                        // Array of objects or strings
                        recipientsText = emailData.recipients.map(recipient => {
                            if (typeof recipient === 'object' && recipient !== null) {
                                return recipient.email || recipient.name || JSON.stringify(recipient);
                            }
                            return recipient;
                        }).join(', ');
                    } else {
                        // Single object
                        recipientsText = emailData.recipients.email || 
                                        emailData.recipients.name || 
                                        JSON.stringify(emailData.recipients);
                    }
                } else {
                    // Handle simple string or other primitive
                    recipientsText = String(emailData.recipients);
                }
            }
            
            // Clean up any remaining [object Object] that might have slipped through
            recipientsText = recipientsText.replace(/\[object Object\]/g, '');
            
            // Set the cleaned text or default message
            toElement.textContent = recipientsText || 'No Recipients';
            
            // Make sure to remove any validation classes from metadata fields
            toElement.classList.remove('is-invalid', 'is-valid');
            
            // Remove any validation messages that might have been added to metadata
            const metadataContainer = document.querySelector('.email-meta');
            if (metadataContainer) {
                const errorMessages = metadataContainer.querySelectorAll('.invalid-feedback');
                errorMessages.forEach(msg => msg.remove());
            }
        }

        // Update date
        const dateElement = document.querySelector('.email-meta .date span');
        if (dateElement) {
            const formattedDate = emailData.date ? formatDetailDate(emailData.date) : formatDetailDate(new Date());
            dateElement.textContent = formattedDate;
            dateElement.setAttribute('data-date', emailData.date || new Date().toISOString());
        }

        // Update content
        const contentElement = document.getElementById('emailContent');
        if (contentElement) {
            contentElement.innerHTML = emailData.body || emailData.snippet || 'No content available';
        }

        // Update attachments
        const attachmentsSection = document.getElementById('emailAttachments');
        if (attachmentsSection) {
            if (emailData.has_attachments && emailData.attachments?.length > 0) {
                attachmentsSection.style.display = 'block';
                const attachmentsList = attachmentsSection.querySelector('.list-group');
                if (attachmentsList) {
                    attachmentsList.innerHTML = emailData.attachments.map(attachment => `
                        <div class="list-group-item">
                            <div>
                                <i class="fas fa-file me-2"></i>
                                ${escapeHtml(attachment)}
                            </div>
                            <div class="btn-group">
                                <a href="/api/attachment/${emailId}/${encodeURIComponent(attachment)}" 
                                   class="btn btn-sm btn-outline-primary" 
                                   download="${escapeHtml(attachment)}" 
                                   title="Download">
                                    <i class="fas fa-download"></i> Download
                                </a>
                                <button type="button" class="btn btn-sm btn-outline-secondary" 
                                        onclick="previewAttachment('${emailId}', '${escapeHtml(attachment)}')" 
                                        title="Preview">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </div>
                        </div>
                    `).join('');
                }
            } else {
                attachmentsSection.style.display = 'none';
            }
        }

        // Show email container
        if (emailContainer) {
            emailContainer.style.display = 'block';
        }

        // Clean up any validation artifacts
        cleanupMetadataValidation();

    } catch (error) {
        console.error('Error loading email:', error);
        
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    ${error.message || 'Failed to load email details'}
                </div>
                <div class="text-center mt-3">
                    <a href="/sent/" class="btn btn-primary">
                        <i class="fas fa-arrow-left me-1"></i> Return to Sent
                    </a>
                </div>
            `;
            errorContainer.style.display = 'block';
        }
    } finally {
        // Hide loading indicator
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    }
}

// Function to clean up any validation artifacts in the metadata
function cleanupMetadataValidation() {
    // Clean up email metadata fields
    const metadataFields = document.querySelectorAll('.email-meta span');
    metadataFields.forEach(field => {
        field.classList.remove('is-invalid', 'is-valid');
    });
    
    // Remove any validation messages
    const metadataContainer = document.querySelector('.email-meta');
    if (metadataContainer) {
        const validationMessages = metadataContainer.querySelectorAll('.invalid-feedback, .valid-feedback');
        validationMessages.forEach(msg => msg.remove());
    }
    
    // Also ensure email content doesn't have validation classes
    const emailContent = document.getElementById('emailContent');
    if (emailContent) {
        emailContent.classList.remove('is-invalid', 'is-valid');
    }
}

// Function to handle back button click
function handleBackButtonClick() {
    window.location.href = '/spam/';
}

// Function to handle reply button click
function handleReplyClick(emailId) {
    replyEmail(emailId);
}

// Function to handle forward button click
function handleForwardClick(emailId) {
    forwardEmail(emailId);
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
            toField.removeAttribute('readonly'); // allow typing
            toField.classList.remove('is-valid', 'is-invalid'); // reset styles

            // **** FIX: Set the recipient email using the new helper ****
            const recipientEmail = extractPrimaryRecipient(email.recipients);
            if (recipientEmail) {
                toField.value = recipientEmail;
                console.log(`Set To field for reply: ${recipientEmail}`);
                // Optionally trigger validation immediately
                validateEmailField(toField);
            } else {
                console.warn("Could not determine recipient email for reply.");
                toField.value = ''; // Ensure it's empty if recipient not found
                showFieldError(toField, 'Could not determine recipient. Please enter manually.');
                toField.focus();
            }
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

// Function to handle voice commands
function handleVoiceCommand(command) {
    if (!command) return;
    
    // Convert to lowercase for case-insensitive matching
    const lowerCommand = command.toLowerCase().trim();
    console.log('Processing voice command:', lowerCommand);
    
    // Get the current email ID
    const emailId = getDirectEmailId();
    
    // Command patterns
    if (lowerCommand.includes('reply') || lowerCommand.includes('respond')) {
        handleReplyClick(emailId);
    } 
    else if (lowerCommand.includes('forward')) {
        handleForwardClick(emailId);
    }
    else if (lowerCommand.includes('read') || lowerCommand.includes('what does it say')) {
        // Read email content aloud
        const emailContent = document.getElementById('emailContent');
        const emailSubject = document.getElementById('emailSubject');
        
        if (emailContent && emailSubject) {
            const contentToRead = `Email subject: ${emailSubject.textContent}. Email content: ${emailContent.innerText || emailContent.textContent}`;
            
            // Use browser's speech synthesis if available
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(contentToRead);
                speechSynthesis.speak(utterance);
                showSuccess('Reading email aloud...');
            } else {
                showError('Text-to-speech is not supported in your browser');
            }
        }
    }
    else if (lowerCommand.includes('go back') || lowerCommand.includes('return to sent')) {
        handleBackButtonClick();
    }
    else if (lowerCommand.includes('close') || lowerCommand.includes('exit')) {
        closeComposeModal();
    }
    else {
        showError(`Sorry, I don't understand the command: "${command}"`);
    }
}

// Function to close compose modal and reset form
function closeComposeModal() {
    // Get the modal instance
    const composeModal = document.getElementById('composeModal');
    if (composeModal) {
        const modal = bootstrap.Modal.getInstance(composeModal);
        if (modal) {
            modal.hide();
        }
    }
    
    // Reset form fields with a slight delay to avoid errors
    setTimeout(() => {
    const form = document.getElementById('composeForm');
    if (form) {
            // Reset form
        form.reset();
        
        // Clear any validation states
        clearValidationMessages(form);
        
        // Reset data attributes
        form.dataset.originalEmailId = '';
        form.dataset.action = 'new';
        
        // Hide CC/BCC fields and show buttons
        const ccContainer = document.getElementById('emailCcContainer');
        const bccContainer = document.getElementById('emailBccContainer');
        const ccButton = document.getElementById('ccButton');
        const bccButton = document.getElementById('bccButton');
        
        if (ccContainer) ccContainer.classList.add('d-none');
        if (bccContainer) bccContainer.classList.add('d-none');
        if (ccButton) ccButton.classList.remove('d-none');
        if (bccButton) bccButton.classList.remove('d-none');
    }
    }, 100);
}

// Function to clear validation messages
function clearValidationMessages(form) {
    if (!form) return;
    
    const errorMessages = form.querySelectorAll('.invalid-feedback');
    errorMessages.forEach(msg => msg.remove());
    
    // Remove invalid states from fields
    const invalidFields = form.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => field.classList.remove('is-invalid'));
    
    // Remove valid states from fields
    const validFields = form.querySelectorAll('.is-valid');
    validFields.forEach(field => field.classList.remove('is-valid'));
}

// Function to validate individual email address
function isValidEmailAddress(email) {
    if (!email) return false;
    
    // Remove any leading/trailing whitespace
    email = email.trim();
    
    // Allow formats like "Name <email@example.com>" or "email@example.com"
    if (email.includes('<') && email.includes('>')) {
        // Extract the email part from "Name <email@example.com>"
        const matches = email.match(/<([^>]+)>/);
        if (matches && matches.length > 1) {
            email = matches[1].trim();
        }
    }
    
    // Simple check - just ensure it has @ symbol for basic validation
    // This is more lenient than before but prevents common issues
    return email.includes('@');
}

// Track submit status to prevent multiple submissions
let isSubmitting = false;

// Function to handle email submission
async function handleEmailSubmission(e) {
    console.log("Email submission triggered", e);
    if (e && typeof e.preventDefault === 'function') {
        e.preventDefault();
    }
    
    if (isSubmitting) {
        console.log("Already submitting, preventing duplicate submission");
        return false;
    }
    
    const form = document.getElementById('composeForm');
    if (!form) {
        showError('Compose form not found');
        console.error("Form element not found");
        return false;
    }
    
    console.log("--- Starting Submission Validation ---");
    clearValidationMessages(form);
    
    // Safely get form elements - with null checks
    const toField = document.getElementById('emailTo');
    const subjectField = document.getElementById('emailSubject');
    const bodyField = document.getElementById('emailBody');
    const ccField = document.getElementById('emailCc');
    const bccField = document.getElementById('emailBcc');
    
    console.log("Form fields found:", {
        toField: !!toField,
        subjectField: !!subjectField,
        bodyField: !!bodyField,
        ccField: !!ccField,
        bccField: !!bccField
    });
    
    // Safety check for required fields
    if (!toField || !subjectField || !bodyField) {
        console.error("Validation Error: Required form fields (To, Subject, Body) not found");
        showError('Required form fields not found');
        return false;
    }
    
    // Get the values directly from the fields and ensure they're strings
    const toValue = toField.value ? String(toField.value).trim() : '';
    const subjectValue = subjectField.value ? String(subjectField.value).trim() : '';
    const bodyValue = bodyField.value ? String(bodyField.value).trim() : '';
    const ccValue = ccField && ccField.value ? String(ccField.value).trim() : '';
    const bccValue = bccField && bccField.value ? String(bccField.value).trim() : '';
    
    console.log("Form values:", {
        to: toValue,
        subject: subjectValue,
        bodyLength: bodyValue ? bodyValue.length : 0,
        ccValue: ccValue ? 'Set' : 'Not Set',
        bccValue: bccValue ? 'Set' : 'Not Set'
    });
    
    let isValid = true;
    let firstInvalidField = null;
    
    // Validate To field with improved email validation
    console.log("Validating To field:", toValue);
    if (!toValue) {
        console.error("Validation Error: Recipient email is required");
        isValid = false;
        showFieldError(toField, 'Recipient email is required');
        if (!firstInvalidField) firstInvalidField = toField;
    } else {
        // Split multiple emails by comma
        const emails = toValue.split(',').map(email => email.trim());
        const invalidEmails = [];
        
        // Check each email
        for (const email of emails) {
            // More lenient check - just ensure it has @ symbol
            if (!email.includes('@')) {
                invalidEmails.push(email);
            }
        }
        
        if (invalidEmails.length > 0) {
            console.error("Validation Error: Invalid email format", invalidEmails);
            isValid = false;
            showFieldError(toField, 'Invalid email address format: ' + invalidEmails.join(', '));
            if (!firstInvalidField) firstInvalidField = toField;
        }
    }
    
    // Validate Subject field (Optional with confirmation)
    if (isValid && !subjectValue) {
        console.warn("Subject field is empty, asking for confirmation.");
        const confirmSend = confirm('Are you sure you want to send this email without a subject?');
        if (!confirmSend) {
            console.error("Validation Error: User cancelled sending without subject");
            isValid = false;
            showFieldError(subjectField, 'Subject is required');
            if (!firstInvalidField) firstInvalidField = subjectField;
        }
    }
    
    // Validate Body field
    if (isValid && !bodyValue) {
        console.error("Validation Error: Body field is empty");
        isValid = false;
        showFieldError(bodyField, 'Message body is required');
        if (!firstInvalidField) firstInvalidField = bodyField;
    }
    
    if (!isValid) {
        if (firstInvalidField) {
            firstInvalidField.focus();
        }
        showError("Please fix the errors in the form before sending.");
        return false;
    }
    
    // Clean the body content
    let cleanedBody = bodyValue;
    try {
        if (typeof cleanEmailBody === 'function') {
            cleanedBody = cleanEmailBody(cleanedBody);
        }
    } catch (cleanError) {
        console.warn('Error cleaning email body, using original content:', cleanError);
    }
    
    // Proceed to send if validation passed
    try {
        console.log("Form is valid, preparing email data...");
        
        // Create email data object
        const emailData = {
            to: toValue,
            subject: subjectValue || '(No Subject)',
            body: cleanedBody,
        };
        
        if (ccValue) emailData.cc = ccValue;
        if (bccValue) emailData.bcc = bccValue;
        
        if (form.dataset.action) {
            emailData.action = form.dataset.action;
        }
        
        console.log("Sending email data:", JSON.stringify(emailData, null, 2));
        
        // Display sending UI
        const sendBtn = document.getElementById('sendEmailBtn');
        if (sendBtn) {
            sendBtn.disabled = true;
            sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Sending...';
        }
        
        isSubmitting = true;
        
        // Send request
        const csrfToken = getCookie('csrftoken');
        const response = await fetch('/api/emails/send/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken || ''
            },
            body: JSON.stringify(emailData),
            credentials: 'same-origin'
        });
        
        console.log("Response status:", response.status);

        if (!response.ok) {
            let errorMessage = `Server Error: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.message || errorData.error || errorMessage;
                console.error("Server returned error:", errorData);
            } catch (err) {
                console.error("Could not parse error response:", err);
            }
            throw new Error(errorMessage);
        }

        const responseData = await response.json();
        console.log("Server response:", responseData);

        // Success handling
        closeComposeModal();
        showSuccess('Email sent successfully!');
        return true;
    } catch (error) {
        console.error('Error during email sending:', error);
        showError(error.message || 'Failed to send email. Please check all fields and try again.');
        
        // Focus on To field if it's likely the issue
        if (error.message && error.message.toLowerCase().includes('recipient')) {
            const toField = document.getElementById('emailTo');
            if (toField) {
                toField.focus();
            }
        }
        
        return false;
    } finally {
        isSubmitting = false;
        // Reset button state
        const sendBtn = document.getElementById('sendEmailBtn');
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fas fa-paper-plane me-1"></i> Send';
        }
    }
}

// Function to validate email field with support for multiple recipients
function validateEmailField(field) {
    if (!field) return false;
    
    // Skip validation for fields that are not in a form or in the compose modal
    const isInForm = field.closest('#composeForm') || field.closest('#composeModal');
    if (!isInForm) {
        console.log('Skipping validation for non-form field:', field.id || field.name);
        return true;
    }
    
    // Get value and handle object values
    let value = field.value;
    
    // Convert to string and trim
    value = String(value || '').trim();
    console.log(`Validating email field ${field.id}:`, value);
    
    // Remove any existing error messages
    const parentNode = field.closest('.position-relative') || field.parentElement;
    if (parentNode) {
        const existingErrors = parentNode.querySelectorAll('.invalid-feedback');
        existingErrors.forEach(error => error.remove());
    }
    
    // Create new error div
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    
    // Always check for empty "To" field (treat as required regardless of attribute)
    if (field.id === 'emailTo' && !value) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        errorDiv.textContent = 'Please enter at least one email address';
        if (parentNode) parentNode.appendChild(errorDiv);
        return false;
    }
    
    // If other field is empty and not required, it's valid
    if (!value && !field.hasAttribute('required')) {
        field.classList.remove('is-invalid', 'is-valid');
        return true;
    }
    
    // If field is empty and required, it's invalid
    if (!value && field.hasAttribute('required')) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        errorDiv.textContent = 'Please enter at least one email address';
        if (parentNode) parentNode.appendChild(errorDiv);
        return false;
    }
    
    // Skip validation if the field is empty (for non-required fields)
    if (!value && field.id !== 'emailTo') {
        return true;
    }
    
    // Split by comma for multiple recipients
    const emails = value.split(',').map(email => email.trim()).filter(email => email.length > 0);
    
    if (emails.length === 0 && (field.hasAttribute('required') || field.id === 'emailTo')) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        errorDiv.textContent = 'Please enter at least one email address';
        if (parentNode) parentNode.appendChild(errorDiv);
        return false;
    }
    
    // Check each email address - use more lenient validation
    const invalidEmails = [];
    for (const email of emails) {
        if (!email.includes('@')) {
            invalidEmails.push(email);
        }
    }
    
    if (invalidEmails.length > 0) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        if (invalidEmails.length === 1) {
            errorDiv.textContent = `Invalid email address: ${invalidEmails[0]}`;
        } else {
            errorDiv.textContent = `Invalid email addresses: ${invalidEmails.join(', ')}`;
        }
        if (parentNode) parentNode.appendChild(errorDiv);
        return false;
    }
    
    // All emails are valid
    field.classList.add('is-valid');
    field.classList.remove('is-invalid');
    return true;
}

// Initialize form handlers
function initializeFormHandlers() {
    const form = document.getElementById('composeForm');
    if (!form) {
        console.error("Compose form not found");
        return;
    }
    
    console.log("Initializing form handlers for:", form.id);
    
    // Get fields
    const toField = document.getElementById('emailTo');
    const ccField = document.getElementById('emailCc');
    const bccField = document.getElementById('emailBcc');
    const subjectField = document.getElementById('emailSubject');
    const bodyField = document.getElementById('emailBody');
    const sendBtn = document.getElementById('sendEmailBtn');
    
    // Make To field editable (allow changing the recipient)
    if (toField) {
        // Remove any readonly attribute
        toField.removeAttribute('readonly');
        
        console.log('Setting up validation handlers for To field');
        // Add validation handlers
        toField.addEventListener('blur', function() {
            console.log('To field blur event triggered, value:', this.value);
            validateEmailField(this);
        });
        
        toField.addEventListener('input', function() {
            console.log('To field input event triggered, value:', this.value);
            // Only validate after user has typed something
            if (this.value.trim().length > 0) {
                validateEmailField(this);
            } else {
                // Clear validation classes if field is empty during typing
                this.classList.remove('is-valid', 'is-invalid');
                const parentNode = this.closest('.position-relative') || this.parentElement;
                if (parentNode) {
                    const errors = parentNode.querySelectorAll('.invalid-feedback');
                    errors.forEach(error => error.remove());
                }
            }
        });
    }
    
    if (ccField) {
        ccField.addEventListener('blur', function() {
            validateEmailField(this);
        });
        
        ccField.addEventListener('input', function() {
            // Only validate after user has typed something
            if (this.value.trim().length > 0) {
                validateEmailField(this);
            } else {
                this.classList.remove('is-valid', 'is-invalid');
            }
        });
    }
    
    if (bccField) {
        bccField.addEventListener('blur', function() {
            validateEmailField(this);
        });
        
        bccField.addEventListener('input', function() {
            // Only validate after user has typed something
            if (this.value.trim().length > 0) {
                validateEmailField(this);
            } else {
                this.classList.remove('is-valid', 'is-invalid');
            }
        });
    }
    
    if (subjectField) {
        subjectField.addEventListener('blur', function() {
            if (this.value.trim()) {
                this.classList.remove('is-invalid');
                const parentNode = this.closest('.position-relative') || this.parentElement;
                const existingErrors = parentNode.querySelectorAll('.invalid-feedback');
                existingErrors.forEach(error => error.remove());
            }
        });
    }
    
    if (bodyField) {
        bodyField.setAttribute('required', 'required');
        bodyField.addEventListener('blur', function() {
            if (!this.value.trim()) {
                this.classList.add('is-invalid');
                showFieldError(this, 'Message body is required');
            } else {
                this.classList.remove('is-invalid');
                const parentNode = this.closest('.position-relative') || this.parentElement;
                const existingErrors = parentNode.querySelectorAll('.invalid-feedback');
                existingErrors.forEach(error => error.remove());
            }
        });
    }
    
    // Add send handler
    if (sendBtn) {
        // Remove existing handler and create a new one
        const newSendBtn = sendBtn.cloneNode(true);
        if (sendBtn.parentNode) {
            sendBtn.parentNode.replaceChild(newSendBtn, sendBtn);
        }
        
        newSendBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Send button clicked');
            handleEmailSubmission(e);
        });
    }
    
    // Add form submit handler
    const newForm = form.cloneNode(true);
    if (form.parentNode) {
        form.parentNode.replaceChild(newForm, form);
    }
    
    newForm.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('Form submitted');
        handleEmailSubmission(e);
    });
    
    // Initialize CC/BCC buttons
    const ccButton = document.getElementById('ccButton');
    const bccButton = document.getElementById('bccButton');
    
    if (ccButton) {
        ccButton.addEventListener('click', () => {
            const ccContainer = document.getElementById('emailCcContainer');
            if (ccContainer) {
                ccContainer.classList.toggle('d-none');
                if (!ccContainer.classList.contains('d-none')) {
                    document.getElementById('emailCc')?.focus();
                }
            }
        });
    }
    
    if (bccButton) {
        bccButton.addEventListener('click', () => {
            const bccContainer = document.getElementById('emailBccContainer');
            if (bccContainer) {
                bccContainer.classList.toggle('d-none');
                if (!bccContainer.classList.contains('d-none')) {
                    document.getElementById('emailBcc')?.focus();
                }
            }
        });
    }
}

// Initialize event handlers when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - initializing sent email detail handlers');
    
    // Format dates
    const dateElements = document.querySelectorAll('[data-date]');
    dateElements.forEach(element => {
        const originalDate = element.getAttribute('data-date');
        if (originalDate) {
            element.textContent = moment(originalDate).format('dddd, MMMM D, YYYY [at] h:mm A');
        }
    });
    
    // Initialize reply buttons using direct click handlers instead of delegated events
    document.querySelectorAll('.reply-btn, [title="Reply"]').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Reply button clicked directly');
            
            // Get the ID from either data attribute or URL
            const emailId = this.getAttribute('data-email-id') || getDirectEmailId();
            if (emailId) {
                replyEmail(emailId);
            } else {
                console.error('No email ID found for reply');
                showError('Could not determine which email to reply to');
            }
        });
    });
    
    // Initialize forward buttons using direct click handlers instead of delegated events
    document.querySelectorAll('.forward-btn, [title="Forward"]').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Forward button clicked directly');
            
            // Get the ID from either data attribute or URL
            const emailId = this.getAttribute('data-email-id') || getDirectEmailId();
            if (emailId) {
                forwardEmail(emailId);
            } else {
                console.error('No email ID found for forward');
                showError('Could not determine which email to forward');
            }
        });
    });
    
    // Initialize send email button
    const sendButton = document.getElementById('sendEmailBtn');
    if (sendButton) {
        sendButton.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Send button clicked');
            handleEmailSubmission(e);
        });
    }
    
    // Initialize voice command button
    setTimeout(() => {
        const voiceCommandBtn = document.getElementById('voiceCommandBtn');
        if (voiceCommandBtn && typeof initSpeechRecognition === 'function') {
            initSpeechRecognition();
        }
    }, 1000);
    
    // Initialize compose form handlers
    if (typeof initializeFormHandlers === 'function') {
        initializeFormHandlers();
    }
    
    // Initialize modal listeners
    const composeModal = document.getElementById('composeModal');
    if (composeModal) {
        composeModal.addEventListener('hidden.bs.modal', function() {
            console.log('Modal hidden, cleaning up');
            // Reset form only after modal is fully hidden
            setTimeout(() => {
            const form = document.getElementById('composeForm');
            if (form) {
                    form.reset();
                clearValidationMessages(form);
                }
            }, 100);
        });
                
        composeModal.addEventListener('shown.bs.modal', function() {
            console.log('Modal shown, initializing form handlers');
            // Re-initialize handlers when modal is shown
            if (typeof initializeFormHandlers === 'function') {
                initializeFormHandlers();
            }
        });
    }
    
    // Load email details if not already loaded
    if (window.location.pathname.includes('/sent_email_detail/')) {
        loadEmailDetails();
    }

    // If there is any event listener for #backToSent, update it to #backToSpam and ensure it navigates to /spam/
    const backToSpamBtn = document.getElementById('backToSpam');
    if (backToSpamBtn) {
        backToSpamBtn.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/spam/';
        });
    }
});

// Fix accessibility issue with aria-hidden
function fixAriaAttributes() {
    // Find elements with aria-hidden that might cause issues
    const modalElements = document.querySelectorAll('[aria-hidden="true"]');
    modalElements.forEach(element => {
        // Check if this is causing the issue
        if (element.querySelector(':focus')) {
            // Remove the aria-hidden attribute that's causing problems
            element.removeAttribute('aria-hidden');
            console.log("Removed problematic aria-hidden attribute");
        }
    });
}

// Function to check if setupComposeModal is needed
function checkAndSetupComposeModal() {
    // If compose modal doesn't exist, create a dummy one to avoid errors
    if (!document.getElementById('composeModal')) {
        console.log('Compose modal not found, setting up dynamically');
        const modalHTML = `
        <div class="modal fade" id="composeModal" tabindex="-1" aria-labelledby="composeModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="composeModalLabel">Compose Email</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="composeForm" class="compose-email-form">
                            <!-- From field -->
                            <div class="compose-field">
                                <label for="composeFrom" class="form-label">From:</label>
                                <input type="text" class="form-control" id="composeFrom" readonly>
                            </div>
                            
                            <!-- To field -->
                            <div class="compose-field">
                                <label for="emailTo" class="form-label">To:</label>
                                <div class="position-relative flex-grow-1">
                                    <input type="email" class="form-control" id="emailTo" required>
                                </div>
                            </div>
                            
                            <!-- CC field -->
                            <div class="compose-field cc-field d-none" id="emailCcContainer">
                                <label for="emailCc" class="form-label">Cc:</label>
                                <div class="position-relative flex-grow-1">
                                    <input type="email" class="form-control" id="emailCc">
                                </div>
                            </div>
                            
                            <!-- BCC field -->
                            <div class="compose-field bcc-field d-none" id="emailBccContainer">
                                <label for="emailBcc" class="form-label">Bcc:</label>
                                <div class="position-relative flex-grow-1">
                                    <input type="email" class="form-control" id="emailBcc">
                                </div>
                            </div>
                            
                            <!-- Field controls -->
                            <div class="compose-field-controls">
                                <button type="button" class="btn btn-link" id="ccButton">Cc</button>
                                <button type="button" class="btn btn-link" id="bccButton">Bcc</button>
                            </div>
                            
                            <!-- Subject field -->
                            <div class="compose-field">
                                <label for="emailSubject" class="form-label">Subject:</label>
                                <div class="position-relative flex-grow-1">
                                    <input type="text" class="form-control" id="emailSubject">
                                </div>
                            </div>
                            
                            <!-- Email body -->
                            <div class="compose-field">
                                <textarea class="form-control compose-body" id="emailBody" rows="10"></textarea>
                                <input type="hidden" id="emailHtmlContent">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="sendEmailBtn">
                            <i class="fas fa-paper-plane me-1"></i> Send
                        </button>
                    </div>
                </div>
            </div>
        </div>`;
        
        const div = document.createElement('div');
        div.innerHTML = modalHTML.trim();
        document.body.appendChild(div.firstChild);
        
        // Initialize event handlers
        setTimeout(() => {
            const modal = document.getElementById('composeModal');
            if (modal) {
                // Add event handlers for modal visibility changes
                modal.addEventListener('shown.bs.modal', function() {
                    console.log('Modal shown, initializing form handlers');
                    if (typeof initializeFormHandlers === 'function') {
                        initializeFormHandlers();
                    }
                });
                
                modal.addEventListener('hidden.bs.modal', function() {
                    console.log('Modal hidden, cleaning up');
                    setTimeout(() => {
            const form = document.getElementById('composeForm');
            if (form) {
                form.reset();
                            clearValidationMessages(form);
                        }
                    }, 100);
                });
                
                // Initialize send button
                const sendBtn = document.getElementById('sendEmailBtn');
                if (sendBtn) {
                    sendBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        console.log('Send button clicked');
                        handleEmailSubmission(e);
                    });
                }
                
                // Set user email if available
                const userEmail = document.getElementById('sidebarEmail')?.textContent?.trim() || '';
                const fromField = document.getElementById('composeFrom');
                if (fromField && userEmail) {
                    fromField.value = userEmail;
                }
            }
        }, 100);
    }
}