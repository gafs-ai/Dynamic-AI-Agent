---
class: FullTextAnalyzer
kind: data_class
roles: [stored_model, request, response]
module: gafs.dynamicaiagent.common.databasemanager.models
collection: FullTextAnalyzers
related_classes:
  - FunctionDefinition
  - TokenizerDefinition
  - FilterDefinition
---

## constants

| name | type | value |
|------|------|-------|
| `COLLECTION_NAME()` | `str` | `"FullTextAnalyzers"` |

## attributes

| name        | type                        | required | description                       |
| ----------- | --------------------------- | -------- | --------------------------------- |
| `id`        | `str`                       | no       | Record ID                         |
| `name`      | `str`                       | yes      | Name of the analyzer              |
| `function`  | `list[FunctionDefinition]`  | no       | User-defined function definitions |
| `tokenizer` | `list[TokenizerDefinition]` | no       | Tokenizer definitions             |
| `filters`   | `list[FilterDefinition]`    | no       | Filter definitions                |
| `comment`   | `str \| None`               | no       | Optional comment                  |

## indexes

| field  | index_type       | analyzer      | notes     |
| ------ | ---------------- | ------------- | --------- |
| `id`   | auto             | —             | automatic |
| `name` | standard, unique | —             |           |
| `name` | FULL TEXT        | default ngram |           |


## methods

---

### DEFAULT_ANALYZER

```python
@staticmethod
def DEFAULT_ANALYZER() -> FullTextAnalyzer
```

| property | value |
|----------|-------|
| description | Return a `FullTextAnalyzer` instance for the default n-gram analyzer. |

#### returns

```json
{
  "id": "default_ngram_analyzer",
  "name": "default_ngram_analyzer",
  "tokenizers": [
    { "tokenizer": "blank" },
    { "tokenizer": "punct" }
  ],
  "filters": [
    { "filter": "ngram", "parameters": { "min": 3, "max": 5 } }
  ]
}
```

---

### DEFAULT_ENGLISH_ANALYZER

```python
@staticmethod
def DEFAULT_ENGLISH_ANALYZER() -> FullTextAnalyzer
```

| property | value |
|----------|-------|
| description | Return a `FullTextAnalyzer` instance for the default English snowball analyzer. |

#### returns

```json
{
  "id": "default_english_analyzer",
  "name": "default_english_analyzer",
  "tokenizers": [
    { "tokenizer": "blank" },
    { "tokenizer": "punct" }
  ],
  "filters": [
    { "filter": "snowball", "parameters": { "language": "english" } }
  ]
}
```

---

### validate_and_normalize

```python
def validate_and_normalize() -> bool
```

| property | value |
|----------|-------|
| description | Validate and normalize the entry by calling validation methods on all attributes. |

#### raises

| exception | condition |
|-----------|-----------|
| `DatabaseManagerInvalidAnalyzerException` | Validation fails |

---

### get_define_analyzer_statement

```python
def get_define_analyzer_statement(overwrite: bool = False) -> str
```

| property | value |
|----------|-------|
| description | Build the `DEFINE ANALYZER` SurrealQL statement for this analyzer. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `overwrite` | `bool` | no | If `True`, adds `OVERWRITE`; otherwise adds `IF NOT EXISTS`. |

---

### get_alter_analyzer_statement

```python
def get_alter_analyzer_statement() -> str
```

| property | value |
|----------|-------|
| description | Build the `ALTER ANALYZER` SurrealQL statement for this analyzer. |

---

### get_drop_analyzer_statement

```python
def get_drop_analyzer_statement() -> str
```

| property | value |
|----------|-------|
| description | Build the `REMOVE ANALYZER` SurrealQL statement for this analyzer. |

---

## related class: FunctionDefinition

### attributes

| name | type | required | description |
|------|------|----------|-------------|
| `name` | `str` | yes | Name of the user-defined function on SurrealDB. The function must be defined directly on SurrealDB. |
| ~~`parameters`~~ | `dict[str, Any] \| None` | — | Reserved. Not yet supported. |

---

## related class: TokenizerDefinition

### attributes

| name | type | required | description |
|------|------|----------|-------------|
| `tokenizer` | `SurrealTokenizer` | yes | Tokenizer type |
| ~~`parameters`~~ | `dict[str, Any] \| None` | — | Reserved. Not yet supported. |

---

## related class: FilterDefinition

### constants

| name | type | value |
|------|------|-------|
| `EDGENGRAM_DEFAULT_MIN()` | `int` | `3` |
| `EDGENGRAM_DEFAULT_MAX()` | `int` | `5` |
| `NGRAM_DEFAULT_MIN()` | `int` | `3` |
| `NGRAM_DEFAULT_MAX()` | `int` | `5` |
| `SNOWBALL_DEFAULT_LANGUAGE()` | `str` | `"english"` |

### attributes

| name | type | required | description |
|------|------|----------|-------------|
| `filter` | `SurrealFilter` | yes | Filter type |
| `parameters` | `dict[str, Any] \| None` | no | Filter parameters. Available keys depend on filter type (see parameters_schema). |

### parameters_schema

| key | type | applicable_filters | required | description |
|-----|------|-------------------|----------|-------------|
| `min` | `int` | `EDGENGRAM`, `NGRAM` | yes | Minimum n-gram size |
| `max` | `int` | `EDGENGRAM`, `NGRAM` | yes | Maximum n-gram size |
| `language` | `str` | `SNOWBALL` | yes | Language name string (e.g. `"english"`, `"french"`). Must be a value in `SurrealFilter.SNOWBALL_LANGUAGES()`. |

### methods

#### validate_and_normalize

```python
def validate_and_normalize() -> bool
```

| property | value |
|----------|-------|
| description | Validate and normalize filter parameters. |

##### rules

1. For `EDGENGRAM` or `NGRAM`: set `min`/`max` to defaults if not set. Raise if `min > max`, `min < 1`, or `max < 1`.
2. For `SNOWBALL`: set `language` to default if not set. Raise if unsupported language is specified.
3. Drop unsupported key-value pairs from `parameters`.

##### raises

| exception | condition |
|-----------|-----------|
| `DatabaseManagerInvalidAnalyzerException` | Validation fails |
