# Data Class Coding Rules (Python)

## Overview

This document defines the coding standards for data classes in this project. **The use of `@dataclass` and `@dataclass_json` decorators is prohibited** due to security concerns and the need for precise control over serialization, validation, and type conversion.

All data classes must implement custom serialization/deserialization methods and validation logic.

---

## 1. Prohibited Decorators

**DO NOT USE:**
- `@dataclass` from `dataclasses`
- `@dataclass_json` from `dataclasses_json`
- and other DataClass libraries

**Reason**: These decorators lack fine-grained control over:
- Type validation during attribute assignment
- Custom conversion logic (e.g., `dict` → custom object)
- Handling of `None` values
- Database-specific type handling (e.g., `RecordID` from SurrealDB)

---

## 2. Required Methods

All data classes must implement the following methods:

1. `__init__(self) -> None`
2. `__setattr__(self, name: str, value: Any) -> None`
3. `__repr__(self) -> str`
4. `to_dict(self, recursive=False,...) -> dict[str, Any]`
5. `to_json(self, ...) -> str`
6. `@classmethod from_dict(cls, data: dict[str, Any]) -> {ClassName}`
7. `@classmethod from_json(cls, json_str: str) -> {ClassName}`


### 2.1. `__init__(self)`

- **Must not** accept parameters other than `self`
- Initialize all fields to `None` or appropriate default values
- **Must** use `object.__setattr__(self, "field_name", value)` to bypass custom `__setattr__` validation
  - **Reason**: Using `self.field = value` triggers `__setattr__`, which may reject `None` values or cause issues during initialization
- **Do not** set default values other than `None`, even if a field should have a specific default value in normal use
  - **Reason**: Database records may have `null` values for fields, and setting defaults in `__init__` would prevent proper deserialization

**Example:**
```python
def __init__(self):
    object.__setattr__(self, "id", None)
    object.__setattr__(self, "name", None)
    object.__setattr__(self, "model_type", None)
    object.__setattr__(self, "priority", None)
    object.__setattr__(self, "tags", None)
    object.__setattr__(self, "config", None)
```

**Why `object.__setattr__`?**
- `self.id = None` would call the custom `__setattr__` method, which may raise `ValueError` for `None`
- `object.__setattr__(self, "id", None)` bypasses custom validation and directly sets the attribute
- This is only necessary in `__init__`; normal attribute assignment should use `self.field = value` to ensure validation

---

### 2.2. `__setattr__(self, name: str, value: Any) -> None`

- **Must** use `object.__setattr__(self, name, value)` to avoid infinite recursion
- **Must** include type validation for each field
- **Must** support automatic type conversion where appropriate. **`str` to `Enum`** and **`dict` to custom object** conversions are mandatory.
- **Must** raise `ValueError` for invalid types or values
- Error messages are optional (As the validation errors here are only expected to occur while development, so detailed massages are usually not required)

#### Type-Specific Validation Examples

##### 2.2.1. Primitive Type (String)

```python
elif name == "name":
    if isinstance(value, str):
        object.__setattr__(self, "name", value)
    else:
        raise ValueError
```

##### 2.2.2. Primitive Type (Integer)

```python
elif name == "priority":
    if isinstance(value, int):
        object.__setattr__(self, "priority", value)
    else:
        raise ValueError
```

##### 2.2.3. List of Primitive Types

```python
elif name == "tags":
    if isinstance(value, list):
        object.__setattr__(self, "tags", value)
    else:
        raise ValueError
```

**NOTE**: Runtime validation of list element types (e.g., `list[str]` vs `list[int]`) is not performed to avoid performance overhead. Type errors in list contents are acceptable during development.
**WRITE AS**: `if isinstance(value, list):`
**DON'T WRITE AS**: `if isinstance(value, list[str]):`

##### 2.2.4. Enum Type (with String Conversion)

```python
elif name == "model_type":
    if isinstance(value, ModelType):
        object.__setattr__(self, "model_type", value)
    elif isinstance(value, str):
        # Automatic conversion from string to Enum.
        # Try-Except is not required here, because ModelType(value) will raise ValueError for invalid values anyway.
        object.__setattr__(self, "model_type", ModelType(value))
    else:
        raise ValueError
```

##### 2.2.5. Custom Object Type

```python
elif name == "deployment":
    if isinstance(value, ModelDeployment):
        object.__setattr__(self, "deployment", value)
    else:
        raise ValueError
```

##### 2.2.6. List of Custom Objects (with Dict Conversion)

```python
elif name == "deployments":
    if isinstance(value, list):
        # Check only the first element (performance trade-off)
        if len(value) > 0 and isinstance(value[0], dict):
            converted: list[ModelDeployment] = []
            for item in value:
                converted.append(ModelCatalogue._deployment_from_dict(item))
            object.__setattr__(self, "deployments", converted)
        else:
            # Assume all elements are already ModelDeployment objects
            object.__setattr__(self, "deployments", value)
    else:
        raise ValueError
```

**Performance Note**: Only the first element is checked for dict type. This is a deliberate trade-off to avoid redundant validation. Errors from mixed types are acceptable.

##### 2.2.7. Else Statement

###### For Data Classes without inheritance

If the dataclass has no parent class, end `__setattr__` with the following else statement.

``` python
if name == "name":
    ...
elif name == "priority":
    ...
else:
    raise ValueError
```

###### For Data Classes with inheritance

If the dataclass inherits a parent class, end `__setattr__` with the following else statement.

``` python
if name == "name":
    ...
elif name == "priority":
    ...
else:
    super().__setattr__(name, value)
```

---

### 2.3. `__repr__(self) -> str`

``` python
def __repr__(self) -> str:
    return self.to_json(recursive=True)
```

### 2.4. `to_dict(self, recursive: bool = False, ...) -> dict[str, Any]`

- **Must** include the `recursive: bool = False` parameter (mandatory)
- **Should** include `exclude_id: bool = False` parameter if the class is persisted to a database
- Additional parameters are optional and can be added as needed
- When `recursive=True`, convert nested objects (Enum, custom objects) to primitive types
- When `recursive=False`, keep nested objects as-is

#### Type-Specific Conversion Examples

##### 2.4.1. Primitive Type

```python
if self.name is not None:
    result["name"] = self.name
if self.priority is not None:
    result["priority"] = self.priority
```

##### 2.4.2. List of Primitive Types

```python
if self.tags is not None:
    result["tags"] = self.tags
```

##### 2.4.3. Enum Type

```python
if self.model_type is not None:
    if recursive:
        result["model_type"] = self.model_type.value  # Convert to string
    else:
        result["model_type"] = self.model_type  # Keep as Enum
```

##### 2.4.4. Custom Object Type

```python
if self.deployment is not None:
    if recursive:
        result["deployment"] = self._deployment_to_dict(self.deployment)
    else:
        result["deployment"] = self.deployment
```

##### 2.4.5. List of Custom Objects

```python
if self.deployments is not None:
    if recursive:
        result["deployments"] = [self._deployment_to_dict(d) for d in self.deployments]
    else:
        result["deployments"] = self.deployments
```

##### 2.4.6. Exclude ID (for Database Persistence)

```python
if not exclude_id:
    if self.id is not None:
        result["id"] = self.id
```

**Complete Example:**
```python
def to_dict(self, recursive: bool = False, exclude_id: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {}

    if not exclude_id:
        if self.id is not None:
            result["id"] = self.id
    
    if self.name is not None:
        result["name"] = self.name
    
    if self.model_type is not None:
        if recursive:
            result["model_type"] = self.model_type.value
        else:
            result["model_type"] = self.model_type
    
    if self.priority is not None:
        result["priority"] = self.priority
    
    if self.tags is not None:
        result["tags"] = self.tags
    
    if self.deployments is not None:
        if recursive:
            result["deployments"] = [self._deployment_to_dict(d) for d in self.deployments]
        else:
            result["deployments"] = self.deployments
    
    return result
```

---

### 2.5. `to_json(self, ...) -> str`

- **Must** use `json.dumps(self.to_dict(recursive=True, ...))` to ensure proper JSON serialization
- **Should** always call `to_dict()` with `recursive=True` to convert all nested objects to primitive types

**Example:**
```python
def to_json(self, exclude_id: bool = False) -> str:
    return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))
```

**Why `recursive=True`?**
- JSON does not support Enum objects or custom classes
- All nested objects must be converted to primitive types (str, int, float, bool, list, dict, None)

---

### 2.6. `from_dict(cls, data: dict[str, Any]) -> {ClassName}`

- **Must** create a new instance using `cls()`
- **Must** use `setattr()` to set field values (leverages `__setattr__` validation logic)
- **Should** skip fields that are not present in `data`
- **Must** skip fields with `None` values to avoid `ValueError` from `__setattr__`

**Example:**
```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> "ModelCatalogue":
    entity = cls()
    
    for key, value in data.items():
        if hasattr(entity, key):
            if value is not None:  # Skip None values
                setattr(entity, key, value)
        else:
            continue  # Ignore unknown fields
    
    return entity
```

**Why skip `None` values?**
- Database records may have `null` values for optional fields
- `__setattr__` may raise `ValueError` when attempting to set `None` to a field
- Keeping the initial `None` from `__init__` is the correct behavior

---

### 2.7. `from_json(cls, json_str: str) -> {ClassName}`

- **Must** parse the JSON string using `json.loads()`
- **Must** validate that the result is a dictionary
- **Must** call `from_dict()` to create the instance

**Example:**
```python
@classmethod
def from_json(cls, json_str: str) -> "ModelCatalogue":
    converted: Any = json.loads(json_str)
    if not isinstance(converted, dict):
        raise ValueError
    return cls.from_dict(converted)
```

**Performance Note**: Avoid calling `json.loads()` twice. Reuse the `converted` variable.

---

## 3. Optional Methods

The following methods are optional and should be implemented if needed:

- `__eq__(self, other)`: For equality comparison
- `__lt__(self, other)`: For sorting
- `__hash__(self)`: For use in sets or as dict keys
- `is_valid(self) -> bool`: For validation logic
- `is_same_version_as(self, other) -> bool`: For version comparison (database entities)

---

## 4. Complete Example

Please check the `ModelCatalogue` class in `modelcomponent` if you need a complete example.

---

## 5. Inheritance Pattern

When a data class inherits from another data class, you need to call methods in parent class in the following methods:

1. `__init__`: Call the constractor of the parent class first.
2. `__setattr__`: Call `__setattr__` of parent class in the last else statement.
3. `to_dict`: Create `dict` with the `to_dict` method of the parent class first.

Other methods usually don't need to directly call the methods of the parent class.

### 5.1. `__init__` - Call Parent First

```python
def __init__(self) -> None:
    # Initialize parent class fields first
    super().__init__()
    
    # Initialize child class specific fields
    object.__setattr__(self, "child_field1", None)
    object.__setattr__(self, "child_field2", None)
    
    # Override parent class defaults if needed
    object.__setattr__(self, "parent_field", "child_specific_value")
```

### 5.2. `__setattr__` - Delegate to Parent

```python
def __setattr__(self, name: str, value: Any) -> None:
    if name == "child_field1":
        # Handle child-specific field
        if isinstance(value, str):
            object.__setattr__(self, "child_field1", value)
        else:
            raise ValueError
    elif name == "child_field2":
        # Handle another child-specific field
        ...
    else:
        # Delegate to parent for parent fields
        super().__setattr__(name, value)
```

### 5.3. `to_dict` - Call Parent and Add Child Fields

```python
def to_dict(self, recursive: bool = False) -> dict[str, Any]:
    # Get parent class fields
    result: dict[str, Any] = super().to_dict(recursive=recursive)
    
    # Add child class specific fields only
    if self.child_field1 is not None:
        result["child_field1"] = self.child_field1
    
    if self.child_field2 is not None:
        result["child_field2"] = self.child_field2
    
    return result
```

**Note**: Parent fields are already included by `super().to_dict()`, so only add child-specific fields.

### 5.4. `from_dict` - No Need to Call Parent

```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> "ChildClass":
    entity = cls()  # __init__ already calls super().__init__()
    
    for key, value in data.items():
        if hasattr(entity, key):
            if value is not None:
                setattr(entity, key, value)  # __setattr__ handles parent fields
        else:
            continue
    
    return entity
```

**Note**: No need to explicitly call parent's `from_dict()` because:
1. `cls()` calls `__init__()`, which calls `super().__init__()`
2. `setattr()` calls `__setattr__()`, which delegates to parent

### 5.5. Other Methods - Usually No Need to Call Parent

- `__repr__`: Just call `self.to_json()` (which uses inherited `to_dict`)
- `to_json`: Just call `self.to_dict(recursive=True)` (which already includes parent fields)
- `from_json`: Just call `cls.from_dict()` (which already handles everything)

### 5.6. Reference Implementation

For an example of inheritance, see:
- **Parent**: `DatabaseProviderOptions` in `Python/gafs/dynamicaiagent/utils/databaseprovider/i_database_provider.py`
- **Child**: `RemoteSurrealDbOptions` in `Python/gafs/dynamicaiagent/utils/databaseprovider/surrealdb_remote_provider.py`

---

## 6. Key Principles Summary

1. **No `@dataclass` or `@dataclass_json`**: Custom implementation required
2. **`__init__` without parameters**: Initialize all fields to `None` using `object.__setattr__()` to bypass validation
3. **`__setattr__` with validation**: Use `object.__setattr__()` to avoid recursion
4. **Enum conversion**: Support both Enum and string in `__setattr__`
5. **Dict-to-object conversion**: Handle `dict` input for nested objects in `__setattr__`
6. **`to_dict(recursive=True)`**: Convert Enums and nested objects to primitive types
7. **`to_json()` uses `to_dict(recursive=True)`**: Always convert to primitive types before JSON serialization
8. **`from_dict()` skips `None`**: Avoid `ValueError` from `__setattr__`
9. **Performance trade-offs**: Only check first element of lists for dict type
10. **Project-specific types**: Handle types like `RecordID` in `__setattr__`
11. **Inheritance**: Call `super()` in `__init__`, `__setattr__`, and `to_dict`; delegate parent fields appropriately

---

## 7. Reference Implementation

For a complete reference implementation, see:

**Non-inheritance example:**
- **File**: `Python/gafs/dynamicaiagent/modelcomponent/model_catalogue.py`
- **Classes**: `ModelCatalogue`, `ModelCatalogueSearchResultEntity`

**Inheritance example:**
- **Parent**: `DatabaseProviderOptions` in `Python/gafs/dynamicaiagent/utils/databaseprovider/i_database_provider.py`
- **Child**: `RemoteSurrealDbOptions` in `Python/gafs/dynamicaiagent/utils/databaseprovider/surrealdb_remote_provider.py`
