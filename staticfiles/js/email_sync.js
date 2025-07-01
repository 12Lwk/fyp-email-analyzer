// Email synchronization handler
class EmailSyncHandler {
    constructor() {
        this.syncInProgress = false;
        this.checkInterval = null;
        this.successSound = new Audio('/static/sounds/sync_complete.mp3');
    }

    async initializeSync() {
        try {
            const response = await fetch('/email/sync/initialize/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.status === 'redirect') {
                // Need Gmail authentication
                window.location.href = data.url;
                return;
            }

            if (data.status === 'success') {
                // Start checking sync status
                this.startStatusCheck();
                return true;
            }

            throw new Error(data.message || 'Failed to initialize sync');

        } catch (error) {
            console.error('Sync initialization error:', error);
            this.showError('Failed to start email synchronization. Please try again.');
            return false;
        }
    }

    async checkSyncStatus() {
        try {
            const response = await fetch('/email/sync/status/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.status === 'success') {
                if (data.completed) {
                    this.syncCompleted();
                    return true;
                }
                return false;
            }

            throw new Error(data.message || 'Failed to check sync status');

        } catch (error) {
            console.error('Sync status check error:', error);
            this.stopStatusCheck();
            this.showError('Failed to check sync status. Please refresh the page.');
            return false;
        }
    }

    startStatusCheck() {
        this.syncInProgress = true;
        this.showProgress();
        
        // Check status every 2 seconds
        this.checkInterval = setInterval(() => {
            this.checkSyncStatus();
        }, 2000);
    }

    stopStatusCheck() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
        this.syncInProgress = false;
    }

    syncCompleted() {
        this.stopStatusCheck();
        this.hideProgress();
        this.playSuccessSound();
        this.showSuccess('Email synchronization completed successfully!');
        
        // Redirect to dashboard after a short delay
        setTimeout(() => {
            window.location.href = '/email/dashboard/';
        }, 1500);
    }

    showProgress() {
        // Show progress indicator (implement based on your UI)
        const progressElement = document.getElementById('sync-progress');
        if (progressElement) {
            progressElement.style.display = 'block';
        }
    }

    hideProgress() {
        // Hide progress indicator
        const progressElement = document.getElementById('sync-progress');
        if (progressElement) {
            progressElement.style.display = 'none';
        }
    }

    showError(message) {
        // Show error message (implement based on your UI)
        const errorElement = document.getElementById('sync-error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }

    showSuccess(message) {
        // Show success message (implement based on your UI)
        const successElement = document.getElementById('sync-success');
        if (successElement) {
            successElement.textContent = message;
            successElement.style.display = 'block';
        }
    }

    playSuccessSound() {
        this.successSound.play().catch(error => {
            console.warn('Could not play success sound:', error);
        });
    }
}

// Export the handler
export const emailSyncHandler = new EmailSyncHandler(); 