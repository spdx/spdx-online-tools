# SPDX-FileCopyrightText: 2026-present SPDX Contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import redis

from src.secret import getRedisHost
from src.version import (
    java_tools_version,
    ntia_conformance_checker_version,
    python_tools_version,
    spdx_license_matcher_version,
    spdx_online_tools_version,
    spdx_python_model_version,
)

if TYPE_CHECKING:
    from django.http import HttpRequest


def _get_license_metadata() -> dict[str, str]:
    """Fetch all license metadata keys in one Redis connection."""
    keys = (
        "license_list_version",
        "license_list_release_date",
        "license_db_last_updated",
    )
    try:
        r = redis.StrictRedis(host=getRedisHost(), port=6379, db=1)
        version_val, release_val, synced_val = r.mget(keys)

        list_version = version_val.decode() if version_val else "Unknown"

        if release_val:
            dt_str = release_val.decode().replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(dt_str)
            release_date = dt.strftime("%Y-%m-%d").strip()
        else:
            release_date = "Unknown"

        if synced_val:
            dt = datetime.datetime.fromisoformat(synced_val.decode())
            last_synced = dt.strftime("%Y-%m-%d %H:%M %Z").strip()
        else:
            last_synced = "Unknown"

    except Exception:
        list_version = release_date = last_synced = "Unknown"

    return {
        "license_list_version": list_version,
        "license_list_release_date": release_date,
        "license_list_last_synced": last_synced,
    }


def tool_versions(request: HttpRequest) -> dict[str, Any]:
    return {
        "java_tools_version": java_tools_version,
        "ntia_conformance_checker_version": ntia_conformance_checker_version,
        "python_tools_version": python_tools_version,
        "spdx_license_matcher_version": spdx_license_matcher_version,
        "spdx_online_tools_version": spdx_online_tools_version,
        "spdx_python_model_version": spdx_python_model_version,
        **_get_license_metadata(),
    }
