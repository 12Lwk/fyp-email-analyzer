document.addEventListener('DOMContentLoaded', function() {
    const googleLoginBtn = document.querySelector('.google-login');
    const uploadExcelBtn = document.querySelector('.upload-excel');
    const uploadExcelInput = document.getElementById('uploadExcel');

    // Handle Gmail login
    googleLoginBtn.addEventListener('click', async function(e) {
        e.preventDefault();
        
        try {
            // Show loading state
            googleLoginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
            googleLoginBtn.disabled = true;
            
            console.log('Attempting to authenticate with Gmail...');
            
            // Step 1: Authenticate with Gmail
            const authResponse = await fetch('/gmail/auth/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                credentials: 'same-origin'
            });
            
            if (!authResponse.ok) {
                const errorData = await authResponse.json();
                throw new Error(errorData.error || 'Failed to authenticate with Gmail');
            }

            const authData = await authResponse.json();
            console.log('Auth response:', authData);
            
            if (authData.status === 'success') {
                // Update button state
                googleLoginBtn.innerHTML = '<i class="fas fa-check"></i> Connected!';
                
                // Redirect to the auth URL if provided
                if (authData.auth_url) {
                    window.location.href = authData.auth_url;
                } else {
                    throw new Error('No authentication URL provided');
                }
            } else {
                throw new Error(authData.message || 'Gmail authentication failed');
            }
        } catch (error) {
            console.error('Error:', error);
            googleLoginBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
            showError(error.message || 'An error occurred during Gmail authentication');
        } finally {
            // Reset button state after 3 seconds if still on the page
            setTimeout(() => {
                if (document.contains(googleLoginBtn)) {
                    googleLoginBtn.innerHTML = '<i class="fab fa-google"></i> Sign in with Gmail';
                    googleLoginBtn.disabled = false;
                }
            }, 3000);
        }
    });

    // Handle Excel file upload
    uploadExcelBtn.addEventListener('click', function(e) {
        e.preventDefault();
        uploadExcelInput.click();
    });

    uploadExcelInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            console.log('Excel file selected:', file.name);
            // Add your file upload logic here
        }
    });
});
