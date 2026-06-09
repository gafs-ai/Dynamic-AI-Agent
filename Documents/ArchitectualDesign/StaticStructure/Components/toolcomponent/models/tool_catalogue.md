## `ToolStatus`

```
kind: enum
module: gafs.dynamicaiagent.toolcomponent.models
```

| name          | value            | description                               |
| ------------- | ---------------- | ----------------------------------------- |
| `DEVELOPMENT` | `"development"`  | Under development                         |
| `EARLY`       | `"early_access"` | Early access / beta release               |
| `ACTIVE`      | `"active"`       | Available for use                         |
| `DEPRECATED`  | `"deprecated"`   | Scheduled for retirement; avoid new usage |
| `RETIRED`     | `"retired"`      | No longer available                       |

---

## `ToolVersionStatus`

```
kind: enum
module: gafs.dynamicaiagent.toolcomponent.models
```

| name          | value            | description                                    |
| ------------- | ---------------- | ---------------------------------------------- |
| `DEVELOPMENT` | `"development"`  | Under development                              |
| `EARLY`       | `"early_access"` | Early access / beta release                    |
| `LATEST`      | `"latest"`       | Latest version recommended for use             |
| `ACTIVE`      | `"active"`       | Available for use (but not the latest version) |
| `DEPRECATED`  | `"deprecated"`   | Scheduled for retirement; avoid new usage      |
| `RETIRED`     | `"retired"`      | No longer available                            |

---

## `InputParameterDefinition`

```
kind: sub data class
module: gafs.dynamicaiagent.toolcomponent.models
```

### attributes

| name             | type                 | required | description                                                                                                                                       |
| ---------------- | -------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`           | `str`                | yes      | Name of the parameter                                                                                                                             |
| `description`    | `str \| None`        | no       | Description of the parameter                                                                                                                      |
| `type`           | `FieldAttributeType` | yes      | Type of the value                                                                                                                                 |
| `required`       | `bool`               | yes      | Defines whether the value is required or not                                                                                                      |
| `default`        | `str`                | no       | Defines the default value.                                                                                                                        |
| `allowed_values` | `set[Any]`           | no       | Defines the allowed values.<br>The type of the values in the set must match the type defined in `type` field.                                     |
| `min_value`      | `Any`                | no       | Defines minimum value (including the boundary).<br>This field is only available for numerically comparable types (int, float, datetime, duration) |
| `max_value`      | `Any`                | no       | Defines maximum value (excluding the boundary).<br>This field is only available for numerically comparable types (int, float, datetime, duration) |

---

## `OutputParameterDefinition`

```
kind: sub data class
module: gafs.dynamicaiagent.toolcomponent.models
```

### attributes

| name          | type                 | required | description                                  |
| ------------- | -------------------- | -------- | -------------------------------------------- |
| `name`        | `str`                | yes      | Name of the parameter                        |
| `description` | `str \| None`        | no       | Description of the parameter                 |
| `type`        | `FieldAttributeType` | yes      | Type of the value                            |
| `nullable`    | `bool`               | yes      | Defines whether the value is nullable or not |

---

## `InputFileDefinition`

```
kind: sub data class
module: gafs.dynamicaiagent.toolcomponent.models
```

### attributes

| name          | type          | required | description                                      |
| ------------- | ------------- | -------- | ------------------------------------------------ |
| `name`        | `str`         | yes      | Name of the parameter                            |
| `description` | `str \| None` | no       | Description of the parameter                     |
| `min`         | `int`         | yes      | Minimum number of files (including the boundary) |
| `max`         | `int`         | yes      | Maximum number of files (excluding the boundary) |
| `max_size`    | `int`         | no       | Size limit of a single file                      |

---

## `OutputFileDefinition`

```
kind: sub data class
module: gafs.dynamicaiagent.toolcomponent.models
```

### attributes

| name          | type          | required | description                                      |
| ------------- | ------------- | -------- | ------------------------------------------------ |
| `name`        | `str`         | yes      | Name of the parameter                            |
| `description` | `str \| None` | no       | Description of the parameter                     |
| `min`         | `int`         | yes      | Minimum number of files (including the boundary) |
| `max`         | `int`         | yes      | Maximum number of files (excluding the boundary) |

---

## `ToolCatalogueEntry`

### constants (class methods)

| name               | return type | value             | description                                    |
| ------------------ | ----------- | ----------------- | ---------------------------------------------- |
| `CollectionName()` | `str`       | `"ToolCatalogue"` | SurrealDB collection name for this record type |


### attributes

| name                 | type                  | required | description                                                              |
| -------------------- | --------------------- | -------- | ------------------------------------------------------------------------ |
| `id`                 | `str \| None`         | yes      | Record ID. Normalized from SurrealDB `RecordID` (table prefix stripped). |
| `status`             | `ToolStatus`          | yes      | Status of the tool                                                       |
| `name`               | `str`                 | yes      | Unique tool name                                                         |
| `description`        | `str \| None`         | no       | Description of the tool                                                  |
| `description_vector` | `list[float] \| None` | no       | Embedding vector for similarity search                                   |
| `tags`               | `list[str]`           | no       | Optional tags for filtering                                              |

### indexes

| field                | index_type | analyzer                                 | notes     |
| -------------------- | ---------- | ---------------------------------------- | --------- |
| `id`                 | auto       | —                                        | automatic |
| `name`               | FULL TEXT  | Defined in `ToolComponentConfigurations` | BM25      |
| `status`             | standard   | —                                        |           |
| `description`        | FULL TEXT  | Defined in `ToolComponentConfigurations` | BM25      |
| `description_vector` | HNSW       | —                                        | dimensions and settings from `ToolComponentConfigurations` |
| `tags`               | standard   | —                                        |           |

---

## `ToolVersionEntry`

```
kind: abstract base class
module: gafs.dynamicaiagent.toolcomponent.models
```

### constants (class methods)

| name               | return type | value            | description                                    |
| ------------------ | ----------- | ---------------- | ---------------------------------------------- |
| `CollectionName()` | `str`       | `"ToolVersions"` | SurrealDB collection name for this record type |

### attributes

| name                     | type                              | required | description                                                                                                                                                                                                                                                             |
| ------------------------ | --------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`                     | `str \| None`                     | yes      | Record ID. Normalized from SurrealDB `RecordID` (table prefix stripped).                                                                                                                                                                                                |
| `tool_id`                | `str`                             | yes      | ID of the tool that references the id field of `ToolCatalogueEntry`                                                                                                                                                                                                     |
| `status`                 | `ToolVersionStatus`               | yes      | Status of the tool version                                                                                                                                                                                                                                              |
| `description`            | `str \| None`                     | no       | Optional description of the tool version                                                                                                                                                                                                                                |
| `language`               | `str`                             | yes      | Language of the program<br>e.g. "Python", "Python3.12"                                                                                                                                                                                                                  |
| `sandbox_id`             | `str`                             | no       | ID of the sandbox that references the id field of `SandboxCatalogueEntry`.<br>If this value is defined, the specified sandbox will be used as the execution environment; otherwise the system will find the suitable environment according to `sandbox_selection_tags`. |
| `sandbox_selection_tags` | `list[str]`                       | no       | List of tags that defines the selection of the execution environment.<br>The sandbox that contains all the specified tags will be used as the execution environment. This field cannot be used together with `sandbox_id`.                                              |
| `code`                   | `str \| None`                     | no       | Program code that is directly stored on the database.                                                                                                                                                                                                                   |
| `code_link`              | `str \| None`                     | no       | Link to the program code repository.                                                                                                                                                                                                                                    |
| `input_parameters`       | `list[InputParameterDefinition]`  | no       | List of parameters that are passed to the script.                                                                                                                                                                                                                       |
| `input_files`            | `list[InputFileDefinition]`       | no       | List of files that are passed to the script.                                                                                                                                                                                                                            |
| `output_parameters`      | `list[OutputParameterDefinition]` | no       | List of parameters that are outputs of the script.                                                                                                                                                                                                                      |
| `output_files`           | `list[OutputFileDefinition]`      | no       | List of parameters that are outputs of the script.                                                                                                                                                                                                                      |

### indexes

| field               | index_type | analyzer | notes     |
| ------------------- | ---------- | -------- | --------- |
| `id`                | auto       | —        | automatic |
| `tool_id`           | standard   | —        |           |
| `tool_id`, `status` | standard   | —        | composite |

### constraints

- `tool_id` must reference a valid tool id.
- Either `code` or `code_link` must not be null.
