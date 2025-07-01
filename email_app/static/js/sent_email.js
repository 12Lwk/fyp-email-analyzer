// Global variables
let currentEmails = [];
let filteredEmails = [];
let currentPage = 1;
let pageSize = 10;
let labelsVisible = true;
let totalItems = 0;

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
        
        // Get URL parameters (page, per_page)
        const urlParams = new URLSearchParams(window.location.search);
        const pageParam = parseInt(urlParams.get('page')) || 1;
        const perPageParam = parseInt(urlParams.get('per_page')) || pageSize;
        
        // Construct API URL with proper pagination parameters
        const apiUrl = new URL('/api/emails/view/', window.location.origin);
        apiUrl.searchParams.set('folder', 'sent');
        apiUrl.searchParams.set('page', pageParam.toString());
        apiUrl.searchParams.set('per_page', perPageParam.toString());
        
        console.log('Fetching emails from:', apiUrl.toString());
        
        // Make API request specifically for sent emails with pagination
        const response = await fetch(apiUrl.toString(), {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'include' // Include credentials for session persistence
        });
        
        if (!response.ok) {
            console.error('HTTP error:', response.status, response.statusText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('API Response:', data); // Log full response
        
        let emailList = [];
        
        // Handle different API response formats
        if (data.status === 'success') {
            if (data.data && Array.isArray(data.data.emails)) {
                // New format with nested data structure
                emailList = data.data.emails;
                
                // Update pagination information if available
                if (data.data.pagination) {
                    currentPage = data.data.pagination.current_page;
                    pageSize = data.data.pagination.per_page;
                    totalItems = data.data.pagination.total_items;
                }
                
                console.log('Using nested data format, found', emailList.length, 'emails');
            } else if (Array.isArray(data.emails)) {
                // Old format with direct emails array
                emailList = data.emails;
                console.log('Using direct array format, found', emailList.length, 'emails');
            }
        } else {
            console.error('API returned error status:', data.message || 'Unknown error');
        }
        
        // Store processed emails
        currentEmails = emailList;
        filteredEmails = [...currentEmails];
        
        console.log(`Loaded ${currentEmails.length} sent emails for current user`);
        
        // Hide loading placeholder - add null check
        const loadingPlaceholder = document.querySelector('.loading-placeholder');
        if (loadingPlaceholder) {
            loadingPlaceholder.style.display = 'none';
        }
        
        // Show/hide no emails message - add null check
        const noEmailsMessage = document.getElementById('noEmailsMessage');
        if (noEmailsMessage) {
            noEmailsMessage.style.display = currentEmails.length === 0 ? 'table-row' : 'none';
        }
        
        displayEmails();
        updatePaginationControls();
        updateEmailCounts();
    } catch (error) {
        console.error('Error loading emails:', error);
        showError('Failed to load emails. Please try again. Error: ' + error.message);
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
    // Show loading again using our improved showLoading function
    showLoading(true);
    // Load emails
    loadEmails();
}

// Show loading state
function showLoading(isLoading) {
    const loadingRow = document.querySelector('.loading-placeholder');
    if (loadingRow) {
        loadingRow.style.display = isLoading ? 'table-row' : 'none';
    } else if (isLoading) {
        // If loading row doesn't exist, try to create one in the table body
        const tbody = document.getElementById('emailTableBody');
        if (tbody) {
            // Check if we already have a loading row
            if (!tbody.querySelector('.loading-placeholder')) {
                const newLoadingRow = document.createElement('tr');
                newLoadingRow.className = 'loading-placeholder';
                newLoadingRow.innerHTML = `
                    <td colspan="7" class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-2">Loading emails...</p>
                    </td>
                `;
                tbody.appendChild(newLoadingRow);
            }
        }
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
    const totalPages = Math.ceil(totalItems / pageSize);
    
    // Update email count
    const emailCountElement = document.getElementById('emailCount');
    if (emailCountElement) {
        emailCountElement.textContent = `${totalItems} emails`;
    }
    
    // Update page info
    const pageInfoElement = document.getElementById('pageInfo');
    if (pageInfoElement) {
        pageInfoElement.textContent = `Page ${currentPage} of ${totalPages || 1}`;
    }
    
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

// Function to safely create an email row with error handling
function createEmailRow(email) {
    if (!email) {
        console.warn('Cannot create row for null/undefined email');
        return null;
    }
    
    try {
        const row = document.createElement('tr');
        row.className = 'email-row';
        row.dataset.emailId = email.id || '';
        
        // Parse recipients if it's a JSON string
        let recipients = '';
        try {
            if (typeof email.recipients === 'string' && email.recipients.startsWith('[')) {
                const recipientsObj = JSON.parse(email.recipients);
                recipients = recipientsObj.map(r => r.email || r).join(', ');
            } else {
                recipients = email.recipients || '';
            }
        } catch (e) {
            console.error('Error parsing recipients:', e);
            recipients = email.recipients || 'No recipient';
        }
        
        // Limit recipients length if too long
        if (recipients.length > 30) {
            recipients = recipients.substring(0, 30) + '...';
        }
        
        // Create checkbox cell
        const checkboxCell = document.createElement('td');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'form-check-input email-checkbox';
        checkboxCell.appendChild(checkbox);
        
        // Create icon cell
        const iconCell = document.createElement('td');
        iconCell.className = 'text-center';
        const icon = document.createElement('i');
        icon.className = 'fas fa-paper-plane text-primary';
        iconCell.appendChild(icon);
        
        // Create recipient cell
        const recipientCell = document.createElement('td');
        // Make recipient text bold with proper ellipsis
        recipientCell.innerHTML = `<strong title="${escapeHtml(recipients)}">${escapeHtml(recipients || 'No recipient')}</strong>`;
        
        // Create subject cell
        const subjectCell = document.createElement('td');
        // Limit subject length if too long
        let subject = email.subject || 'No subject';
        if (subject.length > 40) {
            subject = subject.substring(0, 40) + '...';
        }
        // Make subject text bold with proper ellipsis
        subjectCell.innerHTML = `<strong title="${escapeHtml(email.subject || 'No subject')}">${escapeHtml(subject)}</strong>`;
        
        // Create snippet cell with proper HTML cleanup
        const snippetCell = document.createElement('td');
        snippetCell.className = 'email-snippet-container'; // Updated class name for container
        
        // Create a nested span for the actual snippet text
        const snippetSpan = document.createElement('span');
        snippetSpan.className = 'email-snippet';
        
        // Clean up snippet HTML similar to inbox_email.js
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = email.snippet || ''; // Set HTML content
        
        // Remove style and script tags before extracting text
        tempDiv.querySelectorAll('style, script').forEach(el => el.remove());
        
        // First, clean the HTML content
        let plainTextSnippet = tempDiv.textContent || tempDiv.innerText || ''; // Extract plain text
        
        // Remove HTML comments
        plainTextSnippet = plainTextSnippet.replace(/<!--[\s\S]*?-->/g, '');
        
        // Clean up whitespace and normalize
        plainTextSnippet = plainTextSnippet.replace(/\s+/g, ' ').trim(); // Collapse multiple spaces/newlines
        
        // Replace special HTML entities
        plainTextSnippet = plainTextSnippet.replace(/&nbsp;/g, ' ');
        plainTextSnippet = plainTextSnippet.replace(/&lt;/g, '<');
        plainTextSnippet = plainTextSnippet.replace(/&gt;/g, '>');
        plainTextSnippet = plainTextSnippet.replace(/&amp;/g, '&');
        
        // Remove DOCTYPE and HTML tag declarations
        plainTextSnippet = plainTextSnippet.replace(/<!DOCTYPE[^>]*>/i, '');
        plainTextSnippet = plainTextSnippet.replace(/<html[^>]*>/i, '');
        plainTextSnippet = plainTextSnippet.replace(/<\/html>/i, '');
        plainTextSnippet = plainTextSnippet.replace(/<head[^>]*>[\s\S]*?<\/head>/i, '');
        
        // Truncate the plain text snippet
        const maxLength = 80; // Max characters for snippet display
        if (plainTextSnippet.length > maxLength) {
            plainTextSnippet = plainTextSnippet.substring(0, maxLength) + '...';
        }
        
        snippetSpan.textContent = plainTextSnippet; // Set the processed plain text
        // Set tooltip to the slightly cleaned text (without style/script)
        snippetSpan.title = (tempDiv.textContent || tempDiv.innerText || '').replace(/\s+/g, ' ').trim();
        
        // Append the snippet span to the container cell
        snippetCell.appendChild(snippetSpan);
        
        // Create date cell
        const dateCell = document.createElement('td');
        dateCell.className = 'email-date';
        dateCell.textContent = formatDate(email.date) || 'Invalid Date';
        
        // Create status cell
        const statusCell = document.createElement('td');
        statusCell.className = `label-column ${!labelsVisible ? 'd-none' : ''}`;
        const statusSpan = document.createElement('span');
        statusSpan.className = 'email-label label-sent';
        statusSpan.textContent = 'sent';
        statusCell.appendChild(statusSpan);
        
        // Append all cells to the row
        row.appendChild(checkboxCell);
        row.appendChild(iconCell);
        row.appendChild(recipientCell);
        row.appendChild(subjectCell);
        row.appendChild(snippetCell);
        row.appendChild(dateCell);
        row.appendChild(statusCell);
        
        // Add click event to view email
        row.addEventListener('click', (e) => {
            // Only handle if not clicking checkbox
            if (!e.target.closest('.email-checkbox')) {
                e.preventDefault();
                e.stopPropagation();
                viewEmailDetail(email.id);
            }
        });
        
        return row;
    } catch (error) {
        console.error('Error creating email row:', error, 'Email data:', email);
        return null;
    }
}

// Display emails
function displayEmails() {
    const tbody = document.getElementById('emailTableBody');
    if (!tbody) {
        console.error('Email table body not found');
        return;
    }

    // Clear existing rows
    tbody.innerHTML = '';
    
    console.log('Displaying emails:', currentEmails);

    // Check if currentEmails is valid
    if (!Array.isArray(currentEmails)) {
        console.error('CurrentEmails is not an array:', currentEmails);
        showError('Invalid email data format. Please refresh the page.');
        return;
    }

    // If no emails after filtering, show message
    if (currentEmails.length === 0) {
        const noEmailsRow = document.createElement('tr');
        noEmailsRow.id = 'noEmailsMessage';
        noEmailsRow.innerHTML = `
            <td colspan="7" class="text-center py-4">
                <div class="text-muted">
                    <i class="fas fa-inbox fa-3x mb-3"></i>
                    <p>No sent emails found in your account</p>
                    <p class="small text-muted">Try composing and sending an email first</p>
                    <button class="btn btn-primary mt-3" data-bs-toggle="modal" data-bs-target="#composeModal">
                        <i class="fas fa-plus me-2"></i>Compose New Email
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(noEmailsRow);
        return;
    }
    
    // Create document fragment for better performance
    const fragment = document.createDocumentFragment();
    
    // Create rows for emails
    currentEmails.forEach(email => {
        const row = createEmailRow(email);
        if (row) {
            fragment.appendChild(row);
        }
    });
    
    // Append all rows at once
    tbody.appendChild(fragment);
}

// Function to view email detail
async function viewEmailDetail(emailId) {
    if (!emailId) {
        console.error('No email ID provided for viewing details');
        return;
    }

    try {
        // Show loading state
        const loadingToast = showToast('Opening email...', 'info');
        
        // First verify the session is active
        const response = await fetch('/api/auth/check/', {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        });

        const authData = await response.json();
        console.log('Auth check response:', authData);
        
        // If Gmail session is active, proceed with navigation
        if (authData.status === 'success' && authData.is_gmail_authenticated) {
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
        } else {
            // If not authenticated, redirect to login
            window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
        }
        
    } catch (error) {
        console.error('Error navigating to email detail:', error);
        showError('Unable to open this email. Please try again.');
        // Hide loading state
        hideToast(loadingToast);
    }
}

// Helper function to show error message
function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    if (errorContainer) {
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
        setTimeout(() => {
            errorContainer.style.display = 'none';
        }, 5000);
    }
}

// Helper function to show toast message
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1050;';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    return toast;
}

// Helper function to hide toast
function hideToast(toast) {
    if (toast) {
        const bsToast = bootstrap.Toast.getInstance(toast);
        if (bsToast) {
            bsToast.hide();
        }
    }
}

// Toggle labels visibility
function toggleLabels() {
    labelsVisible = !labelsVisible;
    
    // Update all label columns
    const labelColumns = document.querySelectorAll('.label-column');
    const labelHeader = document.querySelector('th.label-column');
    
    // Update CSS classes
    labelColumns.forEach(column => {
        if (labelsVisible) {
            column.classList.remove('hidden');
        } else {
            column.classList.add('hidden');
        }
    });
    
    if (labelHeader) {
        if (labelsVisible) {
            labelHeader.classList.remove('hidden');
        } else {
            labelHeader.classList.add('hidden');
        }
    }
    
    // Update button text
    const toggleLabelsBtnText = document.getElementById('toggleLabelsBtnText');
    if (toggleLabelsBtnText) {
        toggleLabelsBtnText.textContent = labelsVisible ? 'Hide Labels' : 'Show Labels';
    }
    
    // Add visual feedback for button click
    const toggleLabelsBtn = document.getElementById('toggleLabelsBtn');
    if (toggleLabelsBtn) {
        toggleLabelsBtn.classList.add('btn-active-effect');
        setTimeout(() => {
            toggleLabelsBtn.classList.remove('btn-active-effect');
        }, 200);
    }
    
    // Save preference to localStorage
    localStorage.setItem('labelsVisible', labelsVisible);
}

// Initialize event listeners
document.addEventListener('DOMContentLoaded', () => {
    try {
        // Ensure all Status column cells have the label-column class
        const statusHeaderCell = document.querySelector('th:nth-child(7)');
        if (statusHeaderCell) {
            statusHeaderCell.classList.add('label-column');
            statusHeaderCell.textContent = 'Status'; // Ensure correct header text
        }
        
        // Load profile picture
        loadProfilePicture();
        
        // Load labels visibility preference
        const savedLabelsPref = localStorage.getItem('labelsVisible');
        if (savedLabelsPref !== null) {
            labelsVisible = savedLabelsPref === 'true';
            
            // Update UI to match saved preference
            if (!labelsVisible) {
                // Apply to both the header and data cells
                document.querySelectorAll('.label-column').forEach(col => {
                    col.classList.add('hidden');
                });
                
                // Update the button text
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
                const newSize = parseInt(e.target.value);
                if (!isNaN(newSize) && newSize !== pageSize) {
                    // Update URL with new page size
                    const url = new URL(window.location.href);
                    url.searchParams.set('per_page', newSize.toString());
                    url.searchParams.set('page', '1'); // Reset to first page
                    history.pushState(null, '', url.toString());
                    
                    // Update pageSize and reload
                    pageSize = newSize;
                    loadEmails();
                }
            });
        }

        // Set up pagination buttons
        const prevPageBtn = document.getElementById('prevPage');
        const nextPageBtn = document.getElementById('nextPage');
        
        if (prevPageBtn) {
            prevPageBtn.addEventListener('click', () => {
                if (currentPage > 1) {
                    navigateToPage(currentPage - 1);
                }
            });
        }

        if (nextPageBtn) {
            nextPageBtn.addEventListener('click', () => {
                const totalPages = Math.ceil(totalItems / pageSize);
                if (currentPage < totalPages) {
                    navigateToPage(currentPage + 1);
                }
            });
        }
        
        // Function to navigate to a specific page
        function navigateToPage(page) {
            try {
                // Update URL with new page number
                const url = new URL(window.location.href);
                url.searchParams.set('page', page.toString());
                url.searchParams.set('per_page', pageSize.toString());
                history.pushState(null, '', url.toString());
                
                // Load emails for the new page
                loadEmails();
            } catch (error) {
                console.error('Error navigating to page:', error);
                showError('Failed to navigate to page ' + page);
            }
        }
        
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

        // Initialize page size and current page from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const urlPageSize = parseInt(urlParams.get('per_page'));
        const urlPage = parseInt(urlParams.get('page'));
        
        if (!isNaN(urlPageSize) && urlPageSize > 0) {
            pageSize = urlPageSize;
            // Update the page size selector to match
            if (pageSizeSelect) {
                pageSizeSelect.value = pageSize.toString();
            }
        }
        
        if (!isNaN(urlPage) && urlPage > 0) {
            currentPage = urlPage;
        }

        // Load initial emails
        loadEmails();
    } catch (error) {
        console.error('Error initializing sent email page:', error);
        // Show error on page if possible
        const errorContainer = document.getElementById('errorAlert');
        if (errorContainer) {
            errorContainer.style.display = 'block';
            const errorMessage = document.getElementById('errorMessage');
            if (errorMessage) {
                errorMessage.textContent = 'Failed to initialize page: ' + error.message;
            }
        }
    }
});

// Add this at the end of your file
// This gives another chance to load the profile picture after everything else
window.addEventListener('load', function() {
    console.log("Window fully loaded, trying to load profile picture again");
    loadProfilePicture();
});