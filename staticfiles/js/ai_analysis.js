/**
 * AI Analysis Module for Email System
 * Provides functionality to analyze emails using AI services
 */

// Main function to generate email analysis
function generateAnalysis() {
    console.log('Generating email analysis...');
    
    // Get elements
    const messageOverview = document.getElementById('messageOverview');
    const suggestedActions = document.getElementById('suggestedActions');
    const generateBtn = document.getElementById('generateAnalysisBtn');
    
    // Get email content and metadata
    const emailContent = document.getElementById('emailContent').textContent;
    const emailSubject = document.getElementById('emailSubject').textContent;
    const emailFrom = document.getElementById('emailFrom').textContent;
    
    // Extract email ID from path
    const pathParts = window.location.pathname.split('/');
    const inboxIndex = pathParts.indexOf('inbox');
    const emailId = inboxIndex !== -1 && inboxIndex + 1 < pathParts.length ? pathParts[inboxIndex + 1] : null;
    
    // Show loading state
    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
    }
    
    if (messageOverview) {
        messageOverview.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span>Analyzing your email...</span>
            </div>
        `;
    }
    
    if (suggestedActions) {
        suggestedActions.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span>Generating suggestions...</span>
            </div>
        `;
    }
    
    // Call API
    const apiUrl = emailId 
        ? `/api/emails/analyze/${emailId}/`
        : '/api/emails/analyze/';
    
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            content: emailContent,
            subject: emailSubject,
            sender: emailFrom
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Update UI with analysis results
        updateAnalysisResults(data);
    })
    .catch(error => {
        console.error('Error generating analysis:', error);
        
        // Update UI with error
        if (messageOverview) {
            messageOverview.innerHTML = `
                <div class="alert alert-danger mb-0">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error generating analysis: ${error.message}
                </div>
            `;
        }
        
        if (suggestedActions) {
            suggestedActions.innerHTML = '';
        }
    })
    .finally(() => {
        // Reset button state
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate Analysis';
        }
    });
}

// Update UI with analysis results
function updateAnalysisResults(data) {
    const analysisContainer = document.querySelector('.ai-analysis-results');
    if (!analysisContainer) return;

    // Clear previous results
    analysisContainer.innerHTML = '';

    try {
        // Ensure data is properly formatted
        const analysisData = {
            summary: data.summary || 'No summary available',
            key_points: Array.isArray(data.key_points) ? data.key_points : ['No key points available'],
            actions: Array.isArray(data.actions) ? data.actions : ['No actions available'],
            priority: (data.priority || 'medium').toLowerCase(),
            category: (data.category || 'other').toLowerCase(),
            reply_template: data.reply_template || 'Thank you for your email.'
        };

        // Create sections for each part of the analysis
        const sections = [
            {
                title: 'Summary',
                content: analysisData.summary,
                type: 'text'
            },
            {
                title: 'Key Points',
                content: analysisData.key_points,
                type: 'list'
            },
            {
                title: 'Suggested Actions',
                content: analysisData.actions,
                type: 'list'
            },
            {
                title: 'Priority',
                content: analysisData.priority.toUpperCase(),
                type: 'badge',
                class: `priority-${analysisData.priority}`
            },
            {
                title: 'Category',
                content: analysisData.category.charAt(0).toUpperCase() + analysisData.category.slice(1),
                type: 'badge',
                class: `category-${analysisData.category}`
            }
        ];

        // Create and append each section
        sections.forEach(section => {
            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'analysis-section mb-4';

            const title = document.createElement('h4');
            title.className = 'section-title mb-2';
            title.textContent = section.title;
            sectionDiv.appendChild(title);

            let content;
            switch (section.type) {
                case 'list':
                    content = document.createElement('ul');
                    content.className = 'list-unstyled';
                    if (Array.isArray(section.content)) {
                        section.content.forEach(item => {
                            const li = document.createElement('li');
                            li.innerHTML = `<i class="fas fa-check-circle text-success me-2"></i>${item}`;
                            content.appendChild(li);
                        });
                    }
                    break;

                case 'badge':
                    content = document.createElement('span');
                    content.className = `badge ${section.class} me-2`;
                    content.textContent = section.content;
                    break;

                default:
                    content = document.createElement('div');
                    content.className = 'mb-3';
                    content.textContent = section.content;
                    break;
            }

            sectionDiv.appendChild(content);
            analysisContainer.appendChild(sectionDiv);
        });

        // Add suggested reply section if available
        if (analysisData.reply_template) {
            const replySection = document.createElement('div');
            replySection.className = 'analysis-section mb-4';
            
            const replyTitle = document.createElement('h4');
            replyTitle.className = 'section-title mb-2';
            replyTitle.textContent = 'Suggested Reply';
            replySection.appendChild(replyTitle);
            
            const replyContent = document.createElement('div');
            replyContent.className = 'suggested-reply mb-3';
            replyContent.textContent = analysisData.reply_template;
            replySection.appendChild(replyContent);
            
            const buttonDiv = document.createElement('div');
            buttonDiv.className = 'mt-2';
            buttonDiv.innerHTML = `
                <button onclick="useSuggestedReply()" class="btn btn-primary">
                    <i class="fas fa-reply me-2"></i>Use Suggested Reply
                </button>
            `;
            replySection.appendChild(buttonDiv);
            
            analysisContainer.appendChild(replySection);
        }

        // Show the analysis container
        analysisContainer.style.display = 'block';
        
    } catch (error) {
        console.error('Error updating analysis results:', error);
        analysisContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                Error displaying analysis results. Please try again.
            </div>
        `;
    }
}

// Get CSRF token from cookies
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

// Format date for display
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
        return '';
    }
    
    return date.toLocaleDateString();
}

// Generate reply suggestion
function suggestReply() {
    console.log('Generating reply suggestion...');
    
    // Get email content and metadata
    const emailContent = document.getElementById('emailContent').textContent;
    const emailSubject = document.getElementById('emailSubject').textContent;
    const emailFrom = document.getElementById('emailFrom').textContent;
    
    // Extract email ID from path
    const pathParts = window.location.pathname.split('/');
    const inboxIndex = pathParts.indexOf('inbox');
    const emailId = inboxIndex !== -1 && inboxIndex + 1 < pathParts.length ? pathParts[inboxIndex + 1] : null;
    
    if (!emailId) {
        console.error('Email ID not found');
        return;
    }
    
    // Call API
    fetch(`/api/emails/suggest-reply/${emailId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            content: emailContent,
            subject: emailSubject,
            sender: emailFrom
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Show suggested reply in compose modal
        showComposeModal(data.reply, emailSubject, emailFrom);
    })
    .catch(error => {
        console.error('Error suggesting reply:', error);
        alert('Failed to generate reply suggestion: ' + error.message);
    });
}

// Show compose modal with reply
function showComposeModal(replyText, subject, to) {
    // Assuming you have a compose modal in your HTML
    const composeModal = document.getElementById('composeEmailModal');
    if (!composeModal) {
        console.error('Compose modal not found');
        return;
    }
    
    // Set reply content
    const emailBody = document.getElementById('emailBody');
    if (emailBody) {
        emailBody.value = replyText;
    }
    
    // Set subject with Re: prefix
    const emailSubject = document.getElementById('emailSubject');
    if (emailSubject) {
        if (!subject.startsWith('Re:')) {
            emailSubject.value = 'Re: ' + subject;
        } else {
            emailSubject.value = subject;
        }
    }
    
    // Set recipient
    const emailTo = document.getElementById('emailTo');
    if (emailTo) {
        emailTo.value = to.replace('From: ', '');
    }
    
    // Show modal
    const bsModal = new bootstrap.Modal(composeModal);
    bsModal.show();
}

// Function to handle using suggested reply
function useSuggestedReply() {
    console.log('Using suggested reply...');
    
    // Get all required elements
    const suggestedReplyContent = document.getElementById('suggestedReply')?.textContent?.trim();
    const emailSubject = document.getElementById('emailSubject')?.textContent?.trim();
    const emailFrom = document.getElementById('emailFrom')?.textContent?.trim();
    const emailId = getEmailIdFromPath();
    
    // Validate all required data
    if (!emailId) {
        showError('Cannot use suggested reply: Email ID not found');
        return;
    }
    if (!suggestedReplyContent) {
        showError('Cannot use suggested reply: No suggested reply content available');
        return;
    }
    if (!emailFrom) {
        showError('Cannot use suggested reply: Recipient email not found');
        return;
    }
    if (!emailSubject) {
        showError('Cannot use suggested reply: Email subject not found');
        return;
    }
    
    // Extract clean email address from the From field
    const recipientEmail = emailFrom.replace('From: ', '').trim();
    if (!recipientEmail.includes('@')) {
        showError('Cannot use suggested reply: Invalid recipient email format');
        return;
    }

    // Show confirmation modal
    const modalHtml = `
        <div class="modal fade" id="confirmReplyModal" tabindex="-1" aria-labelledby="confirmReplyModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="confirmReplyModalLabel">Confirm Reply</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label"><strong>To:</strong></label>
                            <input type="email" class="form-control" id="confirmRecipient" value="${recipientEmail}" readonly>
                        </div>
                        <div class="mb-3">
                            <label class="form-label"><strong>Subject:</strong></label>
                            <input type="text" class="form-control" id="confirmSubject" value="Re: ${emailSubject}" readonly>
                        </div>
                        <div class="mb-3">
                            <label class="form-label"><strong>Message:</strong></label>
                            <textarea class="form-control" id="confirmContent" rows="6">${suggestedReplyContent}</textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="sendReplyBtn">
                            <i class="fas fa-paper-plane me-1"></i> Send Reply
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add modal to document
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer);

    // Initialize modal
    const modal = new bootstrap.Modal(document.getElementById('confirmReplyModal'));
    modal.show();

    // Handle send button click
    document.getElementById('sendReplyBtn').addEventListener('click', function() {
        const sendBtn = this;
        const updatedContent = document.getElementById('confirmContent').value.trim();
        
        if (!updatedContent) {
            showError('Reply content cannot be empty');
            return;
        }

        // Show loading state
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Sending...';

        // Set a fetch timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

        // Send the reply
        fetch('/api/emails/send/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                reply_to: emailId,
                recipient: recipientEmail,
                content: updatedContent,
                subject: `Re: ${emailSubject}`
            }),
            signal: controller.signal
        })
        .then(async response => {
            // Clear the fetch timeout
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage;
                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.error || errorJson.message || 'Unknown error occurred';
                } catch (e) {
                    errorMessage = errorText || `HTTP error! status: ${response.status}`;
                }
                throw new Error(errorMessage);
            }
            return response.json();
        })
        .then(data => {
            // Hide modal
            modal.hide();
            
            // Remove modal from DOM after hiding
            modalContainer.remove();
            
            // Show success message with more details
            showSuccess(`Reply sent successfully to ${recipientEmail}!`);
            
            // Redirect to inbox after short delay
            setTimeout(() => {
                window.location.href = '/inbox_email/';
            }, 1500);
        })
        .catch(error => {
            console.error('Error sending reply:', error);
            
            // Show more user-friendly error message
            let errorMessage = 'Failed to send reply: ';
            if (error.name === 'AbortError') {
                errorMessage += 'Request timed out. Please try again.';
            } else if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
                errorMessage += 'Network connection issue. Please check your internet connection.';
            } else {
                errorMessage += error.message;
            }
            
            showError(errorMessage);
        })
        .finally(() => {
            // Reset button state
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fas fa-paper-plane me-1"></i> Send Reply';
        });
    });

    // Clean up modal when it's hidden
    document.getElementById('confirmReplyModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Function to show success message
function showSuccess(message) {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        const container = document.createElement('div');
        container.id = 'alertContainer';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1050;';
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
    
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 150);
    }, 3000);
}

// Function to get email ID from path
function getEmailIdFromPath() {
    const pathParts = window.location.pathname.split('/');
    const inboxIndex = pathParts.indexOf('inbox_email');
    return inboxIndex !== -1 && inboxIndex + 1 < pathParts.length ? pathParts[inboxIndex + 1] : null;
}

// Add event listeners when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Analysis module loaded');
    
    // Connect Generate Analysis button
    const generateBtn = document.getElementById('generateAnalysisBtn');
    const analysisLoading = document.getElementById('analysisLoading');
    const analysisResult = document.getElementById('analysisResult');
    const useSuggestedReplyBtn = document.getElementById('useSuggestedReplyBtn');
    
    if (generateBtn) {
        generateBtn.addEventListener('click', async function() {
            try {
                console.log('Generate Analysis button clicked');
                
                // Show loading state
                generateBtn.disabled = true;
                analysisLoading.innerHTML = `
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Analyzing email content...</p>
                `;
                analysisLoading.classList.remove('d-none');
                analysisResult.classList.add('d-none');
                
                // Get email content and additional metadata
                const emailContent = document.getElementById('emailContent')?.textContent || '';
                const emailSubject = document.getElementById('emailSubject')?.textContent || '';
                const emailFrom = document.getElementById('emailFrom')?.textContent || '';
                const emailCategory = document.querySelector('.email-category')?.textContent.trim() || '';
                const emailPriority = document.querySelector('.email-priority')?.textContent.trim() || '';
                
                console.log('Email data collected:');
                console.log('- Content length:', emailContent.length);
                console.log('- Subject:', emailSubject);
                console.log('- From:', emailFrom);
                console.log('- Category:', emailCategory);
                console.log('- Priority:', emailPriority);
                
                // Show longer loading message after 3 seconds if still loading
                const loadingMessageTimeout = setTimeout(() => {
                    if (analysisLoading.classList.contains('d-none') === false) {
                        const loadingText = analysisLoading.querySelector('p');
                        if (loadingText) {
                            loadingText.innerHTML = 'Analysis is taking longer than expected. Please wait...<br><small>Note: If you haven\'t started the Ollama server, the system will use fallback responses.</small>';
                        }
                    }
                }, 3000);
                
                // Set a fetch timeout
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
                
                try {
                    // Make API call to analyze email
                    console.log('Sending API request to /api/emails/analyze/');
                    const response = await fetch('/api/emails/analyze/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({
                            content: emailContent,
                            subject: emailSubject,
                            sender: emailFrom,
                            category: emailCategory,
                            priority: emailPriority
                        }),
                        signal: controller.signal
                    });
                    
                    // Clear the fetch timeout
                    clearTimeout(timeoutId);
                    
                    // Clear the loading message timeout
                    clearTimeout(loadingMessageTimeout);
                    
                    // Log the status and response text for debugging
                    console.log('Response status:', response.status);
                    const responseText = await response.text();
                    console.log('Raw response:', responseText);
                    
                    // Parse JSON response only if valid
                    let data;
                    try {
                        data = JSON.parse(responseText);
                        console.log('Parsed JSON data:', data);
                    } catch (e) {
                        console.error('JSON parse error:', e);
                        throw new Error('Invalid JSON response: ' + responseText);
                    }
                    
                    if (!response.ok) {
                        console.error('Response not OK:', data);
                        throw new Error(data.error || 'Analysis failed');
                    }
                    
                    // Display diagnostic info if available
                    if (data.diagnostic_info) {
                        console.log('Diagnostic info:', data.diagnostic_info);
                        
                        // Clear any previous notices
                        const existingNotices = analysisResult.querySelectorAll('.alert');
                        existingNotices.forEach(notice => notice.remove());
                        
                        // If using fallback mode, show a notice to the user
                        if (data.diagnostic_info.provider === 'fallback' || data.diagnostic_info.timeout === true) {
                            const infoDiv = document.createElement('div');
                            infoDiv.className = 'alert alert-warning mt-2 mb-2';
                            infoDiv.innerHTML = `
                                <small>
                                    <strong>Note:</strong> Your request is currently being processed. Please note that due to the complexity of the data, the analysis may take a bit more time than usual.
                                </small>
                            `;
                            analysisResult.prepend(infoDiv);
                        }
                    }
                    
                    // Update UI with analysis results
                    console.log('Updating UI with analysis results');
                    
                    // Make sure all necessary elements exist
                    const keyPointsEl = document.getElementById('keyPoints');
                    const sentimentEl = document.getElementById('sentiment');
                    const suggestedActionsEl = document.getElementById('suggestedActions');
                    const suggestedReplyEl = document.getElementById('suggestedReply');
                    
                    if (keyPointsEl) keyPointsEl.innerHTML = formatList(data.summary ? [data.summary] : ['No key points identified']);
                    if (sentimentEl) sentimentEl.textContent = data.tone || 'Neutral';
                    if (suggestedActionsEl) suggestedActionsEl.innerHTML = formatList(data.actions || ['No suggested actions']);
                    if (suggestedReplyEl) suggestedReplyEl.textContent = data.suggested_reply || 'No reply suggestion available';
                    
                    // Show results
                    analysisLoading.classList.add('d-none');
                    analysisResult.classList.remove('d-none');
                    console.log('Analysis complete and displayed');
                } catch (fetchError) {
                    // Handle fetch timeout or network errors
                    if (fetchError.name === 'AbortError') {
                        console.error('Fetch timeout reached');
                        throw new Error('Analysis request timed out. The server might be busy or the server might not be running.');
                    } else {
                        throw fetchError;
                    }
                }
                
            } catch (error) {
                console.error('Error during analysis:', error);
                
                // Display a more helpful error message based on the error type
                let errorMessage = error.message;
                if (error.message.includes('No connection could be made') || 
                    error.message.includes('refused') || 
                    error.message.includes('connection')) {
                    errorMessage = 'Could not connect to the AI service. Please make sure the Ollama server is running or try again later.';
                }
                
                // Update the loading container to show error
                analysisLoading.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        ${errorMessage}
                    </div>
                    <div class="text-center mt-2">
                        <button class="btn btn-outline-primary btn-sm" onclick="window.location.reload()">
                            <i class="fas fa-sync-alt me-1"></i> Retry
                        </button>
                    </div>
                `;
                
                // Keep the loading container visible to show the error
                analysisLoading.classList.remove('d-none');
            } finally {
                generateBtn.disabled = false;
            }
        });
    } else {
        console.warn('Generate Analysis button not found in the DOM');
    }
    
    if (useSuggestedReplyBtn) {
        useSuggestedReplyBtn.addEventListener('click', function() {
            const suggestedReply = document.getElementById('suggestedReply').textContent;
            const replyTextarea = document.querySelector('textarea[name="content"]');
            if (replyTextarea) {
                replyTextarea.value = suggestedReply;
            }
        });
    }
    
    // Helper function to format lists
    function formatList(items) {
        if (!Array.isArray(items)) {
            return items;
        }
        return items.map(item => `<li>${item}</li>`).join('');
    }
});
