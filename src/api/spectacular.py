# SPDX-FileCopyrightText: 2026-present SPDX Contributors
# SPDX-License-Identifier: Apache-2.0


def preprocess_exclude_internal_paths(endpoints, **_):
    """Exclude /auth/ and /api2/ endpoints from the public API schema."""
    return [
        (path, path_regex, method, callback)
        for path, path_regex, method, callback in endpoints
        if not path.startswith("/auth/") and not path.startswith("/api2/")
    ]
