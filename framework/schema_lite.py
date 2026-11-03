#!/usr/bin/env python3
"""Small JSON Schema subset used to check the research data files.

Supported keywords: type, enum, pattern, minLength, minItems, required,
properties, additionalProperties (false), items, oneOf, and $ref to a local
$defs entry or to a sibling schema file. Any other keyword raises, so a
schema cannot silently weaken validation.
"""
from pathlib import Path
import json
import re

IGNORED_KEYWORDS = {'$schema', '$id', 'title', 'description', '$defs', 'examples', 'default'}
SUPPORTED_KEYWORDS = {
    'type', 'enum', 'pattern', 'minLength', 'minItems', 'required',
    'properties', 'additionalProperties', 'items', 'oneOf', '$ref',
} | IGNORED_KEYWORDS

TYPES = {
    'object': dict,
    'array': list,
    'string': str,
    'boolean': bool,
    'null': type(None),
}


def _matches_type(value, name):
    if name == 'integer':
        return isinstance(value, int) and not isinstance(value, bool)
    if name == 'number':
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    expected = TYPES.get(name)
    if expected is None:
        raise ValueError(f'unsupported schema type: {name}')
    if expected is bool:
        return isinstance(value, bool)
    return isinstance(value, expected) and not (expected is int and isinstance(value, bool))


class Validator:
    """Validate instances against schemas loaded from one directory."""

    def __init__(self, schema_dir):
        self.schema_dir = Path(schema_dir)
        self.cache = {}

    def schema(self, name):
        if name not in self.cache:
            path = self.schema_dir / name
            self.cache[name] = json.loads(path.read_text(encoding='utf-8'))
        return self.cache[name]

    def validate(self, instance, schema, path='$', root=None):
        errors = []
        self._check(instance, schema, path, root, errors, depth=0)
        return errors

    def _check(self, value, schema, path, root, errors, depth):
        if depth > 40:
            errors.append(f'{path}: schema reference nesting is too deep')
            return
        unknown = set(schema) - SUPPORTED_KEYWORDS
        if unknown:
            raise ValueError(f'unsupported schema keywords: {sorted(unknown)}')
        root = schema if root is None else root

        if '$ref' in schema:
            self._check_ref(value, schema['$ref'], path, root, errors, depth)
            return

        if 'type' in schema:
            names = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
            if not any(_matches_type(value, name) for name in names):
                errors.append(f'{path}: expected type {" or ".join(names)}')
                return

        if 'enum' in schema and value not in schema['enum']:
            errors.append(f'{path}: value {value!r} is not one of {schema["enum"]}')

        if isinstance(value, str):
            if 'pattern' in schema and not re.search(schema['pattern'], value):
                errors.append(f'{path}: value {value!r} does not match {schema["pattern"]}')
            if 'minLength' in schema and len(value) < schema['minLength']:
                errors.append(f'{path}: value is shorter than {schema["minLength"]} characters')

        if isinstance(value, list):
            if 'minItems' in schema and len(value) < schema['minItems']:
                errors.append(f'{path}: needs at least {schema["minItems"]} items')
            if 'items' in schema:
                for index, item in enumerate(value):
                    self._check(item, schema['items'], f'{path}[{index}]', root, errors, depth + 1)

        if isinstance(value, dict):
            properties = schema.get('properties', {})
            for name in schema.get('required', []):
                if name not in value:
                    errors.append(f'{path}: missing required property {name!r}')
            if schema.get('additionalProperties') is False:
                for name in sorted(set(value) - set(properties)):
                    errors.append(f'{path}: unexpected property {name!r}')
            for name, subschema in properties.items():
                if name in value:
                    self._check(value[name], subschema, f'{path}.{name}', root, errors, depth + 1)

        if 'oneOf' in schema:
            failures = [
                self.validate(value, option, path, root)
                for option in schema['oneOf']
            ]
            if sum(1 for failure in failures if not failure) != 1:
                errors.append(f'{path}: value must match exactly one allowed shape')

    def _check_ref(self, value, reference, path, root, errors, depth):
        if reference.startswith('#/$defs/'):
            name = reference.split('/', 2)[2]
            definitions = root.get('$defs', {})
            if name not in definitions:
                raise ValueError(f'unresolved schema reference: {reference}')
            self._check(value, definitions[name], path, root, errors, depth + 1)
            return
        if reference.startswith('#'):
            raise ValueError(f'unsupported schema reference: {reference}')
        target = self.schema(reference.split('/')[-1])
        self._check(value, target, path, target, errors, depth + 1)


def validate(instance, schema, schema_dir):
    """Convenience wrapper used by tests and the validator."""
    return Validator(schema_dir).validate(instance, schema)
