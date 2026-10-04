import json
from pathlib import Path
from typing import Any

from app.models.user import User
from app.models.donation import Donation
from app.models.request import DonationRequest
from app.models.organization import OrganizationProfile


# -------------------------------------------------------------------
# Persistent data directory
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

USERS_FILE = DATA_DIR / "users.json"
DONATIONS_FILE = DATA_DIR / "donations.json"
REQUESTS_FILE = DATA_DIR / "requests.json"
NOTIFICATIONS_FILE = DATA_DIR / "notifications.json"
AUDIT_LOGS_FILE = DATA_DIR / "audit_logs.json"
ORGANIZATION_PROFILES_FILE = DATA_DIR / "organization_profiles.json"


# -------------------------------------------------------------------
# Ensure data directory and files exist
# -------------------------------------------------------------------

def ensure_data_files():
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = [
        USERS_FILE,
        DONATIONS_FILE,
        REQUESTS_FILE,
        NOTIFICATIONS_FILE,
        AUDIT_LOGS_FILE,
        ORGANIZATION_PROFILES_FILE,
    ]

    for file_path in files:
        if not file_path.exists():
            file_path.write_text(
                "[]",
                encoding="utf-8",
            )


# -------------------------------------------------------------------
# Generic JSON helpers
# -------------------------------------------------------------------

def load_json(file_path: Path) -> list:
    ensure_data_files()

    try:
        content = file_path.read_text(
            encoding="utf-8"
        ).strip()

        if not content:
            return []

        data = json.loads(content)

        if isinstance(data, list):
            return data

        return []

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return []


def save_json(
    file_path: Path,
    data: list,
):
    ensure_data_files()

    file_path.write_text(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# -------------------------------------------------------------------
# Model serialization
# -------------------------------------------------------------------

def serialize_model(item: Any) -> dict:
    if hasattr(item, "model_dump"):
        data = item.model_dump(
            mode="json"
        )

    elif hasattr(item, "dict"):
        data = item.dict()

    else:
        data = dict(item)

    return data


# -------------------------------------------------------------------
# Load persistent data
# -------------------------------------------------------------------

def load_users() -> list[User]:
    return [
        User.model_validate(item)
        for item in load_json(USERS_FILE)
    ]


def load_donations() -> list[Donation]:
    return [
        Donation.model_validate(item)
        for item in load_json(DONATIONS_FILE)
    ]


def load_requests() -> list[DonationRequest]:
    return [
        DonationRequest.model_validate(item)
        for item in load_json(REQUESTS_FILE)
    ]


def load_organization_profiles() -> list[OrganizationProfile]:
    return [
        OrganizationProfile.model_validate(item)
        for item in load_json(
            ORGANIZATION_PROFILES_FILE
        )
    ]


def load_notifications() -> list:
    return load_json(
        NOTIFICATIONS_FILE
    )


def load_audit_logs() -> list:
    return load_json(
        AUDIT_LOGS_FILE
    )


# -------------------------------------------------------------------
# In-memory working lists
#
# These lists are still used by the existing application code.
# JSON files are the persistent source of truth.
# -------------------------------------------------------------------

ensure_data_files()

users = load_users()

donations = load_donations()

requests = load_requests()

organization_profiles = load_organization_profiles()

notifications = load_notifications()

audit_logs = load_audit_logs()


# -------------------------------------------------------------------
# Persistence helpers
# -------------------------------------------------------------------

def save_users():
    save_json(
        USERS_FILE,
        [
            serialize_model(user)
            for user in users
        ],
    )


def save_donations():
    save_json(
        DONATIONS_FILE,
        [
            serialize_model(donation)
            for donation in donations
        ],
    )


def save_requests():
    save_json(
        REQUESTS_FILE,
        [
            serialize_model(request)
            for request in requests
        ],
    )


def save_organization_profiles():
    save_json(
        ORGANIZATION_PROFILES_FILE,
        [
            serialize_model(profile)
            for profile in organization_profiles
        ],
    )


def save_notifications():
    save_json(
        NOTIFICATIONS_FILE,
        notifications,
    )


def save_audit_logs():
    save_json(
        AUDIT_LOGS_FILE,
        audit_logs,
    )


# -------------------------------------------------------------------
# Save everything
# -------------------------------------------------------------------

def save_all():
    save_users()

    save_donations()

    save_requests()

    save_organization_profiles()

    save_notifications()

    save_audit_logs()