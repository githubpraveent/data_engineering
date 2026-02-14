// Dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    loadTests();
    loadEnvironments();
    loadStatistics();
});

async function loadTests() {
    try {
        const response = await fetch('/api/tests');
        const tests = await response.json();
        
        const container = document.getElementById('tests-list');
        
        if (tests.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No tests yet. Create your first test!</p></div>';
            return;
        }
        
        container.innerHTML = tests.map(test => `
            <div class="test-item">
                <div class="test-item-info">
                    <h3>${test.name}</h3>
                    <p>${test.description || 'No description'}</p>
                    <p style="font-size: 11px; color: #9ca3af; margin-top: 5px;">
                        ${test.steps} steps • Created: ${new Date(test.created).toLocaleDateString()}
                    </p>
                </div>
                <div class="test-item-actions">
                    <button class="btn btn-small" onclick="editTest('${test.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-small" onclick="runTest('${test.id}')">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn btn-small btn-danger" onclick="deleteTest('${test.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading tests:', error);
        document.getElementById('tests-list').innerHTML = 
            '<div class="empty-state"><p>Error loading tests</p></div>';
    }
}

async function loadEnvironments() {
    try {
        const response = await fetch('/api/environments');
        const environments = await response.json();
        
        const container = document.getElementById('environments-list');
        container.innerHTML = environments.map(env => `
            <div class="env-item">
                <div>
                    <h3>${env.display_name}</h3>
                    <p>${env.configured ? 'Configured' : 'Not configured'}</p>
                </div>
                <span class="badge ${env.configured ? 'badge-success' : 'badge-warning'}">
                    ${env.configured ? 'Ready' : 'Setup Required'}
                </span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading environments:', error);
    }
}

function loadStatistics() {
    // Placeholder - would load from test execution history
    document.getElementById('total-tests').textContent = '0';
    document.getElementById('passed-tests').textContent = '0';
    document.getElementById('failed-tests').textContent = '0';
}

function editTest(testId) {
    window.location.href = `/test-builder?test=${testId}`;
}

function runTest(testId) {
    window.location.href = `/test-runner?test=${testId}`;
}

async function deleteTest(testId) {
    if (!confirm('Are you sure you want to delete this test?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/tests/${testId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadTests();
        }
    } catch (error) {
        console.error('Error deleting test:', error);
        alert('Error deleting test');
    }
}


