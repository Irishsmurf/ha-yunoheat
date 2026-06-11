"""Config flow for the Yuno Energy Heat integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from yunoheat import (
    APIConnectionError,
    AuthError,
    InMemoryTokenStore,
    PersonCustomer,
    TokenData,
    YunoHeatClient,
    YunoHeatError,
)
from yunoheat import ConfigEntryAuthFailed as YunoHeatAuthFailed

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import CONF_TOKENS, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="email")
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)

STEP_REAUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)


class YunoHeatConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Yuno Energy Heat."""

    VERSION = 1

    async def _async_validate_credentials(
        self, email: str, password: str
    ) -> tuple[dict[str, str], PersonCustomer | None, TokenData | None]:
        """Try to log in with the given credentials.

        Returns an (errors, person, tokens) tuple; on success errors is empty.
        """
        store = InMemoryTokenStore()
        session = aiohttp_client.async_get_clientsession(self.hass)
        try:
            client = await YunoHeatClient.login(
                email, password, session=session, token_store=store
            )
            person = await client.get_person_customer()
        except YunoHeatAuthFailed:
            return {"base": "invalid_auth"}, None, None
        except (AuthError, APIConnectionError, YunoHeatError):
            return {"base": "cannot_connect"}, None, None
        except Exception:
            _LOGGER.exception("Unexpected exception while validating credentials")
            return {"base": "unknown"}, None, None
        return {}, person, await store.load()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors, person, tokens = await self._async_validate_credentials(
                user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
            )
            if person is not None and tokens is not None:
                await self.async_set_unique_id(person.code)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_EMAIL],
                    data={**user_input, CONF_TOKENS: tokens.to_dict()},
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthentication after the password changed."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the new password and validate it."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        if user_input is not None:
            errors, person, tokens = await self._async_validate_credentials(
                reauth_entry.data[CONF_EMAIL], user_input[CONF_PASSWORD]
            )
            if person is not None and tokens is not None:
                await self.async_set_unique_id(person.code)
                self._abort_if_unique_id_mismatch(reason="unique_id_mismatch")
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_TOKENS: tokens.to_dict(),
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_DATA_SCHEMA,
            description_placeholders={CONF_EMAIL: reauth_entry.data[CONF_EMAIL]},
            errors=errors,
        )
