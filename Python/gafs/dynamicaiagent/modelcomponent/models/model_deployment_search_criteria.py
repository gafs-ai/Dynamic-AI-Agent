from __future__ import annotations

import json
from typing import Any

from .ai_deployment_type import AiDeploymentType
from .ai_provider_type import AiProviderType
from .model_catalogue import DeploymentStatus
from .model_catalogue_search_criteria import TagsSearchCriteria
from gafs.dynamicaiagent.utils.databaseprovider import (
    IDatabaseProvider,
    SurrealDbRemoteProvider,
)


class ModelDeploymentSearchCriteria:
    """Search criteria for model deployment queries.

    All filters are optional and combined with AND. Multi-value filters are
    combined with OR within each group.
    """

    @staticmethod
    def _default_search_status() -> list[DeploymentStatus]:
        """Return default deployment status filter (ACTIVE)."""
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
        object.__setattr__(self, "status", self._default_search_status())
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

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "name":
            if isinstance(value, str):
                object.__setattr__(self, "name", value)
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
        elif name == "provider_types":
            if isinstance(value, list):
                if len(value) > 0 and isinstance(value[0], str):
                    converted_pt: list[AiProviderType] = []
                    for item in value:
                        converted_pt.append(AiProviderType(item))
                    object.__setattr__(self, "provider_types", converted_pt)
                else:
                    object.__setattr__(self, "provider_types", value)
            else:
                raise ValueError
        elif name == "status":
            if isinstance(value, list):
                if len(value) > 0 and isinstance(value[0], str):
                    converted_status: list[DeploymentStatus] = []
                    for item in value:
                        converted_status.append(DeploymentStatus(item))
                    object.__setattr__(self, "status", converted_status)
                else:
                    object.__setattr__(self, "status", value)
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
        if self.deployment_types is not None:
            if recursive:
                result["deployment_types"] = [dt.value for dt in self.deployment_types]
            else:
                result["deployment_types"] = self.deployment_types
        if self.provider_types is not None:
            if recursive:
                result["provider_types"] = [pt.value for pt in self.provider_types]
            else:
                result["provider_types"] = self.provider_types
        if self.status is not None:
            if recursive:
                result["status"] = [s.value for s in self.status]
            else:
                result["status"] = self.status
        if self.keywords is not None:
            result["keywords"] = self.keywords
        if self.min_priority is not None:
            result["min_priority"] = self.min_priority
        if self.tags is not None:
            result["tags"] = self.tags
        if self.min_confidence_level is not None:
            result["min_confidence_level"] = self.min_confidence_level
        if self.limit is not None:
            result["limit"] = self.limit
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelDeploymentSearchCriteria":
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
        """Build a SurrealQL query string from this criteria."""
        if not isinstance(database_provider, SurrealDbRemoteProvider):
            raise NotImplementedError(
                f"Database provider {type(database_provider)} is not supported "
                "for Model Deployment Database."
            )

        query: str = f"SELECT * FROM {collection_name} WHERE"
        need_and: bool = False

        if self.name is not None:
            if need_and:
                query += " AND"
            query += f" name ∋ '{self.name}'"
            need_and = True

        if self.deployment_types is not None and len(self.deployment_types) > 0:
            if need_and:
                query += " AND"
            if len(self.deployment_types) == 1:
                query += f" deployment_type = '{self.deployment_types[0].value}'"
            else:
                query += f" (deployment_type = '{self.deployment_types[0].value}'"
                for index in range(1, len(self.deployment_types)):
                    query += (
                        f" OR deployment_type = '{self.deployment_types[index].value}'"
                    )
                query += ")"
            need_and = True

        if self.provider_types is not None and len(self.provider_types) > 0:
            if need_and:
                query += " AND"
            if len(self.provider_types) == 1:
                query += f" provider_type = '{self.provider_types[0].value}'"
            else:
                query += f" (provider_type = '{self.provider_types[0].value}'"
                for index in range(1, len(self.provider_types)):
                    query += f" OR provider_type = '{self.provider_types[index].value}'"
                query += ")"
            need_and = True

        if self.status is not None and len(self.status) > 0:
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

        if self.keywords is not None and len(self.keywords) > 0:
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

        if self.tags is not None and len(self.tags.tags) > 0:
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

        if self.min_confidence_level > 0:
            if need_and:
                query += " AND"
            query += f" max_confidence_level >= {self.min_confidence_level}"
            need_and = True

        if not need_and:
            query += " true"

        if self.limit > 0:
            query += f" LIMIT {self.limit}"

        query += ";"
        return query
