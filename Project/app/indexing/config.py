from __future__ import annotations

"""Backward-compatible shim for the indexing package.

Keeps imports like ``from app.indexing.config import settings`` stable while all
configuration now comes from ``app.shared.configs.settings``.
"""

from app.shared.configs import settings as _shared_settings


class _IndexingSettingsShim:
    def __getattr__(self, name: str):
        if hasattr(_shared_settings, name):
            return getattr(_shared_settings, name)
        raise AttributeError(name)

    @property
    def data_input_dir(self) -> str:
        return _shared_settings.index_data_input_dir


settings = _IndexingSettingsShim()
