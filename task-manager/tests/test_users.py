import copy
import pytest
from services.users import (create_user, get_notification_pref, set_notification_pref,
                            get_user, USERS)
from utils.errors import NotFoundError, ValidationError

@pytest.fixture
def restore_users():
    snapshot = copy.deepcopy(USERS)
    yield
    USERS.clear()
    USERS.update(snapshot)

def test_get_notification_pref_valid():
    assert get_notification_pref(1) == "none"

def test_get_notification_pref_unknown_user():
    with pytest.raises(NotFoundError):
        get_notification_pref(999)

def test_set_notification_pref_valid(restore_users):
    result = set_notification_pref(1, "email")
    assert result["id"] == 1
    assert result["notification_pref"] == "email"
    assert get_notification_pref(1) == "email"

def test_set_notification_pref_invalid():
    with pytest.raises(ValidationError):
        set_notification_pref(1, "pigeon")
    assert get_notification_pref(1) == "none"

def test_set_notification_pref_unknown_user():
    with pytest.raises(NotFoundError):
        set_notification_pref(999, "email")

def test_create_user_default_notification_pref(restore_users):
    result = create_user("Carol", "carol@example.com")
    assert result["notification_pref"] == "none"
    assert get_user(result["id"])["notification_pref"] == "none"
