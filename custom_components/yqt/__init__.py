from __future__ import annotations

from typing import TYPE_CHECKING

from .const import CONF_LOGINNAME, CONF_PASSWORD, CONF_REGION, DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

PLATFORMS = (
    "device_tracker",
    "sensor",
    "button",
    "binary_sensor",
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    import aiohttp

    from homeassistant.helpers.aiohttp_client import async_create_clientsession

    from .core.async_client import YQTApiClient
    from .coordinator import YQTDataUpdateCoordinator, YQTDndSettingsCoordinator

    session = async_create_clientsession(
        hass,
        cookie_jar=aiohttp.CookieJar(unsafe=True),
    )
    client = YQTApiClient(
        session,
        region=entry.data[CONF_REGION],
        loginname=entry.data[CONF_LOGINNAME],
        password=entry.data[CONF_PASSWORD],
    )
    coordinator = YQTDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    # Unverified endpoint (see YQTDndSettingsCoordinator) -- a plain refresh
    # rather than async_config_entry_first_refresh(), so it can't block setup
    # of the rest of the entry if it doesn't work against this account.
    dnd_coordinator = YQTDndSettingsCoordinator(hass, client, coordinator)
    await dnd_coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "dnd_coordinator": dnd_coordinator,
    }

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        runtime = hass.data[DOMAIN].pop(entry.entry_id, None)
        if runtime is not None:
            runtime["coordinator"].async_shutdown()
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
