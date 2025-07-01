// Function to load profile picture from localStorage
function loadProfilePicture() {
    const profileImage = document.getElementById('sidebarUserAvatar');
    const savedImage = localStorage.getItem('profileImage');
    
    if (profileImage && savedImage) {
        profileImage.src = savedImage;
    }
}


// Compose Email Modal Functionality
document.addEventListener('DOMContentLoaded', function() {
    
    // Period buttons
    const periodButtons = document.querySelectorAll('.btn-group[aria-label="Time Period"] .btn');
    periodButtons.forEach(button => {
        button.addEventListener('click', function() {
            periodButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            updateTimeframe(this.getAttribute('data-period'));
        });
    });
    
    // Category view buttons
    const viewButtons = document.querySelectorAll('.btn-group[aria-label="Category View"] .btn');
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            viewButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            toggleCategoryView(this.getAttribute('data-view'));
        });
    });

    const composeForm = document.getElementById('composeForm');
    const attachFileBtn = document.getElementById('attachFileBtn');
    const fileInput = document.getElementById('fileInput');
    const attachmentList = document.getElementById('attachmentList');
    const saveAsDraftBtn = document.getElementById('saveAsDraft');
    const composeModal = document.getElementById('composeModal');
    
    // Handle file attachments
    attachFileBtn.addEventListener('click', () => {
        fileInput.click();
    });
    
    fileInput.addEventListener('change', () => {
        attachmentList.innerHTML = '';
        Array.from(fileInput.files).forEach(file => {
            const fileSize = (file.size / (1024 * 1024)).toFixed(2); // Convert to MB
            const attachmentDiv = document.createElement('div');
            attachmentDiv.className = 'attachment-item d-flex align-items-center mt-2';
            attachmentDiv.innerHTML = `
                <i class="fas fa-file me-2"></i>
                <span class="flex-grow-1">${file.name} (${fileSize} MB)</span>
                <button type="button" class="btn btn-sm btn-link text-danger remove-attachment">
                    <i class="fas fa-times"></i>
                </button>
            `;
            attachmentList.appendChild(attachmentDiv);
        });
    });
    
    // Handle attachment removal
    attachmentList.addEventListener('click', (e) => {
        if (e.target.closest('.remove-attachment')) {
            e.target.closest('.attachment-item').remove();
            fileInput.value = ''; // Clear the file input
        }
    });
    
    // Handle form submission
    composeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData();
        formData.append('to', document.getElementById('emailTo').value);
        formData.append('cc', document.getElementById('emailCc').value);
        formData.append('bcc', document.getElementById('emailBcc').value);
        formData.append('subject', document.getElementById('emailSubject').value);
        formData.append('body', document.getElementById('emailBody').value);
        
        // Add files if any
        Array.from(fileInput.files).forEach(file => {
            formData.append('attachments', file);
        });
        
        try {
            const response = await fetch('/api/emails/send', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                showNotification('Email sent successfully!', 'success');
                bootstrap.Modal.getInstance(composeModal).hide();
                resetComposeForm();
            } else {
                throw new Error('Failed to send email');
            }
        } catch (error) {
            console.error('Error sending email:', error);
            showNotification('Failed to send email. Please try again.', 'error');
        }
    });
    
    // Handle save as draft
    saveAsDraftBtn.addEventListener('click', async () => {
        const formData = new FormData();
        formData.append('to', document.getElementById('emailTo').value);
        formData.append('cc', document.getElementById('emailCc').value);
        formData.append('bcc', document.getElementById('emailBcc').value);
        formData.append('subject', document.getElementById('emailSubject').value);
        formData.append('body', document.getElementById('emailBody').value);
        
        try {
            const response = await fetch('/api/emails/draft', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                showNotification('Draft saved successfully!', 'success');
                bootstrap.Modal.getInstance(composeModal).hide();
                resetComposeForm();
            } else {
                throw new Error('Failed to save draft');
            }
        } catch (error) {
            console.error('Error saving draft:', error);
            showNotification('Failed to save draft. Please try again.', 'error');
        }
    });
    
    // Reset form when modal is closed
    composeModal.addEventListener('hidden.bs.modal', resetComposeForm);
});

// Reset compose form
function resetComposeForm() {
    document.getElementById('composeForm').reset();
    document.getElementById('attachmentList').innerHTML = '';
    document.getElementById('fileInput').value = '';
}

// Show notification
function showNotification(message, type = 'info') {
    // You can implement your preferred notification system here
    alert(message);
}

// Chart Initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize showAllCategories state
    window.showAllCategories = false;
    
    // Set initial button text
    const toggleBtn = document.getElementById('toggleCategoryView');
    if (toggleBtn) {
        toggleBtn.textContent = 'Show All';
    }
    
    // Load profile picture
    loadProfilePicture();
    
    // Initialize all charts
    initializeCharts();
    
    // Add window resize listener
    window.addEventListener('resize', debounce(function() {
        updateCharts();
    }, 250));
});

// Initialize all charts
function initializeCharts() {
    // Email Volume Chart
    const emailsCtx = document.getElementById('emailsChart').getContext('2d');
    window.emailsChart = new Chart(emailsCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Emails',
                data: [],
                borderColor: '#4e73df',
                backgroundColor: 'rgba(78, 115, 223, 0.05)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });

    // Priority Distribution Chart
    const priorityCtx = document.getElementById('priorityChart').getContext('2d');
    window.priorityChart = new Chart(priorityCtx, {
        type: 'doughnut',
        data: {
            labels: ['HIGH', 'MEDIUM', 'LOW'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: ['#dc3545', '#ffc107', '#28a745'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: {
                            size: 12
                        }
                    }
                }
            },
            cutout: '70%'
        }
    });

    // Category Chart
    const categoryCtx = document.getElementById('categoryChart').getContext('2d');
    window.categoryChart = new Chart(categoryCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: '#4e73df',
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });

    // Response Time Chart
    const responseTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
    window.responseTimeChart = new Chart(responseTimeCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Response Time',
                data: [],
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });

    // Load initial data
    fetchDashboardData('day');
}

// Fetch dashboard data from API
async function fetchDashboardData(timeframe) {
    try {
        const response = await fetch(`/api/dashboard-data/${timeframe}/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        // Update charts with the fetched data
        updateVolumeChart(data.volume_data);
        updateCategoryChart(data.categories, window.showAllCategories);
        updatePriorityChart(data.priorities);
        
        // Hide any existing error messages
        const errorElement = document.getElementById('dashboardError');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        showErrorMessage('Failed to fetch dashboard data. Please try again later.');
    }
}

// Update dashboard with new data
function updateDashboard(data) {
    // Update stats
    if (data.stats) {
        document.getElementById('totalEmails').textContent = formatNumber(data.stats.total_emails || 0);
        document.getElementById('highPriorityEmails').textContent = formatNumber(data.stats.high_priority || 0);
        document.getElementById('mediumPriorityEmails').textContent = formatNumber(data.stats.medium_priority || 0);
        
        // Calculate low priority percentage
        const total = data.stats.total_emails || 0;
        const lowPriority = data.stats.low_priority || 0;
        const lowPriorityPercentage = total > 0 ? Math.round((lowPriority / total) * 100) : 0;
        document.getElementById('lowPriorityEmails').textContent = `${lowPriorityPercentage}%`;
    }

    // Update Volume Chart
    if (window.emailsChart && data.volume_trend) {
        window.emailsChart.data.labels = data.volume_trend.labels;
        window.emailsChart.data.datasets[0].data = data.volume_trend.data;
        window.emailsChart.update();
    }

    // Update Priority Chart
    if (window.priorityChart && data.priority_distribution) {
        window.priorityChart.data.labels = data.priority_distribution.labels;
        window.priorityChart.data.datasets[0].data = data.priority_distribution.data;
        window.priorityChart.update();
    }

    // Update Category Chart
    if (window.categoryChart && data.category_distribution) {
        window.categoryChart.data.labels = data.category_distribution.labels;
        window.categoryChart.data.datasets[0].data = data.category_distribution.data;
        window.categoryChart.update();
    }

    // Update Response Time Chart
    if (window.responseTimeChart && data.response_time) {
        window.responseTimeChart.data.labels = data.response_time.labels;
        window.responseTimeChart.data.datasets[0].data = data.response_time.data;
        window.responseTimeChart.update();
    }

    // Update high priority emails table
    if (data.high_priority_emails) {
        updateHighPriorityEmailsList(data.high_priority_emails);
    }
}

// Format numbers with commas
function formatNumber(num) {
    if (!num) return '0';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Change timeframe and update data
function updateTimeframe(period) {
    currentTimeframe = period;
    
    // Update active state of buttons
    document.querySelectorAll('.btn-group .btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-period') === period) {
            btn.classList.add('active');
        }
    });

    // Get current show_all state
    const showAllBtn = document.getElementById('toggleCategoryView');
    const showAll = showAllBtn.textContent.trim() === 'Show Less' ? 'true' : 'false';

    // Fetch updated data with current timeframe and show_all state
    fetch(`/api/dashboard-data/?timeframe=${period}&show_all=${showAll}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateCharts(data);
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
        });
}

// Update high priority emails list
function updateHighPriorityEmailsList(emails) {
    const tbody = document.getElementById('highPriorityEmailsList');
    if (!tbody) return;

    tbody.innerHTML = '';
    if (!emails || !emails.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No high priority emails</td></tr>';
        return;
    }

    emails.forEach(email => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${email.subject || 'No Subject'}</td>
            <td>${email.sender || 'Unknown'}</td>
            <td>${email.priority_score ? email.priority_score.toFixed(1) : 'N/A'}</td>
            <td>${formatDate(email.date)}</td>
            <td><span class="badge bg-danger">High Priority</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Refresh high priority emails
function refreshHighPriorityEmails() {
    fetchDashboardData(document.querySelector('.btn-group[aria-label="Time Period"] .btn.active').getAttribute('data-period'));
}

// Update charts on window resize
function updateCharts() {
    if (window.emailsChart) window.emailsChart.resize();
    if (window.priorityChart) window.priorityChart.resize();
    if (window.categoryChart) window.categoryChart.resize();
    if (window.responseTimeChart) window.responseTimeChart.resize();
}

// Debounce function to limit resize events
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(function() {
            func.apply(context, args);
        }, wait);
    };
}

// Timeframe and Category View Selection
document.addEventListener('DOMContentLoaded', function() {
    // Time Period Buttons
    const timeframeButtons = document.querySelectorAll('.btn-group[aria-label="Time Period"] .btn');
    timeframeButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            timeframeButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            // Get the period from data attribute
            const period = this.getAttribute('data-period');
            updateTimeframe(period);
        });
    });
    
    // Category View Buttons
    const categoryButtons = document.querySelectorAll('.btn-group[aria-label="Category View"] .btn');
    categoryButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            categoryButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            // Get the view from data attribute
            const view = this.getAttribute('data-view');
            toggleCategoryView(view);
        });
    });
});

let showAllCategories = false;

function toggleCategoryView(showAll) {
    const button = document.getElementById('toggleCategoryView');
    if (!button) {
        console.error('Category toggle button not found');
        return;
    }

    // Toggle state
    window.showAllCategories = showAll === 'true';
    
    // Update button text
    button.textContent = window.showAllCategories ? 'Show Top 5' : 'Show All';
    
    // Fetch and update data based on state
    fetchDashboardData(currentTimeframe)
        .then(data => {
            if (data) {
                updateCategoryChart(data.categories, window.showAllCategories);
            }
        })
        .catch(error => {
            console.error('Error updating category view:', error);
            showErrorMessage('Failed to update category view. Please try again.');
        });
}

function showErrorMessage(message) {
    const errorDiv = document.getElementById('dashboardError') || createErrorElement();
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    // Hide error after 5 seconds
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function createErrorElement() {
    const errorDiv = document.createElement('div');
    errorDiv.id = 'dashboardError';
    errorDiv.className = 'alert alert-danger';
    errorDiv.style.position = 'fixed';
    errorDiv.style.top = '20px';
    errorDiv.style.right = '20px';
    errorDiv.style.zIndex = '1000';
    document.body.appendChild(errorDiv);
    return errorDiv;
}

// Load high priority emails
async function loadHighPriorityEmails() {
    try {
        const response = await fetch('/api/emails/high-priority');
        const data = await response.json();
        updateHighPriorityEmailsList(data.emails);
    } catch (error) {
        console.error('Error loading high priority emails:', error);
        showNotification('Failed to load high priority emails', 'error');
    }
}

// Update priority stats
function updatePriorityStats(stats) {
    document.getElementById('highPriorityEmails').textContent = formatNumber(stats.high);
    document.getElementById('mediumPriorityEmails').textContent = formatNumber(stats.medium);
    document.getElementById('lowPriorityEmails').textContent = formatNumber(stats.low);
}

// Load emails function
async function loadEmails(page = 1, perPage = 10, folder = 'INBOX', category = '', searchQuery = '') {
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: perPage,
            folder: folder,
            category: category,
            q: searchQuery
        });

        const response = await fetch(`/api/emails/view/?${params.toString()}`);
        if (!response.ok) {
            throw new Error('Failed to load emails');
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error loading emails:', error);
        showNotification('Failed to load emails. Please try again.', 'error');
        throw error;
    }
}

// Update email list
function updateEmailList(emails) {
    const emailList = document.querySelector('.email-list');
    if (!emailList) return;

    emailList.innerHTML = '';
    
    if (!emails || emails.length === 0) {
        emailList.innerHTML = '<div class="text-center p-4">No emails found</div>';
        return;
    }

    emails.forEach(email => {
        const emailItem = document.createElement('div');
        emailItem.className = 'email-item d-flex align-items-center p-3 border-bottom';
        emailItem.innerHTML = `
            <div class="form-check">
                <input type="checkbox" class="form-check-input" id="email-${email.id}">
            </div>
            <div class="ms-3 flex-grow-1">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-1">${email.sender}</h6>
                    <small class="text-muted">${formatDate(email.date)}</small>
                </div>
                <div class="subject">${email.subject}</div>
                <div class="snippet text-muted">${email.snippet}</div>
            </div>
            <div class="ms-3 d-flex flex-column align-items-end">
                ${email.has_attachments ? '<i class="fas fa-paperclip"></i>' : ''}
                ${email.priority ? `<span class="badge bg-${getPriorityColor(email.priority)}">${email.priority}</span>` : ''}
                ${email.category ? `<span class="badge bg-secondary">${email.category}</span>` : ''}
            </div>
        `;
        emailList.appendChild(emailItem);
    });
}

// Get priority color
function getPriorityColor(priority) {
    switch (priority.toLowerCase()) {
        case 'high':
            return 'danger';
        case 'medium':
            return 'warning';
        case 'low':
            return 'success';
        default:
            return 'secondary';
    }
}

// Initialize email loading
document.addEventListener('DOMContentLoaded', async function() {
    try {
        const data = await loadEmails();
        updateEmailList(data.emails);
        
        // Update pagination if needed
        if (data.total_pages > 1) {
            // Implement pagination UI update
        }
    } catch (error) {
        console.error('Error initializing emails:', error);
    }
});

function updateCategoryChart(categories, showAll) {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) {
        console.error('Category chart canvas not found');
        return;
    }

    // Sort categories by count in descending order
    const sortedCategories = Object.entries(categories)
        .sort(([,a], [,b]) => b - a);

    // Take all categories or just top 5 based on state
    const displayCategories = showAll ? sortedCategories : sortedCategories.slice(0, 5);

    const labels = displayCategories.map(([category]) => category);
    const data = displayCategories.map(([, count]) => count);

    // Generate colors for each category
    const colors = generateColors(labels.length);

    if (window.categoryChart) {
        window.categoryChart.destroy();
    }

    window.categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function generateColors(count) {
    const baseColors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF9F40'
    ];
    
    if (count <= baseColors.length) {
        return baseColors.slice(0, count);
    }
    
    // Generate additional colors if needed
    const colors = [...baseColors];
    while (colors.length < count) {
        const hue = (colors.length * 137.508) % 360; // Golden angle approximation
        colors.push(`hsl(${hue}, 70%, 60%)`);
    }
    return colors;
}

// Add event listener when document is ready
document.addEventListener('DOMContentLoaded', function() {
    
    // Add event listener for category toggle button
    const toggleButton = document.getElementById('toggleCategoriesBtn');
    if (toggleButton) {
        toggleButton.addEventListener('click', toggleCategoryView);
    }
    
}); 