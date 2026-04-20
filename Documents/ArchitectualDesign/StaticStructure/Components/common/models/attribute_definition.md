---
class: AttributeDefinition
kind: data_class
module: gafs.dynamicaiagent.common.models
---

## attributes

| name               | type                                         | required | description                                                                                                                                                                                                                                                                                                                                      |
| ------------------ | -------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `key`              | `str`                                        | yes      | Key (or name) of the attribute.                                                                                                                                                                                                                                                                                                                  |
| `description`      | `str \| None`                                | no       | Optional human-readable description.                                                                                                                                                                                                                                                                                                             |
| `type`             | `FieldAttributeType`                         | yes      | Data type of the value(s).                                                                                                                                                                                                                                                                                                                       |
| `allowed_values`   | `set[int] \| set[float] \| set[str] \| None` | no       | Set of allowed values. The element types must match the scalar base of `type`. If the set is non-empty, any value assigned to the attribute must be a member of this set; otherwise validation fails.                                                                                                                                             |
| `min`              | `int \| float \| None`                       | no       | Allowed minimum value (inclusive). Applicable only for `INT` and `FLOAT` types.                                                                                                                                                                                                                                                                  |
| `max`              | `int \| float \| None`                       | no       | Allowed maximum value (exclusive). Applicable only for `INT` and `FLOAT` types.                                                                                                                                                                                                                                                                  |
| `custom_validator` | `str \| None`                                | no       | `function_id` of a custom validation function called on set / update of the field. References a `ToolCatalogue` entry managed as a `validated_by` edge internally. Exposed as a plain attribute value when communicated to callers. |

## notes

- `type` accepts both `FieldAttributeType` enum instances and their string values (auto-converted).
- `allowed_values` accepts both `set` and `list` inputs; stored internally as a `set`. Serialized as a sorted `list` in `to_dict` / `to_json`.
- `min` and `max` accept both `int` and `float`, and then casted to the defined `type`.
- Supports `from_dict` / `from_json` / `to_dict(recursive: bool = False)` / `to_json()`.


