"""Real phone calls through LiveKit SIP: dial, play the prompt, read the key the customer presses."""

from __future__ import annotations

import asyncio
import contextlib
import time
import uuid

import structlog
from livekit import api, rtc

from modules.voice.adapters.speech_client import Audio, SpeechClient
from modules.workflows.ports.channels import CallRequest, CallResult

logger = structlog.get_logger()

_BUSY = {486, 600, 603}
_NO_ANSWER = {408, 480, 487}
_FRAME_MS = 20
_CALLEE = "customer"


async def _play(source: rtc.AudioSource, audio: Audio, stop: asyncio.Event | None = None) -> None:
    """Stream audio in 20 ms frames; stops early when `stop` is set (a key was pressed)."""
    samples = audio.sample_rate * _FRAME_MS // 1000
    step = samples * 2
    for offset in range(0, len(audio.pcm), step):
        if stop is not None and stop.is_set():
            source.clear_queue()
            return
        chunk = audio.pcm[offset : offset + step].ljust(step, b"\x00")
        await source.capture_frame(rtc.AudioFrame(chunk, audio.sample_rate, 1, samples))
    await source.wait_for_playout()


class LiveKitKeypadTelephony:
    def __init__(
        self,
        url: str,
        api_key: str,
        api_secret: str,
        sip_trunk_id: str,
        speech: SpeechClient,
        caller_number: str | None = None,
    ) -> None:
        self._url, self._key, self._secret = url, api_key, api_secret
        self._trunk = sip_trunk_id
        self._caller = caller_number or ""
        self._speech = speech

    async def place_keypad_call(self, request: CallRequest) -> CallResult:
        # Synthesize everything before dialing, so a TTS outage never leaves a customer in silence.
        prompt = await self._speech.synthesize(request.prompt, request.language)
        replies = {k: await self._speech.synthesize(v, request.language) for k, v in request.replies.items()}

        room_name = f"call-{request.run_id.hex[:12]}-{uuid.uuid4().hex[:6]}"
        lk = api.LiveKitAPI(self._url, self._key, self._secret)
        room = rtc.Room()
        digits: asyncio.Queue[str] = asyncio.Queue()
        pressed = asyncio.Event()
        hung_up = asyncio.Event()

        @room.on("sip_dtmf_received")
        def _on_dtmf(dtmf: rtc.SipDTMF) -> None:
            digits.put_nowait(dtmf.digit)
            pressed.set()

        @room.on("participant_disconnected")
        def _on_left(participant: rtc.RemoteParticipant) -> None:
            if participant.identity == _CALLEE:
                hung_up.set()

        try:
            token = (
                api.AccessToken(self._key, self._secret)
                .with_identity("ivr")
                .with_grants(api.VideoGrants(room_join=True, room=room_name))
                .to_jwt()
            )
            await room.connect(self._url, token)
            source = rtc.AudioSource(prompt.sample_rate, 1)
            track = rtc.LocalAudioTrack.create_audio_track("prompt", source)
            await room.local_participant.publish_track(
                track, rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
            )

            try:
                await lk.sip.create_sip_participant(
                    api.CreateSIPParticipantRequest(
                        sip_trunk_id=self._trunk,
                        sip_call_to=request.to,
                        sip_number=self._caller,
                        room_name=room_name,
                        participant_identity=_CALLEE,
                        wait_until_answered=True,
                    )
                )
            except api.SipCallError as exc:
                code, detail = exc.sip_status_code, str(exc)[:300]
                if code in _BUSY:
                    return CallResult("busy", provider_ref=room_name, error=detail)
                if code in _NO_ANSWER:
                    return CallResult("no_answer", provider_ref=room_name, error=detail)
                return CallResult("failed", provider_ref=room_name, error=detail)

            answered = time.monotonic()
            digit = await self._collect_digit(source, prompt, request, digits, pressed, hung_up)
            if not hung_up.is_set():
                outcome = request.digits.get(digit or "")
                await _play(source, replies[outcome] if outcome else replies["no_input"])
            return CallResult(
                "answered", digit=digit, duration_seconds=int(time.monotonic() - answered), provider_ref=room_name
            )
        finally:
            with contextlib.suppress(Exception):
                await lk.room.delete_room(api.DeleteRoomRequest(room=room_name))
            with contextlib.suppress(Exception):
                await room.disconnect()
            await lk.aclose()

    @staticmethod
    async def _collect_digit(
        source: rtc.AudioSource,
        prompt: Audio,
        request: CallRequest,
        digits: asyncio.Queue[str],
        pressed: asyncio.Event,
        hung_up: asyncio.Event,
    ) -> str | None:
        """Play the prompt up to `repeat_prompt` times; return the first valid key pressed."""
        for _ in range(request.repeat_prompt):
            await _play(source, prompt, stop=pressed)
            deadline = time.monotonic() + request.input_timeout_seconds
            while not hung_up.is_set() and (remaining := deadline - time.monotonic()) > 0:
                try:
                    digit = await asyncio.wait_for(digits.get(), timeout=min(remaining, 0.5))
                except TimeoutError:
                    continue
                if digit in request.digits:
                    return digit
            if hung_up.is_set():
                return None
            pressed.clear()
        return None
