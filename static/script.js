const fileInput = document.getElementById('file-input');
const uploadBtn = document.getElementById('upload-btn');
const ingestBtn = document.getElementById('ingest-btn');
const fileList = document.getElementById('file-list');
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

// Settings Elements
const chunkSizeInput = document.getElementById('chunk-size');
const chunkOverlapInput = document.getElementById('chunk-overlap');
const topKInput = document.getElementById('top-k');
const temperatureInput = document.getElementById('temperature');
const enableEvaluationCheckbox = document.getElementById('enable-evaluation');

const chunkSizeVal = document.getElementById('chunk-size-val');
const chunkOverlapVal = document.getElementById('chunk-overlap-val');
const topKVal = document.getElementById('top-k-val');
const temperatureVal = document.getElementById('temperature-val');

// Load files on startup
fetchFiles();

// Event Listeners
uploadBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileUpload);
ingestBtn.addEventListener('click', handleIngest);
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Settings Listeners
chunkSizeInput.addEventListener('input', (e) => chunkSizeVal.textContent = e.target.value);
chunkOverlapInput.addEventListener('input', (e) => chunkOverlapVal.textContent = e.target.value);
topKInput.addEventListener('input', (e) => topKVal.textContent = e.target.value);
temperatureInput.addEventListener('input', (e) => temperatureVal.textContent = e.target.value);

async function fetchFiles() {
    try {
        const response = await fetch('/files');
        const data = await response.json();
        renderFileList(data.files);
    } catch (error) {
        console.error('Error fetching files:', error);
    }
}

function renderFileList(files) {
    fileList.innerHTML = '';
    if (files.length === 0) {
        fileList.innerHTML = '<div class="file-item">No files uploaded</div>';
        return;
    }
    files.forEach(file => {
        const div = document.createElement('div');
        div.className = 'file-item';

        // Add file type icon
        const icon = document.createElement('span');
        icon.className = 'file-icon';
        if (file.endsWith('.pdf')) {
            icon.textContent = '📄';
        } else if (file.endsWith('.docx')) {
            icon.textContent = '📝';
        } else if (file.endsWith('.xlsx')) {
            icon.textContent = '📊';
        } else {
            icon.textContent = '📎';
        }

        const fileName = document.createElement('span');
        fileName.className = 'file-name';
        fileName.textContent = file;

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-btn';
        deleteBtn.innerHTML = '✕';
        deleteBtn.title = 'Delete file';
        deleteBtn.onclick = () => deleteFile(file);

        div.appendChild(icon);
        div.appendChild(fileName);
        div.appendChild(deleteBtn);
        fileList.appendChild(div);
    });
}

async function deleteFile(filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"?\n\nNote: You'll need to re-process documents after deletion.`)) {
        return;
    }

    try {
        const response = await fetch(`/files/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            addSystemMessage(data.message + '. ' + data.recommendation);
            await fetchFiles();
        } else {
            alert('Error deleting file: ' + data.detail);
        }
    } catch (error) {
        console.error('Error deleting file:', error);
        alert('Error deleting file');
    }
}

async function handleFileUpload(e) {
    const files = e.target.files;
    if (files.length === 0) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    try {
        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Uploading...';

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            await fetchFiles();
        } else {
            alert('Upload failed');
        }
    } catch (error) {
        console.error('Error uploading:', error);
        alert('Error uploading files');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
            Upload Documents (.pdf, .docx, .xlsx)
        `;
        fileInput.value = '';
    }
}

async function handleIngest() {
    try {
        ingestBtn.disabled = true;
        ingestBtn.textContent = 'Processing...';

        const response = await fetch('/ingest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                chunk_size: parseInt(chunkSizeInput.value),
                chunk_overlap: parseInt(chunkOverlapInput.value)
            })
        });

        const data = await response.json();
        if (response.ok) {
            addSystemMessage(data.message);
        } else {
            addSystemMessage('Error processing documents: ' + data.detail);
        }
    } catch (error) {
        console.error('Error ingesting:', error);
        addSystemMessage('Error processing documents');
    } finally {
        ingestBtn.disabled = false;
        ingestBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path></svg>
            Process Docs
        `;
    }
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // Add user message
    addMessage(text, 'user');
    userInput.value = '';
    userInput.style.height = 'auto';

    // Show loading state
    const loadingId = addMessage('Thinking...', 'bot', true);

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: text,
                top_k: parseInt(topKInput.value),
                temperature: parseFloat(temperatureInput.value),
                evaluate: enableEvaluationCheckbox.checked
            })
        });

        const data = await response.json();

        // Remove loading message
        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) loadingMsg.remove();

        if (response.ok) {
            addMessage(data.response, 'bot', false, data.sources, data.evaluation);
        } else {
            addMessage('Error: ' + data.detail, 'bot');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) loadingMsg.remove();
        addMessage('Error connecting to server', 'bot');
    }
}

function addMessage(text, sender, isLoading = false, sources = null, evaluation = null) {
    const div = document.createElement('div');
    div.className = `message ${sender}-message`;
    if (isLoading) div.id = 'loading-' + Date.now();

    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;

    div.appendChild(content);

    // Add sources if present
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';

        const sourcesTitle = document.createElement('div');
        sourcesTitle.className = 'sources-title';
        sourcesTitle.textContent = '📄 Sources:';
        sourcesDiv.appendChild(sourcesTitle);

        sources.forEach(source => {
            const sourceItem = document.createElement('div');
            sourceItem.className = 'source-item';
            const fileName = source.file.split('\\').pop().split('/').pop();

            // UPDATED: Include source_id if present
            if (source.source_id) {
                sourceItem.innerHTML = `<strong>Source ${source.source_id}:</strong> ${fileName} - Page ${source.page}`;
            } else {
                sourceItem.textContent = `${fileName} - Page ${source.page}`;
            }

            sourcesDiv.appendChild(sourceItem);
        });

        div.appendChild(sourcesDiv);
    }

    // Add evaluation results if present
    if (evaluation) {
        const evalDiv = document.createElement('div');
        evalDiv.className = 'evaluation-results';

        const evalHeader = document.createElement('div');
        evalHeader.className = 'evaluation-header';
        evalHeader.innerHTML = `📊 RAG Quality Metrics <span class="overall-score">${(evaluation.overall_score * 100).toFixed(0)}%</span>`;
        evalDiv.appendChild(evalHeader);

        // Add each metric
        const metrics = evaluation.metrics;

        // Context Relevance
        if (metrics.context_relevance) {
            evalDiv.appendChild(createMetricElement('Context Relevance', metrics.context_relevance));
        }

        // Faithfulness
        if (metrics.faithfulness) {
            evalDiv.appendChild(createMetricElement('Faithfulness', metrics.faithfulness));
        }

        // Answer Relevance
        if (metrics.answer_relevance) {
            evalDiv.appendChild(createMetricElement('Answer Relevance', metrics.answer_relevance));
        }

        // Citation Quality (if present)
        if (metrics.citation_quality) {
            evalDiv.appendChild(createMetricElement('Citation Quality', metrics.citation_quality));
        }

        div.appendChild(evalDiv);
    }

    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return div.id;
}

function createMetricElement(name, metricData) {
    const metricDiv = document.createElement('div');
    metricDiv.className = 'metric';

    const metricName = document.createElement('div');
    metricName.className = 'metric-name';
    metricName.textContent = name;
    metricDiv.appendChild(metricName);

    const metricScore = document.createElement('div');
    metricScore.className = 'metric-score';

    const scoreBar = document.createElement('div');
    scoreBar.className = 'score-bar';

    const scoreBarFill = document.createElement('div');
    scoreBarFill.className = 'score-bar-fill';

    const score = metricData.score;
    scoreBarFill.style.width = `${score * 100}%`;

    // Set color based on score
    if (score >= 0.7) {
        scoreBarFill.classList.add('high');
    } else if (score >= 0.5) {
        scoreBarFill.classList.add('medium');
    } else {
        scoreBarFill.classList.add('low');
    }

    scoreBar.appendChild(scoreBarFill);
    metricScore.appendChild(scoreBar);

    const scoreValue = document.createElement('span');
    scoreValue.className = 'score-value';
    scoreValue.textContent = (score * 100).toFixed(0) + '%';
    metricScore.appendChild(scoreValue);

    const verdict = document.createElement('span');
    verdict.className = `verdict ${metricData.verdict.toLowerCase().includes('pass') || metricData.verdict.toLowerCase().includes('faithful') || metricData.verdict.toLowerCase().includes('relevant') ? 'pass' : 'fail'}`;
    verdict.textContent = metricData.verdict;
    metricScore.appendChild(verdict);

    metricDiv.appendChild(metricScore);

    return metricDiv;
}

function addSystemMessage(text) {
    const div = document.createElement('div');
    div.className = 'message system-message';

    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;

    div.appendChild(content);
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Auto-resize textarea
userInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});
