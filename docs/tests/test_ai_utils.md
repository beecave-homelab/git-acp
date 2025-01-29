# Test Plan for `ai_utils.py`

**Module Overview:**
This module provides utilities for AI-powered commit message generation, including the `AIClient` class for interacting with AI models, functions to create AI prompts, gather commit context, edit commit messages, and generate commit messages using AI.

**Functionality to Test:**

1. **`AIClient` Class:**
    - **Initialization:**
        - **Description:** Initializes the AI client with configuration settings.
        - **Test Cases:**
            - Successful initialization with valid configurations.
            - Handling invalid URLs or connection failures gracefully.
            - Ensuring that verbose mode triggers appropriate debug outputs.
        - **How to Test:**
            - Use `pytest-mock` to mock the `OpenAI` client, simulating successful and failed initializations.
            - Test with different configurations and assert that exceptions are raised for invalid setups using `pytest.raises`.

    - **`chat_completion(messages, **kwargs)`**
        - **Description:** Sends a chat completion request to the AI model and retrieves the response.
        - **Test Cases:**
            - Successful retrieval of AI-generated commit messages.
            - Handling timeouts and ensuring that `GitError` is raised.
            - Managing connection errors and invalid responses.
        - **How to Test:**
            - Use `pytest-mock` to mock the `OpenAI` client's `chat.completions.create` method, returning expected responses.
            - Simulate timeouts and connection errors and verify that `GitError` is raised with appropriate messages using `pytest.raises`.

2. **Prompt Creation Functions:**
    - **`create_advanced_commit_message_prompt(context, config)`**
        - **Description:** Creates a detailed AI prompt incorporating repository context for advanced commit message generation.
        - **Test Cases:**
            - Correct formatting of the advanced prompt with repository context.
            - Handling cases where context information is incomplete or missing.
        - **How to Test:**
            - Provide mock `context` dictionaries using `pytest` fixtures and assert that the generated prompt matches the expected format.
            - Test with partial or empty context to ensure graceful handling.

    - **`create_simple_commit_message_prompt(context, config)`**
        - **Description:** Creates a simple AI prompt for commit message generation.
        - **Test Cases:**
            - Correct formatting of the simple prompt.
            - Handling cases with minimal context.
        - **How to Test:**
            - Provide mock `context` dictionaries using `pytest` fixtures and assert that the generated prompt matches the expected format.

3. **Context Gathering:**
    - **`get_commit_context(config)`**
        - **Description:** Gathers Git repository context, including staged changes, recent commits, related commits, and commit patterns.
        - **Test Cases:**
            - Accurate retrieval of staged and unstaged changes.
            - Correct analysis of recent and related commits.
            - Handling cases with no commits or changes.
        - **How to Test:**
            - Use `pytest-mock` to mock functions like `get_diff`, `get_recent_commits`, and `find_related_commits` to provide controlled context data.
            - Assert that the returned context dictionary contains accurate and expected information.

4. **Commit Message Editing:**
    - **`edit_commit_message(message, config)`**
        - **Description:** Allows the user to edit the AI-generated commit message if interactive mode is enabled.
        - **Test Cases:**
            - Successfully editing a commit message when interactive mode is enabled.
            - Skipping editing when interactive mode is disabled.
            - Handling user cancellations or empty edits gracefully.
        - **How to Test:**
            - Use `pytest-mock` to mock `questionary.confirm` and `questionary.text`, simulating user interactions.
            - Assert that the edited message is returned correctly or that the original message is retained based on user input.

5. **Commit Message Generation:**
    - **`generate_commit_message(config)`**
        - **Description:** Orchestrates the process of generating a commit message using AI, including context gathering, prompt creation, AI interaction, and message editing.
        - **Test Cases:**
            - Successful end-to-end generation of commit messages with both simple and advanced prompts.
            - Handling failures at any stage (e.g., context gathering, AI interaction) and ensuring proper error reporting.
            - Verifying that edited commit messages are correctly returned.
        - **How to Test:**
            - Use `pytest-mock` to mock all dependent functions (`AIClient`, `get_commit_context`, etc.) to control the flow.
            - Simulate successful and failed AI responses and assert that `GitError` is raised appropriately using `pytest.raises`.
            - Verify that the final commit message matches expectations based on mocked inputs.

**Types of Testing:**

- **Unit Testing:** Utilize `pytest` and `pytest-mock` to mock external dependencies like the `OpenAI` client, `questionary` prompts, and Git operations. Test each function and method in isolation to ensure they handle inputs and outputs correctly.
- **Integration Testing:** Employ `pytest` to simulate AI responses and verify that commit messages are generated and formatted correctly when functions work together.
- **Functional Testing:** Use `pytest` to simulate user interactions for editing commit messages and verify the overall workflow, ensuring that end-to-end functionality works as intended.
- **Error Handling Testing:** Use `pytest-mock` to simulate various failure scenarios (e.g., AI timeouts, invalid configurations) and ensure that errors are handled gracefully with informative messages using `pytest.raises`. 