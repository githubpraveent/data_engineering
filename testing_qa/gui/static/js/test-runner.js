// Test Runner functionality
document.addEventListener('DOMContentLoaded', function() {
    loadTests();
    
    // Load test if ID provided in URL
    const urlParams = new URLSearchParams(window.location.search);
    const testId = urlParams.get('test');
    if (testId) {
        selectTestById(testId);
    }
});

async function loadTests() {
    try {
        const response = await fetch('/api/tests');
        const tests = await response.json();
        
        const container = document.getElementById('tests-selector');
        
        if (tests.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No tests available. Create tests first!</p></div>';
            return;
        }
        
        container.innerHTML = tests.map(test => `
            <div class="test-selector-item">
                <input type="checkbox" id="test-${test.id}" value="${test.id}">
                <div class="test-selector-item-info">
                    <h4>${test.name}</h4>
                    <p>${test.description || 'No description'} • ${test.steps} steps</p>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading tests:', error);
    }
}

function selectTestById(testId) {
    const checkbox = document.getElementById(`test-${testId}`);
    if (checkbox) {
        checkbox.checked = true;
    }
}

function selectAll() {
    const checkboxes = document.querySelectorAll('#tests-selector input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = true);
}

function getSelectedTests() {
    const checkboxes = document.querySelectorAll('#tests-selector input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

async function runSelectedTests() {
    const testIds = getSelectedTests();
    
    if (testIds.length === 0) {
        alert('Please select at least one test to run');
        return;
    }
    
    const output = document.getElementById('execution-output');
    output.innerHTML = '';
    
    addLog('info', `Starting execution of ${testIds.length} test(s)...`);
    
    let passed = 0;
    let failed = 0;
    
    for (const testId of testIds) {
        addLog('info', `\nRunning test: ${testId}`);
        
        try {
            const response = await fetch(`/api/tests/${testId}/run`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                addLog('success', `✓ Test ${testId} passed`);
                passed++;
            } else {
                addLog('error', `✗ Test ${testId} failed`);
                if (result.error) {
                    addLog('error', result.error);
                }
                failed++;
            }
            
            if (result.output) {
                addLog('info', result.output);
            }
        } catch (error) {
            addLog('error', `Error running test ${testId}: ${error.message}`);
            failed++;
        }
    }
    
    addLog('info', `\n\nExecution complete: ${passed} passed, ${failed} failed`);
    updateResultsSummary(passed, failed, testIds.length);
}

function addLog(type, message) {
    const output = document.getElementById('execution-output');
    const line = document.createElement('div');
    line.className = `log-line ${type}`;
    line.textContent = message;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
}

function updateResultsSummary(passed, failed, total) {
    const container = document.getElementById('results-summary');
    container.innerHTML = `
        <div class="result-card total">
            <h3>Total Tests</h3>
            <div class="result-value">${total}</div>
        </div>
        <div class="result-card success">
            <h3>Passed</h3>
            <div class="result-value">${passed}</div>
        </div>
        <div class="result-card failed">
            <h3>Failed</h3>
            <div class="result-value">${failed}</div>
        </div>
    `;
}

function clearOutput() {
    document.getElementById('execution-output').innerHTML = `
        <div class="empty-state">
            <i class="fas fa-play-circle fa-3x"></i>
            <p>Select tests and click "Run Selected" to start execution</p>
        </div>
    `;
    document.getElementById('results-summary').innerHTML = `
        <div class="empty-state">
            <p>No tests executed yet</p>
        </div>
    `;
}


