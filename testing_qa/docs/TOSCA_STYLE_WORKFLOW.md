# Tosca-Style Workflow Guide - Step-by-Step Automation

This guide provides detailed, step-by-step instructions similar to Tosca's visual workflow for creating automated tests without writing code.

---

## Table of Contents
1. [Tosca-Style Test Creation Workflow](#tosca-style-test-creation-workflow)
2. [Visual Step-by-Step Guide](#visual-step-by-step-guide)
3. [Tosca Concepts Mapped to Our Framework](#tosca-concepts-mapped-to-our-framework)
4. [Complete Example: Order Processing Test](#complete-example-order-processing-test)

---

## Tosca-Style Test Creation Workflow

### Phase 1: Test Planning (Like Tosca's Test Case Design)

#### Step 1.1: Define Test Objective
**What you're doing:** Planning what to test

**GUI Steps:**
1. Open Test Builder (`http://localhost:5000/test-builder`)
2. In "Test Properties" panel (left side):
   - **Test Name**: Enter descriptive name
     - Example: `Order Creation and Processing E2E Test`
   - **Description**: Write what this test validates
     - Example: `Validates complete order flow from creation through processing to final status verification`
   - **Environment**: Select target environment
     - Choose: `dev`, `qa`, or `prod`

**Tosca Equivalent:** Creating a Test Case in Tosca Commander

---

### Phase 2: Building Test Steps (Like Tosca's Module Creation)

#### Step 2.1: Add API Call Step (Like Tosca's Action Mode)

**What you're doing:** Creating the first action - calling your API

**GUI Steps:**

1. **Click "🌐 API Call" button** (in left panel under "Add Step")
   - A new step card appears in center panel
   - Right panel opens automatically for configuration

2. **Configure Step Properties:**
   - **Step Name**: `Create Order via API`
   - **HTTP Method**: Select `POST` from dropdown
   - **Endpoint**: Type `/orders`
   - **Request Body (JSON)**: Enter:
     ```json
     {
       "customerId": "customer-123",
       "items": [
         {
           "productId": "prod-456",
           "quantity": 2,
           "price": 50.00
         }
       ],
       "totalAmount": 100.00,
       "paymentMethod": "credit_card"
     }
     ```
   - **Expected Status Code**: `202` (for async) or `201` (for sync)

3. **Add Response Validation:**
   - Scroll to "Validations" section
   - Click **"➕ Add Validation"**
   - **JSON Path**: `orderId`
   - **Expected Value**: (leave empty to just check existence)
   - Click **"➕ Add Validation"** again
   - **JSON Path**: `status`
   - **Expected Value**: `pending`

4. **Save Step:**
   - Click **"✓ Apply"** button (bottom right)
   - Step is now configured and appears in center panel

**Tosca Equivalent:** 
- Creating an Action Mode module
- Configuring API TestStep
- Adding Buffer Verification

**Visual Guide:**
```
Left Panel          Center Panel              Right Panel
┌─────────────┐     ┌──────────────────┐    ┌──────────────┐
│ Add Step    │     │ Step 1: Create    │    │ Step Config  │
│ [API Call]  │────▶│ Order via API     │◀───│ - Name       │
│ [Wait]      │     │ [POST /orders]    │    │ - Method     │
│ [Poll]      │     │                   │    │ - Endpoint   │
└─────────────┘     └──────────────────┘    │ - Body       │
                                             │ - Validations│
                                             └──────────────┘
```

---

#### Step 2.2: Add Wait Step (Like Tosca's Delay)

**What you're doing:** Adding a pause for async processing

**GUI Steps:**

1. **Click "⏱️ Wait" button** (in left panel)
   - New step appears in center panel

2. **Configure Wait:**
   - Right panel opens
   - **Step Name**: `Wait for Lambda Processing`
   - **Duration (seconds)**: `5`
   - Click **"✓ Apply"**

**Tosca Equivalent:** Using Delay TestStep or Wait Buffer

**Why this step:** 
- Gives Lambda time to process the order
- Allows queue messages to be consumed
- Prevents race conditions

---

#### Step 2.3: Add Poll/Verify Step (Like Tosca's Buffer Verification with Retry)

**What you're doing:** Checking if async operation completed

**GUI Steps:**

1. **Click "🔄 Poll/Verify" button** (in left panel)
   - New step appears

2. **Configure Poll:**
   - **Step Name**: `Verify Order Processing Complete`
   - **Poll Condition**: `Check if order status is "processed"`
   - **Max Wait Time (seconds)**: `60`
   - Click **"✓ Apply"**

**Tosca Equivalent:**
- Buffer Verification with Retry
- Conditional Execution
- Loop with condition

**What happens behind the scenes:**
- System polls the order status endpoint
- Checks every 2 seconds (configurable)
- Stops when condition is met or timeout reached

---

#### Step 2.4: Add Verification Step (Like Tosca's Buffer Verification)

**What you're doing:** Final verification of end state

**GUI Steps:**

1. **Click "🌐 API Call" button** again
   - New step appears

2. **Configure Final Check:**
   - **Step Name**: `Get Final Order Status`
   - **HTTP Method**: `GET`
   - **Endpoint**: `/orders/{orderId}`
     - Note: `{orderId}` will use the orderId from Step 1 response
   - **Expected Status Code**: `200`

3. **Add Validations:**
   - Click **"➕ Add Validation"**
   - **JSON Path**: `status`
   - **Expected Value**: `processed`
   - Click **"➕ Add Validation"** again
   - **JSON Path**: `paymentStatus`
   - **Expected Value**: `completed`

4. **Click "✓ Apply"**

**Tosca Equivalent:**
- Buffer Verification
- Multiple buffer checks
- Assertion validation

---

### Phase 3: Test Organization (Like Tosca's Test Case Structure)

#### Step 3.1: Review Test Steps

**GUI Steps:**

1. **View all steps in center panel:**
   - Step 1: Create Order via API
   - Step 2: Wait for Lambda Processing
   - Step 3: Verify Order Processing Complete
   - Step 4: Get Final Order Status

2. **Reorder if needed:**
   - Click and hold step number
   - Drag to new position
   - Release to drop

3. **Edit any step:**
   - Click on step card
   - Right panel opens
   - Make changes
   - Click **"✓ Apply"**

**Tosca Equivalent:** Organizing TestSteps in TestCase

---

#### Step 3.2: Save Test

**GUI Steps:**

1. **In left panel, click "💾 Save Test"**
   - Success message appears
   - Test is saved with unique ID

2. **Verify on Dashboard:**
   - Click **"🏠 Dashboard"** in navigation
   - Your test appears in "My Tests" list

**Tosca Equivalent:** Saving TestCase in Tosca Commander

---

### Phase 4: Test Execution (Like Tosca's Execution)

#### Step 4.1: Run Test from Dashboard

**GUI Steps:**

1. **Navigate to Dashboard:**
   - Click **"🏠 Dashboard"** in top navigation

2. **Find your test:**
   - Scroll to "My Tests" card
   - Locate your test by name

3. **Run test:**
   - Click **"▶️ Play"** button next to test
   - You're redirected to Test Runner

**Tosca Equivalent:** Executing TestCase from Tosca Commander

---

#### Step 4.2: Monitor Execution

**GUI Steps:**

1. **View Test Execution Panel:**
   - Shows real-time output
   - Green text = success
   - Red text = errors
   - Blue text = information

2. **Watch progress:**
   - Each step executes in sequence
   - Status updates appear in real-time

3. **View Results Summary:**
   - Total tests: 1
   - Passed: 1 (if successful)
   - Failed: 0 (if successful)

**Tosca Equivalent:** Execution List in Tosca Commander

---

## Visual Step-by-Step Guide

### Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    TEST CREATION WORKFLOW                    │
└─────────────────────────────────────────────────────────────┘

1. LAUNCH GUI
   └─▶ Open browser → http://localhost:5000
       └─▶ See Dashboard

2. CREATE TEST
   └─▶ Click "Test Builder"
       └─▶ Fill Test Properties:
           ├─ Test Name: "Order Flow Test"
           ├─ Description: "E2E order processing"
           └─ Environment: "dev"

3. ADD STEPS (Repeat for each step)
   └─▶ Click Step Type Button
       └─▶ Configure in Right Panel
           ├─ Fill all required fields
           ├─ Add validations (if needed)
           └─ Click "Apply"
       └─▶ Step appears in Center Panel

4. SAVE TEST
   └─▶ Click "Save Test" button
       └─▶ Success message appears

5. RUN TEST
   └─▶ Go to Dashboard or Test Runner
       └─▶ Select test(s)
       └─▶ Click "Run Selected"
       └─▶ View results

┌─────────────────────────────────────────────────────────────┐
│                    DETAILED STEP CONFIGURATION                │
└─────────────────────────────────────────────────────────────┘

API CALL STEP CONFIGURATION:
┌─────────────────────────────────────┐
│ Step Configuration                  │
├─────────────────────────────────────┤
│ Step Name: [Create Order        ]   │
│ HTTP Method: [POST ▼]              │
│ Endpoint: [/orders              ]   │
│ Request Body:                       │
│ ┌─────────────────────────────────┐ │
│ │ {                               │ │
│ │   "customerId": "123",          │ │
│ │   "amount": 100.00              │ │
│ │ }                               │ │
│ └─────────────────────────────────┘ │
│ Expected Status: [201]              │
│                                     │
│ Validations:                        │
│ ┌─────────────────────────────────┐ │
│ │ JSON Path: [orderId         ]  │ │
│ │ Expected:  [              ]    │ │
│ │                    [Remove]     │ │
│ └─────────────────────────────────┘ │
│          [➕ Add Validation]        │
│                                     │
│        [✓ Apply]  [✗ Cancel]       │
└─────────────────────────────────────┘
```

---

## Tosca Concepts Mapped to Our Framework

| Tosca Concept | Our Framework Equivalent | How to Use |
|--------------|--------------------------|------------|
| **TestCase** | Test in Test Builder | Create test with name, description, environment |
| **TestStep** | Step in test | Add step using step type buttons |
| **Action Mode** | API Call Step | Click "API Call", configure HTTP method, endpoint, body |
| **Buffer** | Response data | Automatically captured from API responses |
| **Buffer Verification** | Validation | Add validation in API Call step configuration |
| **Delay** | Wait Step | Click "Wait", set duration |
| **Retry** | Poll/Verify Step | Click "Poll/Verify", set condition and max wait |
| **Module** | Reusable step template | Step templates in left panel |
| **Execution List** | Test Runner | View and run tests from Test Runner page |
| **Execution** | Test Run | Click "Run Selected" in Test Runner |
| **Execution Result** | Results Summary | View in Test Runner results panel |

---

## Complete Example: Order Processing Test

### Scenario
Test the complete order processing flow:
1. Create order
2. Verify order queued
3. Wait for processing
4. Verify final status

### Step-by-Step Creation

#### Step 1: Setup
```
Action: Open Test Builder
Location: Click "Test Builder" in navigation
Result: Test Builder page opens
```

#### Step 2: Test Properties
```
Action: Fill test information
Fields:
  - Test Name: "Complete Order Processing Flow"
  - Description: "Tests order creation through async processing to completion"
  - Environment: "dev"
Result: Test properties saved (not yet persisted)
```

#### Step 3: Add Step 1 - Create Order
```
Action: Click "🌐 API Call"
Result: New step appears

Action: Configure step
Fields:
  - Step Name: "Create Order"
  - HTTP Method: POST
  - Endpoint: /orders
  - Request Body:
    {
      "customerId": "test-customer-001",
      "items": [{"productId": "prod-123", "quantity": 1, "price": 99.99}],
      "totalAmount": 99.99
    }
  - Expected Status: 202

Action: Add validation
  - JSON Path: orderId
  - Expected Value: (empty - just verify exists)

Action: Click "✓ Apply"
Result: Step 1 configured and visible in center panel
```

#### Step 4: Add Step 2 - Wait
```
Action: Click "⏱️ Wait"
Result: New step appears

Action: Configure step
Fields:
  - Step Name: "Wait for Queue Processing"
  - Duration: 3 seconds

Action: Click "✓ Apply"
Result: Step 2 configured
```

#### Step 5: Add Step 3 - Poll Status
```
Action: Click "🔄 Poll/Verify"
Result: New step appears

Action: Configure step
Fields:
  - Step Name: "Wait for Order Processing"
  - Poll Condition: "Order status becomes 'processed'"
  - Max Wait Time: 60 seconds

Action: Click "✓ Apply"
Result: Step 3 configured
```

#### Step 6: Add Step 4 - Final Verification
```
Action: Click "🌐 API Call"
Result: New step appears

Action: Configure step
Fields:
  - Step Name: "Verify Final Order Status"
  - HTTP Method: GET
  - Endpoint: /orders/{orderId}
  - Expected Status: 200

Action: Add validations
  Validation 1:
    - JSON Path: status
    - Expected Value: "processed"
  Validation 2:
    - JSON Path: paymentStatus
    - Expected Value: "completed"

Action: Click "✓ Apply"
Result: Step 4 configured
```

#### Step 7: Save Test
```
Action: Click "💾 Save Test" button
Result: 
  - Success message: "Test saved successfully!"
  - Test ID assigned: "test_20240101_120000"
  - Test appears in Dashboard
```

#### Step 8: Execute Test
```
Action: Navigate to Dashboard
Location: Click "🏠 Dashboard"

Action: Find test
Location: "My Tests" card

Action: Click "▶️ Play" button
Result: Redirected to Test Runner

Action: Test executes automatically
Result: 
  - Execution output shows in real-time
  - Results summary updates
  - Green checkmarks for passed steps
```

#### Step 9: Review Results
```
Location: Test Runner page

View Execution Output:
  ✓ Starting execution of 1 test(s)...
  ✓ Running test: test_20240101_120000
  ✓ Step 1: Create Order - PASSED
  ✓ Step 2: Wait for Queue Processing - PASSED
  ✓ Step 3: Wait for Order Processing - PASSED
  ✓ Step 4: Verify Final Order Status - PASSED
  ✓ Test test_20240101_120000 passed

View Results Summary:
  Total Tests: 1
  Passed: 1
  Failed: 0
```

---

## Quick Reference: Tosca to Our Framework

### Creating a Test
**Tosca:** Right-click → New → TestCase  
**Our Framework:** Click "Test Builder" → Fill properties → Add steps

### Adding a Step
**Tosca:** Drag TestStep from Module to TestCase  
**Our Framework:** Click step type button → Configure in right panel

### Configuring API Call
**Tosca:** Set Action Mode → Configure parameters  
**Our Framework:** Select HTTP method → Enter endpoint → Add body → Set validations

### Adding Verification
**Tosca:** Add Buffer Verification TestStep  
**Our Framework:** Add validation in API Call step or use Poll/Verify step

### Running Test
**Tosca:** Right-click TestCase → Execute  
**Our Framework:** Select test → Click "Run Selected"

### Viewing Results
**Tosca:** Execution List → Select execution → View details  
**Our Framework:** Test Runner → View execution output and results summary

---

## Tips for Non-Coders

1. **Start Simple**
   - Begin with one API call
   - Add complexity gradually

2. **Use Descriptive Names**
   - Step names should explain what they do
   - Test names should describe the scenario

3. **Test in DEV First**
   - Always test in development environment
   - Verify test works before using in QA/PROD

4. **Check Validations**
   - Always validate important fields
   - Use JSON path correctly (case-sensitive)

5. **Save Frequently**
   - Click "Save Test" after major changes
   - Don't lose your work

6. **Review Execution Output**
   - Read error messages carefully
   - They tell you what went wrong

7. **Ask for Help**
   - Check this documentation
   - Review example tests
   - Consult with team members

---

This workflow mirrors Tosca's visual, no-code approach while being tailored for serverless API → Lambda → downstream testing scenarios.

