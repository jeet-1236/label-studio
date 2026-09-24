import pytest
from unittest.mock import Mock, patch

from rest_framework.exceptions import ValidationError
from data_export.serializers import ExportConvertSerializer


@pytest.fixture
def dummy_project():
    """A minimal stand‑in for a Project instance."""
    return Mock(name="Project")


@pytest.fixture
def serializer_context(dummy_project):
    """Context required by ExportConvertSerializer (only the project is used)."""
    return {"project": dummy_project}


def test_validate_export_type_accepts_supported_format(serializer_context):
    """Regression test for the bug where every format was rejected.

    The serializer should accept a format that is listed in the project's
    export formats.
    """
    supported_formats = [{"name": "CSV"}, {"name": "JSON"}, {"name": "COCO"}]

    with patch("data_export.serializers.DataExport.get_export_formats", return_value=supported_formats):
        serializer = ExportConvertSerializer(context=serializer_context)
        # Should return the same value without raising.
        assert serializer.validate_export_type("CSV") == "CSV"


def test_validate_export_type_rejects_unsupported_format(serializer_context):
    """When the requested format is not among the project's export formats a
    ValidationError must be raised.
    """
    supported_formats = [{"name": "CSV"}, {"name": "JSON"}]

    with patch("data_export.serializers.DataExport.get_export_formats", return_value=supported_formats):
        serializer = ExportConvertSerializer(context=serializer_context)
        with pytest.raises(ValidationError) as excinfo:
            serializer.validate_export_type("COCO")
        # The error message should contain the offending format name.
        assert "COCO is not supported export format" in str(excinfo.value)


def test_validate_export_type_is_idempotent(serializer_context):
    """The validation method should be idempotent: calling it repeatedly with the
    same supported value yields the same result.
    """
    supported_formats = [{"name": "JSON"}]

    with patch("data_export.serializers.DataExport.get_export_formats", return_value=supported_formats):
        serializer = ExportConvertSerializer(context=serializer_context)
        first = serializer.validate_export_type("JSON")
        second = serializer.validate_export_type("JSON")
        assert first == second == "JSON"
