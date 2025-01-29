# Test Plan for `formatting.py`

**Module Overview:**
This module provides utility functions for formatting and displaying output in the terminal. It includes functions for debug information, success messages, warnings, and status updates using the `rich` library.

**Functionality to Test:**

1. **Formatting Functions:**
    - **`debug_header(message)`**
        - **Description:** Prints a debug header message with appropriate styling.
        - **Test Cases:**
            - Verify that the message is formatted with the correct color and prefix.
            - Handle empty or extremely long messages gracefully.
        - **How to Test:**
            - Use `pytest-mock` to mock `rich.print` and assert that it is called with the correctly formatted string.
            - Test with different message inputs and verify output consistency.

    - **`debug_item(label, value)`**
        - **Description:** Prints a debug item with an optional value.
        - **Test Cases:**
            - Verify correct formatting when `value` is provided.
            - Verify correct formatting when `value` is `None`.
            - Handle labels and values with special characters or spaces.
        - **How to Test:**
            - Mock `rich.print` using `pytest-mock` and assert that it receives the correctly formatted strings for both cases.

    - **`debug_json(data, indent)`**
        - **Description:** Prints formatted JSON data with debug styling.
        - **Test Cases:**
            - Verify that JSON data is correctly indented and formatted.
            - Handle empty dictionaries and complex nested structures.
            - Ensure that newline characters are properly escaped and displayed.
        - **How to Test:**
            - Use `pytest-mock` to mock `rich.print` and assert that the JSON string is formatted as expected.
            - Test with various JSON inputs to ensure correctness.

    - **`debug_preview(text, num_lines)`**
        - **Description:** Prints a preview of text content limited to a specified number of lines.
        - **Test Cases:**
            - Verify that only the first `num_lines` lines are displayed.
            - Handle cases where `text` has fewer lines than `num_lines`.
            - Ensure proper formatting with the preview indicator.
        - **How to Test:**
            - Mock `rich.print` using `pytest-mock` and assert that the previewed text matches expectations.
            - Test with different `num_lines` values and text inputs.

    - **`success(message)`**
        - **Description:** Prints a success message with a checkmark.
        - **Test Cases:**
            - Verify that the success message includes the checkmark and is styled correctly.
            - Handle empty or extremely long messages gracefully.
        - **How to Test:**
            - Mock `rich.print` using `pytest-mock` and assert that it is called with the correctly formatted success message.

    - **`warning(message)`**
        - **Description:** Prints a warning message with appropriate styling.
        - **Test Cases:**
            - Verify correct formatting and color of warning messages.
            - Handle empty or special character-containing messages.
        - **How to Test:**
            - Use `pytest-mock` to mock `rich.print` and assert that the warning message is formatted as expected.

    - **`status(message)`**
        - **Description:** Creates a status context with a styled message.
        - **Test Cases:**
            - Verify that the status context is created with the correct message and styling.
            - Ensure that the status context can be used as a context manager without errors.
        - **How to Test:**
            - Mock `rich.console.Console.status` using `pytest-mock` and assert that it is called with the correctly formatted message.
            - Use context managers in tests to ensure proper entry and exit.

**Types of Testing:**

- **Unit Testing:** Utilize `pytest` and `pytest-mock` to mock the `rich` library's `Console` and `print` functions, capturing and verifying the output of each formatting function.
- **Snapshot Testing:** Employ `pytest-snapshot` to capture the output of formatting functions and compare them against expected snapshots to detect unintended changes.
- **Edge Case Testing:** Test formatting functions with empty strings, very long messages, and special characters using `pytest` to ensure robustness.
- **Integration Testing:** Use the formatting functions in combination with other modules to ensure seamless integration and correct output formatting. 