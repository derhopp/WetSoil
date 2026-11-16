"""Localized native sensor labels retain diagnostic machine codes."""
import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "custom_components/wetsoil"
spec = importlib.util.spec_from_file_location("wetsoil_native_locales", BASE/"text_labels.py")
labels = importlib.util.module_from_spec(spec)
spec.loader.exec_module(labels)


def test_german_statuses_are_human_readable():
    assert labels.status_text("intensity_72h_complete", "de") == (
        "Niederschlagsintensität für 72 Stunden vollständig ausgewertet"
    )
    assert labels.status_text("automatic_disabled", "de") == "Automatik deaktiviert"
    assert labels.status_text("rain_today_limit", "de") == "Regenlimit für heute erreicht"


def test_english_and_fallback_behaviour():
    assert labels.status_text("intensity_72h_complete", "en").startswith("72-hour")
    assert labels.status_text("rain_3d_limit", "fr") == "Historical precipitation limit reached"
    assert labels.status_text("custom_code", "de") == "custom_code"
    assert labels.status_text(None, "de") is None


def test_native_name_translation_is_not_coupled_to_storage_key():
    assert labels.name_text("Scheduled start time", "de") == "Geplante Startzeit"
    assert labels.name_text("Precipitation sensor type", "de") == "Art der Niederschlagsmessung"
    assert labels.name_text("Scheduled start time", "en") == "Scheduled start time"
