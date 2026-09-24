import pytest
from rest_framework.exceptions import ValidationError

from data_export.serializers import ExportConvertSerializer
from data_export.models import DataExport
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
    assert serializer.is_valid(), f"Unexpected errors: {serializer.errors}"
    assert serializer.validated_data["export_type"] == "JSON"


@pytest.mark.django_db
def test_unsupported_export_type_is_rejected():
    """
    An unknown format (e.g. "FAKE_FORMAT") must be rejected with a ValidationError.
    """
    project = ProjectFactory()
    serializer = ExportConvertSerializer(
        data={"export_type": "FAKE_FORMAT"},
        context={"project": project},
    )
    with pytest.raises(ValidationError) as exc_info:
        serializer.validate_export_type("FAKE_FORMAT")
    assert "not supported" in str(exc_info.value).lower()


@pytest.mark.django_db
def test_all_known_formats_pass_validation():
    """
    Every format returned by DataExport.get_export_formats should be accepted.
    This guards against regressions where the whitelist logic is inverted.
    """
    project = ProjectFactory()
    serializer = ExportConvertSerializer(context={"project": project})
    supported_names = [fmt["name"] for fmt in DataExport.get_export_formats(project)]

    for name in supported_names:
        # The validator should return the same value it received for supported formats
        assert serializer.validate_export_type(name) == name


@pytest.mark.django_db
def test_random_unknown_format_is_rejected():
    """
    A format that is not in the supported list must raise ValidationError.
    """
    project = ProjectFactory()
    serializer = ExportConvertSerializer(context={"project": project})
    unsupported = "UNKNOWN_FORMAT_12345"
    # Ensure the test is meaningful: the name should not be in the supported list
    assert unsupported not in [fmt["name"] for fmt in DataExport.get_export_formats(project)]

    with pytest.raises(ValidationError):
        serializer.validate_export_type(unsupported)
