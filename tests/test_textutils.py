import pytest

from app.textutils import fix_articles, smart_title


@pytest.mark.parametrize("raw, expected", [
    ("a IoT-based system", "an IoT-based system"),
    ("a AI-powered app", "an AI-powered app"),
    ("an web portal", "a web portal"),
    ("a SMS alert", "an SMS alert"),
    ("a 2D game", "a 2D game"),
    ("an unified platform", "a unified platform"),
    ("A augmented reality app", "An augmented reality app"),
    ("a mobile app", "a mobile app"),
])
def test_fix_articles(raw, expected):
    assert fix_articles(raw) == expected


def test_smart_title_keeps_acronyms_and_small_words():
    assert smart_title("AgriSense: a IoT-based crop monitoring system for small-scale farmers") == \
        "AgriSense: A IoT-Based Crop Monitoring System for Small-Scale Farmers"
    assert smart_title("development of a system with SMS notifications") == \
        "Development of a System with SMS Notifications"
