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
            throw new Error('Failed to fetch draft details');
        }
        
        const draft = await response.json();
        
        // Populate compose modal with draft data
        document.getElementById('draftId').value = draft.id;
        document.getElementById('emailTo').value = draft.recipients || '';
        document.getElementById('emailCc').value = draft.cc || '';
        document.getElementById('emailBcc').value = draft.bcc || '';
        document.getElementById('emailSubject').value = draft.subject || '';
        document.getElementById('emailBody').value = draft.content || '';
        
        // Update modal title
        document.getElementById('composeModalLabel').textContent = 'Edit Draft';
        
        // Show modal
        const composeModal = new bootstrap.Modal(document.getElementById('composeModal'));
        composeModal.show();
        
    } catch (error) {
        console.error('Error loading draft:', error);
        alert('Failed to load draft. Please try again.');
    }
}

// Function to send selected drafts
async function sendSelected() {
    const selectedEmails = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
        .map(checkbox => checkbox.dataset.emailId);
    
    if (selectedEmails.length === 0) return;
    
    try {
        const response = await fetch('/api/drafts/send/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ draftIds: selectedEmails })
        });
        
        if (response.ok) {
            // Refresh the email list
            await loadEmails();
            // Show success message
            alert('Selected drafts sent successfully');
        } else {
            throw new Error('Failed to send drafts');
        }
    } catch (error) {
        console.error('Error sending drafts:', error);
        alert('Failed to send drafts. Please try again.');
    }
}

// Function to delete selected drafts
async function deleteSelected() {
    const selectedEmails = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
        .map(checkbox => checkbox.dataset.emailId);
    
    if (selectedEmails.length === 0) return;
    
    if (!confirm('Are you sure you want to delete these drafts?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/drafts/delete/', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ draftIds: selectedEmails })
        });
        
        if (response.ok) {
            // Refresh the email list
            await loadEmails();
            // Show success message
            alert('Selected drafts deleted successfully');
        } else {
            throw new Error('Failed to delete drafts');
        }
    } catch (error) {
        console.error('Error deleting drafts:', error);
        alert('Failed to delete drafts. Please try again.');
    }
}

// Function to refresh emails
async function refreshEmails() {
    await loadEmails();
}

// Load emails from the server
async function loadEmails() {
    try {
        // Get page from URL or default to 1
        const urlParams = new URLSearchParams(window.location.search);
        currentPage = parseInt(urlParams.get('page')) || 1;
        
        console.log('Fetching drafts from server...');
        const response = await fetch('/api/emails/view/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Raw data from server:', data);
        
        if (data.status === 'success' && Array.isArray(data.emails)) {
            console.log('Total emails received:', data.emails.length);
            
            // Store all emails first
            allEmails = data.emails;
            
            // Filter for draft emails - show emails in DRAFTS folder
            currentEmails = allEmails.filter(email => {
                return email.folder === 'DRAFTS';
            });
            
            console.log('Filtered draft emails:', currentEmails.length);
            filteredEmails = [...currentEmails];
            
            // Update the display
            displayEmails();
            updateEmailCount(currentEmails.length);
        } else {
            console.error('Invalid data format or error:', data);
            showError('Error loading drafts. Invalid data format.');
        }
    } catch (error) {
        console.error('Error loading drafts:', error);
        showError('Failed to load drafts. Please try again.');
    }
}

// Function to show error message
function showError(message) {
    console.error('Error:', message);
    const tableBody = document.getElementById('emailTableBody');
    if (tableBody) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7">
                    <div class="alert alert-danger m-3">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        ${message}
                    </div>
                </td>
            </tr>
        `;
    }
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
    const searchInput = document.getElementById('emailSearch');
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
