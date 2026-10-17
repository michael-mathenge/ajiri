"""Bounded plain-text CV input. No routes or generation side effects.

see docs/CONCEPTS.md#cv-builder-schema
"""
import json
import re
import uuid
from collections.abc import Mapping
from rest_framework import serializers

MAX_CONTENT_BYTES = 100 * 1024
MAX_DOCUMENT_BYTES = 2 * 1024 * 1024


class StrictText(serializers.CharField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail('invalid')
        # Markup-looking input is literal text; renderers must escape it, never
        # interpret it as HTML, template source or executable document fields.
        return super().to_internal_value(data)


class StrictBoolean(serializers.BooleanField):
    def to_internal_value(self, data):
        if type(data) is not bool:
            raise serializers.ValidationError('Expected true or false.')
        return data


class SchemaVersion(serializers.IntegerField):
    def to_internal_value(self, data):
        if type(data) is not int:
            raise serializers.ValidationError('Expected integer schema version.')
        return super().to_internal_value(data)


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, Mapping):
            raise serializers.ValidationError({'non_field_errors': ['Expected an object.']})
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({str(key): ['Unknown field.'] for key in sorted(unknown, key=str)})
        return super().to_internal_value(data)


def text(limit=255):
    return StrictText(max_length=limit, required=False, allow_blank=True, default='')


class MonthField(StrictText):
    def __init__(self, **kwargs):
        super().__init__(max_length=7, required=False, allow_blank=True, default='', **kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if value and not re.fullmatch(r'[1-9][0-9]{3}-(0[1-9]|1[0-2])', value):
            raise serializers.ValidationError('Use YYYY-MM with a valid month.')
        return value


class Entry(StrictSerializer):
    id = serializers.UUIDField(required=False, default=uuid.uuid4)
    description = text(2000)


class DatedEntry(Entry):
    start = MonthField()
    end = MonthField()
    current = StrictBoolean(required=False, default=False)

    def validate(self, attrs):
        if attrs['current'] and attrs['end']:
            raise serializers.ValidationError({'end': ['A current entry cannot have an end date.']})
        if attrs['start'] and attrs['end'] and attrs['end'] < attrs['start']:
            raise serializers.ValidationError({'end': ['End must not precede start.']})
        return attrs


class Employment(DatedEntry):
    title = StrictText(max_length=255)
    organisation = StrictText(max_length=255)
    achievements = serializers.ListField(child=StrictText(max_length=500), max_length=10, required=False, default=list)


class Education(DatedEntry):
    qualification = StrictText(max_length=255)
    institution = StrictText(max_length=255)


class Certification(Entry):
    name = StrictText(max_length=255)
    issuer = StrictText(max_length=255)
    issued = MonthField()
    expiry = MonthField()

    def validate(self, attrs):
        if attrs['issued'] and attrs['expiry'] and attrs['expiry'] < attrs['issued']:
            raise serializers.ValidationError({'expiry': ['Expiry must not precede issue date.']})
        return attrs


class Project(Entry):
    name = StrictText(max_length=255)
    organisation = text()
    url = text(2048)

    def validate_url(self, value):
        if value:
            serializers.URLField(max_length=2048).run_validation(value)
            if not value.lower().startswith(('https://', 'http://')):
                raise serializers.ValidationError('Use an absolute HTTP(S) URL.')
        return value


class Contact(StrictSerializer):
    name = text()
    email = text(254)
    phone = text(20)
    location = text()

    def validate_email(self, value):
        if value:
            serializers.EmailField().run_validation(value)
        return value


class CVContent(StrictSerializer):
    schema_version = SchemaVersion(min_value=1, max_value=1)
    contact = Contact()
    headline = text()
    summary = text(3000)
    skills = serializers.ListField(child=StrictText(max_length=100), max_length=50, required=False, default=list)
    employment = Employment(many=True, max_length=20, required=False, default=list)
    education = Education(many=True, max_length=15, required=False, default=list)
    certifications = Certification(many=True, max_length=20, required=False, default=list)
    projects = Project(many=True, max_length=20, required=False, default=list)

    def validate(self, attrs):
        for section in ('employment', 'education', 'certifications', 'projects'):
            ids = [row['id'] for row in attrs[section]]
            if len(set(ids)) != len(ids):
                raise serializers.ValidationError({section: ['Entry identifiers must be unique within a section.']})
        return attrs


def validate_content(content, *, for_approval=False):
    """Validate a complete merged document; partial PATCH merging belongs to service.

    Return JSON-safe normalized data, including generated entry identifiers.
    """
    try:
        size = len(json.dumps(content, ensure_ascii=False, allow_nan=False).encode('utf-8'))
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise serializers.ValidationError({'content': ['Expected valid JSON content.']})
    if size > MAX_CONTENT_BYTES:
        raise serializers.ValidationError({'content': ['CV content must not exceed 100 KiB.']})
    serializer = CVContent(data=content)
    serializer.is_valid(raise_exception=True)
    result = dict(serializer.data)
    if len(json.dumps(result, ensure_ascii=False).encode('utf-8')) > MAX_CONTENT_BYTES:
        raise serializers.ValidationError({'content': ['CV content must not exceed 100 KiB.']})
    if for_approval:
        errors = {}
        if not result['contact']['name']:
            errors['contact'] = {'name': ['Enter your name before approval.']}
        if not any(result[key] for key in ('summary', 'skills', 'employment', 'education', 'certifications', 'projects')):
            errors['non_field_errors'] = ['Add at least one substantive CV section before approval.']
        if errors:
            raise serializers.ValidationError(errors)
    return result
