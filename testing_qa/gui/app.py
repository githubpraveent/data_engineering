"""
Web-based GUI for no-code test automation
Similar to Tosca's visual test builder
"""
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import threading
from datetime import datetime

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
CORS(app)

# Test storage
TESTS_DIR = Path(__file__).parent.parent / "tests" / "gui_tests"
TESTS_DIR.mkdir(parents=True, exist_ok=True)


@app.route('/')
def index():
    """Main dashboard"""
    return render_template('dashboard.html')


@app.route('/test-builder')
def test_builder():
    """Visual test builder"""
    return render_template('test_builder.html')


@app.route('/test-runner')
def test_runner():
    """Test execution interface"""
    return render_template('test_runner.html')


@app.route('/api/tests', methods=['GET'])
def list_tests():
    """List all GUI-created tests"""
    tests = []
    for test_file in TESTS_DIR.glob("*.json"):
        with open(test_file, 'r') as f:
            test_data = json.load(f)
            tests.append({
                "id": test_file.stem,
                "name": test_data.get("name", test_file.stem),
                "description": test_data.get("description", ""),
                "created": test_data.get("created", ""),
                "steps": len(test_data.get("steps", []))
            })
    return jsonify(tests)


@app.route('/api/tests', methods=['POST'])
def create_test():
    """Create a new test via GUI"""
    data = request.json
    test_id = data.get("id") or f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    test_data = {
        "id": test_id,
        "name": data.get("name", "Untitled Test"),
        "description": data.get("description", ""),
        "environment": data.get("environment", "dev"),
        "created": datetime.now().isoformat(),
        "steps": data.get("steps", [])
    }
    
    test_file = TESTS_DIR / f"{test_id}.json"
    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    return jsonify({"success": True, "id": test_id})


@app.route('/api/tests/<test_id>', methods=['GET'])
def get_test(test_id):
    """Get test details"""
    test_file = TESTS_DIR / f"{test_id}.json"
    if not test_file.exists():
        return jsonify({"error": "Test not found"}), 404
    
    with open(test_file, 'r') as f:
        return jsonify(json.load(f))


@app.route('/api/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    """Update test"""
    test_file = TESTS_DIR / f"{test_id}.json"
    if not test_file.exists():
        return jsonify({"error": "Test not found"}), 404
    
    data = request.json
    with open(test_file, 'r') as f:
        test_data = json.load(f)
    
    test_data.update({
        "name": data.get("name", test_data.get("name")),
        "description": data.get("description", test_data.get("description")),
        "environment": data.get("environment", test_data.get("environment")),
        "steps": data.get("steps", test_data.get("steps")),
        "updated": datetime.now().isoformat()
    })
    
    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    return jsonify({"success": True})


@app.route('/api/tests/<test_id>', methods=['DELETE'])
def delete_test(test_id):
    """Delete test"""
    test_file = TESTS_DIR / f"{test_id}.json"
    if test_file.exists():
        test_file.unlink()
        return jsonify({"success": True})
    return jsonify({"error": "Test not found"}), 404


@app.route('/api/tests/<test_id>/run', methods=['POST'])
def run_test(test_id):
    """Run a test"""
    test_file = TESTS_DIR / f"{test_id}.json"
    if not test_file.exists():
        return jsonify({"error": "Test not found"}), 404
    
    with open(test_file, 'r') as f:
        test_data = json.load(f)
    
    # Generate Python test file from GUI test
    python_test = generate_python_test(test_data)
    python_file = TESTS_DIR / f"{test_id}_generated.py"
    with open(python_file, 'w') as f:
        f.write(python_test)
    
    # Run the test
    env = test_data.get("environment", "dev")
    result = subprocess.run(
        ["pytest", str(python_file), "-v", f"--env={env}", "--json-report", "--json-report-file=test-reports/gui_test.json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    
    # Parse results
    try:
        with open(Path(__file__).parent.parent / "test-reports" / "gui_test.json", 'r') as f:
            report = json.load(f)
    except:
        report = {"summary": {"total": 0, "passed": 0, "failed": 0}}
    
    return jsonify({
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr,
        "report": report
    })


@app.route('/api/environments', methods=['GET'])
def list_environments():
    """List available environments"""
    config_dir = Path(__file__).parent.parent / "config" / "environments"
    environments = []
    for env_file in config_dir.glob("*.example.json"):
        env_name = env_file.stem.replace(".example", "")
        environments.append({
            "name": env_name,
            "display_name": env_name.upper(),
            "configured": (config_dir / f"{env_name}.json").exists()
        })
    return jsonify(environments)


def generate_python_test(test_data: Dict[str, Any]) -> str:
    """Generate Python test code from GUI test definition"""
    test_name = test_data.get("name", "GUI Test").replace(" ", "_")
    test_id = test_data.get("id", "test")
    environment = test_data.get("environment", "dev")
    steps = test_data.get("steps", [])
    
    code = f'''"""
Auto-generated test from GUI
Test ID: {test_id}
Generated: {datetime.now().isoformat()}
"""
import pytest
from framework.api.client import APIClient
from framework.api.validator import ResponseValidator
from framework.async.polling import PollingVerifier
from framework.async.state_checker import StateChecker
from framework.config import get_config


@pytest.mark.gui
@pytest.mark.e2e
class Test{test_name.replace("_", "")}:
    """{test_data.get("description", "GUI-generated test")}"""
    
    def test_{test_id}(self):
        """{test_data.get("name", "GUI Test")}"""
        api_client = APIClient()
        validator = ResponseValidator()
        config = get_config("{environment}")
        
'''
    
    for i, step in enumerate(steps, 1):
        step_type = step.get("type")
        step_name = step.get("name", f"Step {i}")
        
        if step_type == "api_call":
            method = step.get("method", "GET").upper()
            endpoint = step.get("endpoint", "")
            body = step.get("body")
            expected_status = step.get("expected_status", 200)
            
            code += f"        # {step_name}\n"
            if method == "GET":
                code += f"        response = api_client.get(\"{endpoint}\")\n"
            elif method == "POST":
                body_json = json.dumps(body) if body else "{}"
                code += f"        response = api_client.post(\"{endpoint}\", json={body_json})\n"
            elif method == "PUT":
                body_json = json.dumps(body) if body else "{}"
                code += f"        response = api_client.put(\"{endpoint}\", json={body_json})\n"
            elif method == "DELETE":
                code += f"        response = api_client.delete(\"{endpoint}\")\n"
            
            code += f"        assert validator.validate_status_code(response, {expected_status})\n"
            
            # Add validations
            validations = step.get("validations", [])
            for validation in validations:
                if validation.get("type") == "json_path":
                    path = validation.get("path")
                    expected = validation.get("expected")
                    code += f"        assert validator.validate_json_path(response, \"{path}\", {repr(expected)})\n"
        
        elif step_type == "wait":
            duration = step.get("duration", 5)
            code += f"        # {step_name}\n"
            code += f"        import time\n"
            code += f"        time.sleep({duration})\n"
        
        elif step_type == "poll":
            condition = step.get("condition")
            max_wait = step.get("max_wait", 60)
            code += f"        # {step_name}\n"
            code += f"        poller = PollingVerifier(max_wait_time={max_wait})\n"
            # Simplified polling - would need more complex code generation
            code += f"        # Polling condition: {condition}\n"
        
        code += "\n"
    
    return code


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')


