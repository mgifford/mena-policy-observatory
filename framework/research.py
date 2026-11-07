#!/usr/bin/env python3
"""Load and validate the structured research fields for each policy record.

The JSON Schema checks shape. These checks cover what a schema cannot:
reference integrity, date consistency, artifact existence, excerpt and
summary attribution, and the difference between an unknown value and a
negative legal finding.
"""
from datetime import date
import json
import re
from pathlib import Path

try:  # imported as framework.research
    from .schema_lite import Validator
except ImportError:  # run as a script
    from schema_lite import Validator

RESEARCH_FILENAME = 'research.json'
SCHEMA_FILENAME = 'research-record.schema.json'
PROVISION_HEADING = re.compile(r'^## (P-[0-9]{2}):[ \t]*(.+?)[ \t]*$', re.MULTILINE)
QUESTION_HEADING = re.compile(
    r'^#{2,3} ([A-Z]{2}[A-Z0-9-]*)[ \t]*(?::|\|)[ \t]*(.+?)[ \t]*$', re.MULTILINE)
ISO_DATE = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
BCP47 = re.compile(r'^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$')
EXPRESSION_KINDS = (
    'original_authoritative', 'additional_authoritative', 'official_translation',
    'research_translation', 'machine_assisted_draft', 'translation_pending',
    'translation_unavailable', 'authority_unresolved',
)
EXPRESSION_REVIEW_STATES = ('unreviewed', 'in_review', 'reviewed', 'native_reviewed', 'disputed')
REVIEWED_EXPRESSION_STATES = ('reviewed', 'native_reviewed', 'disputed')
CONFIRMED_EFFECT = ('in_force_confirmed', 'not_in_force_confirmed')
ACYCLIC_RELATIONS = {'amends', 'supersedes'}


def relation_cycles(relations_by_record):
    """Return cycles among internal amending/superseding relations.

    A cycle in a citation graph is ordinary. A cycle in an amendment or
    supersession chain is not, so only those labels are checked here.
    """
    graph = {}
    for record_id, relations in relations_by_record.items():
        for relation in _as_list(relations):
            if not isinstance(relation, dict):
                continue
            if relation.get('relation') not in ACYCLIC_RELATIONS:
                continue
            target = relation.get('target') if isinstance(relation.get('target'), dict) else {}
            target_id = target.get('record_id') if target.get('kind') == 'internal_record' else None
            if target_id:
                graph.setdefault(record_id, set()).add(target_id)

    cycles, state, stack = [], {}, []

    def visit(node):
        state[node] = 'open'
        stack.append(node)
        for next_id in sorted(graph.get(node, ())):
            if state.get(next_id) == 'open':
                cycles.append(stack[stack.index(next_id):] + [next_id])
            elif state.get(next_id) is None:
                visit(next_id)
        stack.pop()
        state[node] = 'done'

    for node in sorted(graph):
        if state.get(node) is None:
            visit(node)
    return cycles


def load_research(policy_dir):
    return json.loads((policy_dir / RESEARCH_FILENAME).read_text(encoding='utf-8'))


def _artifact_ids(path, pattern):
    return {match.group(1): match.group(2) for match in pattern.finditer(path.read_text(encoding='utf-8'))}


def _as_list(value):
    return value if isinstance(value, list) else []


def _duplicates(values):
    seen, repeated = set(), set()
    for value in values:
        if value in seen:
            repeated.add(value)
        seen.add(value)
    return sorted(repeated)


def _iso(value):
    """Return an ISO date string only when it is also a real calendar date."""
    if not isinstance(value, str) or not ISO_DATE.match(value):
        return None
    try:
        date.fromisoformat(value)
    except ValueError:
        return None
    return value


def validate_record(policy_dir, record_id, validator, known_record_ids=None,
                    warnings=None):
    """Return semantic errors for one research.json. Shape errors come first.

    Warnings record unusual but acceptable chronology, such as a retrospective
    effective date. They never change an error into a pass; callers decide how
    to display them.
    """
    warnings = [] if warnings is None else warnings
    prefix = f'{record_id}: '
    path = policy_dir / RESEARCH_FILENAME
    if not path.is_file():
        return [prefix + f'missing {RESEARCH_FILENAME}']
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        return [prefix + f'{RESEARCH_FILENAME} is not valid JSON: {exc}']

    errors = [prefix + error for error in validator.validate(data, validator.schema(SCHEMA_FILENAME))]
    if not isinstance(data, dict):
        return errors

    if data.get('record_id') != record_id:
        errors.append(prefix + f'record_id {data.get("record_id")!r} does not match directory {record_id!r}')

    artifacts = data.get('artifacts') if isinstance(data.get('artifacts'), dict) else {}
    artifact_text = {}
    for key, filename in artifacts.items():
        artifact_path = policy_dir / str(filename)
        if not artifact_path.is_file():
            errors.append(prefix + f'artifact {filename!r} ({key}) does not exist')
            continue
        artifact_text[filename] = artifact_path.read_text(encoding='utf-8')

    sources = _as_list(data.get('sources'))
    provisions = _as_list(data.get('provisions'))
    interpretations = _as_list(data.get('interpretations'))
    relations = _as_list(data.get('relations'))

    for label, items in (('source', sources), ('provision', provisions),
                         ('interpretation', interpretations), ('relation', relations)):
        for duplicate in _duplicates([item.get('id') for item in items if isinstance(item, dict)]):
            errors.append(prefix + f'duplicate {label} id {duplicate!r}')

    source_ids = {source.get('id') for source in sources if isinstance(source, dict)}
    provision_ids = {provision.get('id') for provision in provisions if isinstance(provision, dict)}
    interpretation_ids = {item.get('id') for item in interpretations if isinstance(item, dict)}

    expression_ids = set()
    for source in sources:
        if not isinstance(source, dict):
            continue
        _check_dates(source, prefix, errors, warnings)
        _check_excerpt(source, prefix, policy_dir, artifact_text, errors)
        _check_translation(source, prefix, errors)
        _check_expressions(source, record_id, prefix, errors, expression_ids)

    for provision in provisions:
        if not isinstance(provision, dict):
            continue
        provision_id = provision.get('id')
        for source_id in _as_list(provision.get('source_ids')):
            if source_id not in source_ids:
                errors.append(prefix + f'provision {provision_id} references unknown source {source_id!r}')
        linked = _as_list(provision.get('interpreting_questions'))
        for question_id in linked:
            if question_id not in interpretation_ids:
                errors.append(prefix + f'provision {provision_id} references unknown question {question_id!r}')
        unresolved = [
            question_id for question_id in linked
            if any(item.get('id') == question_id and item.get('status') != 'resolved' for item in interpretations)
        ]
        if provision.get('encoding_status') == 'reviewed':
            if provision.get('effect_assessment') not in CONFIRMED_EFFECT:
                errors.append(prefix + f'provision {provision_id} cannot be reviewed without a confirmed effect assessment')
            if unresolved:
                errors.append(prefix + f'provision {provision_id} cannot be reviewed with unresolved questions: {unresolved}')

    for interpretation in interpretations:
        if not isinstance(interpretation, dict):
            continue
        question_id = interpretation.get('id')
        provision_id = interpretation.get('provision_id')
        if provision_id is not None and provision_id not in provision_ids:
            errors.append(prefix + f'question {question_id} references unknown provision {provision_id!r}')
        if interpretation.get('status') == 'resolved':
            missing = [key for key in ('resolution', 'reviewer', 'reviewed_at')
                       if not interpretation.get(key)]
            if missing:
                errors.append(prefix + f'question {question_id} is resolved but lacks {missing}')
        elif interpretation.get('resolution') is not None:
            errors.append(prefix + f'question {question_id} has a resolution but is not marked resolved')
        for alternative in _as_list(interpretation.get('alternatives')):
            if isinstance(alternative, dict) and alternative.get('review_state') == 'reviewed':
                errors.append(prefix + f'question {question_id} alternative {alternative.get("id")} claims review without recorded evidence')

    for relation in relations:
        if not isinstance(relation, dict):
            continue
        relation_id = relation.get('id')
        target = relation.get('target') if isinstance(relation.get('target'), dict) else {}
        if relation.get('relation') != 'unspecified' and relation.get('review_state') != 'reviewed':
            errors.append(prefix + f'relation {relation_id} asserts {relation.get("relation")!r} without review')
        if relation.get('relation') == 'unspecified' and not relation.get('recorded_label'):
            errors.append(prefix + f'relation {relation_id} needs a recorded label when the relation is unspecified')
        if target.get('kind') == 'internal_record':
            if not target.get('record_id'):
                errors.append(prefix + f'relation {relation_id} needs a target record_id')
            elif target['record_id'] == record_id:
                errors.append(prefix + f'relation {relation_id} points at its own record')
            elif known_record_ids is not None and target['record_id'] not in known_record_ids:
                errors.append(prefix + f'relation {relation_id} points at unknown record {target["record_id"]!r}')
            if target.get('url') is not None:
                errors.append(prefix + f'relation {relation_id} points at an internal record and a URL')
        if target.get('kind') == 'external_document' and not target.get('url'):
            errors.append(prefix + f'relation {relation_id} needs a target URL')

    _check_artifacts(artifacts, artifact_text, provisions, interpretations, prefix, errors)
    return errors


def _check_dates(source, prefix, errors, warnings=None):
    warnings = [] if warnings is None else warnings
    publication = _iso(source.get('publication_date'))
    effective = _iso(source.get('effective_date'))
    if publication and effective and effective < publication:
        warnings.append(
            prefix + f'source {source.get("id")}: effective date precedes publication date; '
                      'verify whether the instrument has retrospective effect')
    for field in ('publication_date', 'effective_date'):
        value = source.get(field)
        if isinstance(value, str) and value != 'unknown':
            if not ISO_DATE.match(value) or _iso(value) is None:
                errors.append(prefix + f'source {source.get("id")}: {field} must be a '
                                       'valid ISO calendar date or "unknown"')
    capture = source.get('capture') if isinstance(source.get('capture'), dict) else {}
    if capture.get('bytes_stored'):
        if not capture.get('sha256'):
            errors.append(prefix + f'source {source.get("id")}: stored bytes need a SHA-256 checksum')
        if not capture.get('captured_at'):
            errors.append(prefix + f'source {source.get("id")}: stored bytes need a capture timestamp')
    elif capture.get('sha256'):
        errors.append(prefix + f'source {source.get("id")}: a checksum is recorded for bytes that are not stored')


def _check_excerpt(source, prefix, policy_dir, artifact_text, errors):
    status = source.get('excerpt_status')
    excerpt = source.get('excerpt')
    if status == 'recorded' and not excerpt:
        errors.append(prefix + f'source {source.get("id")}: excerpt_status is recorded but no excerpt is present')
    if status != 'recorded' and excerpt:
        errors.append(prefix + f'source {source.get("id")}: excerpt present but excerpt_status is {status!r}')
    if not isinstance(excerpt, dict):
        return
    artifact = excerpt.get('artifact')
    text = artifact_text.get(artifact)
    if text is None:
        errors.append(prefix + f'source {source.get("id")}: excerpt artifact {artifact!r} is not declared in artifacts')
    elif excerpt.get('text') not in text:
        errors.append(prefix + f'source {source.get("id")}: excerpt text is not found verbatim in {artifact}')


def _check_expressions(source, record_id, prefix, errors, expression_ids):
    expressions = source.get('expressions')
    if expressions is None:
        return
    if not isinstance(expressions, list):
        errors.append(prefix + f'source {source.get("id")}: expressions must be an array')
        return
    source_id = source.get('id')
    originals = 0
    seen_pairs = set()
    for expression in expressions:
        if not isinstance(expression, dict):
            errors.append(prefix + f'source {source_id}: each expression must be an object')
            continue
        expression_id = expression.get('id')
        label = f'source {source_id} expression {expression_id!r}'
        if not expression_id:
            errors.append(prefix + f'source {source_id}: an expression needs an id')
        elif expression_id in expression_ids:
            errors.append(prefix + f'{label}: duplicate expression id')
        else:
            expression_ids.add(expression_id)
        kind = expression.get('kind')
        if kind not in EXPRESSION_KINDS:
            errors.append(prefix + f'{label}: unknown kind {kind!r}')
        if expression.get('source_id') != source_id:
            errors.append(prefix + f'{label}: source_id must match the parent source')
        if expression.get('instrument_id') != record_id:
            errors.append(prefix + f'{label}: instrument_id must match the record id')
        language = expression.get('language')
        original_language = expression.get('original_language')
        for field, value in (('language', language), ('original_language', original_language)):
            if not isinstance(value, str) or not BCP47.match(value):
                errors.append(prefix + f'{label}: {field} must be a BCP47 language tag')
        review_status = expression.get('review_status')
        if review_status not in EXPRESSION_REVIEW_STATES:
            errors.append(prefix + f'{label}: unknown review_status {review_status!r}')
        url = expression.get('url')
        if url is not None and (not isinstance(url, str) or not url.startswith('https://')):
            errors.append(prefix + f'{label}: url must be an https URL or null')
        authority = expression.get('authority')
        if authority is not None and (not isinstance(authority, str) or not authority.strip()):
            errors.append(prefix + f'{label}: authority must be a nonempty string or null')
        if kind in ('official_translation', 'additional_authoritative') and not authority:
            errors.append(prefix + f'{label}: {kind} needs a recorded authority')
        if kind in ('translation_pending', 'translation_unavailable'):
            if url is not None or authority is not None:
                errors.append(prefix + f'{label}: {kind} may not record a URL or authority')
            if review_status in REVIEWED_EXPRESSION_STATES:
                errors.append(prefix + f'{label}: {kind} may not claim review')
        if kind == 'authority_unresolved' and review_status in REVIEWED_EXPRESSION_STATES:
            errors.append(prefix + f'{label}: an unresolved authority may not claim review')
        if kind == 'machine_assisted_draft':
            if expression.get('translation_method') != 'machine_assisted':
                errors.append(prefix + f'{label}: a machine-assisted draft must use that method')
            if review_status in REVIEWED_EXPRESSION_STATES:
                errors.append(prefix + f'{label}: a machine-assisted draft may not claim review')
        if kind == 'original_authoritative':
            originals += 1
            if originals > 1:
                errors.append(prefix + f'source {source_id}: more than one original expression')
            if isinstance(language, str) and isinstance(source.get('language'), str):
                source_language = source['language'].lower()
                if source_language != 'unknown' and language.lower() != source_language:
                    errors.append(prefix + f'{label}: original language does not match the '
                                           'source language')
        if review_status in REVIEWED_EXPRESSION_STATES:
            if _iso(expression.get('reviewed_at')) is None:
                errors.append(prefix + f'{label}: reviewed status needs an ISO reviewed_at')
            if not isinstance(expression.get('reviewer_role'), str) or \
                    not expression['reviewer_role'].strip():
                errors.append(prefix + f'{label}: reviewed status needs a reviewer_role')
            if expression.get('translation_method') not in ('human', None):
                errors.append(prefix + f'{label}: reviewed status needs a human method')
        if expression.get('reviewed_at') is not None and _iso(expression.get('reviewed_at')) is None:
            errors.append(prefix + f'{label}: reviewed_at must be a valid ISO date or null')
        if review_status == 'unreviewed' and (expression.get('reviewed_at') is not None
                                              or expression.get('reviewer_role') is not None):
            errors.append(prefix + f'{label}: unreviewed status may not carry review metadata')
        pair = (language, kind)
        if pair in seen_pairs:
            errors.append(prefix + f'{label}: duplicate language and kind')
        seen_pairs.add(pair)


def _check_translation(source, prefix, errors):
    translation = source.get('translation') if isinstance(source.get('translation'), dict) else {}
    status = translation.get('status')
    if status == 'not_translated':
        if translation.get('target_language') is not None:
            errors.append(prefix + f'source {source.get("id")}: an untranslated source names a target language')
        if translation.get('provenance') is not None:
            errors.append(prefix + f'source {source.get("id")}: an untranslated source records provenance')
    elif status in ('draft', 'complete') and not translation.get('provenance'):
        errors.append(prefix + f'source {source.get("id")}: a translation needs recorded provenance')
    if translation.get('review_state') == 'native_reviewed' and not translation.get('provenance'):
        errors.append(prefix + f'source {source.get("id")}: native review needs recorded provenance')


def _check_artifacts(artifacts, artifact_text, provisions, interpretations, prefix, errors):
    provisions_file = artifacts.get('provisions')
    if provisions_file in artifact_text:
        documented = _artifact_ids_from_text(artifact_text[provisions_file], PROVISION_HEADING)
        declared = {provision.get('id'): provision.get('heading')
                    for provision in provisions if isinstance(provision, dict)}
        for provision_id, heading in documented.items():
            if provision_id not in declared:
                errors.append(prefix + f'{provisions_file} documents provision {provision_id} with no structured entry')
            elif declared[provision_id] != heading:
                errors.append(prefix + f'provision {provision_id} heading does not match {provisions_file}')
        for provision_id in sorted(set(declared) - set(documented)):
            errors.append(prefix + f'structured provision {provision_id} is not documented in {provisions_file}')
        for provision in provisions:
            if not isinstance(provision, dict):
                continue
            summary = provision.get('summary')
            if isinstance(summary, str) and summary not in artifact_text[provisions_file]:
                errors.append(prefix + f'provision {provision.get("id")} summary is not found verbatim in {provisions_file}')

    interpretations_file = artifacts.get('interpretations')
    if interpretations_file in artifact_text:
        documented = _artifact_ids_from_text(artifact_text[interpretations_file], QUESTION_HEADING)
        declared = {item.get('id'): item.get('statement')
                    for item in interpretations if isinstance(item, dict)}
        for question_id in documented:
            if question_id not in declared:
                errors.append(prefix + f'{interpretations_file} documents question {question_id} with no structured entry')
        for question_id in sorted(set(declared) - set(documented)):
            errors.append(prefix + f'structured question {question_id} is not documented in {interpretations_file}')
        for interpretation in interpretations:
            if not isinstance(interpretation, dict):
                continue
            statement = interpretation.get('statement')
            if isinstance(statement, str) and statement not in artifact_text[interpretations_file]:
                errors.append(prefix + f'question {interpretation.get("id")} statement is not found verbatim in {interpretations_file}')


def _artifact_ids_from_text(text, pattern):
    return {match.group(1): match.group(2) for match in pattern.finditer(text)}


def validate_region(base, region, warnings=None):
    """Validate every structured research file in one region."""
    warnings = [] if warnings is None else warnings
    base = Path(base)
    validator = Validator(base / 'schemas')
    records = json.loads((base / 'data' / 'policies.json').read_text(encoding='utf-8'))
    record_ids = [record['id'] for record in records]
    known = set(record_ids)
    directories = {path.name for path in (base / 'policies').iterdir() if path.is_dir()}

    errors = []
    relations_by_record = {}
    for record_id in record_ids:
        if record_id not in directories:
            errors.append(f'{region}: {record_id} has a record entry but no policy directory')
            continue
        policy_dir = base / 'policies' / record_id
        errors.extend(validate_record(policy_dir, record_id, validator, known, warnings))
        if (policy_dir / RESEARCH_FILENAME).is_file():
            try:
                relations_by_record[record_id] = load_research(policy_dir).get('relations')
            except (json.JSONDecodeError, OSError):
                pass  # already reported by validate_record
    for extra in sorted(directories - known):
        errors.append(f'{region}: {extra} has a policy directory but no record entry')
    for cycle in relation_cycles(relations_by_record):
        errors.append(f'{region}: amending/superseding relations form a cycle: '
                      + ' -> '.join(cycle))
    return errors


if __name__ == '__main__':
    import sys
    root = Path(__file__).resolve().parents[1]
    problems = validate_region(root / 'regions' / 'mena', 'mena')
    if problems:
        print('\n'.join(problems), file=sys.stderr)
        sys.exit(1)
    print('Research model validation passed; no legal or RuleSpec verification implied.')
