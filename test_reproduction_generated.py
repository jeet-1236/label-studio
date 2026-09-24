import pytest
from rest_framework.exceptions import ValidationError

from data_export.serializers import ExportConvertSerializer
from projects.tests.factories import ProjectFactory


@pytest.mark.django_db
def test_supported_export_type_is_accepted():
    """
    The export dialog offers formats like JSON, CSV, COCO.
    The serializer must accept these formats without raising a validation error.
    """
    project = ProjectFactory()
    serializer = ExportConvertSerializer(
        data={"export_type": "JSON"},
        context={"project": project},
    )
    # is_valid() should succeed and the cleaned value should be the upper‑cased format
    assert serializer.is_valid(), f"Unexpected errors: {serializer.errors}"
    assert serializer.validated_data["export_type"] == "JSON"


@pytest.mark.django_db
def test_unsupported_export_type_is_rejected():
    """
    An unknown format (e.g. "FAKE_FORMAT") must be rejected with a ValidationError.
    The current bug incorrectly treats all formats as unsupported, so this test will
    fail until the validation logic is fixed.
    """
    project = ProjectFactory()
    serializer = ExportConvertSerializer(
        data={"export_type": "FAKE_FORMAT"},
        context={"project": project},
    )
    # The serializer should not be valid and must raise a ValidationError for the field.
    with pytest.raises(ValidationError) as exc_info:
        # Directly invoke the field validator to ensure the exception is raised.
        serializer.validate_export_type("FAKE_FORMAT")
    # The error message should mention that the format is not supported.
    assert "not supported" in str(exc_info.value).lower()
