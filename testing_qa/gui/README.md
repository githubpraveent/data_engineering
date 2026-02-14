# GUI Application - No-Code Test Automation

## Quick Start

### 1. Start the GUI Server

```bash
# Navigate to project directory
cd /path/to/cursor_Testing

# Install dependencies (if not already done)
pip install -r requirements.txt

# Start GUI server
python gui/app.py
```

### 2. Access the GUI

Open your web browser and navigate to:
```
http://localhost:5000
```

### 3. Start Creating Tests

1. Click **"Test Builder"** in navigation
2. Fill in test properties
3. Add steps using the step type buttons
4. Configure each step
5. Save and run!

## Features

- ✅ **Visual Test Builder** - No coding required
- ✅ **Drag-and-Drop Steps** - Easy reordering
- ✅ **Real-time Execution** - See results as tests run
- ✅ **Multi-Environment Support** - DEV, QA, PROD
- ✅ **Step Templates** - Pre-configured step types
- ✅ **Validation Builder** - Visual validation configuration

## Documentation

- [Complete User Guide](../docs/GUI_USER_GUIDE.md) - Detailed step-by-step instructions
- [Tosca-Style Workflow](../docs/TOSCA_STYLE_WORKFLOW.md) - Workflow guide for Tosca users

## Troubleshooting

### Port Already in Use

If port 5000 is already in use, edit `gui/app.py`:

```python
# Change this line:
app.run(debug=True, port=5000, host='0.0.0.0')

# To:
app.run(debug=True, port=5001, host='0.0.0.0')
```

Then access at `http://localhost:5001`

### Dependencies Missing

```bash
pip install flask flask-cors
```

### Tests Not Saving

- Check write permissions in project directory
- Ensure `tests/gui_tests/` directory exists
- Check browser console for errors (F12)

## Architecture

```
gui/
├── app.py                 # Flask application
├── templates/             # HTML templates
│   ├── dashboard.html
│   ├── test_builder.html
│   └── test_runner.html
└── static/               # Static assets
    ├── css/
    │   ├── style.css
    │   ├── test-builder.css
    │   └── test-runner.css
    └── js/
        ├── dashboard.js
        ├── test-builder.js
        └── test-runner.js
```

## API Endpoints

- `GET /` - Dashboard
- `GET /test-builder` - Test Builder interface
- `GET /test-runner` - Test Runner interface
- `GET /api/tests` - List all tests
- `POST /api/tests` - Create new test
- `GET /api/tests/<id>` - Get test details
- `PUT /api/tests/<id>` - Update test
- `DELETE /api/tests/<id>` - Delete test
- `POST /api/tests/<id>/run` - Execute test

## Next Steps

1. Read the [User Guide](../docs/GUI_USER_GUIDE.md)
2. Follow the [Tosca-Style Workflow](../docs/TOSCA_STYLE_WORKFLOW.md)
3. Create your first test
4. Run and verify results

