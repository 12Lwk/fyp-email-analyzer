// Initialize AI analysis from the email detail page
window.initializeAIAnalysis = function(params) {
    console.log('Initializing AI analysis with params:', params);
    
    // Extract sender information from params
    const senderName = params.senderName || '';
    const senderEmail = params.senderEmail || '';
    const emailContent = params.emailContent || '';
    const subject = params.subject || '';
    const userName = params.userName || '';
    const userEmail = params.userEmail || '';
    
    // Store this information for later use
    window.emailAnalysisData = {
        senderName: senderName,
        senderEmail: senderEmail,
        emailContent: emailContent,
        subject: subject,
        userName: userName,
        userEmail: userEmail
    };
    
    // Store user information in localStorage if provided
    if (userName) localStorage.setItem('userName', userName);
    if (userEmail) localStorage.setItem('userEmail', userEmail);
    
    console.log('Email analysis initialized with user:', userName, userEmail);
};

// Main function to generate email analysis
function generateAnalysis() {
    console.log('Generating email analysis...');
    
    // Get elements
    const messageOverview = document.getElementById('messageOverview');
    const suggestedActions = document.getElementById('suggestedActions');
    const generateBtn = document.getElementById('generateAnalysisBtn');
    
    // Get email content and metadata - first try from the stored data, then from DOM
    const emailData = window.emailAnalysisData || {};
    const emailContent = emailData.emailContent || document.getElementById('emailContent')?.textContent || '';
    const emailSubject = emailData.subject || document.getElementById('emailSubject')?.textContent || '';
    const senderName = emailData.senderName || '';
    const senderEmail = emailData.senderEmail || '';
    
    // Combined sender info for API
    const emailFrom = senderName && senderEmail ? 
        `${senderName} <${senderEmail}>` : 
        (senderName || senderEmail || document.getElementById('emailFrom')?.textContent || '');
    
    // Get current user information - try multiple sources
    const currentUserEmail = localStorage.getItem('userEmail') || getCurrentUserEmail();
    let currentUserName = localStorage.getItem('userName') || 
        document.getElementById('sidebarUserName')?.textContent.trim() || 
        document.querySelector('.user-name')?.textContent.trim() ||
        (currentUserEmail ? currentUserEmail.split('@')[0] : '');
        
    // Clean up username if it's an email address
    if (currentUserName && currentUserName.includes('@')) {
        currentUserName = currentUserName.split('@')[0];
    }
    
    // Log the username being used
    console.log('Using username:', currentUserName || 'Not available');
    
    // Ensure we have a valid username
    if (!currentUserName || currentUserName.trim() === '' || currentUserName.toLowerCase() === 'user') {
        showNotification('No user name found. Using default name. Please update your profile settings to include your name.', 'warning');
        currentUserName = 'User';  // Ensure we always have a default name
    }
    
    console.log('Using username:', currentUserName);
    
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
    
    // Prepare email content with user information
    const contentWithUserInfo = `Current User: ${currentUserName}\nCurrent Email: ${currentUserEmail}\n\n${emailContent}`;
    console.log('User info being sent:', currentUserName, currentUserEmail);
    
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
            content: contentWithUserInfo,
            subject: emailSubject,
            sender: emailFrom,
            current_user: currentUserName,
            current_email: currentUserEmail
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.reply_template) {
            // Clean up any existing signature
            data.reply_template = data.reply_template.replace(
                /\s*(?:Best regards|Sincerely|Kind regards),?.*$/i,
                ''
            ).trim();

            // Add the signature with username
            if (currentUserName && currentUserName.trim()) {
                data.reply_template = data.reply_template.trim() + `\n\nBest regards,\n${currentUserName}`;
            } else {
                data.reply_template = data.reply_template.trim() + '\n\nBest regards';
            }
        }
        
        // Update UI with analysis results
        updateAnalysisResults(data);
        
        // Scroll to results after updating UI
        const analysisResult = document.getElementById('analysisResult');
        if (analysisResult) {
            setTimeout(() => {
                analysisResult.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start'
                });
            }, 150); // Slightly increased delay for potentially complex rendering
        }
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

        // Ensure results container is visible before scrolling
        const analysisResultCard = document.getElementById('analysisResult');
        if (analysisResultCard && !analysisResultCard.classList.contains('d-none')) {
            setTimeout(() => {
                console.log('Scrolling to analysis results in finally block...');
                analysisResultCard.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'nearest' // Use nearest to avoid excessive scrolling if already visible
                });
            }, 150); // Delay for rendering
        }
    });
}

// Update UI with analysis results
function updateAnalysisResults(data) {
    const analysisResultCard = document.getElementById('analysisResult'); 
    if (!analysisResultCard) {
        console.error('Analysis result card element (#analysisResult) not found!');
        return;
    }
    
    const analysisContentArea = analysisResultCard.querySelector('.card-body');
    if (!analysisContentArea) {
        console.error('Analysis content area (.card-body) not found inside #analysisResult!');
        return;
    }

    // Clear previous results from the content area
    analysisContentArea.innerHTML = '';

    try {
        // Get current user information
        const currentUserEmail = localStorage.getItem('userEmail') || getCurrentUserEmail();
        const currentUserName = localStorage.getItem('userName') || 
            document.getElementById('sidebarUserName')?.textContent.trim() || 
            document.querySelector('.user-name')?.textContent.trim() ||
            (currentUserEmail ? currentUserEmail.split('@')[0] : '');
        
        console.log('Using user in results display:', currentUserName);
        
        // Get sender information from stored data or DOM
        const emailData = window.emailAnalysisData || {};
        let senderName = emailData.senderName || '';
        let senderEmail = emailData.senderEmail || '';
        
        // Fallback to DOM if needed
        if (!senderName && !senderEmail) {
            const emailFrom = document.getElementById('emailFrom')?.textContent || '';
            
            if (emailFrom.includes('<')) {
                // Format: "Name <email@example.com>"
                senderName = emailFrom.split('<')[0].replace('From:', '').trim();
                senderEmail = emailFrom.split('<')[1].replace('>', '').trim();
            } else {
                // Format: "From: email@example.com" or just "email@example.com"
                senderEmail = emailFrom.replace('From:', '').trim();
                // For no-reply or system emails, use the domain part as name
                if (senderEmail.toLowerCase().includes('noreply') || senderEmail.toLowerCase().includes('no-reply')) {
                    const domain = senderEmail.split('@')[1].split('.')[0];
                    senderName = `${domain.charAt(0).toUpperCase() + domain.slice(1)} Team`;
                } else {
                    senderName = senderEmail.split('@')[0];
                }
            }
        }
        
        // Clean up sender name
        if (!senderName || senderName.toLowerCase() === 'from:') {
            if (senderEmail.toLowerCase().includes('noreply') || senderEmail.toLowerCase().includes('no-reply')) {
                const domain = senderEmail.split('@')[1].split('.')[0];
                senderName = `${domain.charAt(0).toUpperCase() + domain.slice(1)} Team`;
            } else if (senderEmail && senderEmail.includes('@')) {
                senderName = senderEmail.split('@')[0];
            } else {
                senderName = 'Support Team';
            }
        }

        // Ensure data is properly formatted
        const analysisData = {
            summary: data.summary || 'No summary available',
            key_points: Array.isArray(data.key_points) ? data.key_points : ['No key points available'],
            actions: Array.isArray(data.actions) ? data.actions : ['No actions available'],
            priority: (data.priority || 'medium').toLowerCase(),
            category: (data.category || 'other').toLowerCase(),
            reply_template: data.reply_template || ''
        };
        
        // If no reply template provided, create a default one
        if (!analysisData.reply_template) {
            analysisData.reply_template = `Dear ${senderName},

Thank you for your email. I will review your message and respond accordingly.

Best regards,
${currentUserName}`;
        } else {
            // Clean up any existing signatures to prevent duplicates
            analysisData.reply_template = analysisData.reply_template
                .replace(/\s*(?:Best regards|Sincerely|Kind regards|Regards),?.*$/gim, '')
                .trim();
                
            // Add signature only if it doesn't already have one
            if (!analysisData.reply_template.includes('Best regards')) {
                analysisData.reply_template += `\n\nBest regards,\n${currentUserName}`;
            }
        }

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
            analysisContentArea.appendChild(sectionDiv);
        });

        // Add suggested reply section
        const replySection = document.createElement('div');
        replySection.className = 'analysis-section mb-4';
        
        const replyTitle = document.createElement('h4');
        replyTitle.className = 'section-title mb-2';
        replyTitle.textContent = 'Suggested Reply';
        replySection.appendChild(replyTitle);
        
        // Create a paragraph element for the reply content
        const replyContent = document.createElement('p');
        replyContent.className = 'suggested-reply mb-3';
        replyContent.id = 'suggestedReply';
        replyContent.style.cssText = `
            white-space: pre-line;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            border: 1px solid #dee2e6;
            line-height: 1.8;
            margin-bottom: 1rem;
        `;

        // Split the reply into sections
        const replyParts = analysisData.reply_template.split(/[,.]\s+/);
        
        // Format each part and join with proper punctuation and line breaks
        const formattedReply = replyParts.map((part, index) => {
            part = part.trim();
            
            // Handle greeting
            if (part.startsWith('Dear')) {
                return part + ',\n\n';
            }
            
            // Handle signature
            if (part.toLowerCase().includes('best regards')) {
                return '\n\n' + part + ',\n';
            }
            
            // Handle the name at the end
            if (index === replyParts.length - 1 && part.includes(currentUserName)) {
                return part;
            }
            
            // Add comma and space for normal parts
            return part + ', ';
        }).join('').trim();

        replyContent.textContent = formattedReply;
        replySection.appendChild(replyContent);
        
        const buttonDiv = document.createElement('div');
        buttonDiv.className = 'mt-3';
        buttonDiv.innerHTML = `
            <button class="btn btn-primary btn-use-suggested-reply">
                <i class="fas fa-reply me-2"></i>Use Suggested Reply
            </button>
        `;
        replySection.appendChild(buttonDiv);
        
        analysisContentArea.appendChild(replySection);

        // Show the analysis container
        analysisResultCard.classList.remove('d-none');
        
        // Add smooth scrolling *after* content is updated and card is visible
        setTimeout(() => {
            console.log('Scrolling to analysis results...');
            analysisResultCard.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }, 150); // Delay to ensure rendering
        
    } catch (error) {
        console.error('Error updating analysis results UI:', error);
        analysisContentArea.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                Error displaying analysis results. Please try again.
            </div>
        `;
         // Ensure the card is visible even if there's an error displaying results
        analysisResultCard.classList.remove('d-none');
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
    
    // Set reply content with proper formatting
    const emailBody = document.getElementById('emailBody');
    if (emailBody) {
        emailBody.value = formatReplyText(replyText);
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

// Function to properly format reply text
function formatReplyText(text) {
    if (!text) return '';
    
    // First, normalize line endings to ensure consistent handling
    text = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    
    // Convert line breaks to proper HTML paragraphs
    let paragraphs = text.split(/\n\n+/);
    
    // Format each paragraph with proper HTML
    let htmlContent = paragraphs
        .map(para => {
            // Handle individual line breaks within paragraphs
            para = para.replace(/\n/g, '<br>');
            return `<p style="margin: 0 0 10px 0; line-height: 1.5;">${para}</p>`;
        })
        .join('');
    
    // Add signature with proper styling
    htmlContent += `
        <p style="margin-top: 20px; padding-top: 10px; border-top: 1px solid #eee;">
            --<br>
            <span style="color: #666; font-size: 12px;">Sent from Smart Email Management System</span>
        </p>
    `;
    
    return htmlContent;
}

// Function to use the suggested reply
function useSuggestedReply() {
    console.log('Using suggested reply');

    try {
        // Get the suggested reply content from the analysis section
        const suggestedReplyElement = document.querySelector('.analysis-category:last-child .analysis-content');
        if (!suggestedReplyElement) {
            console.error('Suggested reply element not found');
            showNotification('Could not find suggested reply content', 'error');
            return;
        }

        const replyText = suggestedReplyElement.textContent.trim();
        console.log('Reply text:', replyText);

        // Get the current user email
        const userEmail = (getCurrentUserEmail() || '').trim().toLowerCase();

        // Get the original sender and recipient from the email meta section
        let senderEmail = '';
        let recipientEmail = '';
        let fromText = '';
        let toText = '';

        // Try to get sender and recipient from the email meta section
        const metaSection = document.querySelector('.email-meta');
        if (metaSection) {
            const metaLines = metaSection.querySelectorAll('p');
            metaLines.forEach(line => {
                if (line.textContent.startsWith('From:')) {
                    fromText = line.textContent.replace('From:', '').trim();
                }
                if (line.textContent.startsWith('To:')) {
                    toText = line.textContent.replace('To:', '').trim();
                }
            });
        }

        // Extract sender email
        senderEmail = extractEmailAddress(fromText);
        // Extract recipient email(s)
        recipientEmail = extractEmailAddress(toText);

        // Decide who to reply to: if you are the recipient, reply to sender; if you are the sender, reply to recipient
        let replyTo = '';
        if (recipientEmail && recipientEmail.toLowerCase() === userEmail && senderEmail && senderEmail.toLowerCase() !== userEmail) {
            replyTo = senderEmail;
        } else if (senderEmail && senderEmail.toLowerCase() === userEmail && recipientEmail && recipientEmail.toLowerCase() !== userEmail) {
            replyTo = recipientEmail;
        } else if (senderEmail && senderEmail.toLowerCase() !== userEmail) {
            replyTo = senderEmail;
        } else if (recipientEmail && recipientEmail.toLowerCase() !== userEmail) {
            replyTo = recipientEmail;
        } else {
            replyTo = '';
        }

        // Open the compose modal
        const composeModalElement = document.getElementById('composeModal');
        if (!composeModalElement) {
            console.error('Compose modal not found');
            showNotification('Compose modal not found', 'error');
            return;
        }
        const composeModal = new bootstrap.Modal(composeModalElement);

        // Set fields after modal is shown
        composeModalElement.addEventListener('shown.bs.modal', function modalShownHandler() {
            // Set From field
            const fromField = composeModalElement.querySelector('#emailFrom');
            if (fromField) {
                fromField.value = userEmail;
            }
            // Set To field
            const toField = composeModalElement.querySelector('#emailTo');
            if (toField) {
                toField.value = replyTo;
            }
            // Set Subject field
            const subjectField = composeModalElement.querySelector('#emailSubject');
            if (subjectField) {
                const subject = document.querySelector('#emailSubject')?.textContent || '';
                subjectField.value = subject.startsWith('Re:') ? subject : `Re: ${subject}`;
            }
            // Set Body field
            const bodyField = composeModalElement.querySelector('#emailBody');
            if (bodyField) {
                bodyField.value = replyText;
                bodyField.focus();
            }
            // Remove this event listener after running once
            composeModalElement.removeEventListener('shown.bs.modal', modalShownHandler);
        });

        // Show the modal
        composeModal.show();

    } catch (error) {
        console.error('Error using suggested reply:', error);
        showNotification('Error using suggested reply: ' + error.message, 'error');
    }
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

// Helper function to get current user email
function getCurrentUserEmail() {
    // Try to find user email in the sidebar
    const sidebarEmail = document.getElementById('sidebarEmail');
    if (sidebarEmail) {
        const email = sidebarEmail.textContent.trim();
        if (email && email.includes('@')) {
            return email;
        }
        
        // Try data attribute
        const dataEmail = sidebarEmail.getAttribute('data-user-email');
        if (dataEmail && dataEmail.includes('@')) {
            return dataEmail;
        }
    }
    
    // Fallback - look for email-like patterns in the page
    const emailRegex = /[\w._%+-]+@[\w.-]+\.[a-zA-Z]{2,}/g;
    const bodyText = document.body.textContent;
    const matches = bodyText.match(emailRegex);
    
    if (matches && matches.length > 0) {
        // Find most common email which is likely the user's
        const emailCounts = {};
        matches.forEach(email => {
            emailCounts[email] = (emailCounts[email] || 0) + 1;
        });
        
        // Find email with most occurrences
        let mostCommonEmail = null;
        let highestCount = 0;
        
        for (const email in emailCounts) {
            if (emailCounts[email] > highestCount) {
                highestCount = emailCounts[email];
                mostCommonEmail = email;
            }
        }
        
        if (mostCommonEmail) {
            return mostCommonEmail;
        }
    }
    
    // Last resort - return a generic placeholder
    return 'user@example.com';
}

// Add event listeners when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Analysis module loaded');
    
    // Connect Generate Analysis button
    const generateBtn = document.getElementById('generateAnalysisBtn');
    const analysisLoading = document.getElementById('analysisLoading');
    const analysisResult = document.getElementById('analysisResult');
    
    // Add event listener for Use Suggested Reply button (both static and dynamic)
    document.addEventListener('click', function(e) {
        const target = e.target;
        
        // Check if the clicked element is the Use Suggested Reply button or its icon
        if (target.id === 'useSuggestedReplyBtn' || 
            target.closest('#useSuggestedReplyBtn') ||
            target.classList.contains('btn-use-suggested-reply') || 
            target.closest('.btn-use-suggested-reply')) {
            
            e.preventDefault();
            console.log('Use Suggested Reply button clicked');
            useSuggestedReply();
        }
    });

    // Add direct event listener for the static button
    const staticSuggestedReplyBtn = document.getElementById('useSuggestedReplyBtn');
    if (staticSuggestedReplyBtn) {
        staticSuggestedReplyBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Static Use Suggested Reply button clicked');
            useSuggestedReply();
        });
    }

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

                // Ensure results container is visible before scrolling
                const analysisResultCard = document.getElementById('analysisResult');
                if (analysisResultCard && !analysisResultCard.classList.contains('d-none')) {
                    setTimeout(() => {
                        console.log('Scrolling to analysis results in finally block...');
                        analysisResultCard.scrollIntoView({ 
                            behavior: 'smooth', 
                            block: 'nearest' // Use nearest to avoid excessive scrolling if already visible
                        });
                    }, 150); // Delay for rendering
                }
            }
        });
    } else {
        console.warn('Generate Analysis button not found in the DOM');
    }
    
    // Helper function to format lists
    function formatList(items) {
        if (!Array.isArray(items)) {
            return items;
        }
        return items.map(item => `<li>${item}</li>`).join('');
    }
});

// Helper function to extract email address from a string
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

// Helper function to show notifications
function showNotification(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alert.innerHTML = `
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        <i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
        ${message}
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 150);
    }, 5000);
}

// Helper function to create alert container
function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1050; max-width: 400px;';
    document.body.appendChild(container);
    return container;
}
