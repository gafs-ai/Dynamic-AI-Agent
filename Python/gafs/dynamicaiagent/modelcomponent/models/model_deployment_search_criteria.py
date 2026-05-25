"""model_deployment_search_criteria.py - Search criteria for the model_deployments collection."""

from __future__ import annotations

import json
from typing import Any

from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider
from gafs.dynamicaiagent.utils.databaseprovider.surrealdbremote import SurrealDbRemoteProvider

from .ai_deployment_type import AiDeploymentType
from .ai_provider_type import AiProviderType
from .model_catalogue import DeploymentStatus
from .model_catalogue_search_criteria import TagsSearchCriteria


class ModelDeploymentSearchCriteria:
    """Search criteria for model deployment queries.

    All filters are optional and combined with AND across fields.
    Multi-value filters (``deployment_types``, ``provider_types``, ``status``)
    are combined with OR within their field.

    Attributes:
        name: Filter by exact deployment name.
        deployment_types: Filter by deployment type (OR).
        provider_types: Filter by provider type (OR).
        status: Filter by deployment status (OR); defaults to ``[ACTIVE]``.
        keywords: Full-text search keywords (OR).
        min_priority: Minimum priority threshold (inclusive).
        tags: Tag filter.
        min_confidence_level: Minimum ``max_confidence_level`` required.
        limit: Maximum number of results.
    """

    @staticmethod
    def _default_status() -> list[DeploymentStatus]:
        return [DeploymentStatus.ACTIVE]

    def __init__(
        self,
        name: str | None = None,
        deployment_types: list[AiDeploymentType] | None = None,
        provider_types: list[AiProviderType] | None = None,
        status: list[DeploymentStatus] | None = None,
        keywords: list[str] | None = None,
        min_priority: int = 0,
        tags: TagsSearchCriteria | None = None,
        min_confidence_level: int = 0,
        limit: int = 100,
    ) -> None:
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "deployment_types", None)
        object.__setattr__(self, "provider_types", None)
        object.__setattr__(self, "status", self._default_status())
        object.__setattr__(self, "keywords", None)
        object.__setattr__(self, "min_priority", 0)
        object.__setattr__(self, "tags", None)
        object.__setattr__(self, "min_confidence_level", 0)
        object.__setattr__(self, "limit", 100)

        if name is not None:
            self.name = name
        if deployment_types is not None:
            self.deployment_types = deployment_types
        if provider_types is not None:
            self.provider_types = provider_types
        if status is not None:
            self.status = status
        if keywords is not None:
            self.keywords = keywords
        self.min_priority = min_priority
        if tags is not None:
            self.tags = tags
        self.min_confidence_level = min_confidence_level
        self.limit = limit

    def __setattr__(self, name: str, value: Any) -> None:  # noqa: C901
        if name == "name":
            if isinstance(value, str):
                object.__setattr__(self, "name", value)
            else:
                raise ValueError(f"name must be str, got {type(value)}")
        elif name == "deployment_types":
            if isinstance(value, list):
                converted: list[AiDeploymentType] = []
                for item in value:
                    if isinstance(item, AiDeploymentType):
                        converted.append(item)
                    elif isinstance(item, str):
                        converted.append(AiDeploymentType(item))
                    else:
                        raise ValueError(f"deployment_types items must be AiDeploymentType or str, got {type(item)}")
                object.__setattr__(self, "deployment_types", converted)
            else:
                raise ValueError("deployment_types must be list")
        elif name == "provider_types":
            if isinstance(value, list):
                # Store as-is since AiProviderType is an abstract enum; subclass values are accepted.
                object.__setattr__(self, "provider_types", value)
            else:
                raise ValueError("provider_types must be list")
        elif name == "status":
            if isinstance(value, list):
                converted_s: list[DeploymentStatus] = []
                for item in value:
                    if isinstance(item, DeploymentStatus):
                        converted_s.append(item)
                    elif isinstance(item, str):
                        converted_s.append(DeploymentStatus(item))
                    else:
                        raise ValueError(f"status items must be DeploymentStatus or str, got {type(item)}")
                object.__setattr__(self, "status", converted_s)
            else:
                raise ValueError("status must be list")
        elif name == "keywords":
            if isinstance(value, list):
                object.__setattr__(self, "keywords", value)
            else:
                raise ValueError("keywords must be list[str]")
        elif name == "min_priority":
            if isinstance(value, int):
                object.__setattr__(self, "min_priority", value)
            else:
                raise ValueError(f"min_priority must be int, got {type(value)}")
        elif name == "tags":
            if isinstance(value, TagsSearchCriteria):
                object.__setattr__(self, "tags", value)
            elif isinstance(value, dict):
                object.__setattr__(self, "tags", TagsSearchCriteria.from_dict(value))
            else:
                raise ValueError(f"tags must be TagsSearchCriteria or dict, got {type(value)}")
        elif name == "min_confidence_level":
            if isinstance(value, int):
                object.__setattr__(self, "min_confidence_level", value)
            else:
                raise ValueError(f"min_confidence_level must be int, got {type(value)}")
        elif name == "limit":
            if isinstance(value, int):
                object.__setattr__(self, "limit", value)
            else:
                raise ValueError(f"limit must be int, got {type(value)}")
        else:
            raise ValueError(f"Unknown attribute: {name}")

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.name is not None:
            result["name"] = self.name
        if self.deployment_types is not None:
            result["deployment_types"] = (
                [dt.value for dt in self.deployment_types] if recursive else self.deployment_types
            )
        if self.provider_types is not None:
            if recursive:
                result["provider_types"] = [
                    pt.value if hasattr(pt, "value") else pt for pt in self.provider_types
                ]
            else:
                result["provider_types"] = self.provider_types
        if self.status is not None:
            result["status"] = [s.value for s in self.status] if recursive else self.status
        if self.keywords is not None:
            result["keywords"] = self.keywords
        result["min_priority"] = self.min_priority
        if self.tags is not None:
            result["tags"] = self.tags.to_dict(recursive=recursive) if recursive else self.tags
        result["min_confidence_level"] = self.min_confidence_level
        result["limit"] = self.limit
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelDeploymentSearchCriteria":
        if not isinstance(data, dict):
            raise ValueError("data must be a dict")
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "ModelDeploymentSearchCriteria":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)

    def to_query(
        self,
        database_provider: IDatabaseProvider,
        collection_name: str,
    ) -> str:
        """Build a SurrealQL SELECT query string from this criteria.

        Args:
            database_provider: The database provider (must be SurrealDbRemoteProvider).
            collection_name: The collection / table name to query.

        Returns:
            Full SurrealQL SELECT query string.

        Raises:
            NotImplementedError: When the provider is not SurrealDbRemoteProvider.
        """
        if not isinstance(database_provider, SurrealDbRemoteProvider):
            raise NotImplementedError(
                f"Database provider {type(database_provider)} is not supported "
                "for ModelDeployment queries."
            )

        select = (
            f"SELECT *, ->references_secret->Secrets.id AS secrets "
            f"FROM {collection_name} WHERE"
        )
        conditions: list[str] = []

        if self.name is not None:
            escaped = self.name.replace("'", "''")
            conditions.append(f"name = '{escaped}'")

        if self.deployment_types:
            dt_parts = [f"deployment_type = '{dt.value}'" for dt in self.deployment_types]
            if len(dt_parts) == 1:
                conditions.append(dt_parts[0])
            else:
                conditions.append("(" + " OR ".join(dt_parts) + ")")

        if self.provider_types:
            pt_parts = [
                f"provider_type = '{pt.value if hasattr(pt, 'value') else pt}'"
                for pt in self.provider_types
            ]
            if len(pt_parts) == 1:
                conditions.append(pt_parts[0])
            else:
                conditions.append("(" + " OR ".join(pt_parts) + ")")

        if self.status:
            st_parts = [f"status = '{s.value}'" for s in self.status]
            if len(st_parts) == 1:
                conditions.append(st_parts[0])
            else:
                conditions.append("(" + " OR ".join(st_parts) + ")")

        if self.keywords:
            kw_parts = [f"description @@ '{kw.replace(chr(39), chr(39)*2)}'" for kw in self.keywords]
            if len(kw_parts) == 1:
                conditions.append(kw_parts[0])
            else:
                conditions.append("(" + " OR ".join(kw_parts) + ")")

        if self.min_priority > 0:
            conditions.append(f"priority >= {self.min_priority}")

        if self.tags and self.tags.tags:
            tag_parts = [f"tags ∋ '{t.replace(chr(39), chr(39)*2)}'" for t in self.tags.tags]
            if self.tags.operator.value == "AND":
                conditions.append(" AND ".join(tag_parts) if len(tag_parts) > 1 else tag_parts[0])
            else:
                if len(tag_parts) == 1:
                    conditions.append(tag_parts[0])
                else:
                    conditions.append("(" + " OR ".join(tag_parts) + ")")

        if self.min_confidence_level > 0:
            conditions.append(f"max_confidence_level >= {self.min_confidence_level}")

        if not conditions:
            conditions.append("true")

        where_clause = " AND ".join(conditions)
        query = f"{select} {where_clause} LIMIT {self.limit};"
        return query
