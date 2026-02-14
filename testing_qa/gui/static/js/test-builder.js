// Test Builder functionality
let currentTest = {
    id: null,
    name: '',
    description: '',
    environment: 'dev',
    steps: []
};

let selectedStepIndex = null;
let stepConfigTemplate = null;

document.addEventListener('DOMContentLoaded', function() {
    // Load test if ID provided in URL
    const urlParams = new URLSearchParams(window.location.search);
    const testId = urlParams.get('test');
    if (testId) {
        loadTestById(testId);
    }
    
    // Load step configuration templates
    stepConfigTemplate = document.getElementById('step-templates');
    
    // Initialize drag and drop
    initializeDragAndDrop();
});

function addStep(type) {
    const step = {
        type: type,
        name: `Step ${currentTest.steps.length + 1}`,
        id: Date.now().toString()
    };
    
    // Set defaults based on type
    if (type === 'api_call') {
        step.method = 'GET';
        step.endpoint = '';
        step.body = null;
        step.expected_status = 200;
        step.validations = [];
    } else if (type === 'wait') {
        step.duration = 5;
    } else if (type === 'poll') {
        step.condition = '';
        step.max_wait = 60;
    }
    
    currentTest.steps.push(step);
    renderSteps();
    selectStep(currentTest.steps.length - 1);
}

function renderSteps() {
    const container = document.getElementById('steps-container');
    const count = document.getElementById('step-count');
    
    count.textContent = `${currentTest.steps.length} step${currentTest.steps.length !== 1 ? 's' : ''}`;
    
    if (currentTest.steps.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-mouse-pointer fa-3x"></i>
                <p>Click "Add Step" to start building your test</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = currentTest.steps.map((step, index) => {
        const typeLabel = step.type.replace('_', ' ').toUpperCase();
        const details = getStepDetails(step);
        
        return `
            <div class="step-item ${selectedStepIndex === index ? 'selected' : ''}" 
                 data-index="${index}"
                 draggable="true">
                <div class="step-item-header">
                    <div style="display: flex; align-items: center; flex: 1;">
                        <span class="step-item-number">${index + 1}</span>
                        <span class="step-item-title">${step.name}</span>
                        <span class="step-item-type">${typeLabel}</span>
                    </div>
                    <div class="step-item-actions">
                        <button onclick="selectStep(${index})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deleteStep(${index})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="step-item-details">
                    ${details}
                </div>
            </div>
        `;
    }).join('');
    
    // Re-attach drag handlers
    attachDragHandlers();
}

function getStepDetails(step) {
    if (step.type === 'api_call') {
        return `<strong>${step.method}</strong> ${step.endpoint || '(no endpoint)'}`;
    } else if (step.type === 'wait') {
        return `Wait for <strong>${step.duration}</strong> seconds`;
    } else if (step.type === 'poll') {
        return `Poll until: ${step.condition || '(no condition)'}`;
    }
    return '';
}

function selectStep(index) {
    selectedStepIndex = index;
    const step = currentTest.steps[index];
    
    // Show configuration panel
    const panel = document.getElementById('step-config-panel');
    panel.style.display = 'block';
    
    // Load step configuration template
    const template = stepConfigTemplate.querySelector(`[data-step-type="${step.type}"]`);
    if (template) {
        const content = document.getElementById('step-config-content');
        content.innerHTML = template.innerHTML;
        
        // Populate with step data
        if (content.querySelector('.step-name')) {
            content.querySelector('.step-name').value = step.name || '';
        }
        if (content.querySelector('.step-method')) {
            content.querySelector('.step-method').value = step.method || 'GET';
        }
        if (content.querySelector('.step-endpoint')) {
            content.querySelector('.step-endpoint').value = step.endpoint || '';
        }
        if (content.querySelector('.step-body')) {
            content.querySelector('.step-body').value = step.body ? JSON.stringify(step.body, null, 2) : '';
        }
        if (content.querySelector('.step-status')) {
            content.querySelector('.step-status').value = step.expected_status || 200;
        }
        if (content.querySelector('.step-duration')) {
            content.querySelector('.step-duration').value = step.duration || 5;
        }
        if (content.querySelector('.step-condition')) {
            content.querySelector('.step-condition').value = step.condition || '';
        }
        if (content.querySelector('.step-max-wait')) {
            content.querySelector('.step-max-wait').value = step.max_wait || 60;
        }
        
        // Render validations
        if (step.validations) {
            renderValidations(step.validations);
        }
    }
    
    renderSteps();
}

function saveStepConfig() {
    if (selectedStepIndex === null) return;
    
    const step = currentTest.steps[selectedStepIndex];
    const content = document.getElementById('step-config-content');
    
    // Save step configuration
    if (content.querySelector('.step-name')) {
        step.name = content.querySelector('.step-name').value;
    }
    if (content.querySelector('.step-method')) {
        step.method = content.querySelector('.step-method').value;
    }
    if (content.querySelector('.step-endpoint')) {
        step.endpoint = content.querySelector('.step-endpoint').value;
    }
    if (content.querySelector('.step-body')) {
        const bodyText = content.querySelector('.step-body').value.trim();
        if (bodyText) {
            try {
                step.body = JSON.parse(bodyText);
            } catch (e) {
                alert('Invalid JSON in request body');
                return;
            }
        } else {
            step.body = null;
        }
    }
    if (content.querySelector('.step-status')) {
        step.expected_status = parseInt(content.querySelector('.step-status').value);
    }
    if (content.querySelector('.step-duration')) {
        step.duration = parseInt(content.querySelector('.step-duration').value);
    }
    if (content.querySelector('.step-condition')) {
        step.condition = content.querySelector('.step-condition').value;
    }
    if (content.querySelector('.step-max-wait')) {
        step.max_wait = parseInt(content.querySelector('.step-max-wait').value);
    }
    
    renderSteps();
    cancelStepConfig();
}

function cancelStepConfig() {
    selectedStepIndex = null;
    document.getElementById('step-config-panel').style.display = 'none';
    renderSteps();
}

function deleteStep(index) {
    if (confirm('Are you sure you want to delete this step?')) {
        currentTest.steps.splice(index, 1);
        if (selectedStepIndex === index) {
            cancelStepConfig();
        }
        renderSteps();
    }
}

function addValidation() {
    if (selectedStepIndex === null) return;
    
    const step = currentTest.steps[selectedStepIndex];
    if (!step.validations) {
        step.validations = [];
    }
    
    step.validations.push({
        type: 'json_path',
        path: '',
        expected: ''
    });
    
    renderValidations(step.validations);
}

function renderValidations(validations) {
    const container = document.getElementById('validations-list');
    if (!container) return;
    
    container.innerHTML = validations.map((val, index) => `
        <div class="validation-item">
            <div class="validation-item-info">
                <label>JSON Path</label>
                <input type="text" value="${val.path || ''}" 
                       onchange="updateValidation(${selectedStepIndex}, ${index}, 'path', this.value)">
            </div>
            <div class="validation-item-info">
                <label>Expected Value</label>
                <input type="text" value="${val.expected || ''}" 
                       onchange="updateValidation(${selectedStepIndex}, ${index}, 'expected', this.value)">
            </div>
            <button onclick="removeValidation(${selectedStepIndex}, ${index})">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

function updateValidation(stepIndex, valIndex, field, value) {
    currentTest.steps[stepIndex].validations[valIndex][field] = value;
}

function removeValidation(stepIndex, valIndex) {
    currentTest.steps[stepIndex].validations.splice(valIndex, 1);
    renderValidations(currentTest.steps[stepIndex].validations);
}

async function saveTest() {
    // Get test properties
    currentTest.name = document.getElementById('test-name').value;
    currentTest.description = document.getElementById('test-description').value;
    currentTest.environment = document.getElementById('test-environment').value;
    
    if (!currentTest.name) {
        alert('Please enter a test name');
        return;
    }
    
    try {
        const url = currentTest.id ? `/api/tests/${currentTest.id}` : '/api/tests';
        const method = currentTest.id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(currentTest)
        });
        
        if (response.ok) {
            const result = await response.json();
            if (!currentTest.id) {
                currentTest.id = result.id;
            }
            alert('Test saved successfully!');
        } else {
            alert('Error saving test');
        }
    } catch (error) {
        console.error('Error saving test:', error);
        alert('Error saving test');
    }
}

async function loadTest() {
    const testId = prompt('Enter test ID to load:');
    if (testId) {
        await loadTestById(testId);
    }
}

async function loadTestById(testId) {
    try {
        const response = await fetch(`/api/tests/${testId}`);
        if (response.ok) {
            currentTest = await response.json();
            
            // Populate form
            document.getElementById('test-name').value = currentTest.name || '';
            document.getElementById('test-description').value = currentTest.description || '';
            document.getElementById('test-environment').value = currentTest.environment || 'dev';
            
            renderSteps();
        } else {
            alert('Test not found');
        }
    } catch (error) {
        console.error('Error loading test:', error);
        alert('Error loading test');
    }
}

// Drag and Drop
function initializeDragAndDrop() {
    // Implementation for drag and drop reordering
}

function attachDragHandlers() {
    const steps = document.querySelectorAll('.step-item');
    steps.forEach(step => {
        step.addEventListener('dragstart', handleDragStart);
        step.addEventListener('dragover', handleDragOver);
        step.addEventListener('drop', handleDrop);
        step.addEventListener('dragend', handleDragEnd);
    });
}

function handleDragStart(e) {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', e.target.dataset.index);
    e.target.classList.add('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    e.target.closest('.step-item')?.classList.add('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    const fromIndex = parseInt(e.dataTransfer.getData('text/html'));
    const toItem = e.target.closest('.step-item');
    if (!toItem) return;
    
    const toIndex = parseInt(toItem.dataset.index);
    if (fromIndex !== toIndex) {
        // Reorder steps
        const [removed] = currentTest.steps.splice(fromIndex, 1);
        currentTest.steps.splice(toIndex, 0, removed);
        renderSteps();
    }
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
    document.querySelectorAll('.drag-over').forEach(item => {
        item.classList.remove('drag-over');
    });
}


