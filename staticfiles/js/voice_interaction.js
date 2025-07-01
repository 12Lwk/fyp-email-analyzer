/**
 * Voice Interaction Module for Email System
 * Provides functionality for voice commands and speech synthesis
 */

// Global variables
let isListening = false;
let recognition = null;
let audioContext = null;
let audioAnalyser = null;
let currentVoiceName = 'en-US-Standard-C';
let visualizerCanvas = null;
let visualizerContext = null;
let isVisualizerActive = false;

// Initialize speech recognition
function initSpeechRecognition() {
    try {
        // Check if browser supports speech recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.error('Speech recognition not supported in this browser');
            showNotification('Speech recognition is not supported in your browser.', 'error');
            return false;
        }
        
        // Create recognition object
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        // Set up event handlers
        recognition.onstart = () => {
            console.log('Voice recognition started');
            document.getElementById('voiceCommandBtn').classList.add('listening');
            document.getElementById('voiceCommandBtn').innerHTML = '<i class="fas fa-microphone-alt"></i> Listening...';
            startVisualizer();
        };
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log('Voice command recognized:', transcript);
            
            // Show the recognized text
            showVoiceInput(transcript);
            
            // Process command via API
            processVoiceCommand(transcript);
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            if (event.error === 'no-speech') {
                showNotification('No speech detected. Please try again.', 'warning');
            } else {
                showNotification(`Error: ${event.error}`, 'error');
            }
            stopListening();
        };
        
        recognition.onend = () => {
            console.log('Voice recognition ended');
            stopListening();
        };
        
        return true;
    } catch (e) {
        console.error('Error initializing speech recognition:', e);
        showNotification('Could not initialize speech recognition.', 'error');
        return false;
    }
}

// Start listening for voice commands
function startListening() {
    if (isListening) return;
    
    if (!recognition && !initSpeechRecognition()) {
        return;
    }
    
    try {
        recognition.start();
        isListening = true;
    } catch (e) {
        console.error('Error starting speech recognition:', e);
        showNotification('Error starting speech recognition.', 'error');
    }
}

// Stop listening for voice commands
function stopListening() {
    if (!isListening) return;
    
    try {
        recognition.stop();
    } catch (e) {
        console.error('Error stopping speech recognition:', e);
    }
    
    isListening = false;
    document.getElementById('voiceCommandBtn').classList.remove('listening');
    document.getElementById('voiceCommandBtn').innerHTML = '<i class="fas fa-microphone"></i> Voice Command';
    stopVisualizer();
}

// Process voice command
function processVoiceCommand(text) {
    console.log('Processing voice command:', text);
    
    // Quick client-side intent detection for faster response
    const textLower = text.toLowerCase();
    
    if (textLower.includes('read') && (textLower.includes('email') || textLower.includes('message'))) {
        speakResponse('Reading the email for you.');
        readEmailContent();
        return;
    } else if (textLower.includes('summarize') || textLower.includes('summary') || textLower.includes('analyze')) {
        speakResponse('Generating an analysis of this email.');
        generateAnalysis();
        return;
    } else if (textLower.includes('reply')) {
        speakResponse('Preparing a reply to this email.');
        // Call reply function if it exists
        if (typeof suggestReply === 'function') {
            suggestReply();
        } else {
            speakResponse('Reply functionality is not available.');
        }
        return;
    }
    
    // If the client-side detection doesn't match, send to the server
    // for more sophisticated processing
    fetch('/api/voice/process-command/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            text: text
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Command processing result:', data);
        
        if (data.success) {
            // Speak the response if available
            if (data.response) {
                speakResponse(data.response);
            }
            
            // Execute the command based on intent
            executeCommand(data.intent);
        } else {
            speakResponse("I'm sorry, I couldn't understand that command.");
        }
    })
    .catch(error => {
        console.error('Error processing command:', error);
        speakResponse("Sorry, there was an error processing your command.");
    });
}

// Execute a command based on intent
function executeCommand(intentData) {
    const intent = intentData.intent || 'unknown';
    
    switch (intent) {
        case 'read_email':
            readEmailContent();
            break;
        case 'summarize':
            generateAnalysis();
            break;
        case 'reply':
            if (typeof suggestReply === 'function') {
                suggestReply();
            }
            break;
        case 'forward':
            // Call forward function if it exists
            if (typeof forwardEmail === 'function') {
                const recipient = intentData.entities.recipient;
                forwardEmail(null, recipient);
            }
            break;
        case 'delete':
            // Call delete function if it exists
            if (typeof deleteEmail === 'function') {
                deleteEmail();
            }
            break;
        case 'help':
            showHelp();
            break;
        default:
            console.log('Unknown intent:', intent);
    }
}

// Read email content using TTS
function readEmailContent() {
    console.log('Reading email content');
    
    const emailContent = document.getElementById('emailContent').textContent;
    const emailSubject = document.getElementById('emailSubject').textContent;
    
    // Call TTS API
    fetch('/api/voice/read-email/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            content: emailContent,
            subject: emailSubject,
            voice: currentVoiceName
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.blob();
    })
    .then(audioBlob => {
        playAudio(audioBlob);
    })
    .catch(error => {
        console.error('Error reading email:', error);
        showNotification('Error reading email: ' + error.message, 'error');
    });
}

// Read email summary using TTS
function readSummary() {
    console.log('Reading email summary');
    
    const summaryElement = document.getElementById('messageOverview');
    
    // Check if we have a summary
    if (!summaryElement || summaryElement.textContent.includes('Click "Generate Analysis"')) {
        speakResponse('No summary available. Please generate an analysis first.');
        // Generate analysis if not available
        generateAnalysis();
        return;
    }
    
    // Get summary text
    const summaryText = summaryElement.textContent;
    
    // Call TTS API
    speakText(summaryText);
}

// Read recommendations using TTS
function readRecommendations() {
    console.log('Reading recommendations');
    
    const recommendationsElement = document.getElementById('suggestedActions');
    
    // Check if we have recommendations
    if (!recommendationsElement || recommendationsElement.children.length === 0) {
        speakResponse('No recommendations available. Please generate an analysis first.');
        // Generate analysis if not available
        generateAnalysis();
        return;
    }
    
    // Get recommendations text
    let recommendationsText = 'Here are my suggestions: ';
    
    // Get all list items
    const listItems = recommendationsElement.querySelectorAll('li');
    if (listItems.length > 0) {
        // Add each recommendation
        listItems.forEach((item, index) => {
            recommendationsText += `${index + 1}. ${item.textContent.trim()} `;
        });
    } else {
        // If no list items, use the whole text
        recommendationsText += recommendationsElement.textContent;
    }
    
    // Call TTS API
    speakText(recommendationsText);
}

// Speak text using TTS
function speakText(text) {
    if (!text) return;
    
    console.log('Speaking text');
    
    // Call TTS API
    fetch('/api/voice/text-to-speech/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            text: text,
            voice: currentVoiceName
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.blob();
    })
    .then(audioBlob => {
        playAudio(audioBlob);
    })
    .catch(error => {
        console.error('Error speaking text:', error);
        showNotification('Error speaking text: ' + error.message, 'error');
    });
}

// Play a quick response
function speakResponse(text) {
    console.log('Speaking response:', text);
    speakText(text);
}

// Play audio blob
function playAudio(audioBlob) {
    // Create audio URL
    const audioUrl = URL.createObjectURL(audioBlob);
    
    // Create audio element
    const audio = new Audio(audioUrl);
    
    // Play the audio
    audio.play();
    
    // Clean up after playback
    audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
    };
}

// Get CSRF token from cookies
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    
    return cookieValue || '';
}

// Show notification
function showNotification(message, type = 'info') {
    console.log(`Notification (${type}):`, message);
    
    // Check if we have an existing notification element
    let notificationElement = document.getElementById('voiceNotification');
    
    if (!notificationElement) {
        // Create notification element
        notificationElement = document.createElement('div');
        notificationElement.id = 'voiceNotification';
        notificationElement.className = 'voice-notification';
        
        // Add to document
        document.body.appendChild(notificationElement);
    }
    
    // Set notification content
    notificationElement.innerHTML = `
        <div class="notification-${type}">
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Show notification
    notificationElement.classList.add('show');
    
    // Hide after 5 seconds
    setTimeout(() => {
        notificationElement.classList.remove('show');
    }, 5000);
}

// Show recognized voice input
function showVoiceInput(text) {
    console.log('Voice input:', text);
    
    // Check if we have an existing voice input element
    let voiceInputElement = document.getElementById('voiceInput');
    
    if (!voiceInputElement) {
        // Create voice input element
        voiceInputElement = document.createElement('div');
        voiceInputElement.id = 'voiceInput';
        voiceInputElement.className = 'voice-input';
        
        // Add to document
        document.body.appendChild(voiceInputElement);
    }
    
    // Set voice input content
    voiceInputElement.innerHTML = `
        <div class="voice-input-text">
            <i class="fas fa-microphone"></i>
            <span>${text}</span>
        </div>
    `;
    
    // Show voice input
    voiceInputElement.classList.add('show');
    
    // Hide after 5 seconds
    setTimeout(() => {
        voiceInputElement.classList.remove('show');
    }, 5000);
}

// Start audio visualizer
function startVisualizer() {
    if (!isListening || isVisualizerActive) return;
    
    try {
        // Get canvas element
        visualizerCanvas = document.getElementById('voiceVisualizer');
        
        if (!visualizerCanvas) {
            // Create canvas element
            visualizerCanvas = document.createElement('canvas');
            visualizerCanvas.id = 'voiceVisualizer';
            visualizerCanvas.className = 'voice-visualizer';
            visualizerCanvas.width = 300;
            visualizerCanvas.height = 100;
            
            // Add to document
            const voiceCommandBtn = document.getElementById('voiceCommandBtn');
            if (voiceCommandBtn) {
                voiceCommandBtn.parentNode.appendChild(visualizerCanvas);
            } else {
                document.body.appendChild(visualizerCanvas);
            }
        }
        
        // Get canvas context
        visualizerContext = visualizerCanvas.getContext('2d');
        
        // Create audio context and analyser
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        // Get microphone input
        navigator.mediaDevices.getUserMedia({ audio: true, video: false })
            .then(stream => {
                // Create analyser
                audioAnalyser = audioContext.createAnalyser();
                audioAnalyser.fftSize = 256;
                
                // Connect microphone to analyser
                const source = audioContext.createMediaStreamSource(stream);
                source.connect(audioAnalyser);
                
                // Start visualization
                isVisualizerActive = true;
                visualize();
            })
            .catch(err => {
                console.error('Error accessing microphone:', err);
            });
    } catch (e) {
        console.error('Error starting visualizer:', e);
    }
}

// Visualize audio input
function visualize() {
    if (!isVisualizerActive || !audioAnalyser || !visualizerContext) return;
    
    // Get frequency data
    const bufferLength = audioAnalyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    audioAnalyser.getByteFrequencyData(dataArray);
    
    // Clear canvas
    visualizerContext.clearRect(0, 0, visualizerCanvas.width, visualizerCanvas.height);
    
    // Draw visualization
    const barWidth = (visualizerCanvas.width / bufferLength) * 2.5;
    let x = 0;
    
    for (let i = 0; i < bufferLength; i++) {
        const barHeight = dataArray[i] / 2;
        
        // Use gradient based on frequency
        const gradient = visualizerContext.createLinearGradient(0, 0, 0, visualizerCanvas.height);
        gradient.addColorStop(0, '#3699ff');
        gradient.addColorStop(1, '#1e7be2');
        
        visualizerContext.fillStyle = gradient;
        visualizerContext.fillRect(x, visualizerCanvas.height - barHeight, barWidth, barHeight);
        
        x += barWidth + 1;
    }
    
    // Continue animation
    if (isVisualizerActive) {
        requestAnimationFrame(visualize);
    }
}

// Stop audio visualizer
function stopVisualizer() {
    isVisualizerActive = false;
    
    if (visualizerCanvas) {
        // Clear canvas
        visualizerContext.clearRect(0, 0, visualizerCanvas.width, visualizerCanvas.height);
    }
}

// Continuous listening mode
function toggleContinuousListening() {
    const toggleSwitch = document.getElementById('continuousListeningToggle');
    
    if (!toggleSwitch) return;
    
    if (toggleSwitch.checked) {
        // Start continuous listening
        enableContinuousListening();
        showNotification('Continuous listening mode activated. Say "Email Assistant" to activate.', 'info');
    } else {
        // Stop continuous listening
        disableContinuousListening();
        showNotification('Continuous listening mode deactivated.', 'info');
    }
}

// Enable continuous listening
function enableContinuousListening() {
    try {
        // Check if browser supports speech recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.error('Speech recognition not supported in this browser');
            showNotification('Speech recognition is not supported in your browser.', 'error');
            return;
        }
        
        // Create continuous recognition object
        const continuousRecognition = new SpeechRecognition();
        continuousRecognition.continuous = true;
        continuousRecognition.interimResults = false;
        continuousRecognition.lang = 'en-US';
        
        // Set up event handlers
        continuousRecognition.onstart = () => {
            console.log('Continuous listening started');
            document.getElementById('continuousListeningStatus').innerHTML = '<i class="fas fa-circle text-success"></i> Listening';
        };
        
        continuousRecognition.onresult = (event) => {
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript.toLowerCase();
                console.log('Heard:', transcript);
                
                // Check for wake word
                if (transcript.includes('email assistant') || transcript.includes('hey assistant')) {
                    // Play activation sound
                    new Audio('/static/sounds/activate.mp3').play();
                    
                    // Process command part after wake word
                    const commandPart = transcript.split(/email assistant|hey assistant/i)[1];
                    if (commandPart) {
                        showVoiceInput(commandPart.trim());
                        processVoiceCommand(commandPart.trim());
                    } else {
                        // Prompt for command if none given
                        speakResponse("How can I help with your email?");
                        // Temporarily stop continuous and start normal recognition
                        continuousRecognition.stop();
                        startListening();
                        
                        // Restart continuous recognition after command is processed
                        recognition.onend = () => {
                            stopListening();
                            setTimeout(() => {
                                continuousRecognition.start();
                            }, 1000);
                        };
                    }
                }
            }
        };
        
        continuousRecognition.onerror = (event) => {
            console.error('Continuous recognition error:', event.error);
            
            if (event.error === 'no-speech') {
                // No speech is common in continuous mode, don't show notification
                console.log('No speech detected in continuous mode');
            } else {
                showNotification(`Continuous listening error: ${event.error}`, 'error');
                document.getElementById('continuousListeningToggle').checked = false;
            }
        };
        
        continuousRecognition.onend = () => {
            console.log('Continuous recognition ended');
            
            // Check if toggle is still on
            const toggleSwitch = document.getElementById('continuousListeningToggle');
            if (toggleSwitch && toggleSwitch.checked) {
                // Restart if it was stopped unexpectedly
                setTimeout(() => {
                    continuousRecognition.start();
                }, 1000);
            } else {
                document.getElementById('continuousListeningStatus').innerHTML = '<i class="fas fa-circle text-danger"></i> Not Listening';
            }
        };
        
        // Start continuous recognition
        continuousRecognition.start();
        
        // Store recognition object for later
        window.continuousRecognition = continuousRecognition;
    } catch (e) {
        console.error('Error enabling continuous listening:', e);
        showNotification('Could not enable continuous listening.', 'error');
        
        // Reset toggle
        const toggleSwitch = document.getElementById('continuousListeningToggle');
        if (toggleSwitch) {
            toggleSwitch.checked = false;
        }
    }
}

// Disable continuous listening
function disableContinuousListening() {
    try {
        if (window.continuousRecognition) {
            window.continuousRecognition.stop();
        }
        
        document.getElementById('continuousListeningStatus').innerHTML = '<i class="fas fa-circle text-danger"></i> Not Listening';
    } catch (e) {
        console.error('Error disabling continuous listening:', e);
    }
}

// Show help dialog
function showHelp() {
    console.log('Showing voice commands help');
    
    // Create help dialog if it doesn't exist
    let helpDialog = document.getElementById('voiceCommandsHelp');
    if (!helpDialog) {
        helpDialog = document.createElement('div');
        helpDialog.id = 'voiceCommandsHelp';
        helpDialog.className = 'modal fade';
        helpDialog.setAttribute('tabindex', '-1');
        
        helpDialog.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Voice Commands Help</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>You can use the following voice commands:</p>
                        <ul class="list-group">
                            <li class="list-group-item"><i class="fas fa-volume-up"></i> <strong>Read email</strong> - Read the email content</li>
                            <li class="list-group-item"><i class="fas fa-search"></i> <strong>Summarize</strong> - Generate a summary of the email</li>
                            <li class="list-group-item"><i class="fas fa-reply"></i> <strong>Reply</strong> - Suggest a reply to the email</li>
                            <li class="list-group-item"><i class="fas fa-forward"></i> <strong>Forward to [person]</strong> - Forward the email</li>
                            <li class="list-group-item"><i class="fas fa-trash"></i> <strong>Delete</strong> - Delete the email</li>
                            <li class="list-group-item"><i class="fas fa-question-circle"></i> <strong>Help</strong> - Show this help dialog</li>
                        </ul>
                        <p class="mt-3">In continuous listening mode, start with <strong>"Email Assistant"</strong> or <strong>"Hey Assistant"</strong> followed by your command.</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Got it!</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(helpDialog);
    }
    
    // Show the dialog
    const bsModal = new bootstrap.Modal(helpDialog);
    bsModal.show();
}

// Add event listeners when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Voice interaction module loaded');
    
    // Initialize voice buttons
    const voiceCommandBtn = document.getElementById('voiceCommandBtn');
    const readEmailBtn = document.getElementById('readEmailBtn');
    const readSummaryBtn = document.getElementById('readSummaryBtn');
    const voiceHelpBtn = document.getElementById('voiceHelpBtn');
    const continuousListeningToggle = document.getElementById('continuousListeningToggle');
    
    // Initialize speech recognition
    initSpeechRecognition();
    
    // Voice command button
    if (voiceCommandBtn) {
        voiceCommandBtn.addEventListener('click', function() {
            if (isListening) {
                stopListening();
            } else {
                startListening();
            }
        });
    }
    
    // Read email button
    if (readEmailBtn) {
        readEmailBtn.addEventListener('click', readEmailContent);
    }
    
    // Read summary button
    if (readSummaryBtn) {
        readSummaryBtn.addEventListener('click', readSummary);
    }
    
    // Voice help button
    if (voiceHelpBtn) {
        voiceHelpBtn.addEventListener('click', showHelp);
    }
    
    // Continuous listening toggle
    if (continuousListeningToggle) {
        continuousListeningToggle.addEventListener('change', toggleContinuousListening);
    }
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Alt+V to toggle voice command
        if (e.altKey && e.key === 'v') {
            e.preventDefault();
            if (isListening) {
                stopListening();
            } else {
                startListening();
            }
        }
        
        // Alt+R to read email
        if (e.altKey && e.key === 'r') {
            e.preventDefault();
            readEmailContent();
        }
        
        // Alt+S to read summary
        if (e.altKey && e.key === 's') {
            e.preventDefault();
            readSummary();
        }
    });
}); 