// Function to get URL parameters
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// Function to extract email ID from URL path
function getEmailIdFromPath() {
    const pathParts = window.location.pathname.split('/');
    console.log('Path parts:', pathParts);
    const emailId = pathParts[pathParts.length - 2]; // Get second to last part before trailing slash
    console.log('Found email ID:', emailId);
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

// Function to load email details
async function loadEmailDetails() {
    const emailId = getUrlParameter('id');
    if (!emailId) {
        showError('No email ID provided');
        return;
    }

    try {
        console.log('Fetching sent email details for ID:', emailId);
        const response = await fetch(`/api/emails/${encodeURIComponent(emailId)}/`);
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Data received:', data);

        if (data.status === 'success' && data.email) {
            displayEmailDetails(data.email);
            const deliveryMetrics = document.getElementById('deliveryMetrics');
            if (deliveryMetrics) {
                deliveryMetrics.textContent = 'Click "Generate Analysis" to get delivery metrics for this email.';
            }
        } else {
            throw new Error(data.message || 'Failed to load email details');
        }
    } catch (error) {
        console.error('Error loading email:', error);
        showError(`Error loading email: ${error.message}`);
    }
}

// Function to display email details
function displayEmailDetails(email) {
    console.log('Displaying sent email:', email);
    
    // Helper function to safely update element text content
    const updateElement = (id, value) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        } else {
            console.warn(`Element with id '${id}' not found`);
        }
    };

    // Update header information
    updateElement('emailSubject', email.subject || 'No Subject');
    updateElement('emailFrom', `${email.sender}`);
    updateElement('emailTo', `${email.recipients || 'No recipients'}`);
    updateElement('emailDate', formatDetailDate(email.date));
    
    // Update email content
    const content = document.getElementById('emailContent');
    if (content) {
        content.innerHTML = email.body || email.snippet || 'No content available';
    }
    
    // Update labels
    const labelsContainer = document.getElementById('emailLabels');
    if (labelsContainer) {
        labelsContainer.innerHTML = '';
        if (email.label) {
            const labels = email.label.split(',').map(label => label.trim());
            labels.forEach(label => {
                labelsContainer.innerHTML += `
                    <span class="email-label label-${getLabelClass(label)}">
                        <i class="fas fa-tag"></i> ${escapeHtml(label)}
                    </span>
                `;
            });
        }
        // Add sent label
        labelsContainer.innerHTML += `
            <span class="email-label label-sent">
                <i class="fas fa-paper-plane"></i> Sent
            </span>
        `;
    }
    
    // Update delivery status
    const deliveryStatus = document.getElementById('deliveryStatus');
    if (deliveryStatus) {
        deliveryStatus.innerHTML = `
            <div class="delivery-status-item">
                <i class="fas fa-check-circle"></i>
                <span>Email sent successfully</span>
            </div>
            <div class="delivery-status-item">
                <i class="fas fa-clock"></i>
                <span>Sent on ${formatDetailDate(email.date)}</span>
            </div>
        `;
    }
    
    // Update attachments
    const attachmentsContainer = document.getElementById('emailAttachments');
    if (attachmentsContainer) {
        if (email.has_attachments) {
            attachmentsContainer.style.display = 'block';
            attachmentsContainer.innerHTML = `
                <h6><i class="fas fa-paperclip"></i> Attachments</h6>
                <div class="attachment-item">
                    <i class="fas fa-file"></i>
                    <span>Attachment</span>
                </div>
            `;
        } else {
            attachmentsContainer.style.display = 'none';
        }
    }

    // Update page title
    document.title = `${email.subject || 'Sent Email'} - Email Analytics`;
}

// Function to get label class
function getLabelClass(label) {
    if (!label) return 'default';
    const labelLower = label.toLowerCase();
    if (labelLower.includes('sent')) return 'sent';
    if (labelLower.includes('delivered')) return 'delivered';
    if (labelLower.includes('read')) return 'read';
    return 'default';
}

// Function to generate AI analysis
async function generateAnalysis() {
    const deliveryMetrics = document.getElementById('deliveryMetrics');
    const impactAnalysis = document.getElementById('impactAnalysis');
    const emailContent = document.getElementById('emailContent');
    const emailSubject = document.getElementById('emailSubject');
    const emailTo = document.getElementById('emailTo');

    if (!deliveryMetrics || !emailContent || !emailSubject || !emailTo) {
        console.error('Required elements not found');
        return;
    }

    deliveryMetrics.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="spinner-border text-primary spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            Generating analysis...
        </div>
    `;

    try {
        // TODO: Implement actual API call to Ollama or other analysis service
        setTimeout(() => {
            deliveryMetrics.innerHTML = `
                <div class="mb-3">
                    <strong>Delivery Information:</strong><br>
                    • Sent to: ${emailTo.textContent}<br>
                    • Status: Delivered<br>
                    • Delivery Time: Immediate
                </div>
            `;

            if (impactAnalysis) {
                impactAnalysis.innerHTML = `
                    <div class="mb-3">
                        <strong>Email Statistics:</strong><br>
                        • Length: ${emailContent.textContent.length} characters<br>
                        • Subject Length: ${emailSubject.textContent.length} characters<br>
                        • Recipients: ${emailTo.textContent.split(',').length}
                    </div>
                `;
            }
        }, 1500);
    } catch (error) {
        deliveryMetrics.innerHTML = `
            <div class="alert alert-danger mb-0">
                <i class="fas fa-exclamation-circle me-2"></i>
                Error generating analysis: ${error.message}
            </div>
        `;
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

// Initialize event listeners
document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, initializing...');
    loadEmailDetails();
    
    // Add event listener for the generate analysis button
    const generateAnalysisBtn = document.getElementById('generateAnalysisBtn');
    if (generateAnalysisBtn) {
        generateAnalysisBtn.addEventListener('click', generateAnalysis);
    }

    // Update back button href to include the page number
    const backButton = document.querySelector('.back-button');
    if (backButton) {
        const page = getUrlParameter('page') || '1';
        backButton.href = `sent_email.html?page=${page}`;
    }
});

// Function to load and display email details
async function loadSentEmailDetails() {
    console.log('Loading sent email details...');
    
    // Hide any previous error messages
    const alertContainer = document.getElementById('alertContainer');
    if (alertContainer) {
        alertContainer.innerHTML = '';
    }
    
    // Show loading state
    const contentContainer = document.getElementById('emailContent');
    if (contentContainer) {
        contentContainer.innerHTML = '<div class="text-center p-4"><i class="fas fa-spinner fa-spin fa-2x"></i><p class="mt-2">Loading email details...</p></div>';
    }
    
    try {
        // Get email ID from URL path
        const emailId = getEmailIdFromPath();
        if (!emailId) {
            throw new Error('No email ID found in URL');
        }
        
        // Construct API URL
        const apiUrl = `/api/emails/${encodeURIComponent(emailId)}/`;
        console.log('Fetching from API:', apiUrl);
        
        // Fetch email details
        const response = await fetch(apiUrl);
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`Failed to load email (HTTP ${response.status})`);
        }
        
        const data = await response.json();
        console.log('Received data:', data);
        
        if (!data.email) {
            throw new Error('No email data received');
        }
        
        // Update email details in DOM
        const email = data.email;
        
        // Update subject
        document.title = `${email.subject || 'Sent Email'} - Email Analytics`;
        const subjectElement = document.querySelector('.email-detail-header h2');
        if (subjectElement) {
            subjectElement.textContent = email.subject || 'No Subject';
        }
        
        // Update metadata
        const metadataDiv = document.querySelector('.email-metadata');
        if (metadataDiv) {
            metadataDiv.innerHTML = `
                <p><strong>From:</strong> ${escapeHtml(email.sender)}</p>
                <p><strong>To:</strong> ${escapeHtml(email.recipients || 'No recipients')}</p>
                <p><strong>Date:</strong> ${escapeHtml(formatDetailDate(email.date))}</p>
                ${email.has_attachments ? '<p><strong>Attachments:</strong> Yes</p>' : ''}
            `;
        }
        
        // Update email body
        const bodyDiv = document.querySelector('.email-body');
        if (bodyDiv) {
            bodyDiv.innerHTML = email.body || email.snippet || 'No content available';
        }
        
        // Handle attachments if present
        if (email.has_attachments && email.attachments) {
            const attachmentsContainer = document.createElement('div');
            attachmentsContainer.className = 'email-attachments mt-3';
            attachmentsContainer.innerHTML = `
                <h6><i class="fas fa-paperclip"></i> Attachments</h6>
                ${email.attachments.map(attachment => `
                    <div class="attachment-item">
                        <i class="fas fa-file"></i>
                        <span>${escapeHtml(attachment)}</span>
                    </div>
                `).join('')}
            `;
            bodyDiv.appendChild(attachmentsContainer);
        }
        
    } catch (error) {
        console.error('Error loading sent email:', error);
        showError(`Failed to load email details: ${error.message}`);
        
        // Show error in content area
        if (contentContainer) {
            contentContainer.innerHTML = `
                <div class="alert alert-danger m-3">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    ${escapeHtml(error.message)}
                </div>
            `;
        }
    }
}

// Load email details when page is ready
document.addEventListener('DOMContentLoaded', loadSentEmailDetails);
