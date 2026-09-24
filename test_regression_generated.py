import pytest
from rest_framework.exceptions import ValidationError

from tasks.serializers import sanitize_prediction_import_payload


def test_missing_result_in_prediction_is_rejected():
    """
    A prediction payload that does not contain a ``result`` field must be
    rejected with a clear validation error.
    """
    bad_prediction = {"score": 0.42}  # ``result`` key is missing
    with pytest.raises(ValidationError):
        sanitize_prediction_import_payload(bad_prediction)
