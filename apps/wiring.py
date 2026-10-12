"""Composition root: builds each tenant's channel adapters from settings and saved integrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from modules.integrations.adapters.shopify import ShopifyOutcomeSink
from modules.integrations.adapters.webhook import CallbackOutcomeSink
from modules.integrations.application import store
from modules.messaging.adapters.meta_whatsapp import MetaWhatsAppSender
from modules.tenancy.adapters.database import tenant_session
from modules.tenancy.domain.settings import Settings, get_settings
from modules.voice.adapters.livekit_keypad import LiveKitKeypadTelephony
from modules.voice.adapters.simulated import SimulatedTelephony
from modules.voice.adapters.speech_client import SpeechClient
from modules.workflows.application.engine import WorkflowEngine
from modules.workflows.ports.channels import Channels, OutcomeSink, TelephonyPort

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


class TenantChannelProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._speech = SpeechClient(settings.speech_url)

    async def for_tenant(self, session: AsyncSession, tenant_id: uuid.UUID) -> Channels:
        s = self._settings
        conns = await store.connections(session, tenant_id)

        telephony: TelephonyPort | None = None
        if s.telephony_backend == "simulated":
            telephony = SimulatedTelephony(s.simulated_digit, s.simulated_delay_seconds)
        else:
            tel = conns.get("telephony")
            trunk = (tel.config.get("sip_trunk_id") if tel else None) or s.livekit_sip_trunk_id
            if trunk:
                telephony = LiveKitKeypadTelephony(
                    s.livekit_url,
                    s.livekit_api_key,
                    s.livekit_api_secret,
                    trunk,
                    self._speech,
                    caller_number=tel.config.get("caller_number") if tel else None,
                )

        whatsapp = None
        if wa := conns.get("whatsapp"):
            whatsapp = MetaWhatsAppSender(
                wa.config["phone_number_id"], wa.secrets["access_token"], s.whatsapp_api_version
            )

        sinks: dict[str, OutcomeSink] = {}
        if shop := conns.get("shopify"):
            sinks["shopify"] = ShopifyOutcomeSink(
                shop.config["shop_domain"], shop.secrets["access_token"], s.shopify_api_version
            )
        if hook := conns.get("webhook"):
            sinks["webhook"] = CallbackOutcomeSink(hook.config.get("callback_url"), hook.secrets["signing_secret"])

        return Channels(telephony=telephony, whatsapp=whatsapp, outcome_sinks=sinks)


def build_engine(settings: Settings | None = None) -> WorkflowEngine:
    return WorkflowEngine(tenant_session, TenantChannelProvider(settings or get_settings()))
