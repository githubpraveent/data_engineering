# GUI User Guide - No-Code Test Automation

## Table of Contents
1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Creating Your First Test](#creating-your-first-test)
4. [Step-by-Step: Building a Test](#step-by-step-building-a-test)
5. [Running Tests](#running-tests)
6. [Common Workflows](#common-workflows)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Step 1: Launch the GUI Application

1. **Open Terminal/Command Prompt**
   - On Windows: Press `Win + R`, type `cmd`, press Enter
   - On Mac: Press `Cmd + Space`, type `Terminal`, press Enter
   - On Linux: Press `Ctrl + Alt + T`

2. **Navigate to Project Directory**
   ```bash
   cd /path/to/cursor_Testing
   ```

3. **Start the GUI Server**
   ```bash
   python gui/app.py
   ```

4. **Open Web Browser**
   - Open your web browser (Chrome, Firefox, Safari, or Edge)
   - Navigate to: `http://localhost:5000`
   - You should see the **Dashboard** page

### Step 2: Verify Environment Setup

1. **Check Environment Status**
   - On the Dashboard, look at the "Environments" card
   - You should see DEV, QA, and PROD environments
   - Green badge = Ready to use
   - Yellow badge = Needs configuration

2. **Configure Environment (if needed)**
   - Copy environment file: `config/environments/dev.example.json` to `config/environments/dev.json`
   - Edit the file with your actual API endpoints and credentials
   - Repeat for QA and PROD if needed

---

## Dashboard Overview

### Main Navigation

The dashboard has three main sections accessible via the top navigation bar:

1. **🏠 Dashboard** - View all tests, statistics, and environments
2. **🔧 Test Builder** - Create and edit tests visually
3. **▶️ Test Runner** - Execute tests and view results

### Dashboard Cards

1. **My Tests Card**
   - Lists all your created tests
   - Shows test name, denription, and number of steps
   - Actions: Edit, Run, Delete

2. **Test Statistics Card**
   - Total tests count
   - Passed tests count
   - Failed tests count

3. **Environments Card**
   - Shows available environments (DEV, QA, PROD)
   - Status indicator for each environment

---

## Creating Your First Test

### Scenario: Test Order Creation Flow

Let's create a test that:
1. Creates an order via API
2. Waits for processing
3. Verifies the order status

### Step-by-Step Instructions

#### Step 1: Navigate to Test Builder

1. Click on **"Test Builder"** in the top navigation bar
2. You'll see three panels:
   - **Left Panel**: Test Properties and Step Templates
   - **Center Panel**: Your test steps (currently empty)
   - **Right Panel**: Step configuration (hidden until you select a step)

#### Step 2: Fill Test Properties

**In the Left Panel, under "Test Properties":**

1. **Test Name**: 
   - Click in the "Test Name" field
   - Type: `Create Order Flow Test`
   - This is required (marked with *)

2. **Description**:
   - Click in the "Description" field
   - Type: `Tests the complete order creation and processing flow`

3. **Environment**:
   - Click the dropdown menu
   - Select: `dev` (for development environment)

#### Step 3: Add First Step - API Call

1. **In the Left Panel, under "Add Step" section:**
   - Click the **"🌐 API Call"** button
   - A new step appears in the center panel

2. **Configure the API Call:**
   - The right panel opens automatically
   - **Step Name**: Type `Create Order`
   - **HTTP Method**: Select `POST` from dropdown
   - **Endpoint**: Type `/orders`
   - **Request Body (JSON)**: Paste or type:
     ```json
     {
       "customerId": "customer-123",
       "items": [
         {
           "productId": "prod-123",
           "quantity": 2,
           "price": 50.00
         }
       ],
       "totalAmount": 100.00
     }
     ```
   - **Expected Status Code**: Type `201` (or `202` for async)

3. **Add Validation:**
   - Scroll down to "Validations" section
   - Click **"➕ Add Validation"** button
   - **JSON Path**: Type `orderId`
   - **Expected Value**: Leave empty (we just want to verify it exists)
   - This checks that the response contains an `orderId` field

4. **Apply Configuration:**
   - Click **"✓ Apply"** button at the bottom
   - The step is now configured and saved

#### Step 4: Add Second Step - Wait

1. **Add Wait Step:**
   - In Left Panel, click **"⏱️ Wait"** button
   - New step appears in center panel

2. **Configure Wait:**
   - Right panel opens
   - **Step Name**: Type `Wait for Processing`
   - **Duration (seconds)**: Type `5`
   - Click **"✓ Apply"**

#### Step 5: Add Third Step - Poll/Verify

1. **Add Poll Step:**
   - In Left Panel, click **"🔄 Poll/Verify"** button
   - New step appears

2. **Configure Poll:**
   - **Step Name**: Type `Verify Order Status`
   - **Poll Condition**: Type `Check if order status is "processed"`
   - **Max Wait Time (seconds)**: Type `60`
   - Click **"✓ Apply"**

#### Step 6: Save Your Test

1. **In the Left Panel:**
   - Click **"💾 Save Test"** button
   - A success message appears
   - Your test is now saved!

2. **View Your Test:**
   - Click **"🏠 Dashboard"** in navigation
   - Your new test appears in "My Tests" card

---

## Step-by-Step: Building a Test

### Understanding Step Types

#### 1. API Call Step

**When to use:** When you need to make HTTP requests to your API

**Configuration Fields:**
- **Step Name**: Descriptive name (e.g., "Create User", "Get Order Details")
- **HTTP Method**: GET, POST, PUT, DELETE, or PATCH
- **Endpoint**: API path (e.g., `/orders`, `/users/123`)
- **Request Body**: JSON data for POST/PUT requests
- **Expected Status Code**: What HTTP status code you expect (200, 201, 404, etc.)
- **Validations**: Add checks on the response

**Example - GET Request:**
```
Step Name: Get Order Details
HTTP Method: GET
Endpoint: /orders/{orderId}
Expected Status Code: 200
```

**Example - POST Request:**
```
Step Name: Create Order
HTTP Method: POST
Endpoint: /orders
Request Body: {"customerId": "123", "amount": 100}
Expected Status Code: 201
```

**Adding Validations:**
1. Click **"➕ Add Validation"**
2. **JSON Path**: Path to check in response (e.g., `status`, `data.orderId`)
3. **Expected Value**: What value you expect (e.g., `"processed"`, `"123"`)

**JSON Path Examples:**
- `status` - Checks top-level status field
- `data.orderId` - Checks nested orderId in data object
- `items[0].price` - Checks first item's price in array

#### 2. Wait Step

**When to use:** When you need to pause execution (e.g., waiting for async processing)

**Configuration Fields:**
- **Step Name**: Descriptive name (e.g., "Wait for Processing")
- **Duration (seconds)**: How long to wait (1-300 seconds)

**Example:**
```
Step Name: Wait for Lambda Processing
Duration: 10 seconds
```

#### 3. Poll/Verify Step

**When to use:** When you need to repeatedly check a condition until it's met

**Configuration Fields:**
- **Step Name**: Descriptive name
- **Poll Condition**: Description of what to check
- **Max Wait Time**: Maximum time to keep checking (in seconds)

**Example:**
```
Step Name: Wait for Order Status Update
Poll Condition: Check if order status changes to "processed"
Max Wait Time: 60 seconds
```

**Note:** The system will automatically poll the API endpoint from the previous step to check the condition.

---

## Running Tests

### Method 1: Run from Dashboard

1. **Navigate to Dashboard**
   - Click **"🏠 Dashboard"** in navigation

2. **Find Your Test**
   - Scroll through "My Tests" card
   - Find the test you want to run

3. **Run Test**
   - Click the **"▶️ Play"** button next to the test
   - You're redirected to Test Runner

### Method 2: Run from Test Runner

1. **Navigate to Test Runner**
   - Click **"▶️ Test Runner"** in navigation

2. **Select Tests**
   - Check the boxes next to tests you want to run
   - You can select multiple tests

3. **Run Selected Tests**
   - Click **"▶️ Run Selected"** button
   - Execution starts immediately

4. **View Results**
   - **Test Execution Panel**: Shows real-time output
   - **Results Summary Panel**: Shows pass/fail counts

### Understanding Test Results

#### Execution Output Colors:
- **🟢 Green**: Success messages
- **🔴 Red**: Error messages
- **🔵 Blue**: Information messages
- **🟡 Yellow**: Warning messages

#### Results Summary:
- **Total Tests**: Number of tests executed
- **Passed**: Tests that completed successfully
- **Failed**: Tests that encountered errors

---

## Common Workflows

### Workflow 1: Simple API Test

**Goal:** Test a single API endpoint

**Steps:**
1. Create new test
2. Add one "API Call" step
3. Configure endpoint, method, and expected response
4. Save and run

**Example:**
```
Test: Get User Profile
Step 1: API Call
  - Method: GET
  - Endpoint: /users/123
  - Expected Status: 200
  - Validation: Check that "email" field exists
```

### Workflow 2: Create and Verify Flow

**Goal:** Create a resource and verify it was created

**Steps:**
1. Add "API Call" step to create resource
2. Add "Wait" step (2-5 seconds)
3. Add "API Call" step to get the resource
4. Add validation to verify data

**Example:**
```
Test: Create Order and Verify
Step 1: API Call - POST /orders
Step 2: Wait - 3 seconds
Step 3: API Call - GET /orders/{orderId}
Step 4: Validation - Check status = "created"
```

### Workflow 3: Async Processing Flow

**Goal:** Test asynchronous operations (API → Lambda → Queue → Processing)

**Steps:**
1. Add "API Call" step to trigger async operation
2. Add "Poll/Verify" step to wait for completion
3. Add "API Call" step to check final status
4. Add validations

**Example:**
```
Test: Async Order Processing
Step 1: API Call - POST /orders (returns 202 Accepted)
Step 2: Poll/Verify - Wait for status = "processed" (max 60s)
Step 3: API Call - GET /orders/{orderId}
Step 4: Validation - Check status = "processed"
```

### Workflow 4: Multi-Step Business Flow

**Goal:** Test complete business process

**Steps:**
1. Create resource
2. Update resource
3. Verify updates
4. Check downstream effects

**Example:**
```
Test: Complete Order Lifecycle
Step 1: API Call - POST /orders (Create)
Step 2: Wait - 2 seconds
Step 3: API Call - PUT /orders/{orderId} (Update status)
Step 4: Wait - 5 seconds
Step 5: API Call - GET /orders/{orderId} (Verify)
Step 6: Validation - Check status = "shipped"
```

---

## Advanced Features

### Editing Existing Tests

1. **From Dashboard:**
   - Click **"✏️ Edit"** button next to test
   - Test opens in Test Builder

2. **Modify Steps:**
   - Click on any step to edit it
   - Right panel opens with current configuration
   - Make changes and click **"✓ Apply"**

3. **Reorder Steps:**
   - Drag and drop steps to reorder
   - Click and hold step number
   - Drag to new position
   - Release to drop

4. **Delete Steps:**
   - Click **"🗑️ Delete"** button on step
   - Confirm deletion

5. **Save Changes:**
   - Click **"💾 Save Test"** button

### Using Test Data Templates

**Pre-defined Test Data:**
- Order payloads are available in `test_data/` folder
- You can reference these in your request bodies

**Example:**
```json
{
  "orderId": "test-123",
  "customerId": "customer-456",
  "amount": 100.00
}
```

### Environment-Specific Tests

**Different Environments:**
- **DEV**: Development environment (safe for testing)
- **QA**: Quality Assurance environment
- **PROD**: Production environment (use with caution!)

**Selecting Environment:**
1. In Test Builder, use "Environment" dropdown
2. Select appropriate environment
3. Save test
4. Test will use that environment's configuration when run

---

## Troubleshooting

### Problem: GUI won't start

**Solution:**
1. Check Python is installed: `python --version`
2. Install dependencies: `pip install -r requirements.txt`
3. Check port 5000 is not in use
4. Try different port: Edit `gui/app.py`, change `port=5000` to `port=5001`

### Problem: Test fails with "Connection Error"

**Solution:**
1. Check environment configuration file exists
2. Verify API endpoint URL is correct
3. Check API key/credentials are set
4. Verify network connectivity

### Problem: Test fails with "Timeout"

**Solution:**
1. Increase wait times in "Wait" steps
2. Increase "Max Wait Time" in "Poll/Verify" steps
3. Check if API is responding slowly
4. Verify environment is accessible

### Problem: Validation fails

**Solution:**
1. Check JSON path is correct (case-sensitive)
2. Verify expected value matches actual response
3. Use browser developer tools to inspect API response
4. Check for nested paths (use dot notation: `data.orderId`)

### Problem: Can't save test

**Solution:**
1. Ensure "Test Name" is filled (required field)
2. Check you have write permissions in project directory
3. Verify test has at least one step
4. Try refreshing the page

### Problem: Steps not appearing

**Solution:**
1. Refresh the page
2. Check browser console for errors (F12)
3. Ensure JavaScript is enabled
4. Try different browser

---

## Quick Reference

### Keyboard Shortcuts
- **Ctrl/Cmd + S**: Save test (when in Test Builder)
- **F5**: Refresh page
- **Esc**: Close step configuration panel

### Step Icons
- **🌐 API Call**: Make HTTP request
- **⏱️ Wait**: Pause execution
- **🔄 Poll/Verify**: Repeatedly check condition
- **✓ Validation**: Check response data

### Status Indicators
- **🟢 Green Badge**: Ready/Passed
- **🔴 Red Badge**: Failed/Error
- **🟡 Yellow Badge**: Warning/Needs Setup

---

## Best Practices

1. **Name Tests Clearly**
   - Use descriptive names: "Create Order Flow" not "Test1"
   - Include environment if test is environment-specific

2. **Add Descriptions**
   - Help others understand what the test does
   - Document any special requirements

3. **Use Appropriate Wait Times**
   - Don't use excessive wait times (slows down tests)
   - Don't use too short waits (may cause flaky tests)

4. **Add Validations**
   - Always validate important response fields
   - Check both success and error scenarios

5. **Organize Steps Logically**
   - Follow the actual user/system flow
   - Group related steps together

6. **Test in DEV First**
   - Always test in DEV environment first
   - Only use QA/PROD after DEV tests pass

7. **Keep Tests Focused**
   - One test = one scenario
   - Don't try to test everything in one test

---

## Getting Help

### Documentation
- Check this guide first
- Review example tests in `tests/` folder
- Check framework documentation in `docs/` folder

### Support
- Check error messages in Test Runner output
- Review browser console (F12) for JavaScript errors
- Check server logs in terminal where GUI is running

---

## Next Steps

After mastering the basics:
1. Create tests for your specific APIs
2. Set up CI/CD integration (see CI/CD documentation)
3. Explore advanced features like API simulation
4. Build a comprehensive test suite

Happy Testing! 🚀
