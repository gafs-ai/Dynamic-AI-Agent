from enum import Enum
from typing import Any
import json

from .ai_operation_type import AiOperationType
from .ai_deployment_type import AiDeploymentType
from .model_catalogue import ModelStatus
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider, SurrealDbRemoteProvider

class LogicalOperator(Enum):
    """Logical operator for combining tag conditions."""

    AND = "AND"
    OR = "OR"


class VectorSearchCriteria:
    """Criteria for vector (embedding) similarity search.

    The distance metric is not set here; SurrealDB uses the HNSW index default.

    Attributes:
        vector: Query vector for similarity.
        vector_limit: Maximum number of nearest neighbours to return.
        options: Optional parameters (e.g. ``effort`` for HNSW, if supported by the server).
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
        if vector_limit is not None:
            self.vector_limit = vector_limit
        if options is not None:
            self.options = options

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "vector":
            if isinstance(value, list):
                object.__setattr__(self, "vector", value)
            else:
                raise ValueError
        elif name == "vector_limit":
            if isinstance(value, int):
                object.__setattr__(self, "vector_limit", value)
            else:
                raise ValueError
        elif name == "options":
            if isinstance(value, dict):
                object.__setattr__(self, "options", value)
            else:
                raise ValueError
        else:
            if not isinstance(self.options, dict):
                object.__setattr__(self, "options", {})
            self.options[name] = value

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.vector is not None:
            result["vector"] = self.vector
        if self.vector_limit is not None:
            result["vector_limit"] = self.vector_limit
        if self.options is not None:
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


class TagsSearchCriteria:
    """Criteria for tag-based filtering (AND or OR of tags).

    Attributes:
        tags: List of tag values to match.
        operator: LogicalOperator.AND or OR for combining tags.
    """

    tags: list[str]
    operator: LogicalOperator = LogicalOperator.AND

    def __init__(
        self,
        tags: list[str],
        operator: LogicalOperator = LogicalOperator.AND,
    ) -> None:
        """Initialize tags criteria.

        Args:
            tags: List of tag values.
            operator: AND or OR for combining tag conditions.
        """
        super().__setattr__("tags", tags)
        super().__setattr__("operator", operator)

    def __setattr__(self, name: str, value: Any) -> None:
        """Validate and set operator; delegate rest to super."""
        if name == "operator" and isinstance(value, str):
            try:
                super().__setattr__(name, LogicalOperator[value.upper()])
            except KeyError:
                raise ValueError(f"Invalid logical operator: {value}") from None
        else:
            super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a JSON-serializable structure."""
        result: dict[str, Any] = {}
        if self.tags is not None:
            result["tags"] = self.tags
        if self.operator is not None:
            if recursive:
                result["operator"] = self.operator.value
            else:
                result["operator"] = self.operator
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))


class ModelCatalogueSearchCriteria:
    """Search criteria for model catalogue queries.

    All optional; combined with AND. status, keywords, tags, and
    deployment_types use OR within their group.

    Attributes:
        name: Filter by model name (contains).
        type: Filter by model type.
        status: Filter by status (OR); default [RECOMMENDED, ACTIVE]. None = no status filter.
        vector: Optional vector similarity criteria.
        keywords: Filter by keywords (OR).
        min_priority: Minimum priority (>=).
        tags: Filter by tags (OR).
        deployment_types: Filter by deployment type in deployments array (OR).
        min_confidence_level: Minimum max_confidence_level in deployments (>=).
        limit: Maximum number of results; default 100.
    """

    @staticmethod
    def _default_search_status() -> list[ModelStatus]:
        """Return default status filter for search (RECOMMENDED, ACTIVE)."""
        return [ModelStatus.RECOMMENDED, ModelStatus.ACTIVE]

    def __init__(
        self,
        name: str | None = None,
        type: AiOperationType | None = None,  # noqa: A002
        status: list[ModelStatus] | None = None,
        vector: VectorSearchCriteria | None = None,
        keywords: list[str] | None = None,
        min_priority: int = 0,
        tags: TagsSearchCriteria | None = None,
        deployment_types: list[AiDeploymentType] | None = None,
        min_confidence_level: int = 0,
        limit: int = 100,
    ) -> None:
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "type", None)
        object.__setattr__(self, "status", self._default_search_status())
        object.__setattr__(self, "vector", None)
        object.__setattr__(self, "keywords", None)
        object.__setattr__(self, "min_priority", 0)
        object.__setattr__(self, "tags", None)
        object.__setattr__(self, "deployment_types", None)
        object.__setattr__(self, "min_confidence_level", 0)
        object.__setattr__(self, "limit", 100)

        if name is not None:
            self.name = name
        if type is not None:
            self.type = type
        if status is not None:
            self.status = status
        if vector is not None:
            self.vector = vector
        if keywords is not None:
            self.keywords = keywords
        self.min_priority = min_priority
        if tags is not None:
            self.tags = tags
        if deployment_types is not None:
            self.deployment_types = deployment_types
        self.min_confidence_level = min_confidence_level
        self.limit = limit

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "name":
            if isinstance(value, str):
                object.__setattr__(self, "name", value)
            else:
                raise ValueError
        elif name == "type":
            if isinstance(value, AiOperationType):
                object.__setattr__(self, "type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "type", AiOperationType(value))
            else:
                raise ValueError
        elif name == "status":
            if isinstance(value, list):
                if len(value) > 0 and isinstance(value[0], str):
                    converted: list[ModelStatus] = []
                    for item in value:
                        converted.append(ModelStatus(item))
                    object.__setattr__(self, "status", converted)
                else:
                    object.__setattr__(self, "status", value)
            else:
                raise ValueError
        elif name == "vector":
            if isinstance(value, VectorSearchCriteria):
                object.__setattr__(self, "vector", value)
            elif isinstance(value, dict):
                object.__setattr__(self, "vector", VectorSearchCriteria.from_dict(value))
            else:
                raise ValueError
        elif name == "keywords":
            if isinstance(value, list):
                object.__setattr__(self, "keywords", value)
            else:
                raise ValueError
        elif name == "min_priority":
            if isinstance(value, int):
                object.__setattr__(self, "min_priority", value)
            else:
                raise ValueError
        elif name == "tags":
            if isinstance(value, TagsSearchCriteria):
                object.__setattr__(self, "tags", value)
            elif isinstance(value, dict):
                object.__setattr__(self, "tags", TagsSearchCriteria(**value))
            else:
                raise ValueError
        elif name == "deployment_types":
            if isinstance(value, list):
                if len(value) > 0 and isinstance(value[0], str):
                    converted_dt: list[AiDeploymentType] = []
                    for item in value:
                        converted_dt.append(AiDeploymentType(item))
                    object.__setattr__(self, "deployment_types", converted_dt)
                else:
                    object.__setattr__(self, "deployment_types", value)
            else:
                raise ValueError
        elif name == "min_confidence_level":
            if isinstance(value, int):
                object.__setattr__(self, "min_confidence_level", value)
            else:
                raise ValueError
        elif name == "limit":
            if isinstance(value, int):
                object.__setattr__(self, "limit", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.name is not None:
            result["name"] = self.name
        if self.type is not None:
            result["type"] = self.type.value if recursive else self.type
        if self.status is not None:
            if recursive:
                result["status"] = [s.value for s in self.status]
            else:
                result["status"] = self.status
        if self.vector is not None:
            result["vector"] = (
                self.vector.to_dict(recursive=recursive) if recursive else self.vector
            )
        if self.keywords is not None:
            result["keywords"] = self.keywords
        if self.min_priority is not None:
            result["min_priority"] = self.min_priority
        if self.tags is not None:
            result["tags"] = self.tags.to_dict(recursive=recursive)
        if self.deployment_types is not None:
            if recursive:
                result["deployment_types"] = [dt.value for dt in self.deployment_types]
            else:
                result["deployment_types"] = self.deployment_types
        if self.min_confidence_level is not None:
            result["min_confidence_level"] = self.min_confidence_level
        if self.limit is not None:
            result["limit"] = self.limit
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelCatalogueSearchCriteria":
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
        self, database_provider: IDatabaseProvider, collection_name: str
    ) -> str:
        """Build a SurrealQL query string from this criteria.

        Supports SurrealDbRemoteProvider only. Uses WHERE conditions and
        optional vector similarity (<| k |>), and LIMIT.

        Args:
            database_provider: Provider used to decide query form (e.g. SurrealQL).
            collection_name: Table/collection name in the query.

        Returns:
            A full SurrealQL SELECT query string.

        Raises:
            NotImplementedError: When the provider is not SurrealDbRemoteProvider.
        """
        if not isinstance(database_provider, SurrealDbRemoteProvider):
            raise NotImplementedError(
                f"Database provider {type(database_provider)} is not supported "
                "for Model Catalogue Database."
            )

        if self.vector is not None:
            query: str = f"SELECT *, vector::distance::knn() as distance FROM {collection_name} WHERE"
        else:
            query: str = f"SELECT * FROM {collection_name} WHERE"
        need_and: bool = False

        if self.vector is not None:
            query += f" description_vector <|{self.vector.vector_limit}"
            if "effort" in self.vector.options:
                query += f", {self.vector.options['effort']}"
            # kNN without explicit distance: uses the vector index default.
            query += "|>" + json.dumps(self.vector.vector)
            need_and = True
        
        #TODO: Need to support p for Minkowski distance

        if self.name is not None:
            if need_and:
                query += " AND"
            query += f" `name` ∋ '{self.name}'"
            need_and = True

        if self.type is not None:
            if need_and:
                query += " AND"
            query += f" `type` ∋ '{self.type.value}'"
            need_and = True

        if self.status is not None:
            if need_and:
                query += " AND"
            if len(self.status) == 1:
                query += f" status = '{self.status[0].value}'"
            else:
                query += f" (status = '{self.status[0].value}'"
                for index in range(1, len(self.status)):
                    query += f" OR status = '{self.status[index].value}'"
                query += ")"
            need_and = True

        if self.keywords is not None:
            if need_and:
                query += " AND"
            if len(self.keywords) == 1:
                query += f" description ∋ '{self.keywords[0]}'"
            else:
                query += f" (description ∋ '{self.keywords[0]}'"
                for index in range(1, len(self.keywords)):
                    query += f" OR description ∋ '{self.keywords[index]}'"
                query += ")"
            need_and = True

        if self.min_priority > 0:
            if need_and:
                query += " AND"
            query += f" priority >= {self.min_priority}"
            need_and = True

        if self.tags is not None:
            if need_and:
                query += " AND"
            if len(self.tags.tags) == 1:
                query += f" tags ∋ '{self.tags.tags[0]}'"
            else:
                query += f" (tags ∋ '{self.tags.tags[0]}'"
                for index in range(1, len(self.tags.tags)):
                    query += f" OR tags ∋ '{self.tags.tags[index]}'"
                query += ")"
            need_and = True

        if self.deployment_types is not None and len(self.deployment_types) > 0:
            if need_and:
                query += " AND"
            deployment_type_values = " OR ".join(
                f"deployment_type = '{dt.value}'" for dt in self.deployment_types
            )
            query += (
                " (array::any(deployments ?? [], |$d| "
                f"array::len((SELECT VALUE id FROM model_deployments WHERE {deployment_type_values} AND array::last(string::split(string::concat(id), ':')) = $d)) > 0))"
            )
            need_and = True

        if self.min_confidence_level > 0:
            if need_and:
                query += " AND"
            query += (
                " (array::any(deployments ?? [], |$d| "
                f"array::len((SELECT VALUE id FROM model_deployments WHERE max_confidence_level >= {self.min_confidence_level} AND array::last(string::split(string::concat(id), ':')) = $d)) > 0))"
            )
            need_and = True

        if not need_and:
            query += " true"
        if self.vector is not None:
            query += " ORDER BY distance"
        if self.limit > 0:
            query += f" LIMIT {self.limit}"

        query += ";"
        
        return query
