# Testing Rules

## Test Code

Code-based testing primarily applies to testing logic-related code. Test requirements for User Interface are defined separately.

1. Create test files with the `test_` prefix (e.g., `test_my_module.py`).
2. OPTIONAL: You can use the **pytest** framework for testing.
3. Test all public methods and important private methods, as long as they can be tested independently.

## Secret Test Configuration Files

For test configuration files that contain secrets such as passwords, use the following naming convention:

- `secret_test_config_{number}.json` (e.g., `secret_test_config_0.json`, `secret_test_config_1.json`)

These files **must not** be committed to the repository, and the project `.gitignore` is configured to ignore such files.

## Mocking

You can **mock** external dependencies (databases, APIs) in tests if the target method cannot be tested independently but you need to test the method.
However, mocking is usually not required if the functionality of the method can be tested soon after with the actual dependencies.

## Test Report

Document the test execution and completion status in the documentation:

1. List the test files that were executed (e.g., `test_my_module.py`, `test_another_module.py`).
2. State that all tests have been completed.
3. Unless there are special notes, include a statement confirming that testing has been performed based on the code and that all tests have been completed successfully.
4. If the test results are considered to depend on the test execution environment, mention the execution environment (e.g., operating system, Python version, dependencies).
