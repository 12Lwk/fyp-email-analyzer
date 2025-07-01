document.addEventListener('DOMContentLoaded', function() {
    // Get sidebar elements
    const sidebarUserAvatar = document.getElementById('sidebarUserAvatar');
    const sidebarDisplayName = document.getElementById('sidebarDisplayName');
    const sidebarEmail = document.getElementById('sidebarEmail');
    
    // Load profile image from localStorage if available
    const profileImage = localStorage.getItem('profileImage');
    if (profileImage && sidebarUserAvatar) {
        console.log('Setting profile image from localStorage');
        sidebarUserAvatar.src = profileImage;
    }
    
    // Load display name from localStorage if available
    const profileSettings = JSON.parse(localStorage.getItem('profileSettings') || '{}');
    if (profileSettings.displayName && sidebarDisplayName) {
        console.log('Setting display name from localStorage');
        sidebarDisplayName.textContent = profileSettings.displayName;
    }
    
    // Create a fixed menu toggle button
    function createFixedMenuToggle() {
        // Remove any existing button first to avoid duplicates
        const existingContainer = document.getElementById('fixed-menu-toggle-container');
        if (existingContainer) {
            existingContainer.remove();
        }
        
        // Create container with absolute positioning
        const container = document.createElement('div');
        container.id = 'fixed-menu-toggle-container';
        
        // Set inline styles - but don't force display:block by default
        Object.assign(container.style, {
            position: 'fixed',
            left: '15px',
            top: '15px',
            zIndex: '9999',
            display: 'none' // Hide by default
        });
        
        // Add important flag to ensure these styles cannot be overridden
        container.setAttribute('style', 'position: fixed !important; left: 15px !important; top: 15px !important; z-index: 9999 !important; display: none !important;');
        
        // Create button with improved styling
        const button = document.createElement('button');
        button.id = 'fixed-menu-toggle';
        button.className = 'btn btn-primary';
        button.title = 'Show Sidebar (Ctrl+B)';
        button.setAttribute('aria-label', 'Show Sidebar');
        
        // Create icon
        const icon = document.createElement('i');
        icon.className = 'fas fa-bars';
        
        // Assemble
        button.appendChild(icon);
        container.appendChild(button);
        document.body.appendChild(container);
        
        return container;
    }
    
    // Create the fixed toggle button immediately
    const fixedToggleContainer = createFixedMenuToggle();
    
    // Sidebar toggle functionality
    const menuToggle = document.getElementById('menu-toggle');
    const fixedToggle = document.getElementById('fixed-menu-toggle');
    const wrapper = document.getElementById('wrapper');
    const sidebar = document.getElementById('sidebar');
    const pageContentWrapper = document.getElementById('page-content-wrapper');
    const navbar = document.querySelector('.navbar');
    
    function adjustDashboardContent() {
        // Specifically target dashboard content elements that might be cut off
        const titles = document.querySelectorAll('h1, h2, h3, .chart-title');
        const charts = document.querySelectorAll('.chart-container, .card');
        const containers = document.querySelectorAll('.container-fluid > div');
        
        const isCollapsed = wrapper.classList.contains('toggled');
        
        if (isCollapsed) {
            // Adjust all potential elements that might be cut off
            titles.forEach(title => {
                title.style.paddingLeft = '30px';
                title.style.marginLeft = '15px';
            });
            
            charts.forEach(chart => {
                chart.style.paddingLeft = '40px';
                chart.style.width = '100%';
                chart.style.boxSizing = 'border-box';
            });
            
            containers.forEach(container => {
                container.style.paddingLeft = '30px';
            });
            
            // Fix specific elements by ID if they exist
            ['email-volume-trend', 'category-distribution', 'volume-trend'].forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    element.style.paddingLeft = '40px';
                    element.style.width = '100%';
                }
            });
        } else {
            // Reset styles when sidebar is visible
            titles.forEach(title => {
                title.style.paddingLeft = '';
                title.style.marginLeft = '';
            });
            
            charts.forEach(chart => {
                chart.style.paddingLeft = '';
                chart.style.width = '';
            });
            
            containers.forEach(container => {
                container.style.paddingLeft = '';
            });
            
            // Reset specific elements
            ['email-volume-trend', 'category-distribution', 'volume-trend'].forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    element.style.paddingLeft = '';
                    element.style.width = '';
                }
            });
        }
    }
    
    function updateLayout(isCollapsed) {
        if (isCollapsed) {
            // Hide sidebar
            wrapper.classList.add('toggled');
            if (sidebar) sidebar.classList.add('collapsed');
            
            // Adjust navbar position
            if (navbar) {
                navbar.style.left = '0';
                navbar.style.width = '100%';
                navbar.style.paddingLeft = window.innerWidth < 576 ? '55px' : '70px';
            }
            
            // Expand content area
            if (pageContentWrapper) {
                pageContentWrapper.style.marginLeft = '0';
                pageContentWrapper.style.width = '100%';
                pageContentWrapper.style.paddingLeft = '60px';
                pageContentWrapper.style.paddingRight = '20px';
            }
            
            // Show the fixed toggle button ONLY when sidebar is collapsed
            if (fixedToggleContainer) {
                fixedToggleContainer.style.display = 'block';
                fixedToggleContainer.setAttribute('style', 'position: fixed !important; left: 15px !important; top: 15px !important; z-index: 9999 !important; display: block !important;');
            }
            
        } else {
            // Show sidebar
            wrapper.classList.remove('toggled');
            if (sidebar) sidebar.classList.remove('collapsed');
            
            // Restore navbar position
            if (navbar) {
                navbar.style.left = '250px';
                navbar.style.width = 'calc(100% - 250px)';
                navbar.style.paddingLeft = '20px';
            }
            
            // Restore content area
            if (pageContentWrapper) {
                pageContentWrapper.style.marginLeft = '250px';
                pageContentWrapper.style.width = 'calc(100% - 250px)';
                pageContentWrapper.style.paddingLeft = '20px';
                pageContentWrapper.style.paddingRight = '20px';
            }
            
            // Hide the fixed toggle button when sidebar is visible
            if (fixedToggleContainer) {
                fixedToggleContainer.style.display = 'none';
                fixedToggleContainer.setAttribute('style', 'position: fixed !important; left: 15px !important; top: 15px !important; z-index: 9999 !important; display: none !important;');
            }
        }
        
        // Force adjust content that might be cut off
        setTimeout(adjustDashboardContent, 100);
        
        // Update localStorage
        localStorage.setItem('sidebarCollapsed', isCollapsed);
        console.log('Sidebar toggled, collapsed state:', isCollapsed);
    }
    
    // Initialize sidebar state
    if (wrapper) {
        // Check if the sidebar should be collapsed based on localStorage
        const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        
        // Apply initial state with a slight delay to ensure DOM is ready
        setTimeout(() => {
            updateLayout(sidebarCollapsed);
        }, 100);
    }
    
    // Add click handler to main menu toggle
    if (menuToggle && wrapper) {
        menuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            const isCollapsing = !wrapper.classList.contains('toggled');
            updateLayout(isCollapsing);
        });
    }
    
    // Add click handler to fixed toggle
    if (fixedToggle) {
        fixedToggle.addEventListener('click', function(e) {
            e.preventDefault();
            const isCollapsed = wrapper.classList.contains('toggled');
            updateLayout(!isCollapsed);
        });
    }
    
    // Mobile sidebar close button
    const sidebarClose = document.getElementById('sidebar-close');
    if (sidebarClose && wrapper) {
        sidebarClose.addEventListener('click', function() {
            updateLayout(false);
        });
    }
    
    // Keyboard shortcut for sidebar toggle (Ctrl+B)
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'b') {
            e.preventDefault();
            if (wrapper) {
                const isCollapsing = !wrapper.classList.contains('toggled');
                updateLayout(isCollapsing);
            }
        }
    });
    
    // Handle window resize
    window.addEventListener('resize', function() {
        const isCollapsed = wrapper.classList.contains('toggled');
        
        if (window.innerWidth <= 768) {
            if (navbar) {
                navbar.style.left = '0';
                navbar.style.width = '100%';
                navbar.style.paddingLeft = window.innerWidth < 576 ? '55px' : '65px';
            }
            
            if (pageContentWrapper) {
                pageContentWrapper.style.marginLeft = '0';
                pageContentWrapper.style.width = '100%';
                pageContentWrapper.style.paddingLeft = '50px';
            }
            
            if (fixedToggleContainer) {
                fixedToggleContainer.style.left = window.innerWidth < 576 ? '5px' : '10px';
            }
        } else {
            if (!isCollapsed) {
                if (navbar) {
                    navbar.style.left = '250px';
                    navbar.style.width = 'calc(100% - 250px)';
                    navbar.style.paddingLeft = '20px';
                }
                
                if (pageContentWrapper) {
                    pageContentWrapper.style.marginLeft = '250px';
                    pageContentWrapper.style.width = 'calc(100% - 250px)';
                }
            } else {
                if (pageContentWrapper) {
                    pageContentWrapper.style.paddingLeft = '60px';
                }
                
                // Ensure toggle button is visible on all screen sizes
                if (fixedToggleContainer) {
                    fixedToggleContainer.style.display = 'block';
                }
            }
        }
        
        // Adjust content when resizing
        adjustDashboardContent();
    });
    
    // Run an initial content adjustment
    setTimeout(adjustDashboardContent, 500);
});
