"""Serialize concept note metadata to canonical-order YAML."""

from __future__ import annotations

import re
from collections import OrderedDict
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, cast

import yaml

from studium.schemas import ConceptNoteMetadata
from studium.schemas.canonical import (
    CANONICAL_YAML_TOP_LEVEL_KEYS,
    LEARNING_ENCOUNTER_FIELD_ORDER,
    RELATIONSHIP_FIELD_ORDER,
    SCAFFOLD_MODULE_FIELD_ORDER,
    SOURCE_FIELD_ORDER,
)

_ISO_Z_DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def serialize_metadata_to_yaml(metadata: ConceptNoteMetadata) -> str:
    """Serialize metadata to YAML text in canonical key order."""
    ordered = metadata_to_ordered_dict(metadata)
    plain = _to_plain_containers(ordered)
    return yaml.dump(
        plain,
        Dumper=_StudiumYamlDumper,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )


def metadata_to_ordered_dict(metadata: ConceptNoteMetadata) -> OrderedDict[str, Any]:
    """Convert metadata to an ordered mapping ready for YAML serialization."""
    raw = metadata.model_dump(mode="json")
    ordered: OrderedDict[str, Any] = OrderedDict()
    for key in CANONICAL_YAML_TOP_LEVEL_KEYS:
        if key not in raw:
            continue
        value = raw[key]
        if key == "learning_encounters":
            ordered[key] = [_order_learning_encounter(encounter) for encounter in value]
        elif key == "scaffold_modules":
            ordered[key] = [_order_scaffold_module(module) for module in value]
        elif key == "relationships":
            ordered[key] = [_order_relationship(relationship) for relationship in value]
        elif key in {"created_at", "updated_at"}:
            ordered[key] = _format_datetime(value)
        else:
            ordered[key] = value
    return ordered


def _order_learning_encounter(encounter: Mapping[str, Any]) -> OrderedDict[str, Any]:
    ordered: OrderedDict[str, Any] = OrderedDict()
    for key in LEARNING_ENCOUNTER_FIELD_ORDER:
        if key == "source":
            source = encounter.get("source")
            if isinstance(source, Mapping):
                ordered[key] = _order_source(cast(Mapping[str, Any], source))
            continue
        ordered[key] = encounter.get(key)
    return ordered


def _order_source(source: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict((key, source.get(key)) for key in SOURCE_FIELD_ORDER)


def _order_scaffold_module(module: Mapping[str, Any]) -> OrderedDict[str, Any]:
    ordered: OrderedDict[str, Any] = OrderedDict()
    for key in SCAFFOLD_MODULE_FIELD_ORDER:
        if key in module:
            ordered[key] = module[key]
    return ordered


def _order_relationship(relationship: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict((key, relationship.get(key)) for key in RELATIONSHIP_FIELD_ORDER)


def _format_datetime(value: Any) -> str:
    if isinstance(value, datetime):
        dt = value.astimezone(UTC) if value.tzinfo is not None else value.replace(tzinfo=UTC)
        return dt.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(value)


def _to_plain_containers(value: Any) -> Any:
    if isinstance(value, OrderedDict):
        ordered = cast(OrderedDict[str, Any], value)
        return {key: _to_plain_containers(item) for key, item in ordered.items()}
    if isinstance(value, list):
        items = cast(list[Any], value)
        return [_to_plain_containers(item) for item in items]
    return value


class _StudiumYamlDumper(yaml.SafeDumper):
    pass


def _represent_none(dumper: _StudiumYamlDumper, _: None) -> yaml.nodes.ScalarNode:
    scalar: yaml.nodes.ScalarNode = dumper.represent_scalar(  # pyright: ignore[reportUnknownMemberType]
        "tag:yaml.org,2002:null",
        "",
    )
    return scalar


def _represent_str(dumper: _StudiumYamlDumper, data: str) -> yaml.nodes.ScalarNode:
    style = "" if _ISO_Z_DATETIME_PATTERN.match(data) else None
    scalar: yaml.nodes.ScalarNode = dumper.represent_scalar(  # pyright: ignore[reportUnknownMemberType]
        "tag:yaml.org,2002:str",
        data,
        style=style,
    )
    return scalar


_StudiumYamlDumper.add_representer(type(None), _represent_none)
_StudiumYamlDumper.add_representer(str, _represent_str)
