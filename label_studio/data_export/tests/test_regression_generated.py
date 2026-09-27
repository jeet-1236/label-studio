import pytest
from types import SimpleNamespace
from data_export.models import DataExport

# Helper to monkeypatch the Converter used inside DataExport.get_export_formats
class DummyConverter:
    def __init__(self, config, project_dir=None, **kwargs):
        # config is ignored for the dummy; we just expose supported_formats and all_formats
        self._supported = set(['JSON', 'CSV'])  # base supported formats
        self._all = {
            SimpleNamespace(name='JSON'): {'description': 'json'},
            SimpleNamespace(name='CSV'): {'description': 'csv'},
            SimpleNamespace(name='DOCLANG'): {'description': 'doclang'},
        }

    @property
    def supported_formats(self):
        return self._supported

    def all_formats(self):
        return self._all


@pytest.fixture(autouse=True)
def patch_converter(monkeypatch):
    """
    Replace the real Converter with our DummyConverter for the duration of the tests.
    """
    import label_studio_sdk.converter

    monkeypatch.setattr(label_studio_sdk.converter, "Converter", DummyConverter, raising=False)


def make_project(use_custom_interface=None):
    """
    Build a minimal project object compatible with DataExport.get_export_formats.
    If use_custom_interface is None, the project will not have an lse_project attribute.
    """
    project = SimpleNamespace(
        get_parsed_config=lambda: {},
    )
    if use_custom_interface is not None:
        project.lse_project = SimpleNamespace(use_custom_interface=use_custom_interface)
    return project




def test_doclang_enabled_when_custom_interface():
    """
    When the project enables the custom interface, the DOCLANG format must be enabled.
    """
    project = make_project(use_custom_interface=True)
    formats = DataExport.get_export_formats(project)
    doclang = next(f for f in formats if f["name"] == "DOCLANG")
    assert doclang.get("disabled", False) is False


def test_formats_sorted_by_disabled_flag():
    """
    The list returned by get_export_formats must be ordered so that all enabled formats
    appear before any disabled ones.
    """
    # Test both configurations to ensure the sorting holds in each case
    for flag in (False, True):
        project = make_project(use_custom_interface=flag)
        formats = DataExport.get_export_formats(project)

        seen_disabled = False
        for fmt in formats:
            if fmt.get("disabled", False):
                seen_disabled = True
            else:
                # If we have already seen a disabled format, encountering an enabled one is a bug
                assert not seen_disabled, "Enabled format found after a disabled one"
        # Additionally, ensure that at least one format is enabled and at least one is disabled
        assert any(not f.get("disabled", False) for f in formats), "No enabled formats returned"
        assert any(f.get("disabled", False) for f in formats), "No disabled formats returned"
