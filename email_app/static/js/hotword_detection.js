// Voice command system with improved state management
document.addEventListener('DOMContentLoaded', function() {
    // Single instance of recognition
    let recognition = null;
    let isListening = false;
    let commandTimeout = null;

    // Helper function to get email ID (similar to inbox_email_detail.js)
    function getVoiceCommandEmailId() {
        const path = window.location.pathname;
        const regex = /\/inbox_email_detail\/([0-9a-f]+)\/?$/i;
        const match = path.match(regex);
        if (match && match[1]) {
            return match[1];
        }
        // Fallback if needed
        const segments = path.split('/').filter(Boolean);
        for (let i = segments.length - 1; i >= 0; i--) {
            if (/^[a-f0-9]{8,}$/i.test(segments[i])) return segments[i];
        }
        console.warn('Could not determine email ID for voice command.');
        return null;
    }

    // Define voice commands
    const VOICE_COMMANDS = {
        'use_suggested_reply': {
            phrases: ['use suggested reply', 'use suggested email', 'use the suggested reply', 'use the suggested email', 'use suggested e-mail', 'you suggested reply', 'you suggested email', 'suggested reply'],
            action: function() {
                console.log('[hotword] Executing use_suggested_reply action');

                try {
                    // First try to click the actual "Use Suggested Reply" button if it exists
                    const suggestButton = document.getElementById('useSuggestedReplyBtn');
                    if (suggestButton) {
                        console.log('[hotword] Found useSuggestedReplyBtn, clicking it');
                        suggestButton.click();
                        return;
                    }

                    // If button not found, try to get the suggested reply content
                    let suggestedReply = '';
                    let source = '';
                    
                    // Try to get from suggestedReply div first (this is the most reliable source)
                    const suggestedReplyDiv = document.getElementById('suggestedReply');
                    if (suggestedReplyDiv && suggestedReplyDiv.textContent.trim()) {
                        console.log('[hotword] Found suggested reply in suggestedReply div');
                        suggestedReply = cleanEmailContent(suggestedReplyDiv.textContent.trim());
                        source = 'suggestedReply div';
                    }

                    // Only try other sources if we couldn't find it in the div
                    if (!suggestedReply) {
                        // Try window.currentEmailData
                        if (window.currentEmailData && window.currentEmailData.suggested_reply) {
                            console.log('[hotword] Found suggested reply in currentEmailData');
                            suggestedReply = cleanEmailContent(window.currentEmailData.suggested_reply);
                            source = 'currentEmailData';
                        }

                        // Try analysis results
                        if (!suggestedReply) {
                            const analysisResults = document.querySelector('.ai-analysis-results');
                            if (analysisResults) {
                                const suggestedReplyElement = analysisResults.querySelector('.suggested-reply');
                                if (suggestedReplyElement) {
                                    console.log('[hotword] Found suggested reply in analysis results');
                                    suggestedReply = cleanEmailContent(suggestedReplyElement.textContent);
                                    source = 'analysis results';
                                }
                            }
                        }
                    }

                    // Debug log the current state
                    console.log('[hotword] Suggested reply search results:', {
                        found: !!suggestedReply,
                        source: source || 'none',
                        suggestedReplyDiv: document.getElementById('suggestedReply') ? 'exists' : 'missing',
                        suggestedReplyBtn: document.getElementById('useSuggestedReplyBtn') ? 'exists' : 'missing',
                        currentEmailData: window.currentEmailData ? 'exists' : 'missing',
                        analysisResults: document.querySelector('.ai-analysis-results') ? 'exists' : 'missing'
                    });

                    if (!suggestedReply) {
                        console.error('[hotword] No suggested reply found in any source');
                        showFeedback('No suggested reply available. Try generating an analysis first.', 'error');
                        return;
                    }

                    console.log('[hotword] Using suggested reply:', suggestedReply);

                    // Get the current email data
                    const email = window.currentEmailData;
                    if (!email) {
                        showFeedback('Could not find email data. Please try refreshing the page.', 'error');
                        return;
                    }

                    // Open compose modal
                    const modalElement = document.getElementById('composeModal');
                    if (!modalElement) {
                        showFeedback('Compose modal not found. Please try refreshing the page.', 'error');
                        return;
                    }

                    // Close any existing modals first
                    const existingModal = bootstrap.Modal.getInstance(modalElement);
                    if (existingModal) {
                        existingModal.hide();
                        // Wait a bit before showing new modal
                        setTimeout(() => {
                            showComposeWithSuggestedReply(modalElement, email, suggestedReply);
                        }, 300);
                    } else {
                        showComposeWithSuggestedReply(modalElement, email, suggestedReply);
                    }

                } catch (error) {
                    console.error('[hotword] Error using suggested reply:', error);
                    showFeedback('Error using suggested reply: ' + error.message, 'error');
                }
            }
        },
        'read_suggested_reply': {
            phrases: ['read suggested reply', 'read suggested email', 'read the suggested reply', 'read the suggested email'],
            action: function() {
                const suggestedReply = document.getElementById('suggestedReply')?.textContent;
                if (suggestedReply) {
                    speakText(suggestedReply);
                    showFeedback('Reading suggested reply...', 'info');
                } else {
                    showFeedback('No suggested reply available to read', 'warning');
                }
            }
        },
        'read': { 
            phrases: ['read', 'read email', 'read this', 'read this email'],
            action: function() {
                const emailContent = document.querySelector('.email-content')?.textContent || 'No content available';
                const emailSubject = document.getElementById('emailSubject')?.textContent || 'No subject';
                speakText(`Email subject: ${emailSubject}. Content: ${emailContent}`);
                showFeedback('Reading email content...', 'info');
            }
        },
        'reply': {
            phrases: ['reply', 'reply to this email', 'reply to email', 'reply to this message', 'reply to message', 'reply to this e-mail'],
            action: function() {
                console.log('[hotword] Executing reply action');
                const emailId = getVoiceCommandEmailId();
                if (!emailId) {
                    showFeedback('Could not determine email ID for reply', 'error');
                    return;
                }

                try {
                    // Get the current email data
                    const email = window.currentEmailData;
                    if (!email) {
                        showFeedback('Could not find email data', 'error');
                        return;
                    }

                    // Open compose modal
                    const modalElement = document.getElementById('composeModal');
                    if (!modalElement) {
                        showFeedback('Compose modal not found', 'error');
                        return;
                    }

                    const composeModal = new bootstrap.Modal(modalElement);
                    composeModal.show();

                    // Set up the reply
                    modalElement.addEventListener('shown.bs.modal', function onModalShown() {
                        modalElement.removeEventListener('shown.bs.modal', onModalShown);

                        // Set recipient
                        const toField = document.getElementById('emailTo');
                        if (toField) {
                            toField.value = email.sender_email || email.sender || '';
                        }

                        // Set subject
                        const subjectField = document.getElementById('emailSubject');
                        if (subjectField) {
                            const subject = email.subject || 'No Subject';
                            subjectField.value = subject.startsWith('Re:') ? subject : `Re: ${subject}`;
                        }

                        // Set body with cleaned content
                        const bodyField = document.getElementById('emailBody');
                        if (bodyField) {
                            bodyField.value = formatEmailForReply(email);
                            bodyField.focus();
                        }
                    });

                    showFeedback('Replying to email...', 'info');
                } catch (error) {
                    console.error('[hotword] Error in reply action:', error);
                    showFeedback('Error preparing reply: ' + error.message, 'error');
                }
            }
        },
        'go_back': {
            phrases: ['go back', 'back to inbox', 'return to inbox', 'inbox'],
            action: function() {
                console.log('[hotword] Executing go_back action...');
                if (typeof handleBackButtonClick === 'function') {
                    showFeedback('Going back to inbox...', 'info');
                     console.log('[hotword] Calling handleBackButtonClick function...');
                    handleBackButtonClick();
                } else {
                     console.warn('[hotword] handleBackButtonClick function not found. Attempting button click fallback.');
                     const backButton = document.getElementById('backToInbox'); // Use ID
                     if(backButton){
                        showFeedback('Going back to inbox (via button click)...', 'info');
                        console.log('[hotword] Found back button, clicking...');
                        backButton.click();
                     } else {
                        showFeedback('Back function/button is not available.', 'error');
                        console.error('[hotword] Could not find handleBackButtonClick function or button.');
                     }
                }
            }
        },
        'send_email': {
            phrases: ['send this email', 'send email', 'send the email', 'send this reply', 'send reply', 'send the reply', 'send suggested email', 'send suggested reply', 'send this e-mail', 'send e-mail'],
            action: function() {
                console.log('[hotword] Executing send email action');

                try {
                    // First try to find the send button
                    const sendBtn = document.querySelector('#sendEmailBtn');
                    if (!sendBtn) {
                        console.error('[hotword] Send button not found');
                        showFeedback('Could not find send button', 'error');
                        return;
                    }

                    console.log('[hotword] Found send button:', sendBtn);

                    // Get the form data before sending
                    const form = document.querySelector('#composeForm');
                    if (!form) {
                        console.error('[hotword] Form not found');
                        showFeedback('Could not find email form', 'error');
                        return;
                    }

                    // Get form fields
                    const toField = form.querySelector('#emailTo');
                    const subjectField = form.querySelector('#emailSubject');
                    const bodyField = form.querySelector('#emailBody');

                    // Validate required fields
                    let isValid = true;
                    let errorMessage = '';

                    if (!toField || !toField.value.trim()) {
                        isValid = false;
                        errorMessage = 'Recipient email is required';
                    }

                    if (!subjectField || !subjectField.value.trim()) {
                        isValid = false;
                        errorMessage = errorMessage || 'Subject is required';
                    }

                    if (!bodyField || !bodyField.value.trim()) {
                        isValid = false;
                        errorMessage = errorMessage || 'Message body is required';
                    }

                    if (!isValid) {
                        showFeedback(errorMessage, 'error');
                        return;
                    }

                    // Simply trigger the send button click
                    console.log('[hotword] Triggering send button click');
                    sendBtn.click();
                    showFeedback('Sending email...', 'info');

                } catch (error) {
                    console.error('[hotword] Error in send email action:', error);
                    showFeedback('Error sending email: ' + error.message, 'error');
                }
            }
        },
        'close_email': {
            phrases: ['close this email', 'close email', 'close the email', 'close this reply', 'close reply', 'close the reply', 'cancel email', 'cancel reply', 'close this e-mail'],
            action: function() {
                console.log('Executing close email action');
                
                let closeBtn = null;

                // Method 1: Try finding the Cancel button by class and text
                const buttons = Array.from(document.querySelectorAll('button.btn.btn-secondary'));
                console.log('Found secondary buttons:', buttons.length);
                
                for (const btn of buttons) {
                    console.log('Checking button:', btn.textContent, btn.innerHTML);
                    if (btn.textContent && btn.textContent.trim() === 'Cancel') {
                        closeBtn = btn;
                        break;
                    }
                }

                // Method 2: Try finding the modal close button
                if (!closeBtn) {
                    closeBtn = document.querySelector('.btn-close[data-bs-dismiss="modal"]');
                }

                // Method 3: Try finding by aria-label
                if (!closeBtn) {
                    closeBtn = document.querySelector('button[aria-label="Close"]');
                }

                if (closeBtn) {
                    console.log('Found close button:', closeBtn);
                    try {
                        // Try clicking the button
                        closeBtn.click();
                        
                        // Also try closing the modal directly
                        const modal = document.querySelector('.modal.show');
                        if (modal) {
                            const bsModal = bootstrap.Modal.getInstance(modal);
                            if (bsModal) {
                                bsModal.hide();
                            }
                        }
                        
                        showFeedback('Closing email...', 'info');
                    } catch (error) {
                        console.error('Error closing email:', error);
                        showFeedback('Error closing email', 'error');
                    }
                    return;
                }

                console.error('Could not find close button');
                showFeedback('Could not find the close button', 'error');
                
                // Debug log all buttons
                console.log('All available buttons:', 
                    Array.from(document.querySelectorAll('button')).map(b => ({
                        text: b.textContent?.trim() || '',
                        class: b.className,
                        id: b.id,
                        type: b.type,
                        html: b.innerHTML
                    }))
                );
            }
        },
        'forward': {
            phrases: ['forward', 'forward email', 'forward this email'],
            action: function() {
                const forwardBtn = document.querySelector('.forward-btn');
                if (forwardBtn) {
                    forwardBtn.click();
                    showFeedback('Opening forward form...', 'info');
                }
            }
        },
        'analyze': {
            phrases: ['analyze', 'analyse', 'analyze email', 'analyse email', 'analyze this email', 'analyse this email', 'analysis'],
            action: function() {
                console.log('Triggering analysis...');
                const analyzeBtn = document.getElementById('generateAnalysisBtn');
                if (analyzeBtn) {
                    console.log('Analysis button found, clicking...');
                    analyzeBtn.click();
                    showFeedback('Generating email analysis...', 'info');
                    
                    // Show the analysis section
                    const analysisSection = document.querySelector('.ai-analysis-section');
                    if (analysisSection) {
                        analysisSection.scrollIntoView({ behavior: 'smooth' });
                    }
                } else {
                    console.error('Analysis button not found');
                    showFeedback('Error: Could not find analysis button', 'error');
                }
            }
        }
    };

    // Add this helper function
    function showComposeWithSuggestedReply(modalElement, email, suggestedReply) {
        // Show the modal
        const modal = new bootstrap.Modal(modalElement);
        modal.show();

        // Wait for modal to be fully shown before setting values
        modalElement.addEventListener('shown.bs.modal', function () {
            try {
                // Set the recipient
                const toField = document.getElementById('compose-to');
                if (toField) {
                    toField.value = email.sender || '';
                }

                // Set the subject - prepend "Re:" if not already there
                const subjectField = document.getElementById('compose-subject');
                if (subjectField) {
                    let subject = email.subject || '';
                    if (!subject.toLowerCase().startsWith('re:')) {
                        subject = 'Re: ' + subject;
                    }
                    subjectField.value = subject;
                }

                // Set the suggested reply in the body
                const bodyField = document.getElementById('compose-body');
                if (bodyField) {
                    bodyField.value = suggestedReply;
                    
                    // Trigger input event to activate any listeners
                    const event = new Event('input', {
                        bubbles: true,
                        cancelable: true,
                    });
                    bodyField.dispatchEvent(event);
                }

                // Show success feedback
                showFeedback('Suggested reply loaded in compose window', 'success');

            } catch (error) {
                console.error('[hotword] Error setting compose values:', error);
                showFeedback('Error setting compose values: ' + error.message, 'error');
            }
        }, { once: true }); // Remove listener after first use
    }

    // Modify the command processing function
    function processRecognizedCommand(transcript) {
        // Clean the transcript thoroughly
        const command = transcript.toLowerCase().trim().replace(/[.,!?]/g, '');
        console.log(`[hotword] Processing cleaned command: "${command}"`);

        // Define commands object
        const COMMANDS = {
            USE_SUGGESTED_REPLY: VOICE_COMMANDS.use_suggested_reply.phrases,
            READ_SUGGESTED_REPLY: VOICE_COMMANDS.read_suggested_reply.phrases,
            SEND_EMAIL: VOICE_COMMANDS.send_email.phrases,
            CLOSE_EMAIL: VOICE_COMMANDS.close_email.phrases,
            READ: VOICE_COMMANDS.read.phrases,
            REPLY: VOICE_COMMANDS.reply.phrases,
            FORWARD: VOICE_COMMANDS.forward.phrases,
            ANALYZE: VOICE_COMMANDS.analyze.phrases,
            GO_BACK: VOICE_COMMANDS.go_back.phrases
        };

        // Check for suggested reply first (most specific)
        if (COMMANDS.USE_SUGGESTED_REPLY.some(phrase => {
            const matches = command.includes(phrase);
            console.log(`[hotword] Checking "${command}" against "${phrase}": ${matches}`);
            return matches;
        })) {
            console.log(`[hotword] Matched USE_SUGGESTED_REPLY`);
            VOICE_COMMANDS.use_suggested_reply.action();
            return;
        }

        // Check for read suggested reply next
        if (COMMANDS.READ_SUGGESTED_REPLY.some(phrase => command.includes(phrase))) {
            console.log(`[hotword] Matched READ_SUGGESTED_REPLY`);
            VOICE_COMMANDS.read_suggested_reply.action();
            return;
        }

        // Then check other commands - but make sure we're not matching partial "reply" from "suggested reply"
        if (!command.includes('suggested') && !command.includes('suggest')) {
            if (COMMANDS.REPLY.some(phrase => command === phrase)) {
                console.log(`[hotword] Matched exact REPLY`);
                VOICE_COMMANDS.reply.action();
                return;
            }
        }

        // Check remaining commands
        if (COMMANDS.GO_BACK.some(phrase => command === phrase)) {
            console.log(`[hotword] Matched GO_BACK`);
            VOICE_COMMANDS.go_back.action();
        } else if (COMMANDS.SEND_EMAIL.some(cmd => command.includes(cmd))) {
            console.log(`[hotword] Matched SEND_EMAIL`);
            VOICE_COMMANDS.send_email.action();
        } else if (COMMANDS.CLOSE_EMAIL.some(cmd => command.includes(cmd))) {
            console.log(`[hotword] Matched CLOSE_EMAIL`);
            VOICE_COMMANDS.close_email.action();
        } else if (COMMANDS.READ.some(cmd => command.includes(cmd))) {
            console.log(`[hotword] Matched READ`);
            VOICE_COMMANDS.read.action();
        } else if (COMMANDS.FORWARD.some(cmd => command.includes(cmd))) {
            console.log(`[hotword] Matched FORWARD`);
            VOICE_COMMANDS.forward.action();
        } else if (COMMANDS.ANALYZE.some(cmd => command.includes(cmd))) {
            console.log(`[hotword] Matched ANALYZE`);
            VOICE_COMMANDS.analyze.action();
        } else {
            console.log('[hotword] Command did not match any known phrases');
            showFeedback(`Command not recognized: "${transcript}". Try "Reply", "Forward", "Go back", etc.`, 'warning');
        }
    }

    // Initialize speech recognition
    function initSpeechRecognition() {
        // Always clean up existing instance first
        cleanupRecognition();

        try {
            // Check browser support
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                showFeedback('Speech recognition is not supported in this browser. Please use Chrome or Edge.', 'error');
                return false;
            }

            // Create new instance
            recognition = new SpeechRecognition();
            recognition.continuous = true; // Enable continuous recognition
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            // Setup event handlers
            recognition.onstart = function() {
                console.log('[hotword] Recognition started');
                isListening = true;
                updateButtonState(true);
                showFeedback('Listening continuously... Click button to stop', 'info');
            };

            recognition.onresult = function(event) {
                // Get the latest result
                const lastResultIndex = event.results.length - 1;
                const transcript = event.results[lastResultIndex][0].transcript;
                console.log('[hotword] Recognized:', transcript);
                processRecognizedCommand(transcript);
            };

            recognition.onerror = function(event) {
                console.error('[hotword] Recognition error:', event.error);
                
                let message = 'Error with voice recognition. ';
                switch (event.error) {
                    case 'not-allowed':
                        message += 'Please allow microphone access.';
                        break;
                    case 'no-speech':
                        // Don't show error for no speech in continuous mode
                        return;
                    case 'network':
                        message += 'Network error. Please check your connection.';
                        break;
                    default:
                        message += 'Please try again.';
                }
                
                showFeedback(message, 'error');
                
                // Only cleanup if it's a fatal error
                if (event.error === 'not-allowed' || event.error === 'network') {
                    cleanupRecognition();
                }
            };

            recognition.onend = function() {
                console.log('[hotword] Recognition ended');
                
                // Restart recognition if we're still supposed to be listening
                if (isListening) {
                    console.log('[hotword] Restarting recognition...');
                    try {
                        recognition.start();
                    } catch (error) {
                        console.error('[hotword] Error restarting recognition:', error);
                        cleanupRecognition();
                    }
                } else {
                    cleanupRecognition();
                }
            };

            return true;
        } catch (error) {
            console.error('[hotword] Error initializing speech recognition:', error);
            showFeedback('Failed to initialize speech recognition', 'error');
            return false;
        }
    }

    // Clean up recognition instance
    function cleanupRecognition() {
        if (recognition) {
            try {
                recognition.abort();
            } catch (e) {
                console.log('Cleaning up recognition instance:', e);
            }
            recognition = null;
        }
        
        if (commandTimeout) {
            clearTimeout(commandTimeout);
            commandTimeout = null;
        }
        
        isListening = false;
        updateButtonState(false);
    }

    // Start listening
    function startListening() {
        console.log('[hotword] Starting listening...');
        if (isListening) {
            stopListening();
            return;
        }

        // Always initialize a fresh instance
        if (!initSpeechRecognition()) {
            return;
        }

        try {
            recognition.start();
            showFeedback('Listening continuously... Say commands like "read this email"', 'info');
            
            // Remove the timeout since we want continuous listening
            if (commandTimeout) {
                clearTimeout(commandTimeout);
                commandTimeout = null;
            }
        } catch (error) {
            console.error('[hotword] Error starting recognition:', error);
            showFeedback('Error starting voice recognition. Please try again.', 'error');
            cleanupRecognition();
        }
    }

    // Stop listening
    function stopListening() {
        console.log('[hotword] Stopping listening...');
        showFeedback('Voice recognition stopped', 'info');
        isListening = false; // Set this first so onend doesn't restart
        if (recognition) {
            try {
                recognition.stop();
            } catch (error) {
                console.error('[hotword] Error stopping recognition:', error);
            }
        }
        cleanupRecognition();
    }

    // UI feedback functions
    function showFeedback(message, type = 'info') {
        const feedbackElement = document.getElementById('voiceCommandStatus');
        if (feedbackElement) {
            feedbackElement.textContent = message;
            feedbackElement.className = `alert alert-${type}`;
            feedbackElement.style.display = 'block';

            setTimeout(() => {
                feedbackElement.style.display = 'none';
            }, 5000);
        }
    }

    function updateButtonState(listening) {
        const btn = document.getElementById('voiceCommandBtn');
        if (btn) {
            if (listening) {
                btn.classList.add('listening');
                btn.innerHTML = '<i class="fas fa-microphone"></i> Listening...';
            } else {
                btn.classList.remove('listening');
                btn.innerHTML = '<i class="fas fa-microphone"></i> Voice Command';
            }
        }
    }

    // Text-to-speech function
    function speakText(text) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel(); // Stop any ongoing speech
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'en-US';
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
        }
    }

    // Initialize voice command button
    function initializeVoiceCommandButton() {
        console.log('[hotword] Initializing voice command button...');
        const voiceCommandBtn = document.getElementById('voiceCommandBtn');
        if (voiceCommandBtn) {
            // Remove any existing listeners
            const newBtn = voiceCommandBtn.cloneNode(true);
            voiceCommandBtn.parentNode.replaceChild(newBtn, voiceCommandBtn);
            
            // Add our listener
            newBtn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('[hotword] Voice command button clicked');
                if (isListening) {
                    stopListening();
                } else {
                    startListening();
                }
            });

            console.log('[hotword] Voice command button initialized');
        } else {
            console.error('[hotword] Voice command button not found in DOM');
        }
    }

    // Initialize when document is ready
    initializeVoiceCommandButton();

    // Clean up on page unload
    window.addEventListener('beforeunload', cleanupRecognition);

    // Add visual feedback styles
    const style = document.createElement('style');
    style.textContent = `
        .listening {
            background-color: #dc3545 !important;
            color: white !important;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        #voiceCommandStatus {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1050;
            max-width: 300px;
        }
    `;
    document.head.appendChild(style);

    // Add these utility functions at the top level
    function cleanEmailContent(content) {
        if (!content) return '';
        
        console.log('[hotword] Cleaning email content');
        
        try {
            // Remove HTML tags and decode entities
            let cleaned = content
                // Remove DOCTYPE, xml declarations, and meta tags
                .replace(/<\?xml[^>]*\?>/g, '')
                .replace(/<!DOCTYPE[^>]*>/g, '')
                .replace(/<meta[^>]*>/g, '')
                
                // Remove style tags and their content
                .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
                
                // Remove CSS rules
                .replace(/@media[^{]*{[^}]*}/g, '')
                .replace(/\.[^{]*{[^}]*}/g, '')
                
                // Replace common HTML elements with newlines
                .replace(/<\/(div|p|br|tr|td|th)>/gi, '\n')
                .replace(/<br[^>]*>/gi, '\n')
                
                // Remove all remaining HTML tags
                .replace(/<[^>]+>/g, '')
                
                // Decode HTML entities
                .replace(/&nbsp;/g, ' ')
                .replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>')
                .replace(/&amp;/g, '&')
                .replace(/&quot;/g, '"')
                .replace(/&#39;/g, "'")
                
                // Fix spacing
                .replace(/\s+/g, ' ')
                .replace(/\n\s*\n/g, '\n\n')
                .trim();

            console.log('[hotword] Content cleaned successfully');
            return cleaned;
        } catch (error) {
            console.error('[hotword] Error cleaning content:', error);
            return content; // Return original content if cleaning fails
        }
    }

    function formatEmailForReply(originalEmail) {
        if (!originalEmail) return '';
        
        try {
            const date = originalEmail.date ? formatDetailDate(originalEmail.date) : formatDetailDate(new Date());
            const sender = formatSenderForDisplay(originalEmail.sender, originalEmail.sender_email);
            let content = originalEmail.snippet || '';
            
            // Clean the content
            content = cleanEmailContent(content);
            
            // Format as a proper reply
            return `\n\nOn ${date}, ${sender} wrote:\n${content}`;
        } catch (error) {
            console.error('[hotword] Error formatting email for reply:', error);
            return originalEmail.snippet || '';
        }
    }
}); 