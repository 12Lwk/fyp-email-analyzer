// Global variables
let currentEmails = [];
let currentPage = 1;
let pageSize = 10;
let filteredEmails = [];
let allEmails = [];
let isLoading = false;
let totalItems = 0;

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

// Function to parse date string
function parseDate(dateStr) {
    if (!dateStr) return null;
    try {
        // Handle timezone format consistently
        const normalizedDate = dateStr.replace(' ', 'T');
        const date = new Date(normalizedDate);
        return isNaN(date.getTime()) ? null : date;
    } catch (error) {
        console.error('Failed to parse date:', dateStr, error);
        return null;
    }
}

// Function to format date
function formatDate(dateStr) {
    if (!dateStr) return { shortDate: '', fullDate: '' };
    
    try {
        const date = parseDate(dateStr);
        if (!date) return { shortDate: dateStr, fullDate: dateStr };
        
        // Short date format (e.g., "Apr 2")
        const shortDate = date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
        });
        
        // Full date format for tooltip
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
    } catch (error) {
        console.error('Error formatting date:', dateStr, error);
        return { shortDate: dateStr, fullDate: dateStr };
    }
}

// Function to get priority class for styling
function getPriorityClass(priority) {
    if (!priority) return 'default';
    
    // Ensure we have a string and normalize to uppercase
    priority = String(priority).toUpperCase();
    
    switch (priority) {
        case 'HIGH':
            return 'high';
        case 'MEDIUM':
            return 'medium';
        case 'LOW':
            return 'low';
        default:
    return 'default';
    }
}

// Function to update pagination controls
function updatePaginationControls() {
    const totalPages = Math.ceil(totalItems / pageSize);
    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');
    const emailCount = document.getElementById('emailCount');

    console.log('Updating pagination controls:', {
        currentPage,
        totalPages,
        totalItems,
        pageSize,
        hasPrevButton: !!prevButton,
        hasNextButton: !!nextButton
    });

    if (prevButton) {
        const canGoPrev = currentPage > 1;
        prevButton.disabled = !canGoPrev;
        prevButton.classList.toggle('disabled', !canGoPrev);
        prevButton.style.cursor = canGoPrev ? 'pointer' : 'not-allowed';
    }

    if (nextButton) {
        const canGoNext = currentPage < totalPages;
        nextButton.disabled = !canGoNext;
        nextButton.classList.toggle('disabled', !canGoNext);
        nextButton.style.cursor = canGoNext ? 'pointer' : 'not-allowed';
    }

    if (pageInfo) {
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    }

    if (emailCount) {
        emailCount.textContent = `${totalItems} email${totalItems !== 1 ? 's' : ''} (showing ${pageSize} per page)`;
    }
}

// Function to change page
async function changePage(newPage) {
    console.log('Attempting to change to page:', newPage);
    
    if (isLoading) {
        console.log('Page change blocked: Loading in progress');
        return;
    }
    
    try {
        // Get current URL parameters
        const url = new URL(window.location.href);
        
        // Update URL with new page number
        url.searchParams.set('page', newPage.toString());
        
        // Keep existing parameters
        const perPage = url.searchParams.get('per_page') || pageSize;
        const category = url.searchParams.get('category');
        const search = url.searchParams.get('search');
        
        url.searchParams.set('per_page', perPage.toString());
        if (category && category !== 'all') {
            url.searchParams.set('category', category);
        }
        if (search) {
            url.searchParams.set('search', search);
        }
        
        // Update browser history
        history.pushState(null, '', url.toString());
        
        // Update current page
        currentPage = newPage;
        
        // Load emails for the new page
        await loadEmails();
        
    } catch (error) {
        console.error('Error changing page:', error);
        showError('Failed to change page. Please try again.');
    }
}

// Debounce function to limit API calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Function to initialize pagination
function initializePagination() {
    console.log('Initializing pagination...');
    
    // Get URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const pageParam = parseInt(urlParams.get('page')) || 1;
    const perPageParam = parseInt(urlParams.get('per_page')) || pageSize;
    
    console.log('Initial pagination values:', {
        pageParam,
        perPageParam,
        currentPage,
        pageSize
    });
    
    // Update current values
    currentPage = pageParam;
    pageSize = perPageParam;
    
    // Set up page size select
    const pageSizeSelect = document.getElementById('pageSizeSelect');
    if (pageSizeSelect) {
        pageSizeSelect.value = pageSize.toString();
        pageSizeSelect.onchange = handlePageSizeChange;
    }

    // Set up pagination buttons
    setupPaginationButtons();
    
    // Initial update of controls
    updatePaginationControls();
}

// Function to set up pagination buttons
function setupPaginationButtons() {
    console.log('Setting up pagination buttons');
    
    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');

    if (prevButton) {
        console.log('Found previous button');
        prevButton.onclick = (e) => {
            e.preventDefault();
            console.log('Previous button clicked, current page:', currentPage);
            if (currentPage > 1) {
                changePage(currentPage - 1);
            }
        };
    } else {
        console.warn('Previous button not found');
    }

    if (nextButton) {
        console.log('Found next button');
        nextButton.onclick = (e) => {
            e.preventDefault();
            const totalPages = Math.ceil(totalItems / pageSize);
            console.log('Next button clicked', { currentPage, totalPages });
            if (currentPage < totalPages) {
                changePage(currentPage + 1);
            }
        };
    } else {
        console.warn('Next button not found');
    }
}

// Function to handle page size changes
function handlePageSizeChange(e) {
    const newSize = parseInt(e.target.value);
    console.log('Page size change:', { newSize, oldSize: pageSize });
    
    if (!isNaN(newSize) && newSize !== pageSize) {
        pageSize = newSize;
        currentPage = 1; // Reset to first page
        
        // Update URL
        const url = new URL(window.location.href);
        url.searchParams.set('per_page', newSize.toString());
        url.searchParams.set('page', '1');
        history.pushState(null, '', url.toString());
        
        // Reload emails with new page size
        loadEmails();
    }
}

// Add event listener for DOM content loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing email functionality');
    
    // Initialize search with debounce
    const searchInput = document.getElementById('emailSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function(e) {
            console.log('Search input changed:', e.target.value);
            searchEmails(e.target.value);
        }, 300));
    }

    // Initialize category dropdown
    const categoryDropdown = document.getElementById('categoryDropdown');
    const categoriesList = document.getElementById('categoriesList');
    
    if (categoriesList) {
        const dropdownItems = categoriesList.querySelectorAll('.dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                const value = this.getAttribute('data-value');
                const text = this.textContent.trim();
                console.log('Category selected:', { value, text });
                handleCategoryChange(value, text);
            });
        });
    }

    // Initialize pagination
    initializePagination();

    // Load initial emails
    loadEmails();
});

// Search emails function
function searchEmails(query) {
    console.log('Searching emails with query:', query);
    
    // Reset to first page when searching
    currentPage = 1;
    
    // Get current category if any
    const categoriesList = document.getElementById('categoriesList');
    const activeCategory = categoriesList?.querySelector('.dropdown-item.active')?.getAttribute('data-value');
    
    // Update URL with search parameter
    const url = new URL(window.location.href);
    if (query) {
        url.searchParams.set('search', query);
    } else {
        url.searchParams.delete('search');
    }
    if (activeCategory && activeCategory !== 'all') {
        url.searchParams.set('category', activeCategory);
    }
    url.searchParams.set('page', '1');
    history.pushState(null, '', url.toString());

    // Load emails with search query
    loadEmails(query);
}

// Function to load emails
async function loadEmails(searchQuery = null) {
    if (isLoading) {
        console.log('Already loading emails, skipping...');
        return;
    }

    try {
        isLoading = true;
        console.log('Starting to load emails');
        
        // Show loading state
        const tableBody = document.getElementById('emailTableBody');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-5">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-2">Loading emails...</p>
                    </td>
                </tr>`;
        }

        // Get URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const pageParam = parseInt(urlParams.get('page')) || 1;
        const perPageParam = parseInt(urlParams.get('per_page')) || pageSize;
        const categoryParam = urlParams.get('category');

        // Construct API URL with parameters
        const apiUrl = new URL('/api/emails/view/', window.location.origin);
        
        // Add parameters
        apiUrl.searchParams.set('page', pageParam.toString());
        apiUrl.searchParams.set('per_page', perPageParam.toString());
        if (categoryParam) {
            apiUrl.searchParams.set('category', categoryParam);
        }
        if (searchQuery && searchQuery.trim()) {
            apiUrl.searchParams.set('search', searchQuery.trim());
        }

        console.log('Fetching emails from:', apiUrl.toString());

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
            // If unauthorized, reload the page to trigger Django's auth flow
            if (response.status === 401 || response.status === 403) {
                window.location.reload();
                return;
            }
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        console.log('Received email data:', data);

        if (!data || data.status !== 'success') {
            throw new Error(data.message || 'Invalid response from server');
        }

        // Handle response data
        if (data.data && Array.isArray(data.data.emails)) {
            allEmails = data.data.emails;
            totalItems = data.data.pagination.total_items;
            currentPage = data.data.pagination.current_page;
            pageSize = data.data.pagination.per_page;
        } else {
            throw new Error('Invalid data format received from server');
        }

        // Display emails
        displayEmails();
        
        // Update pagination controls
        updatePaginationControls();

    } catch (error) {
        console.error('Error loading emails:', error);
        showError(`Failed to load emails: ${error.message}`);
        
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-5">
                        <div class="alert alert-danger mb-3">
                            <i class="fas fa-exclamation-circle me-2"></i>
                            ${error.message}
                        </div>
                        <div class="text-center mt-3">
                            <button class="btn btn-primary btn-sm" onclick="retryLoadEmails()">
                                <i class="fas fa-sync-alt me-1"></i> Retry
                            </button>
                        </div>
                    </td>
                </tr>`;
        }
    } finally {
        isLoading = false;
    }
}

// Function to clear search
function clearSearch() {
    const searchInput = document.querySelector('input[type="search"]');
    if (searchInput) {
        searchInput.value = '';
    }
    searchEmails('');
}

// Toggle priority column visibility
function togglePriority() {
    const priorityCells = document.querySelectorAll('.priority-cell');
    const priorityColumn = document.querySelector('.priority-column');
    const button = document.querySelector('.toggle-labels-btn');

    priorityCells.forEach(cell => {
        cell.style.display = cell.style.display === 'none' ? '' : 'none';
    });
    
    if (priorityColumn) {
        priorityColumn.style.display = priorityColumn.style.display === 'none' ? '' : 'none';
    }

    if (button) {
        const isHidden = priorityColumn && priorityColumn.style.display === 'none';
        button.innerHTML = isHidden ? 
            '<i class="fas fa-tags"></i> Show Priority' : 
            '<i class="fas fa-tags"></i> Hide Priority';
    }
}

// Toggle category column visibility
function toggleCategory() {
    const categoryCells = document.querySelectorAll('.category-cell');
    const categoryColumn = document.querySelector('.category-column');
    
    categoryCells.forEach(cell => {
        cell.style.display = cell.style.display === 'none' ? '' : 'none';
    });
    
    if (categoryColumn) {
        categoryColumn.style.display = categoryColumn.style.display === 'none' ? '' : 'none';
    }
}

// Toggle both category and priority labels
function toggleLabels() {
    // Get all elements we need to manipulate
    const categoryCells = document.querySelectorAll('.category-cell');
    const priorityCells = document.querySelectorAll('.priority-cell');
    const categoryHeader = document.querySelector('th:nth-child(7)');
    const priorityHeader = document.querySelector('th:nth-child(8)');
    const button = document.querySelector('.toggle-labels-btn');
    const buttonText = document.getElementById('toggleLabelsBtnText');
    const buttonIcon = button ? button.querySelector('i') : null;
    
    // Visual feedback animation on button click
    if (button) {
        button.classList.add('btn-active-effect');
        setTimeout(() => {
            button.classList.remove('btn-active-effect');
        }, 300);
    }
    
    // Check the current state (are labels currently hidden?)
    const isLabelsHidden = localStorage.getItem('labelsHidden') === 'true';
    console.log('Current label state - hidden:', isLabelsHidden);
    
    // Toggle to new state
    const newState = !isLabelsHidden;
    console.log('New label state - hidden:', newState);
    
    // Update cells and headers based on new state
    if (newState) {
        // Hide all cells and apply styles to headers
        categoryCells.forEach(cell => cell.classList.add('hidden'));
        priorityCells.forEach(cell => cell.classList.add('hidden'));
        if (categoryHeader) categoryHeader.classList.add('hidden');
        if (priorityHeader) priorityHeader.classList.add('hidden');
        
        // Update button
        if (buttonText) buttonText.textContent = 'Show Labels';
        if (buttonIcon) buttonIcon.style.transform = 'rotate(45deg)';
    } else {
        // Show all cells and remove styles from headers
        categoryCells.forEach(cell => cell.classList.remove('hidden'));
        priorityCells.forEach(cell => cell.classList.remove('hidden'));
        if (categoryHeader) categoryHeader.classList.remove('hidden');
        if (priorityHeader) priorityHeader.classList.remove('hidden');
        
        // Update button
        if (buttonText) buttonText.textContent = 'Hide Labels';
        if (buttonIcon) buttonIcon.style.transform = '';
    }
    
    // Save new state to localStorage
    try {
        localStorage.setItem('labelsHidden', newState.toString());
    } catch (e) {
        console.warn('Failed to save label visibility preference:', e);
    }
}

// Utility function to sanitize email IDs for DOM element IDs
function sanitizeEmailId(id) {
    // Convert the ID to string and replace any non-alphanumeric characters with underscores
    return String(id).replace(/[^a-zA-Z0-9]/g, '_');
}

// Function to create an email row
function createEmailRow(email) {
    const row = document.createElement('tr');
    const emailId = sanitizeEmailId(email.id);
    row.id = `email_row_${emailId}`;
    row.className = 'email-row';
    row.dataset.emailId = emailId;
    
    // Add click handler for the row
    row.addEventListener('click', (e) => {
        // Only handle if not clicking checkbox or star
        if (!e.target.matches('input[type="checkbox"]') && 
            !e.target.matches('.fa-star') && 
            !e.target.matches('a')) {
            e.preventDefault();
            e.stopPropagation();
            navigateToEmailDetail(emailId);
        }
    });

    // Create checkbox cell
    const checkboxCell = document.createElement('td');
    checkboxCell.className = 'text-center';
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'email-checkbox';
    checkbox.id = `checkbox_${emailId}`;
    checkbox.addEventListener('click', (e) => {
        e.stopPropagation();
        updateSelectedEmails();
    });
    checkboxCell.appendChild(checkbox);

    // Create star cell
    const starCell = document.createElement('td');
    starCell.className = 'text-center';
    const starIcon = document.createElement('i');
    starIcon.className = `fas fa-star ${email.star ? 'text-warning' : 'text-muted'}`;
    starIcon.style.cursor = 'pointer';
    starIcon.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleEmailStar(email.id);
    });
    starCell.appendChild(starIcon);

    // Create sender cell
    const senderCell = document.createElement('td');
    senderCell.textContent = email.sender || 'No Sender';

    // Create subject cell
    const subjectCell = document.createElement('td');
    subjectCell.textContent = email.subject || 'No Subject';

    // Create snippet cell
    const snippetCell = document.createElement('td');
    snippetCell.textContent = email.snippet || '';
    snippetCell.className = 'email-snippet';

    // Create date cell
    const dateCell = document.createElement('td');
    dateCell.className = 'text-end';
    dateCell.textContent = formatEmailDate(email.date);

    // Create category cell
    const categoryCell = document.createElement('td');
    categoryCell.className = 'category-cell';
    let category = email.category || 'Uncategorized';
    let simplifiedCategory = category;
    
    // Convert full category names to simplified versions for display
    if (category === 'Finance & Transactions') simplifiedCategory = 'Finance';
    else if (category === 'General Business Communication') simplifiedCategory = 'Business';
    else if (category === 'IT Alerts & System Notifications') simplifiedCategory = 'IT Alerts';
    else if (category === 'Internal Policies & HR Updates') simplifiedCategory = 'HR Updates';
    else if (category === 'Legal & Contractual') simplifiedCategory = 'Legal';
    else if (category === 'Meetings & Scheduling') simplifiedCategory = 'Meetings';
    else if (category === 'Personal Communication & Purely Personal') simplifiedCategory = 'Personal';
    else if (category === 'Project Management & Strategy') simplifiedCategory = 'Projects';
    
    const categorySpan = document.createElement('span');
    categorySpan.className = `email-category category-${category.replace(/[^a-zA-Z0-9]/g, '')}`;
    categorySpan.title = category;
    categorySpan.textContent = simplifiedCategory;
    categoryCell.appendChild(categorySpan);

    // Create priority cell
    const priorityCell = document.createElement('td');
    priorityCell.className = 'priority-cell';
    const priority = email.priority || 'Default';
    const priorityClass = getPriorityClass(priority);
    const prioritySpan = document.createElement('span');
    prioritySpan.className = `email-priority priority-${priorityClass}`;
    prioritySpan.textContent = priority.toUpperCase();
    priorityCell.appendChild(prioritySpan);

    // Add all cells to the row in the correct order
    row.appendChild(checkboxCell);
    row.appendChild(starCell);
    row.appendChild(senderCell);
    row.appendChild(subjectCell);
    row.appendChild(snippetCell);
    row.appendChild(dateCell);
    row.appendChild(categoryCell);
    row.appendChild(priorityCell);

    // Check if labels are hidden
    const isLabelsHidden = localStorage.getItem('labelsHidden') === 'true';
    if (isLabelsHidden) {
        categoryCell.classList.add('hidden');
        priorityCell.classList.add('hidden');
    }

    return row;
}

// Function to format email date
function formatEmailDate(dateString) {
    if (!dateString) return 'No Date';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date.toDateString() === today.toDateString()) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (date.toDateString() === yesterday.toDateString()) {
        return 'Yesterday';
    } else if (date.getFullYear() === today.getFullYear()) {
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } else {
        return date.toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
    }
}

// Function to display emails
function displayEmails() {
    console.log('Displaying emails for page:', currentPage);
    const tableBody = document.getElementById('emailTableBody');
    if (!tableBody) {
        console.error('Email table body not found');
        return;
    }

    // Clear existing rows
    tableBody.innerHTML = '';

    if (allEmails.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5">
                    <div class="empty-state">
                        <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                        <h5>No Emails</h5>
                        <p class="text-muted">No emails to display.</p>
                    </div>
                </td>
            </tr>`;
        return;
    }

    // Create document fragment for better performance
    const fragment = document.createDocumentFragment();
    
    // Add rows for current page emails
    allEmails.forEach(email => {
        const row = createEmailRow(email);
        fragment.appendChild(row);
    });
    
    // Append all rows at once
    tableBody.appendChild(fragment);

    // Update pagination controls
    updatePaginationControls();
}

// Function to show error message
function showError(message, canRetry = true) {
    const errorToast = showToast(message, 'danger');
    if (canRetry) {
        setTimeout(() => {
            const retryBtn = document.createElement('button');
            retryBtn.className = 'btn btn-sm btn-light ms-2';
            retryBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Retry';
            retryBtn.onclick = () => {
                errorToast.hide();
                loadEmails();
            };
            errorToast._element.querySelector('.toast-body').appendChild(retryBtn);
        }, 100);
    }
}

// Function to retry loading emails
function retryLoadEmails() {
    console.log('Retrying to load emails...');
    currentPage = 1; // Reset to first page
    loadEmails();
}

// Function to load with a smaller limit
function loadWithSmallerLimit(limit) {
    console.log(`Loading with smaller limit: ${limit}`);
    // Clear any cached data
    sessionStorage.removeItem('emailsCache');
    sessionStorage.removeItem('emailsCacheTimestamp');
    
    const baseUrl = window.location.origin;
    const now = Date.now();
    
    // Show loading indicator
    const tableBody = document.getElementById('emailTableBody');
    if (tableBody) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Loading emails (limited to ${limit})...</p>
                </td>
            </tr>`;
    }
    
    // Set loading state
    isLoading = true;
    
    // Fetch with smaller limit
    fetch(`${baseUrl}/api/emails/view/?_t=${now}&limit=${limit}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            processEmailData(data);
        })
        .catch(error => {
            console.error('Error with smaller limit:', error);
            showError(`Failed to load emails: ${error.message}`);
        })
        .finally(() => {
            isLoading = false;
        });
}

// Function to handle email selection
function handleEmailSelection(checkbox) {
    const emailId = checkbox.dataset.emailId;
    console.log(`Email ${emailId} ${checkbox.checked ? 'selected' : 'deselected'}`);
}

// Function to toggle star
function toggleStar(emailId, starElement) {
    starElement.classList.toggle('starred');
    console.log(`Star toggled for email ${emailId}`);
}

// Function to reliably navigate to a URL across different browsers
function navigateToUrl(url) {
    console.log('Navigating to URL:', url);
    
    // Method 1: Direct window.location assignment
    window.location.href = url;
    
    // If the above doesn't cause navigation to happen after a short delay,
    // try alternative methods
    setTimeout(() => {
        console.log('Trying alternative navigation methods');
        
        // Method 2: Create and click a link
        try {
            const link = document.createElement('a');
            link.href = url;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            setTimeout(() => document.body.removeChild(link), 100);
        } catch (e) {
            console.error('Error using link click method:', e);
            
            // Method 3: Try location.replace
            window.location.replace(url);
        }
    }, 200);
}

// Function to check Gmail authentication
async function checkGmailAuth() {
    try {
        const response = await fetch('/api/auth/check/', {
            method: 'GET',
            credentials: 'include',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            return false;
        }
        
        const data = await response.json();
        return data.status === 'success' && data.authenticated === true && data.is_gmail_authenticated === true;
    } catch (error) {
        console.error('Error checking Gmail authentication:', error);
        return false;
    }
}

// Function to navigate to email detail
async function navigateToEmailDetail(emailId) {
    if (!emailId) {
        console.error('No email ID provided for navigation');
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
            // Construct the detail URL
            const detailUrl = `/inbox_email_detail/${encodeURIComponent(emailId)}/`;
            
            // Log debug information
            console.log('Email ID:', emailId);
            console.log('Current URL:', window.location.href);
            console.log('Navigating to:', detailUrl);
            
            // Navigate to detail page directly
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

// Function to open email (legacy support)
function openEmail(emailId) {
    // Use the new navigation function
    navigateToEmailDetail(emailId);
}

// Function to update email count
function updateEmailCount(count) {
    const emailCount = document.getElementById('emailCount');
    const inboxCount = document.getElementById('inboxCount');
    if (emailCount) {
        emailCount.textContent = `${count} email${count !== 1 ? 's' : ''}`;
    }
    if (inboxCount) {
        inboxCount.textContent = count;
    }
}

// Function to get current page from URL or default to 1
function getCurrentPage() {
    const urlParams = new URLSearchParams(window.location.search);
    return parseInt(urlParams.get('page')) || 1;
}

// Function to get CSRF token from various locations
function getCSRFToken() {
    // Try Django's csrftoken cookie first (most reliable)
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    if (cookieValue) return cookieValue;
    
    // Try hidden input field (Django's {% csrf_token %})
    const inputToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
    if (inputToken) return inputToken;
    
    // Try meta tag last (less common)
    const metaToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (metaToken) return metaToken;
    
    return null;
}

// Function to log URL debug information
function logUrlDebug(emailId, detailUrl) {
    console.group('Email Navigation Debug Info');
    console.log('Email ID:', emailId);
    console.log('Type:', typeof emailId);
    console.log('Length:', emailId.length);
    console.log('URL encoded ID:', encodeURIComponent(emailId));
    console.log('Target URL:', detailUrl);
    console.log('Current location:', window.location.href);
    console.log('Base URL:', window.location.origin);
    console.groupEnd();
}

// Add event listener for popstate to handle browser back/forward
window.addEventListener('popstate', function(event) {
    loadEmails();
});

// Update category filter handling
function handleCategoryChange(selectedValue, selectedText) {
    console.log('Changing category filter:', { value: selectedValue, text: selectedText });

    // Update dropdown button text and style
    const categoryDropdown = document.getElementById('categoryDropdown');
    if (categoryDropdown) {
        categoryDropdown.innerHTML = `
            <i class="fas fa-filter me-1"></i>
            ${selectedText}
        `;
        categoryDropdown.classList.toggle('btn-primary', selectedValue !== 'all');
        categoryDropdown.classList.toggle('btn-outline-primary', selectedValue === 'all');
    }

    // Update active state in dropdown
    const categoriesList = document.getElementById('categoriesList');
    if (categoriesList) {
        const items = categoriesList.querySelectorAll('.dropdown-item');
        items.forEach(item => {
            const isActive = item.getAttribute('data-value') === selectedValue;
            item.classList.toggle('active', isActive);
            if (isActive) {
                item.setAttribute('aria-current', 'true');
            } else {
                item.removeAttribute('aria-current');
            }
        });
    }

    // Get current search query if any
    const searchInput = document.getElementById('emailSearch');
    const searchQuery = searchInput ? searchInput.value.trim() : '';

    // Update URL with both category and search parameters
    const url = new URL(window.location.href);
    if (selectedValue === 'all') {
        url.searchParams.delete('category');
    } else {
        url.searchParams.set('category', selectedValue);
    }
    if (searchQuery) {
        url.searchParams.set('search', searchQuery);
    }
    url.searchParams.set('page', '1');
    history.pushState(null, '', url.toString());
    
    // Save filter preference
    try {
        if (selectedValue === 'all') {
            localStorage.removeItem('categoryFilter');
            localStorage.removeItem('categoryFilterText');
        } else {
            localStorage.setItem('categoryFilter', selectedValue);
            localStorage.setItem('categoryFilterText', selectedText);
        }
    } catch (e) {
        console.warn('Failed to save category filter preference:', e);
    }

    // Reset to first page and reload emails
    currentPage = 1;
    loadEmails(searchQuery);
}

// Function to clear all filters
function clearFilters() {
    console.log('Clearing all filters');
    
    // Reset category filter
    const categoryDropdown = document.getElementById('categoryDropdown');
    if (categoryDropdown) {
        categoryDropdown.innerHTML = `
            <i class="fas fa-filter me-1"></i>
            All Categories
        `;
        categoryDropdown.classList.remove('btn-primary');
        categoryDropdown.classList.add('btn-outline-primary');
    }

    // Reset active state in dropdown
    const categoriesList = document.getElementById('categoriesList');
    if (categoriesList) {
        const items = categoriesList.querySelectorAll('.dropdown-item');
        items.forEach(item => item.classList.remove('active'));
        const allItem = categoriesList.querySelector('[data-value="all"]');
        if (allItem) allItem.classList.add('active');
    }

    // Clear saved preferences
        localStorage.removeItem('categoryFilter');
        localStorage.removeItem('categoryFilterText');

    // Update URL by removing category parameter
    const url = new URL(window.location.href);
    url.searchParams.delete('category');
    url.searchParams.set('page', '1');
    history.pushState(null, '', url.toString());
    
    // Reset page and reload
    currentPage = 1;
    loadEmails();
}

// Function to check if user is logged in
async function isUserLoggedIn() {
    try {
        const response = await fetch('/api/auth/check/', {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            return false;
        }
        
        const data = await response.json();
        return data.status === 'success' && data.authenticated === true;
    } catch (error) {
        console.error('Error checking authentication status:', error);
        return false;
    }
}

// Function to show toast message
function showToast(message, type = 'info') {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    const toastElement = document.createElement('div');
    toastElement.innerHTML = toastHtml;
    document.getElementById('toastContainer').appendChild(toastElement.firstChild);
    
    const toast = new bootstrap.Toast(document.getElementById('toastContainer').lastChild, {
        delay: 3000
    });
    toast.show();
    return toast;
}

// Function to hide toast
function hideToast(toast) {
    if (toast) {
        toast.hide();
    }
}


