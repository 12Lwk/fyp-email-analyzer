// Global variables
let currentEmails = [];
let currentPage = 1;
let pageSize = 10;
let filteredEmails = [];
let allEmails = [];

// Function to load profile picture from localStorage
function loadProfilePicture() {
    const profileImage = document.getElementById('sidebarUserAvatar');
    const savedImage = localStorage.getItem('profileImage');
    
    if (profileImage && savedImage) {
        profileImage.src = savedImage;
    }
}

// Function to escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Function to format date
function formatDate(dateStr) {
    if (!dateStr) return { shortDate: '', fullDate: '' };
    const date = new Date(dateStr);
    
    // Short date format (e.g., "Apr 2")
    const shortDate = date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
    });
    
    // Full date format for tooltip (e.g., "Tuesday, April 2, 2024 7:34 PM")
    const fullDate = date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        hour12: true
    });
    
    return { shortDate, fullDate };
}

// Function to get draft status
function getDraftStatus(draft) {
    if (!draft.subject && !draft.content) return 'incomplete';
    if (!draft.recipients || draft.recipients.length === 0) return 'incomplete';
    return 'ready';
}

// Function to update pagination controls
function updatePaginationControls() {
    const totalPages = Math.ceil(filteredEmails.length / pageSize);
    const prevButton = document.querySelector('.prev-page');
    const nextButton = document.querySelector('.next-page');
    const pageInfo = document.querySelector('.page-info');
    const emailCount = document.querySelector('.email-count');

    if (prevButton) {
        prevButton.disabled = currentPage === 1;
    }

    if (nextButton) {
        nextButton.disabled = currentPage >= totalPages;
    }

    if (pageInfo) {
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    }

    if (emailCount) {
        emailCount.textContent = `${filteredEmails.length} draft${filteredEmails.length !== 1 ? 's' : ''}`;
    }
}

// Function to handle page changes
function changePage(newPage) {
    currentPage = newPage;
    displayEmails();
    // Update URL with new page number
    const url = new URL(window.location.href);
    url.searchParams.set('page', currentPage);
    window.history.pushState({}, '', url);
}

// Search emails function
function searchEmails(query) {
    console.log('Searching drafts with query:', query);
    currentPage = 1; // Reset to first page when searching
    
    if (!query) {
        filteredEmails = [...currentEmails];
    } else {
        const searchQuery = query.toLowerCase();
        filteredEmails = currentEmails.filter(email => {
            return (
                (email.subject && email.subject.toLowerCase().includes(searchQuery)) ||
                (email.recipients && email.recipients.toLowerCase().includes(searchQuery)) ||
                (email.content && email.content.toLowerCase().includes(searchQuery))
            );
        });
    }

    displayEmails();
    updateEmailCount(filteredEmails.length);
}

// Toggle label column visibility
function toggleLabels() {
    const labelCells = document.querySelectorAll('.label-cell');
    const labelColumn = document.querySelector('.label-column');
    const button = document.querySelector('.toggle-labels-btn');

    labelCells.forEach(cell => {
        cell.style.display = cell.style.display === 'none' ? '' : 'none';
    });
    
    if (labelColumn) {
        labelColumn.style.display = labelColumn.style.display === 'none' ? '' : 'none';
    }

    if (button) {
        const isHidden = labelColumn && labelColumn.style.display === 'none';
        button.innerHTML = isHidden ? 
            '<i class="fas fa-tags"></i> Show Labels' : 
            '<i class="fas fa-tags"></i> Hide Labels';
    }
}

// Function to display emails
function displayEmails() {
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    const emailsToShow = filteredEmails.slice(start, end);
    const tableBody = document.getElementById('emailTableBody');
    
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    if (emailsToShow.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td colspan="7" class="text-center">No drafts found</td>';
        tableBody.appendChild(tr);
        return;
    }

    emailsToShow.forEach(email => {
        const row = createEmailRow(email);
        tableBody.appendChild(row);
    });

    updatePaginationControls();
}

// Function to create email row
function createEmailRow(email) {
    const row = document.createElement('tr');
    const status = getDraftStatus(email);
    row.className = `email-row ${status === 'incomplete' ? 'incomplete' : ''}`;
    row.dataset.emailId = email.id;
    row.style.cursor = 'pointer';
    
    const { shortDate, fullDate } = formatDate(email.lastModified);
    
    row.innerHTML = `
        <td class="align-middle">
            <input type="checkbox" class="form-check-input" data-email-id="${email.id}">
        </td>
        <td class="star-col align-middle">
            <i class="fas fa-star ${email.star ? 'starred' : ''}"></i>
        </td>
        <td class="email-recipients align-middle">${escapeHtml(email.recipients || '')}</td>
        <td class="email-subject align-middle">${escapeHtml(email.subject || '(No subject)')}</td>
        <td class="email-content align-middle text-truncate">${escapeHtml(email.content || '')}</td>
        <td class="email-date align-middle" data-bs-toggle="tooltip" title="${fullDate}">
            ${shortDate}
        </td>
        <td class="label-cell align-middle">
            <span class="email-label label-${status}">${status.toUpperCase()}</span>
        </td>
    `;

    // Add event listeners
    const checkbox = row.querySelector('input[type="checkbox"]');
    checkbox.addEventListener('change', () => handleEmailSelection(checkbox));

    const star = row.querySelector('.fa-star');
    star.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleStar(email.id, star);
    });

    row.addEventListener('click', () => {
        editDraft(email.id);
    });

    return row;
}

// Function to handle email selection
function handleEmailSelection(checkbox) {
    const emailId = checkbox.dataset.emailId;
    console.log(`Email ${emailId} ${checkbox.checked ? 'selected' : 'deselected'}`);
    updateActionButtonsState();
}

// Function to update action buttons state
function updateActionButtonsState() {
    const checkedEmails = document.querySelectorAll('input[type="checkbox"]:checked').length;
    const editBtn = document.querySelector('button[onclick="editSelected()"]');
    const sendBtn = document.querySelector('button[onclick="sendSelected()"]');
    const deleteBtn = document.querySelector('button[onclick="deleteSelected()"]');
    
    if (editBtn) {
        editBtn.disabled = checkedEmails !== 1;
    }
    if (sendBtn) {
        sendBtn.disabled = checkedEmails === 0;
    }
    if (deleteBtn) {
        deleteBtn.disabled = checkedEmails === 0;
    }
}

// Function to toggle star
function toggleStar(emailId, starElement) {
    starElement.classList.toggle('starred');
    console.log(`Star toggled for email ${emailId}`);
}

// Function to edit selected draft
async function editSelected() {
    const selectedEmail = document.querySelector('input[type="checkbox"]:checked');
    if (!selectedEmail) return;
    
    const emailId = selectedEmail.dataset.emailId;
    editDraft(emailId);
}

// Function to edit draft
async function editDraft(draftId) {
    try {
        const response = await fetch(`/api/drafts/${draftId}/`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to load draft');
        }
        
        const data = await response.json();
        
        if (data.status !== 'success') {
            throw new Error(data.message || 'Failed to load draft');
        }
        
        const draft = data.data;
        
        // Redirect to compose page with draft data
        window.location.href = `/compose/?draft_id=${draft.id}&subject=${encodeURIComponent(draft.subject || '')}&recipients=${encodeURIComponent(draft.recipients || '')}&content=${encodeURIComponent(draft.snippet || '')}`;
        
    } catch (error) {
        console.error('Error loading draft:', error);
        showError(`Error loading draft: ${error.message}`);
    }
}

// Function to send selected drafts
async function sendSelected() {
    const selectedEmails = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
        .map(checkbox => checkbox.dataset.emailId);
    
    if (selectedEmails.length === 0) {
        showError('No drafts selected');
        return;
    }
    
    if (!confirm(`Send ${selectedEmails.length} selected draft(s)?`)) {
        return;
    }
    
    try {
        for (const emailId of selectedEmails) {
            // First, get the draft details
            const response = await fetch(`/api/drafts/${emailId}/`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to load draft');
            }
            
            const data = await response.json();
            
            if (data.status !== 'success') {
                throw new Error(data.message || 'Failed to load draft');
            }
            
            const draft = data.data;
            
            // Check if draft has required fields
            if (!draft.recipients || !draft.subject) {
                showError(`Draft is incomplete. Please edit it first.`);
                continue;
            }
            
            // Send the email
            const sendResponse = await fetch('/api/emails/send/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    recipients: draft.recipients,
                    subject: draft.subject,
                    body: draft.snippet || ''
                })
            });
            
            if (!sendResponse.ok) {
                const errorData = await sendResponse.json();
                throw new Error(errorData.message || 'Failed to send email');
            }
            
            const sendData = await sendResponse.json();
            
            if (sendData.status !== 'success') {
                throw new Error(sendData.message || 'Failed to send email');
            }
            
            // Delete the draft after sending
            await fetch(`/api/drafts/delete/${emailId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            });
        }
        
        // Refresh emails after sending
        await refreshEmails();
        
        // Show success message
        const messageBox = document.createElement('div');
        messageBox.className = 'alert alert-success';
        messageBox.textContent = `Successfully sent ${selectedEmails.length} draft(s)`;
        document.querySelector('.email-container').prepend(messageBox);
        
        // Remove message after 3 seconds
        setTimeout(() => {
            messageBox.remove();
        }, 3000);
        
    } catch (error) {
        console.error('Error sending drafts:', error);
        showError(`Error sending drafts: ${error.message}`);
    }
}

// Function to delete selected drafts
async function deleteSelected() {
    const selectedEmails = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
        .map(checkbox => checkbox.dataset.emailId);
    
    if (selectedEmails.length === 0) {
        showError('No drafts selected');
        return;
    }
    
    if (!confirm(`Delete ${selectedEmails.length} selected draft(s)? This action cannot be undone.`)) {
        return;
    }
    
    try {
        for (const emailId of selectedEmails) {
            const response = await fetch(`/api/drafts/delete/${emailId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to delete draft');
            }
            
            const data = await response.json();
            
            if (data.status !== 'success') {
                throw new Error(data.message || 'Failed to delete draft');
            }
        }
        
        // Refresh emails after deleting
        await refreshEmails();
        
        // Show success message
        const messageBox = document.createElement('div');
        messageBox.className = 'alert alert-success';
        messageBox.textContent = `Successfully deleted ${selectedEmails.length} draft(s)`;
        document.querySelector('.email-container').prepend(messageBox);
        
        // Remove message after 3 seconds
        setTimeout(() => {
            messageBox.remove();
        }, 3000);
        
    } catch (error) {
        console.error('Error deleting drafts:', error);
        showError(`Error deleting drafts: ${error.message}`);
    }
}

// Function to refresh emails
async function refreshEmails() {
    const searchInput = document.querySelector('#searchInput');
    const searchQuery = searchInput ? searchInput.value : '';
    
    await loadEmails(searchQuery);
}

// Function to load emails
async function loadEmails(searchQuery = '') {
    try {
        // Show loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'text-center my-4';
        loadingIndicator.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        
        const emailContainer = document.querySelector('.email-container');
        if (emailContainer) {
            emailContainer.innerHTML = '';
            emailContainer.appendChild(loadingIndicator);
        }
        
        // Build URL with query parameters
        const url = new URL('/api/drafts/', window.location.origin);
        url.searchParams.set('page', currentPage);
        url.searchParams.set('per_page', pageSize);
        
        if (searchQuery) {
            url.searchParams.set('search', searchQuery);
        }
        
        // Fetch drafts
        const response = await fetch(url);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to load drafts');
        }
        
        const data = await response.json();
        
        if (data.status !== 'success') {
            throw new Error(data.message || 'Failed to load drafts');
        }
        
        // Remove loading indicator
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
        
        // Process drafts
        currentEmails = data.data.drafts || [];
        filteredEmails = [...currentEmails];
        
        // Update pagination
        if (data.data.pagination) {
            const pagination = data.data.pagination;
            currentPage = pagination.current_page;
            
            // Update URL with current page
            const pageUrl = new URL(window.location.href);
            pageUrl.searchParams.set('page', currentPage);
            window.history.replaceState({}, '', pageUrl);
        }
        
        // Display emails
        displayEmails();
        
        // Update email count
        updateEmailCount(filteredEmails.length);
        
    } catch (error) {
        console.error('Error loading drafts:', error);
        showError(`Error loading drafts: ${error.message}`);
    }
}

// Function to get CSRF token
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    
    return cookieValue || '';
}

// Function to show error
function showError(message) {
    // Remove any existing error messages
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Create error message
    const errorMessage = document.createElement('div');
    errorMessage.className = 'alert alert-danger error-message';
    errorMessage.textContent = message;
    
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'btn-close';
    closeButton.setAttribute('data-bs-dismiss', 'alert');
    closeButton.setAttribute('aria-label', 'Close');
    errorMessage.appendChild(closeButton);
    
    // Add to page
    document.querySelector('.email-container').prepend(errorMessage);
    
    // Remove after 5 seconds
    setTimeout(() => {
        errorMessage.remove();
    }, 5000);
}

// Function to update email count
function updateEmailCount(count) {
    const emailCount = document.querySelector('.email-count');
    if (emailCount) {
        emailCount.textContent = `${count} draft${count !== 1 ? 's' : ''}`;
    }
}

// Initialize event listeners
document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, initializing...');
    
    // Load profile picture
    loadProfilePicture();
    
    // Initialize search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchEmails(e.target.value);
        });
    }

    // Initialize toggle labels button
    const toggleLabelsBtn = document.querySelector('.toggle-labels-btn');
    if (toggleLabelsBtn) {
        toggleLabelsBtn.addEventListener('click', toggleLabels);
    }

    // Initialize select all checkbox
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', () => {
            const checkboxes = document.querySelectorAll('input[type="checkbox"][data-email-id]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;
            });
            updateActionButtonsState();
        });
    }

    // Initialize pagination
    initializePagination();

    // Load initial emails
    loadEmails();
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize delete selected button
    const deleteSelectedBtn = document.querySelector('button[onclick="deleteSelected()"]');
    if (deleteSelectedBtn) {
        deleteSelectedBtn.disabled = true;
    }
    
    // Initialize edit selected button
    const editSelectedBtn = document.querySelector('button[onclick="editSelected()"]');
    if (editSelectedBtn) {
        editSelectedBtn.disabled = true;
    }
    
    // Initialize send selected button
    const sendSelectedBtn = document.querySelector('button[onclick="sendSelected()"]');
    if (sendSelectedBtn) {
        sendSelectedBtn.disabled = true;
    }
});

function initializePagination() {
    const prevButton = document.querySelector('.prev-page');
    const nextButton = document.querySelector('.next-page');
    const pageSizeSelect = document.querySelector('.page-size');

    if (prevButton) {
        prevButton.addEventListener('click', () => {
            if (currentPage > 1) {
                changePage(currentPage - 1);
            }
        });
    }

    if (nextButton) {
        nextButton.addEventListener('click', () => {
            const totalPages = Math.ceil(filteredEmails.length / pageSize);
            if (currentPage < totalPages) {
                changePage(currentPage + 1);
            }
        });
    }

    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', (e) => {
            pageSize = parseInt(e.target.value);
            currentPage = 1;
            displayEmails();
            updatePaginationControls();
        });
    }
}


