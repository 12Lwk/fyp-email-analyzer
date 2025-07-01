// Compose Email Modal Functionality
document.addEventListener('DOMContentLoaded', () => {
    const composeForm = document.getElementById('composeForm');
    const attachFileBtn = document.getElementById('attachFileBtn');
    const fileInput = document.getElementById('fileInput');
    const attachmentList = document.getElementById('attachmentList');
    const saveAsDraftBtn = document.getElementById('saveAsDraft');
    const composeModal = document.getElementById('composeModal');
    
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
    
    // Handle form submission
    if (composeForm) {
        composeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = {
                to: document.getElementById('emailTo').value,
                cc: document.getElementById('emailCc').value,
                bcc: document.getElementById('emailBcc').value,
                subject: document.getElementById('emailSubject').value,
                body: document.getElementById('emailBody').value,
                attachments: Array.from(fileInput.files).map(file => file.name)
            };

            try {
                const response = await sendEmail(formData);
                if (response.success) {
                    // Close modal and show success message
                    const modal = bootstrap.Modal.getInstance(document.getElementById('composeModal'));
                    modal.hide();
                    alert('Email sent successfully!');
                    composeForm.reset();
                    clearAttachments();
                } else {
                    alert('Failed to send email. Please try again.');
                }
            } catch (error) {
                console.error('Error sending email:', error);
                alert('An error occurred while sending the email.');
            }
        });
    }
    
    // Handle save as draft
    if (saveAsDraftBtn) {
        saveAsDraftBtn.addEventListener('click', async () => {
            const formData = {
                to: document.getElementById('emailTo').value,
                cc: document.getElementById('emailCc').value,
                bcc: document.getElementById('emailBcc').value,
                subject: document.getElementById('emailSubject').value,
                body: document.getElementById('emailBody').value,
                attachments: Array.from(fileInput.files).map(file => file.name)
            };

            try {
                const response = await saveAsDraft(formData);
                if (response.success) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('composeModal'));
                    modal.hide();
                    alert('Draft saved successfully!');
                    composeForm.reset();
                    clearAttachments();
                } else {
                    alert('Failed to save draft. Please try again.');
                }
            } catch (error) {
                console.error('Error saving draft:', error);
                alert('An error occurred while saving the draft.');
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

    // Function to send email
    async function sendEmail(formData) {
        try {
            console.log('Attempting to send email with data:', formData);
            
            // Use the Django endpoint
            const response = await fetch('/api/emails/send/', {  // Notice the trailing slash
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            // Handle the response
            try {
                const contentType = response.headers.get('content-type');
                
                // Check if response is JSON
                if (contentType && contentType.includes('application/json')) {
                    const data = await response.json();
                    
                    if (response.ok) {
                        console.log('Email sent successfully via Django API');
                        return { success: true, data };
                    } else {
                        console.error('Error response from server:', data);
                        return { 
                            success: false, 
                            error: data.message || 'Failed to send email'
                        };
                    }
                } else {
                    // Handle non-JSON response
                    const text = await response.text();
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

    // Helper function to get CSRF token
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

    // Function to save as draft
    async function saveAsDraft(formData) {
        try {
            // Try to save using Gmail API first
            const gmailResponse = await fetch('/api/gmail/draft', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            // If Gmail API call successful
            if (gmailResponse.ok) {
                const data = await gmailResponse.json();
                return { success: true, data, provider: 'gmail' };
            }
            
            // If not authenticated with Gmail or other error, fall back to original endpoint
            console.log('Gmail API unavailable, falling back to default endpoint');
            const fallbackResponse = await fetch('http://127.0.0.1:5000/api/emails/draft', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await fallbackResponse.json();
            return { success: fallbackResponse.ok, data, provider: 'default' };
        } catch (error) {
            console.error('Error saving draft:', error);
            return { success: false, error };
        }
    }
});

// Reset compose form
function resetComposeForm() {
    document.getElementById('composeForm').reset();
    document.getElementById('attachmentList').innerHTML = '';
    document.getElementById('fileInput').value = '';
}

// Show notification
function showNotification(message, type = 'info') {
    const notificationDiv = document.createElement('div');
    notificationDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    notificationDiv.style.zIndex = '9999';
    notificationDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(notificationDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        notificationDiv.remove();
    }, 5000);
} 