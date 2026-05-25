"""model_catalogue_search_criteria.py - Search criteria for the ModelCatalogue collection.

Provides the criteria classes (ModelCatalogueSearchCriteria) and supporting types
(LogicalOperator, TagsSearchCriteria, VectorSearchCriteria) used to build SurrealQL
queries for model catalogue searches.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider
from gafs.dynamicaiagent.utils.databaseprovider.surrealdbremote import SurrealDbRemoteProvider

from .ai_deployment_type import AiDeploymentType
from .ai_operation_type import AiOperationType
from .model_catalogue import ModelStatus


# ---------------------------------------------------------------------------
# Supporting types
# ---------------------------------------------------------------------------

class LogicalOperator(Enum):
    """Logical operator for combining multiple tag conditions."""

    AND = "AND"
    OR = "OR"


class TagsSearchCriteria:
    """Criteria for tag-based filtering.

    Attributes:
        tags: List of tag values to match.
        operator: ``AND`` or ``OR`` for combining tag conditions.
    """

    def __init__(
        self,
        tags: list[str] | None = None,
        operator: LogicalOperator = LogicalOperator.OR,
    ) -> None:
        object.__setattr__(self, "tags", tags if tags is not None else [])
        object.__setattr__(self, "operator", operator)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "tags":
            if isinstance(value, list):
                object.__setattr__(self, "tags", value)
            else:
                raise ValueError("tags must be list[str]")
        elif name == "operator":
            if isinstance(value, LogicalOperator):
                object.__setattr__(self, "operator", value)
            elif isinstance(value, str):
                object.__setattr__(self, "operator", LogicalOperator[value.upper()])
            else:
                raise ValueError(f"operator must be LogicalOperator or str, got {type(value)}")
        else:
            raise ValueError(f"Unknown attribute: {name}")

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        return {
            "tags": self.tags,
            "operator": self.operator.value if recursive else self.operator,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TagsSearchCriteria":
        tags = data.get("tags", [])
        operator = data.get("operator", LogicalOperator.OR)
        return cls(tags=tags, operator=operator)


class VectorSearchCriteria:
    """Criteria for HNSW vector similarity search.

    Attributes:
        vector: Query vector for similarity search.
        vector_limit: Maximum number of nearest neighbours to return.
        options: Optional HNSW parameters (e.g. ``effort``).
    """

    def __init__(
        self,
        vector: list[float] | None = None,
        vector_limit: int = 10,
        options: dict[str, int] | None = None,
    ) -> None:
        object.__setattr__(self, "vector", None)
        object.__setattr__(self, "vector_limit", 10)
        object.__setattr__(self, "options", {})

        if vector is not None:
            self.vector = vector
        self.vector_limit = vector_limit
        if options is not None:
            self.options = options

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "vector":
            if isinstance(value, list):
                object.__setattr__(self, "vector", [float(v) for v in value])
            else:
                raise ValueError("vector must be list[float]")
        elif name == "vector_limit":
            if isinstance(value, int):
                object.__setattr__(self, "vector_limit", value)
            else:
                raise ValueError(f"vector_limit must be int, got {type(value)}")
        elif name == "options":
            if isinstance(value, dict):
                object.__setattr__(self, "options", value)
            else:
                raise ValueError("options must be dict")
        else:
            raise ValueError(f"Unknown attribute: {name}")

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.vector is not None:
            result["vector"] = self.vector
        result["vector_limit"] = self.vector_limit
        if self.options:
            result["options"] = self.options
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VectorSearchCriteria":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "VectorSearchCriteria":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


# ---------------------------------------------------------------------------
# Main search criteria
# ---------------------------------------------------------------------------

class ModelCatalogueSearchCriteria:
    """Search criteria for model catalogue queries.

    All filters are optional and combined with AND across fields.
    Multi-value filters (``status``, ``deployment_types``) are combined with OR
    within their field.

    Attributes:
        name: Filter by exact model name.
        type: Filter by operation type.
        status: Filter by lifecycle status (OR); defaults to ``[ACTIVE]``.
        keywords: Full-text search keywords (OR).
        deployment_types: Filter by deployment type via linked deployments (OR).
        vector_search: Vector similarity search parameters.
        tags: Tag filter.
        limit: Maximum number of results.
    """

    @staticmethod
    def _default_status() -> list[ModelStatus]:
        return [ModelStatus.ACTIVE]

    def __init__(
        self,
        name: str | None = None,
        type: AiOperationType | None = None,  # noqa: A002
        status: list[ModelStatus] | None = None,
        keywords: list[str] | None = None,
        deployment_types: list[AiDeploymentType] | None = None,
        vector_search: VectorSearchCriteria | None = None,
        tags: TagsSearchCriteria | None = None,
        limit: int = 100,
    ) -> None:
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "type", None)
        object.__setattr__(self, "status", self._default_status())
        object.__setattr__(self, "keywords", None)
        object.__setattr__(self, "deployment_types", None)
        object.__setattr__(self, "vector_search", None)
        object.__setattr__(self, "tags", None)
        object.__setattr__(self, "limit", 100)

        if name is not None:
            self.name = name
        if type is not None:
            self.type = type
        if status is not None:
            self.status = status
        if keywords is not None:
            self.keywords = keywords
        if deployment_types is not None:
            self.deployment_types = deployment_types
        if vector_search is not None:
            self.vector_search = vector_search
        if tags is not None:
            self.tags = tags
        self.limit = limit

    def __setattr__(self, name: str, value: Any) -> None:  # noqa: C901
        if name == "name":
            if isinstance(value, str):
                object.__setattr__(self, "name", value)
            else:
                raise ValueError(f"name must be str, got {type(value)}")
        elif name == "type":
            if isinstance(value, AiOperationType):
                object.__setattr__(self, "type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "type", AiOperationType(value))
            else:
                raise ValueError(f"type must be AiOperationType or str, got {type(value)}")
        elif name == "status":
            if isinstance(value, list):
                converted: list[ModelStatus] = []
                for item in value:
                    if isinstance(item, ModelStatus):
                        converted.append(item)
                    elif isinstance(item, str):
                        converted.append(ModelStatus(item))
                    else:
                        raise ValueError(f"status items must be ModelStatus or str, got {type(item)}")
                object.__setattr__(self, "status", converted)
            else:
                raise ValueError("status must be list[ModelStatus]")
        elif name == "keywords":
            if isinstance(value, list):
                object.__setattr__(self, "keywords", value)
            else:
                raise ValueError("keywords must be list[str]")
        elif name == "deployment_types":
            if isinstance(value, list):
                converted_dt: list[AiDeploymentType] = []
                for item in value:
                    if isinstance(item, AiDeploymentType):
                        converted_dt.append(item)
                    elif isinstance(item, str):
                        converted_dt.append(AiDeploymentType(item))
                    else:
                        raise ValueError(f"deployment_types items must be AiDeploymentType or str, got {type(item)}")
                object.__setattr__(self, "deployment_types", converted_dt)
            else:
                raise ValueError("deployment_types must be list[AiDeploymentType]")
        elif name == "vector_search":
            if isinstance(value, VectorSearchCriteria):
                object.__setattr__(self, "vector_search", value)
            elif isinstance(value, dict):
                object.__setattr__(self, "vector_search", VectorSearchCriteria.from_dict(value))
            else:
                raise ValueError(f"vector_search must be VectorSearchCriteria or dict, got {type(value)}")
        elif name == "tags":
            if isinstance(value, TagsSearchCriteria):
                object.__setattr__(self, "tags", value)
            elif isinstance(value, dict):
                object.__setattr__(self, "tags", TagsSearchCriteria.from_dict(value))
            else:
                raise ValueError(f"tags must be TagsSearchCriteria or dict, got {type(value)}")
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
        if self.type is not None:
            result["type"] = self.type.value if recursive else self.type
        if self.status is not None:
            result["status"] = [s.value for s in self.status] if recursive else self.status
        if self.keywords is not None:
            result["keywords"] = self.keywords
        if self.deployment_types is not None:
            result["deployment_types"] = (
                [dt.value for dt in self.deployment_types] if recursive else self.deployment_types
            )
        if self.vector_search is not None:
            result["vector_search"] = (
                self.vector_search.to_dict(recursive=recursive) if recursive else self.vector_search
            )
        if self.tags is not None:
            result["tags"] = self.tags.to_dict(recursive=recursive) if recursive else self.tags
        result["limit"] = self.limit
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelCatalogueSearchCriteria":
        if not isinstance(data, dict):
            raise ValueError("data must be a dict")
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "ModelCatalogueSearchCriteria":
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

        Supports SurrealDB remote providers only.

        Args:
            database_provider: The database provider (must be SurrealDbRemoteProvider).
            collection_name: The collection / table name to query.

        Returns:
            A full SurrealQL SELECT query string.

        Raises:
            NotImplementedError: When the provider is not SurrealDbRemoteProvider.
        """
        if not isinstance(database_provider, SurrealDbRemoteProvider):
            raise NotImplementedError(
                f"Database provider {type(database_provider)} is not supported "
                "for ModelCatalogue queries."
            )

        # Start building the SELECT clause.
        # For vector searches, add edge-resolved deployments and distance column.
        if self.vector_search is not None:
            select = (
                f"SELECT *, ->deployed_as->model_deployments.id AS deployments, "
                f"vector::distance::knn() AS distance FROM {collection_name} WHERE"
            )
        else:
            select = (
                f"SELECT *, ->deployed_as->model_deployments.id AS deployments "
                f"FROM {collection_name} WHERE"
            )

        conditions: list[str] = []

        # Vector KNN condition must appear first in the WHERE clause.
        if self.vector_search is not None:
            vs = self.vector_search
            knn_part = f"description_vector <|{vs.vector_limit}"
            if "effort" in vs.options:
                knn_part += f", {vs.options['effort']}"
            knn_part += "|> " + json.dumps(vs.vector)
            conditions.append(knn_part)

        if self.name is not None:
            escaped = self.name.replace("'", "''")
            conditions.append(f"name = '{escaped}'")

        if self.type is not None:
            conditions.append(f"`type` = '{self.type.value}'")

        if self.status:
            status_parts = [f"status = '{s.value}'" for s in self.status]
            if len(status_parts) == 1:
                conditions.append(status_parts[0])
            else:
                conditions.append("(" + " OR ".join(status_parts) + ")")

        if self.keywords:
            kw_parts = [f"description @@ '{kw.replace(chr(39), chr(39)*2)}'" for kw in self.keywords]
            if len(kw_parts) == 1:
                conditions.append(kw_parts[0])
            else:
                conditions.append("(" + " OR ".join(kw_parts) + ")")

        if self.tags and self.tags.tags:
            tag_parts = [f"tags ∋ '{t.replace(chr(39), chr(39)*2)}'" for t in self.tags.tags]
            if self.tags.operator == LogicalOperator.AND:
                conditions.append(" AND ".join(tag_parts) if len(tag_parts) > 1 else tag_parts[0])
            else:
                if len(tag_parts) == 1:
                    conditions.append(tag_parts[0])
                else:
                    conditions.append("(" + " OR ".join(tag_parts) + ")")

        if self.deployment_types:
            dt_values = " OR ".join(
                f"deployment_type = '{dt.value}'" for dt in self.deployment_types
            )
            deployment_table = "model_deployments"
            conditions.append(
                f"(array::any(->deployed_as->model_deployments, |$d| "
                f"$d.deployment_type IN [{', '.join(repr(dt.value) for dt in self.deployment_types)}]))"
            )

        if not conditions:
            conditions.append("true")

        where_clause = " AND ".join(conditions)
        query = f"{select} {where_clause} LIMIT {self.limit};"
        return query
