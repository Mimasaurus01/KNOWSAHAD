// KNOW SAHAD - AI Hospital Navigator JavaScript

// Configuration
const API_BASE = 'http://localhost:5000/api';

// DOM Elements
const chatBox = document.getElementById("chatBox");
const chatForm = document.getElementById("chatForm");
const userInput = document.getElementById("userInput");
const sendButton = document.getElementById("sendButton");
const typingIndicator = document.getElementById("typingIndicator");
const connectionStatus = document.getElementById("connectionStatus");

// Global variables
let sessionId = 'session-' + Date.now();
let isConnected = false;

// Initialize the chat when page loads
window.addEventListener('load', async function() {
  await checkConnection();
});

// Handle form submission
chatForm.addEventListener("submit", async function (e) {
  e.preventDefault();

  const message = userInput.value.trim();
  if (message === "") return;

  // Disable input while processing
  sendButton.disabled = true;
  userInput.disabled = true;
  sendButton.textContent = "Sending...";

  addMessage("user", message);
  userInput.value = "";
  
  // Show typing indicator with smooth animation
  showTyping();
  
  try {
    const botResponse = await sendMessageToBot(message);
    hideTyping(); // Hide typing immediately when response is received
    
    // Small delay to make the transition smoother
    setTimeout(() => {
      addBotMessage(botResponse);
    }, 200);
    
  } catch (error) {
    hideTyping(); // Hide typing on error too
    setTimeout(() => {
      addMessage("bot", "🚨 I'm having trouble connecting to my navigation system. Please check that the backend is running on port 5000, or try again in a moment.");
    }, 200);
    console.error('Chat error:', error);
  } finally {
    // Re-enable input
    sendButton.disabled = false;
    userInput.disabled = false;
    sendButton.textContent = "Send";
    userInput.focus();
  }
});

// Send message to bot API
async function sendMessageToBot(userMessage) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: userMessage,
      session_id: sessionId
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const data = await response.json();
  return data;
}

// Add simple text message to chat
function addMessage(sender, text) {
  const messageWrapper = document.createElement("div");
  messageWrapper.classList.add("chat-message", sender);

  const messageBubble = document.createElement("div");
  messageBubble.classList.add("message");
  
  if (sender === "bot") {
    messageBubble.classList.add("bot-response");
  }
  
  messageBubble.textContent = text;

  messageWrapper.appendChild(messageBubble);
  chatBox.appendChild(messageWrapper);

  scrollToBottom();
}

// Add formatted bot message with location support
function addBotMessage(responseData) {
  const messageWrapper = document.createElement("div");
  messageWrapper.classList.add("chat-message", "bot");

  const messageBubble = document.createElement("div");
  messageBubble.classList.add("message", "bot-response");
  
  let formattedText = responseData.response || responseData.text || "I couldn't process that request.";
  
  // Check if this is a location response with image
  if (responseData.data && responseData.data.location && responseData.data.location.image) {
    const location = responseData.data.location;
    
    // Create location container
    const locationContainer = document.createElement("div");
    locationContainer.classList.add("location-container");
    
    // Create header with image and title
    const locationHeader = document.createElement("div");
    locationHeader.classList.add("location-header");
    
    // Add location image (beside the title)
    const imageElement = document.createElement("img");
    imageElement.src = `images/${location.image}`;
    imageElement.alt = location.name;
    imageElement.classList.add("location-image");
    imageElement.onclick = function() {
      openImageModal(this.src, location.name);
    };
    imageElement.onerror = function() {
      console.log('Image failed to load:', this.src);
      this.style.display = 'none';
    };
    
    // Add location title with icon
    const locationTitle = document.createElement("div");
    locationTitle.classList.add("location-title");
    
    const locationIcon = document.createElement("span");
    locationIcon.classList.add("location-icon");
    locationIcon.innerHTML = "📍";
    
    const locationName = document.createElement("strong");
    locationName.textContent = location.name;
    locationName.style.color = "rgb(14, 151, 14)";
    
    locationTitle.appendChild(locationIcon);
    locationTitle.appendChild(locationName);
    
    // Assemble header
    locationHeader.appendChild(imageElement);
    locationHeader.appendChild(locationTitle);
    
    // Add description and directions
    const locationInfo = document.createElement("div");
    
    // Format the response text with proper HTML (remove the title since we have it in header)
    let cleanedText = formattedText.replace(/📍\s*\*\*.*?\*\*\s*\n\n?/, '');
    cleanedText = cleanedText
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
    
    locationInfo.innerHTML = cleanedText;
    
    locationContainer.appendChild(locationHeader);
    locationContainer.appendChild(locationInfo);
    
    messageBubble.appendChild(locationContainer);
  } else {
    // Regular message without location image
    formattedText = formattedText
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');

    messageBubble.innerHTML = formattedText;
  }

  messageWrapper.appendChild(messageBubble);
  chatBox.appendChild(messageWrapper);

  scrollToBottom();
}

// Show typing indicator with animation
function showTyping() {
  typingIndicator.style.display = 'flex';
  // Force a reflow then add the show class for smooth animation
  typingIndicator.offsetHeight;
  typingIndicator.classList.add('show');
  scrollToBottom();
}

// Hide typing indicator with animation
function hideTyping() {
  typingIndicator.classList.remove('show');
  // Hide after animation completes
  setTimeout(() => {
    typingIndicator.style.display = 'none';
  }, 300);
}

// Smooth scroll to bottom of chat
function scrollToBottom() {
  // Smooth scroll to bottom
  setTimeout(() => {
    chatBox.scrollTo({
      top: chatBox.scrollHeight,
      behavior: 'smooth'
    });
  }, 50);
}

// Image modal functions
function openImageModal(imageSrc, locationName) {
  const modal = document.getElementById('imageModal');
  const modalImg = document.getElementById('modalImage');
  modal.style.display = 'block';
  modalImg.src = imageSrc;
  modalImg.alt = locationName;
}

function closeImageModal() {
  const modal = document.getElementById('imageModal');
  modal.style.display = 'none';
}

// Close modal when clicking outside the image
window.onclick = function(event) {
  const modal = document.getElementById('imageModal');
  if (event.target == modal) {
    closeImageModal();
  }
}

// Check API connection
async function checkConnection() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    const data = await response.json();
    
    isConnected = true;
    showConnectionStatus('connected', `✅ Connected to Sahad Hospital Navigation System (${data.locations_count} locations loaded)`);
    
  } catch (error) {
    isConnected = false;
    showConnectionStatus('error', '❌ Cannot connect to navigation system. Please ensure the backend is running on port 5000.');
    console.error('Connection check failed:', error);
  }
}

// Show connection status message
function showConnectionStatus(type, message) {
  connectionStatus.className = `connection-status ${type}`;
  connectionStatus.textContent = message;
  connectionStatus.style.display = 'block';
  
  // Hide after 5 seconds if connected
  if (type === 'connected') {
    setTimeout(() => {
      connectionStatus.style.display = 'none';
    }, 5000);
  }
}

// Allow Enter key to send message
userInput.addEventListener('keypress', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event('submit'));
  }
});

// Auto-focus on input when page loads
userInput.focus();