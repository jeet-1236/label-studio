import pytest
from core.label_config import (
    parse_config,
    parse_config_to_json,
    parse_config_to_xml,
    validate_label_config,
)
from rest_framework.exceptions import ValidationError


@pytest.mark.django_db
def test_validate_label_config_multiple_toname():
    config = """
    <View>
      <Image name="img1" value="$img1"/>
      <Image name="img2" value="$img2"/>
      <Choices name="choice" toName="img1,img2">
        <Choice value="A"/>
        <Choice value="B"/>
      </Choices>
    </View>
    """
    # Should parse without errors and validation must succeed
    assert parse_config(config)  # basic parsing
    parsed_json, _ = parse_config_to_json(config)
    assert isinstance(parsed_json, dict)
    # No exception from validation
    validate_label_config(config)
