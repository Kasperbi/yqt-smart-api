from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DND_POLL_INTERVAL, DOMAIN, POLL_INTERVAL, REQUEST_LOCATION_REFRESH_DELAY
from .core.async_client import YQTApiClient
from .core.protocol import DEVICE_OFFLINE_STATUS
from .core.protocol import YQTAuthError, YQTError, YQTResponseError, YQTWatchState

_LOGGER = logging.getLogger(__name__)


class YQTDataUpdateCoordinator(DataUpdateCoordinator[dict[str, YQTWatchState]]):
    def __init__(self, hass: HomeAssistant, client: YQTApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=POLL_INTERVAL,
        )
        self.client = client
        self._delayed_refresh_unsub: CALLBACK_TYPE | None = None

    async def _async_update_data(self) -> dict[str, YQTWatchState]:
        try:
            return await self.client.async_refresh_watch_states(self.data)
        except YQTAuthError as exc:
            raise ConfigEntryAuthFailed(str(exc)) from exc
        except YQTError as exc:
            raise UpdateFailed(str(exc)) from exc

    async def async_request_location(self, did: str) -> None:
        try:
            await self.client.async_request_location(did)
        except YQTAuthError as exc:
            raise ConfigEntryAuthFailed(str(exc)) from exc
        except YQTResponseError as exc:
            if exc.status == DEVICE_OFFLINE_STATUS:
                persistent_notification.async_create(
                    self.hass,
                    exc.message,
                    f"{self.data[did].watch.name} is offline",
                    f"{DOMAIN}_{did}_offline",
                )
                return
            raise UpdateFailed(str(exc)) from exc
        except YQTError as exc:
            raise UpdateFailed(str(exc)) from exc

        persistent_notification.async_dismiss(self.hass, f"{DOMAIN}_{did}_offline")
        self._async_schedule_delayed_refresh()

    @callback
    def async_shutdown(self) -> None:
        if self._delayed_refresh_unsub is not None:
            self._delayed_refresh_unsub()
            self._delayed_refresh_unsub = None

    @callback
    def _async_schedule_delayed_refresh(self) -> None:
        if self._delayed_refresh_unsub is not None:
            return

        self._delayed_refresh_unsub = async_call_later(
            self.hass,
            REQUEST_LOCATION_REFRESH_DELAY,
            self._async_handle_delayed_refresh,
        )

    @callback
    def _async_handle_delayed_refresh(self, _now) -> None:
        self._delayed_refresh_unsub = None
        self.hass.async_create_task(self.async_request_refresh())


class YQTDndSettingsCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Polls the shared watch-settings endpoint (`v2_findSetInfo`) for DND info.

    This endpoint was traced from APK analysis only (see issue #13) and is not
    confirmed to work against a live server. A failure here is logged and only
    marks this coordinator's own entities unavailable -- it must never take
    down `YQTDataUpdateCoordinator`, whose `v2_findLastPosition` polling is
    known-good.
    """

    def __init__(self, hass: HomeAssistant, client: YQTApiClient, main_coordinator: YQTDataUpdateCoordinator) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_dnd_settings",
            update_interval=DND_POLL_INTERVAL,
        )
        self.client = client
        self._main_coordinator = main_coordinator

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        results: dict[str, dict[str, Any]] = {}
        for did in self._main_coordinator.data:
            try:
                results[did] = await self.client.async_find_set_info(did)
            except YQTAuthError as exc:
                raise ConfigEntryAuthFailed(str(exc)) from exc
            except YQTError as exc:
                _LOGGER.debug("find_set_info failed for %s (unverified endpoint): %s", did, exc)
        return results
