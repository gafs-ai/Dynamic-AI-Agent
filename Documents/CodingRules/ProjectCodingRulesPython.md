# Project Coding Rules

## Terminology

- **Public**: Variables, methods, or classes that are intended to be accessed or called from outside the file. These should not have a leading underscore (_) in their names.
- **Private**: Variables, methods, or classes that are intended to be used only within the file. These must have a leading underscore (_) in their names.


## Basic Coding Rules

1. Class
    1. Define all variables and methods inside the class.
    2. One public class per file.

2. Variable
    1. Always use **type hints** for public variables. Variables must have a fixed type and cannot change their type after initialization.
    2. **Define all class-level variables in the constructor** (initialize as None or default value).
    3. Define as public only if the variable is intended to be accessed from outside the class.
    4. Getter / Setter: If you want to validate input or make the variable read-only from outside the class, use the `@property`, `@{property_name}.setter` pattern. You can use this pattern when you want to check the input value in the setter.
        Example:
        ```python
        @property
        def name(self) -> str:
            return self._name
        
        @name.setter
        def name(self, value: str) -> None:
            if not value:
                raise ValueError("Name cannot be empty")
            self._name = value
        ```

3. Methods
    1. Use **type hints** for parameters and return values.
    2. Define as public only if the method is intended to be called from outside the class.

4. Naming Conventions
    1. Package & Directory/Folder
        - **lowercase** (short, all-lowercase names). No underscores.
        - Examples: `common`, `edgeaicomponent`, `utils`
    2. File (Module)
        - **snake_case** (lowercase with underscores)
        - Should match the primary class name in snake_case format
        - Examples: `win_ml.py`, `edge_ai_exception.py`, `application_exception.py`
    3. Class
        - **CamelCaseClassName** for public classes
        - **_CamelCaseClassName** for private classes
    4. Variable
        - **UPPER_SNAKE_CASE_NAME** for public constants
        - **_UPPER_SNAKE_CASE_NAME** for private constants
        - **snake_case_variable_name** for public variables
        - **_snake_case_variable_name** for private variables
    5. Method
        - **snake_case_method_name** for public methods
        - **_snake_case_method_name** for private methods
        - **snake_case_parameter_name** for parameters
        - **snake_case_variable_name** for internal variables

5. Indent
    - 4 spaces

6. Comments, Messages, and Other Text in Code
    1. Always write in English.
    2. Write descriptions for **classes**, *public* **methods**, and *public* **variables**. Use triple double quotes (""") for docstrings.
    3. Docstring format:
       ```python
       class MyClass:
           """Brief description of the class.
           
           Longer description if needed.

           NOTE: Important notice for other engineers.
           """
           
           def public_method(self, param: str) -> bool:
               """Brief description of the method.
               
               Args:
                   param: Description of the parameter.
               
               Returns:
                   Description of the return value.
               
               Raises:
                   ValueError: When param is invalid.

               NOTE: Important notice for other engineers.
               """
               ...
       ```
    4. Use **NOTE: Your Comment** if the comment is important for other engineers.
    5. Use **TODO: Your Task** if a task is left to be done later.

7. Imports
    1. Import order (from top to bottom):
        - Standard library imports
        - Related third party imports
        - Local application/library specific imports (from `gafs.dynamicaiagent.*`)
    2. Import style rules:
        - Use **absolute imports** when importing from a different component (e.g., from `edgeaicomponent` to `common`).
        - Use **relative imports** when importing within the same package/component (e.g., within `edgeaicomponent`).
    3. One import per line for standard library and third-party imports.
    4. Group imports with a blank line between groups.
    5. Examples:
       ```python
       import os
       import sys
       
       import logging
       from enum import Enum
       
       # Absolute import: different component
       from gafs.dynamicaiagent.common.exceptions import ApplicationException
       
       # Relative import: same package
       from .exceptions import EdgeAiException
       from .win_ml import WinML
       ```
    6. NOTE: Do not use old-style imports without the package prefix (e.g., `from edgeaicomponent import ...`).

8. Type Hints

    - `Type | None` (e.g., `str | None`) for variables that can be None
    - `list[Type]` for lists (e.g., `list[str]`). Avoid initializing lists as None; initialize as empty lists instead (e.g., `new_list: list[int] = []`)
    - `dict[KeyType, ValueType]` for dictionaries (e.g., `dict[str, int]`). Avoid initializing dicts as None; initialize as empty dicts instead (e.g., `new_dict: dict[str, any] = {}`)
    - `tuple[Type, ...]` for tuples (e.g., `tuple[str, int]` or `tuple[int, ...]`)
    - Do not use `Type1 | Type2` (e.g., `int | str`) as all variables must have a fixed type
    - You can use `any` type only for dicts

9. Error Handling
    1. Always use try-except blocks when calling external APIs, file operations, or database operations.
    2. Log errors using the logger before re-raising or handling exceptions.
    3. Example:
       ```python
       try:
           result = external_api.call()
       except ConnectionError as e:
           self.logger.error(f"Connection failed: {e}")
           raise ApiConnectionException("Failed to connect to external service", cause=e)
       except ValueError as e:
           self.logger.warning(f"Invalid parameter value: {e}")
           raise UnexpectedValueException(f"Invalid parameter value.", cause=e)
       except Exception as e:
           self.logger.error(f"Unexpected exception: {e}")
           raise ComponentException(cause=e)
       ```

10. Logging
    1. Use the logger instance passed to the initializer. Do not create a new logger.
    2. Log levels (from lowest to highest severity):
       - `logger.debug()`: Detailed information for debugging. Indicate which operations succeed or fail. You can include parameters for the operations for diagnostics.
       - `logger.info()`: Messages that should be recorded in regular use cases.
       - `logger.warning()`: Warning messages for potentially problematic situations. Use when something unexpected happened, but the application can continue to work.
       - `logger.error()`: Error messages for error conditions. Use when an error occurred, but the application can still continue to operate (e.g., a single operation failed, but other operations can still succeed). In components, exceptions will usually be recorded at this level (except for CoreComponent for the entire application or modules for critical operations).
       - `logger.critical()`: Critical error messages. Use when a serious error occurred that may cause the application to stop or fail completely (e.g., database connection completely lost, memory exhaustion, security breach, critical system resource unavailable).
    3. Include relevant context in log messages (e.g., variable values, operation names).
    4. Example:
       ```python
       self.logger.debug(f"Connecting to the database...")
       self.logger.info(f"Processing {count} items")
       self.logger.error(f"Failed to save data for item {item_id}: {error_message}", exc_info=True)
       ```

11. Async/Await
    1. Use `async def` for methods that perform I/O operations (database, network, file operations).
    2. Use `await` when calling async methods if you want to wait for the response.
    3. Type hints for async methods should use `->` with the actual return type.
    4. Example:
       ```python
       async def fetch_data(self, id: str) -> Data | None:
           result = await self.database.get(id)
           return result
       ```

12. File and Directory Structure
    1. One class per file (except for sets of exception classes or small helper classes).
    2. File names should match the primary class name in the file (using snake_case).
    3. Create `__init__.py` files in each **package directory** to make it a Python package.
       - NOTE: The `Python` folder itself is **not** treated as a package and must **not** have `__init__.py`.
    4. Keep related files in the same directory/package.

13. Package Structure
    1. Base Package Name and Folder Layout
        - The project uses `gafs.dynamicaiagent` as the base package name.
        - The **project root** (this repository root) is the Python import root.
        - The `Python/` folder is just a **source folder**, not a Python package.
        - The `gafs/` folder under `Python/` is the **top-level package**, and must have `__init__.py`.
        - The `dynamicaiagent/` folder under `gafs/` is the **application base package**, and must have `__init__.py`.
    2. Component Packages
        - Each component should be organized as a sub-package under `gafs.dynamicaiagent`.
        - Component package names should be lowercase without underscores (e.g., `common`, `edgeaicomponent`).
        - Each component package should have its own `__init__.py` file.
        - Examples:
          - `gafs.dynamicaiagent.edgeaicomponent` for Edge AI components
    3. Package Structure Example
    ```
    - (repository root)/
        - Python/
            - gafs/ # top-level package: gafs
                - __init__.py
                - dynamicaiagent/ # base application package: gafs.dynamicaiagent
                    - __init__.py
                    - edgeaicomponent/ # gafs.dynamicaiagent.edgeaicomponent
                        - __init__.py
                        - i_edge_ai_component.py
                        - win_ml.py
                        - exceptions/
                            - __init__.py
                            - edge_ai_exception.py
    ```
    4. Import Statements
        - **Absolute imports** when importing from a different component.
          - Example: From `edgeaicomponent` to `common`:
            ```python
            from gafs.dynamicaiagent.common.exceptions import ApplicationException
            ```
        - **Relative imports** when importing within the same package/component.
          - Example: Within `edgeaicomponent`:
            ```python
            from .exceptions import EdgeAiException
            from .win_ml import WinML
            ```
        - Do not use old-style imports without the package prefix (e.g., `from edgeaicomponent import ...`).
        - NOTE: This approach balances clarity (absolute imports show component boundaries) with brevity (relative imports for internal references).
    5. Package Documentation
        - Each `__init__.py` file should include a docstring describing the package.
        - The docstring should follow the format: `gafs.dynamicaiagent.{component_name} - {description}`.
        - Example:
          ```python
          """
          gafs.dynamicaiagent.edgeaicomponent - Edge AI functionality.
          """
          ```

14. Initialization
    1. Always define the `__init__` method for classes that need initialization.
    2. Initialize **all instance variables** in `__init__` with type hints.
    3. Initialize instance variables as None or default values.
    4. `__init__` should only contain necessary operations to create an instance. Define a separate `initialize(params...)` function if the instance needs additional initialization operations including API access, DB access, or other types of external access.
    5. Example:
       ```python
       def __init__(self):
           self.name: str = ""
           self.count: int = 0
           self.config: dict[str, str] | None = None
       ```

15. Documentation or Other Files
    1. Documentation:
        - Document Language: English
        - Contents:
            - Structure of the Component
                - Folder
                - File
                - Class (You only need to show public classes)
            - List of Methods / Variables intended to be called / accessed from outside your component
        - Dependencies & Libraries
            - Dependency / Library Name
            - Dependency / Library Website URLs
            - Dependency / Library License Name
            - Dependency / Library License URI
    2. requirements.txt
        - Create `requirements.txt` at the component level.

NOTE: Please reference `PEP8` for coding rules not defined above. If `PEP8` or other PEP documentation conflicts with this document, the definitions in this document take priority.


## Type of Classes / Design & Coding Rules of each type of class

### Data Class

**IMPORTANT**: This project **prohibits** the use of `@dataclass` and `@dataclass_json` decorators for data classes. Custom serialization and validation logic must be implemented manually.

For detailed data class implementation guidelines, see [DataClassCodingRulesPython.md](./DataClassCodingRulesPython.md).

- File Name: `{document_name}.py` (snake_case)
- Class Name: `{DocumentName}` (PascalCase)
- Required Methods:
    - `def __init__(self)`: Initialize all fields to `None` or appropriate default values. **Must not** accept parameters other than `self`.
    - `def __setattr__(self, name: str, value: Any) -> None`: Custom setter with type validation and conversion logic.
    - `def to_dict(self, recursive: bool = False, ...) -> dict[str, Any]`: Convert to dictionary. The `recursive` parameter is **mandatory**.
    - `def to_json(self, ...) -> str`: Convert to JSON string.
    - `@classmethod def from_dict(cls, data: dict[str, Any]) -> {DocumentName}`: Create instance from dictionary.
    - `@classmethod def from_json(cls, json_str: str) -> {DocumentName}`: Create instance from JSON string.
- Optional Methods:
    - `__eq__(self, other)`: If you compare database entities, return true if the documents are different versions of the same document.
    - `__lt__(self, other)`: If the entity classes are comparable
    - `def is_same_version_as(self, other)`
    - `def is_valid(self)`: If validation is required
    - Note that methods for CRUD operations are expected to be defined in the repository class.


### Option Class

- File Name: `{component_name}_options.py` (snake_case)
- Class Name: `{ComponentName}Options` (PascalCase)
- Decorator Policy:
    - `@dataclass` from `dataclasses` is allowed **only** for simple internal configuration containers.
    - `@dataclass_json` from `dataclasses_json` is **prohibited**.
- Serialization / Deserialization:
    - Do not use automatic JSON-to-object conversion decorators.
    - If options are loaded from external inputs (file, API, environment variables, or user input), implement explicit validation logic (for example, a `from_dict()` method) and reject invalid or unknown fields.
    - If data integrity is important, validate input data before creating the option object.
- Methods:
    - If the option class is expected to be persisted to a database or file as a domain entity, follow the **Data Class** rules in full (manual serialization/deserialization and custom validation logic; no `@dataclass`).


### Repository Class

Repository Class is a type of class included in a component and is responsible for data operations—especially for database operations, but file operations, memory operations, or other types of data operations will be implemented as Repository Class.

- File Name: `{document_name}_repository.py` (snake_case) - e.g., `model_catalogue_repository.py` for AI Model Catalogue.
- Class Name: `{DocumentName}Repository` (PascalCase)
- Initializer:
    - Implement `def initialize(logger: Logger, provider: DatabaseProvider)` as the initializer.
    - This method should be called after creating an instance with `__init__`.
    - Store logger and provider as instance variables for later use.
    - This method should be async if I/O operations (including database connections) are required.


### Interface (Abstract Base Class) of Component Classes

Component Class is the main class of the component and contains component operations that are intended to be called from outside the component.

- File Name: `i_{component_name}.py` (snake_case) - e.g., `i_edge_ai_component.py` for Edge AI Component.
- Class Name: `I{ComponentName}` (PascalCase)


### Implementations of Component Classes

- File Name (snake_case):
    - `{component_name}.py` if only one implementation is expected.
    - `{service_name}.py` if multiple implementations are expected - e.g., `win_ml.py` for WinML implementation of Edge AI Component.
- Initializer:
    - Implement `def initialize(logger: Logger, options: {ComponentName}Options)` as the initializer. The initializer can be implemented as an *async* method if a database request or internal request is required, or if the initialization operation is expected to take more than 1 second.
    - This method should be called after creating an instance with `__init__`.
    - Store logger and options as instance variables for later use.


### Exception Classes

#### Base Exception Class (Component Level)

- File Name: `{component_name}_exception.py` (snake_case) - e.g., `edge_ai_exception.py` for Edge AI Component.
- Class Name: `{ComponentName}Exception` (PascalCase)
- Constructor:
    - Extend the `ApplicationException` base exception class of the application.


#### Exception Classes

Create exception classes that extend your base exception class of your component for potential exceptions.


##### When to Implement Exception Classes and Throw Exceptions

Implement exception classes and throw exceptions when the exception occurs due to the *environment* (anything that is not under your control). This includes the following examples:

1. When your program is communicating with the internet, the internet can be disconnected or the remote server can be temporarily unavailable.
2. When a client (or user) of your program sends malformed data or calls a method of your program when it is not ready to be called.


##### How to Throw and Handle Exceptions

1. Throw your component's exception when an error occurs that is related to your component's responsibility.
2. Include meaningful error messages that help with debugging.
3. Preserve the original exception using the `from` keyword when re-raising:
   ```python
   except ValueError as e:
       raise ComponentException("Failed to process data") from e
   ```
4. Do not catch exceptions unless you can handle them meaningfully or need to add context.


### Enum

Use enums when you are using a set of pre-defined options. Pay attention to enum values and ensure they are used consistently throughout the codebase.

- File Name: `{enum_name}.py` (snake_case) - e.g., `processing_result.py` for processing result enum.
- Class Name: `{EnumName}` (PascalCase)
- Implementation:
    - Use the `Enum` class from the `enum` module.
    - Use `UPPER_SNAKE_CASE` for enum member names.
    - Use descriptive string values for enum members.
- Example:
    ```python
    from enum import Enum
    
    class ProcessingResult(Enum):
        SUCCESS = "success"
        NOT_FOUND = "not_found"
        ERROR = "error"
        TIMEOUT = "timeout"
    ```
- Usage:
    - Use enum values instead of magic strings or numbers.
    - Compare enum values using `==` operator (e.g., `result == ProcessingResult.SUCCESS`).
    - Access enum value using `.value` property when needed (e.g., `ProcessingResult.SUCCESS.value`).
