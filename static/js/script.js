document.addEventListener('DOMContentLoaded', function() {
    
    // --- Geolocation and Auto-Insight Fetching ---
    function autoDetectLocationAndFetchInsights() {
        if (sessionStorage.getItem('insightsFetched')) {
            const locationDisplay = document.getElementById("location-display");
            if (locationDisplay && sessionStorage.getItem('userCity')) {
                locationDisplay.innerHTML = `<i class="fas fa-map-marker-alt"></i> ${sessionStorage.getItem('userCity')}`;
            }
            return;
        }
        const locationDisplay = document.getElementById("location-display");
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(positionSuccess, positionError, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
        }
    }

    async function positionSuccess(position) {
        const { latitude: lat, longitude: lon } = position.coords;
        const locationDisplay = document.getElementById("location-display");
        try {
            const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
            const data = await response.json();
            const city = data.address.city || data.address.town || data.address.village || 'Your Area';
            sessionStorage.setItem('userCity', city);
            locationDisplay.innerHTML = `<i class="fas fa-map-marker-alt"></i> ${city}`;
        } catch (e) {
            console.error("Reverse geocoding failed:", e);
        }
        const locationForm = document.getElementById('location-form');
        if (locationForm) {
            document.getElementById('latitude').value = lat;
            document.getElementById('longitude').value = lon;
            sessionStorage.setItem('insightsFetched', 'true');
            locationForm.action = window.location.pathname;
            locationForm.submit();
        }
    }
    
    function positionError(error) { /* Omitted for brevity */ }

    const currentPath = window.location.pathname;
    if (['/farmer', '/buyer', '/consumer'].includes(currentPath)) {
        autoDetectLocationAndFetchInsights();
    }

    // --- Interactive AI Pest Detection ---
    const analyzeBtn = document.getElementById('analyze-pest-btn');
    if(analyzeBtn) {
        analyzeBtn.addEventListener('click', () => {
            const fileInput = document.getElementById('pest-image-upload');
            const resultDiv = document.getElementById('pest-analysis-result');
            if (fileInput.files.length === 0) {
                resultDiv.innerHTML = "<p class='text-danger'>Please select an image first.</p>";
                resultDiv.classList.remove('d-none');
                return;
            }
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            resultDiv.innerHTML = `<div class="spinner-border spinner-border-sm" role="status"></div> Analyzing image...`;
            resultDiv.classList.remove('d-none');

            fetch('/analyze_image', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    resultDiv.innerHTML = (data.status === 'success') ? data.ai_result : `<p class='text-danger'>Analysis failed.</p>`;
                })
                .catch(err => {
                    console.error('Analysis Error:', err);
                    resultDiv.innerHTML = `<p class='text-danger'>An error occurred.</p>`;
                });
        });
    }

    // --- Chatbot Functionality ---
    const chatbotSendBtn = document.getElementById('chatbot-send');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotMessages = document.getElementById('chatbot-messages');

    function renderMarkdown(text) { return marked.parse(text); }
    
    function addMessage(message, sender, isThinking = false) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('chatbot-msg', sender === 'user' ? 'user-msg' : 'bot-msg');
        if (isThinking) {
            msgDiv.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Thinking...`;
            msgDiv.id = 'thinking-indicator';
        } else {
            msgDiv.innerHTML = sender === 'bot' ? renderMarkdown(message) : message;
        }
        chatbotMessages.appendChild(msgDiv);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    function sendChatMessage() {
        const message = chatbotInput.value.trim();
        if (message) {
            addMessage(message, 'user');
            chatbotInput.value = '';
            addMessage('Thinking...', 'bot', true);
            fetch('/chatbot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            }).then(r => r.json()).then(data => {
                document.getElementById('thinking-indicator')?.remove();
                addMessage(data.response, 'bot');
            }).catch(e => {
                document.getElementById('thinking-indicator')?.remove();
                addMessage('Sorry, an error occurred.', 'bot');
            });
        }
    }
    if(chatbotSendBtn) chatbotSendBtn.addEventListener('click', sendChatMessage);
    if(chatbotInput) chatbotInput.addEventListener('keypress', e => e.key === 'Enter' && (e.preventDefault(), sendChatMessage()));

    // --- Add Confirmation for Delete Button ---
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this product?')) {
                e.preventDefault();
            }
        });
    });

});