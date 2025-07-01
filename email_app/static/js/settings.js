document.addEventListener('DOMContentLoaded', function() {
    // Profile Picture Upload
    const profileImage = document.getElementById('profileImage');
    const profileImageInput = document.getElementById('profileImageInput');
    const changeProfilePicture = document.getElementById('changeProfilePicture');
    const sidebarUserAvatar = document.getElementById('sidebarUserAvatar');

    // Debug check of elements
    console.log('Profile Image found:', !!profileImage);
    console.log('Profile Image Input found:', !!profileImageInput);
    console.log('Change Profile Picture button found:', !!changeProfilePicture);
    console.log('Sidebar User Avatar found:', !!sidebarUserAvatar);

    if (changeProfilePicture) {
        changeProfilePicture.addEventListener('click', () => {
            profileImageInput.click();
        });
    }

    if (profileImageInput) {
        profileImageInput.addEventListener('change', function(e) {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    console.log('Image loaded by FileReader');
                    
                    // Update both profile picture and sidebar avatar
                    if (profileImage) profileImage.src = e.target.result;
                    if (sidebarUserAvatar) sidebarUserAvatar.src = e.target.result;
                    
                    // Save to localStorage
                    localStorage.setItem('profileImage', e.target.result);
                    console.log('Profile image saved to localStorage');
                    
                    showNotification('Profile picture updated successfully!', 'success');
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }

    // Profile Form
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const displayName = document.getElementById('displayName').value;
            const timeZone = document.getElementById('timeZone').value;

            // Update sidebar display name
            document.getElementById('sidebarDisplayName').textContent = displayName;

            // Save to localStorage
            const profileSettings = {
                displayName: displayName,
                timeZone: timeZone
            };
            localStorage.setItem('profileSettings', JSON.stringify(profileSettings));
            showNotification('Profile settings saved successfully!', 'success');
        });
    }

    // Email Settings Form
    const emailSettingsForm = document.getElementById('emailSettingsForm');
    if (emailSettingsForm) {
        emailSettingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const settings = {
                showSnippets: document.getElementById('showSnippets').checked,
                showAttachments: document.getElementById('showAttachments').checked,
                confirmDelete: document.getElementById('confirmDelete').checked,
                spellCheck: document.getElementById('spellCheck').checked,
                autoSave: document.getElementById('autoSave').checked,
                defaultFont: document.getElementById('defaultFont').value
            };
            localStorage.setItem('emailSettings', JSON.stringify(settings));
            showNotification('Email settings saved successfully!', 'success');
        });
    }

    // Display Settings Form
    const displaySettingsForm = document.getElementById('displaySettingsForm');
    if (displaySettingsForm) {
        displaySettingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const settings = {
                showLabels: document.getElementById('showLabels').checked,
                compactView: document.getElementById('compactView').checked,
                defaultPageSize: document.getElementById('defaultPageSize').value,
                theme: document.querySelector('input[name="theme"]:checked').id
            };
            localStorage.setItem('displaySettings', JSON.stringify(settings));
            applyTheme(settings.theme);
            showNotification('Display settings saved successfully!', 'success');
        });

        // Handle theme changes
        const themeInputs = document.querySelectorAll('input[name="theme"]');
        themeInputs.forEach(input => {
            input.addEventListener('change', function() {
                applyTheme(this.id);
            });
        });
    }

    // Notification Settings Form
    const notificationSettingsForm = document.getElementById('notificationSettingsForm');
    if (notificationSettingsForm) {
        notificationSettingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const settings = {
                newEmailNotif: document.getElementById('newEmailNotif').checked,
                mentionNotif: document.getElementById('mentionNotif').checked,
                importantNotif: document.getElementById('importantNotif').checked,
                soundEnabled: document.getElementById('soundEnabled').checked,
                desktopNotif: document.getElementById('desktopNotif').checked
            };
            localStorage.setItem('notificationSettings', JSON.stringify(settings));
            showNotification('Notification settings saved successfully!', 'success');

            if (settings.desktopNotif) {
                requestNotificationPermission();
            }
        });
    }

    // Load saved settings
    loadSavedSettings();
});

// Apply theme
function applyTheme(themeId) {
    const body = document.body;
    body.classList.remove('theme-light', 'theme-dark');
    
    switch (themeId) {
        case 'themeLight':
            body.classList.add('theme-light');
            break;
        case 'themeDark':
            body.classList.add('theme-dark');
            break;
        case 'themeSystem':
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                body.classList.add('theme-dark');
            } else {
                body.classList.add('theme-light');
            }
            break;
    }
}

// Load saved settings
function loadSavedSettings() {
    // Load profile settings
    const profileSettings = JSON.parse(localStorage.getItem('profileSettings') || '{}');
    const profileImage = localStorage.getItem('profileImage');
    
    if (profileSettings.displayName) {
        document.getElementById('displayName').value = profileSettings.displayName;
        document.getElementById('sidebarDisplayName').textContent = profileSettings.displayName;
    }
    if (profileSettings.timeZone) {
        document.getElementById('timeZone').value = profileSettings.timeZone;
    }
    if (profileImage) {
        document.getElementById('profileImage').src = profileImage;
        document.getElementById('sidebarUserAvatar').src = profileImage;
    }

    // Load email settings
    const emailSettings = JSON.parse(localStorage.getItem('emailSettings') || '{}');
    if (Object.keys(emailSettings).length > 0) {
        document.getElementById('showSnippets').checked = emailSettings.showSnippets;
        document.getElementById('showAttachments').checked = emailSettings.showAttachments;
        document.getElementById('confirmDelete').checked = emailSettings.confirmDelete;
        document.getElementById('spellCheck').checked = emailSettings.spellCheck;
        document.getElementById('autoSave').checked = emailSettings.autoSave;
        document.getElementById('defaultFont').value = emailSettings.defaultFont;
    }

    // Load display settings
    const displaySettings = JSON.parse(localStorage.getItem('displaySettings') || '{}');
    if (Object.keys(displaySettings).length > 0) {
        document.getElementById('showLabels').checked = displaySettings.showLabels;
        document.getElementById('compactView').checked = displaySettings.compactView;
        document.getElementById('defaultPageSize').value = displaySettings.defaultPageSize;
        if (displaySettings.theme) {
            document.getElementById(displaySettings.theme).checked = true;
            applyTheme(displaySettings.theme);
        }
    }

    // Load notification settings
    const notificationSettings = JSON.parse(localStorage.getItem('notificationSettings') || '{}');
    if (Object.keys(notificationSettings).length > 0) {
        document.getElementById('newEmailNotif').checked = notificationSettings.newEmailNotif;
        document.getElementById('mentionNotif').checked = notificationSettings.mentionNotif;
        document.getElementById('importantNotif').checked = notificationSettings.importantNotif;
        document.getElementById('soundEnabled').checked = notificationSettings.soundEnabled;
        document.getElementById('desktopNotif').checked = notificationSettings.desktopNotif;
    }
}

// Request notification permission
function requestNotificationPermission() {
    if ('Notification' in window) {
        Notification.requestPermission();
    }
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
