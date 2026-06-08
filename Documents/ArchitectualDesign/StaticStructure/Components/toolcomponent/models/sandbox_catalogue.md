## `SandboxType`

```
kind: enum
module: gafs.dynamicaiagent.toolcomponent.models
```

| name     | value      | description                                                     |
| -------- | ---------- | --------------------------------------------------------------- |
| `HOST`   | `"host"`   | Dummy definition that shows the code must be ran on the host os |
| `DOCKER` | `"docker"` | Docker sandbox                                                  |

---

## `SandboxStatus`

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

## `SandboxCatalogueEntry`

```
kind: abstract base class
module: gafs.dynamicaiagent.toolcomponent.models
```

### attributes

| name          | type          | required | description                                                                                                                                                     |
| ------------- | ------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`          | `str \| None` | yes      | Record ID. Normalized from SurrealDB `RecordID` (table prefix stripped).                                                                                        |
| `status`      | `SandboxStatus`  | yes      | Status of the sandbox                                                                                                                                           |
| `name`        | `str`         | yes      | Unique sandbox name                                                                                                                                             |
| `description` | `str \| None` | no       | Description of the sandbox                                                                                                                                      |
| `tags`        | `list[str]`   | no       | Optional tags for filtering.<br>The system will find the suitable sandbox by tags and status when the specific sandbox is not designated in the tool catalogue. |

### indexes

| field    | index_type | analyzer                                 | notes     |
| -------- | ---------- | ---------------------------------------- | --------- |
| `id`     | auto       | —                                        | automatic |
| `name`   | FULL TEXT  | Defined in `ToolComponentConfigurations` | BM25      |
| `status` | standard   | —                                        |           |
| `tags`   | standard   | —                                        |           |

---

## `SandboxCatalogueHostEntry`

```
kind: data class
extends: SandboxCatalogueEntry
module: gafs.dynamicaiagent.toolcomponent.models
```

### attributes

- No additional attributes.

---

## `SandboxCatalogueDockerEntry`

```
kind: data class
extends: SandboxCatalogueEntry
module: gafs.dynamicaiagent.toolcomponent.models
```

### attributes

- The table below contains all the additional attributes

| name          | type  | required | description                                                                                                                                           |
| ------------- | ----- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docker_file` | `str` | yes      | Dockerfile content that defines the image creation steps.                                                                                              |
| `run_options` | `str` | no       | Additional `docker run` options (e.g., `--memory 512m --cpus 1`). Must not override entrypoint, volumes, or container naming — those are set by the system. |

### notes

- The container is always started with `sleep infinity` as its command to keep it running for `docker exec`-based invocations.
- Volume mounts (`/app/codes` and `/app/data`) and the container name are managed exclusively by `IDockerSandboxService`.
