// Global variables
let currentEmails = [];
let filteredEmails = [];
let currentPage = 1;
let pageSize = 10;
let labelsVisible = true;

// Function to load profile picture from localStorage
function loadProfilePicture() {
    console.log("Loading profile picture in sent_email.js...");
    
    const profileImage = document.getElementById('sidebarUserAvatar');
    console.log("Profile image element found:", profileImage);
    
    const savedImage = localStorage.getItem('profileImage');
    console.log("Saved image from localStorage:", savedImage);
    
    if (profileImage && savedImage) {
        console.log("Setting profile image src to:", savedImage);
        profileImage.src = savedImage;
    } else {
        console.log("Could not set profile image: Element or saved image missing");
        
        // If we have the element but no saved image, let's add a placeholder
        if (profileImage && !savedImage) {
            console.log("No profile image in localStorage, using default");
            // Keep using the default image from the template
        }
    }
}

// Helper function to escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Search function
function searchEmails(query) {
    console.log('Searching emails with query:', query);
    currentPage = 1; // Reset to first page when searching
    
    if (!query) {
        filteredEmails = [...currentEmails];
    } else {
        query = query.toLowerCase();
        filteredEmails = currentEmails.filter(email => {
            return (
                (email.recipients && email.recipients.toLowerCase().includes(query)) ||
                (email.subject && email.subject.toLowerCase().includes(query)) ||
                (email.snippet && email.snippet.toLowerCase().includes(query))
            );
        });
    }
    
    displayEmails();
    updatePaginationControls();
}

// Load emails from the server
async function loadEmails() {
    try {
        console.log('Fetching sent emails...');
        
        // Hide any previous error
        hideError();
        
        // Show loading state
        showLoading(true);
        
        const response = await fetch('/api/emails/view/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && Array.isArray(data.emails)) {
            // Filter for sent emails only (SENT folder)
            currentEmails = data.emails.filter(email => email.folder === 'SENT');
            filteredEmails = [...currentEmails];
            
            console.log(`Loaded ${currentEmails.length} sent emails for current user`);
            
            // Hide loading placeholder
            document.querySelector('.loading-placeholder').style.display = 'none';
            
            // Show/hide no emails message
            const noEmailsMessage = document.getElementById('noEmailsMessage');
            if (noEmailsMessage) {
                noEmailsMessage.style.display = currentEmails.length === 0 ? 'table-row' : 'none';
            }
            
            displayEmails();
            updatePaginationControls();
            updateEmailCounts();
        } else {
            throw new Error('Invalid data format received from server');
        }
    } catch (error) {
        console.error('Error loading emails:', error);
        showError('Failed to load emails. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Function to update email counts in sidebar
function updateEmailCounts() {
    const sentCount = document.getElementById('sentCount');
    if (sentCount) {
        sentCount.textContent = currentEmails.length;
    }
}

// Function to refresh emails
function refreshEmails() {
    // Show loading again
    document.querySelector('.loading-placeholder').style.display = 'table-row';
    loadEmails();
}

// Show loading state
function showLoading(isLoading) {
    const loadingRow = document.querySelector('.loading-placeholder');
    if (loadingRow) {
        loadingRow.style.display = isLoading ? 'table-row' : 'none';
    }
}

// Show error message
function showError(message) {
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');
    
    if (errorAlert && errorMessage) {
        errorMessage.textContent = message;
        errorAlert.style.display = 'block';
    } else {
        // Fallback to table error message if alert elements don't exist
        const tbody = document.getElementById('emailTableBody');
        if (tbody) {
            const errorRow = document.createElement('tr');
            errorRow.id = 'errorRow';
            errorRow.innerHTML = `
                <td colspan="7" class="text-center py-4">
                    <div class="alert alert-danger m-3">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        ${message}
                    </div>
                </td>
            `;
            tbody.innerHTML = '';
            tbody.appendChild(errorRow);
        }
    }
}

// Hide error message
function hideError() {
    const errorAlert = document.getElementById('errorAlert');
    if (errorAlert) {
        errorAlert.style.display = 'none';
    }
    
    const errorRow = document.getElementById('errorRow');
    if (errorRow) {
        errorRow.remove();
    }
}

// Update pagination controls
function updatePaginationControls() {
    const totalPages = Math.ceil(filteredEmails.length / pageSize);
    
    // Update email count
    document.getElementById('emailCount').textContent = `${filteredEmails.length} emails`;
    
    // Update page info
    document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages || 1}`;
    
    // Update button states
    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');
    
    if (prevButton) {
        prevButton.disabled = currentPage <= 1;
    }
    if (nextButton) {
        nextButton.disabled = currentPage >= totalPages || totalPages === 0;
    }
}

// Helper function to format date
function formatDate(dateStr) {
    if (!dateStr) return 'Invalid Date';
    const date = new Date(dateStr);
    if (isNaN(date)) return 'Invalid Date';
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
    });
}

// Display emails
function displayEmails() {
    const tbody = document.getElementById('emailTableBody');
    if (!tbody) return;
    
    // Get the loading and no emails rows
    const loadingRow = document.querySelector('.loading-placeholder');
    const noEmailsMessage = document.getElementById('noEmailsMessage');
    
    // Calculate pagination
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    const emailsToShow = filteredEmails.slice(start, end);
    
    // Clear existing email rows but keep loading & no emails message rows
    const existingEmailRows = tbody.querySelectorAll('tr:not(.loading-placeholder):not(#noEmailsMessage)');
    existingEmailRows.forEach(row => row.remove());
    
    // Only process if we have emails to show
    if (emailsToShow.length === 0) {
        // Show no emails message if available
        if (noEmailsMessage) {
            noEmailsMessage.style.display = 'table-row';
        }
        return;
    } else if (noEmailsMessage) {
        noEmailsMessage.style.display = 'none';
    }
    
    // Create rows for emails
    emailsToShow.forEach(email => {
        const row = document.createElement('tr');
        row.className = 'email-row';
        row.dataset.emailId = email.id;
        
        // Create row HTML
        row.innerHTML = `
            <td>
                <input type="checkbox" class="form-check-input email-checkbox">
            </td>
            <td class="text-center">
                <i class="fas fa-paper-plane text-primary"></i>
            </td>
            <td>${escapeHtml(email.recipients || 'No recipient')}</td>
            <td>${escapeHtml(email.subject || 'No subject')}</td>
            <td class="email-snippet">${escapeHtml(email.snippet || '')}</td>
            <td class="email-date">${formatDate(email.date) || 'Invalid Date'}</td>
            <td class="label-column ${!labelsVisible ? 'd-none' : ''}">
                <span class="email-label label-sent">SENT</span>
            </td>
        `;
        
        // Add click event to view email
        row.addEventListener('click', (e) => {
            if (!e.target.closest('.email-checkbox')) {
                viewEmailDetail(email.id);
            }
        });
        
        // Append the new row
        tbody.appendChild(row);
    });
}

// Function to view email detail
function viewEmailDetail(emailId) {
    if (!emailId) {
        console.error('No email ID provided for viewing details');
        return;
    }

    try {
        // Sanitize the email ID
        const sanitizedEmailId = encodeURIComponent(emailId.trim());
        if (!sanitizedEmailId) {
            throw new Error('Invalid email ID');
        }

        // Construct the detail URL using Django's URL pattern
        const detailUrl = `/sent_email_detail/${sanitizedEmailId}/`;
        console.debug('Navigating to sent email detail:', detailUrl);
        
        // Navigate to the detail page
        window.location.href = detailUrl;
    } catch (error) {
        console.error('Error navigating to email detail:', error);
        // Show error message to user
        const errorContainer = document.getElementById('errorContainer');
        if (errorContainer) {
            errorContainer.textContent = 'Error viewing email details. Please try again.';
            errorContainer.style.display = 'block';
            setTimeout(() => {
                errorContainer.style.display = 'none';
            }, 5000);
        }
    }
}

// Toggle labels visibility
function toggleLabels() {
    labelsVisible = !labelsVisible;
    
    // Update all label columns
    const labelColumns = document.querySelectorAll('.label-column');
    labelColumns.forEach(column => {
        if (labelsVisible) {
            column.classList.remove('d-none');
        } else {
            column.classList.add('d-none');
        }
    });
    
    // Update button text
    const toggleLabelsBtnText = document.getElementById('toggleLabelsBtnText');
    if (toggleLabelsBtnText) {
        toggleLabelsBtnText.textContent = labelsVisible ? 'Hide Labels' : 'Show Labels';
    }
    
    // Save preference to localStorage
    localStorage.setItem('labelsVisible', labelsVisible);
}

// Initialize event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Load profile picture
    loadProfilePicture();
    
    // Load labels visibility preference
    const savedLabelsPref = localStorage.getItem('labelsVisible');
    if (savedLabelsPref !== null) {
        labelsVisible = savedLabelsPref === 'true';
        // Update UI to match saved preference
        if (!labelsVisible) {
            document.querySelectorAll('.label-column').forEach(col => {
                col.classList.add('d-none');
            });
            const toggleLabelsBtnText = document.getElementById('toggleLabelsBtnText');
            if (toggleLabelsBtnText) {
                toggleLabelsBtnText.textContent = 'Show Labels';
            }
        }
    }
    
    // Set up search functionality
    const emailSearch = document.getElementById('emailSearch');
    if (emailSearch) {
        emailSearch.addEventListener('input', (e) => {
            searchEmails(e.target.value);
        });
    }

    // Set up page size selector
    const pageSizeSelect = document.getElementById('pageSizeSelect');
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', (e) => {
            pageSize = parseInt(e.target.value);
            currentPage = 1;
            displayEmails();
            updatePaginationControls();
        });
    }

    // Set up pagination buttons
    document.getElementById('prevPage')?.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            displayEmails();
            updatePaginationControls();
        }
    });

    document.getElementById('nextPage')?.addEventListener('click', () => {
        const totalPages = Math.ceil(filteredEmails.length / pageSize);
        if (currentPage < totalPages) {
            currentPage++;
            displayEmails();
            updatePaginationControls();
        }
    });
    
    // Set up toggle labels button
    const toggleLabelsBtn = document.getElementById('toggleLabelsBtn');
    if (toggleLabelsBtn) {
        toggleLabelsBtn.addEventListener('click', toggleLabels);
    }
    
    // Set up select all checkbox
    const selectAllEmails = document.getElementById('selectAllEmails');
    if (selectAllEmails) {
        selectAllEmails.addEventListener('change', (e) => {
            const checkboxes = document.querySelectorAll('.email-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = e.target.checked;
            });
        });
    }

    // Load initial emails
    loadEmails();
});

// Add this at the end of your file
// This gives another chance to load the profile picture after everything else
window.addEventListener('load', function() {
    console.log("Window fully loaded, trying to load profile picture again");
    loadProfilePicture();
});