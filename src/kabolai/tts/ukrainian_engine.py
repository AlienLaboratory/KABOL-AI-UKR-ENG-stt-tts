"""Ukrainian TTS using robinhad/ukrainian-tts (ESPnet v2).

Has timeout protection — if synthesis takes more than 10s, it gives up
rather than hanging the entire pipeline.
"""

import io
import logging
import queue
import threading
from typing import Optional

from kabolai.core.exceptions import TTSError
from kabolai.tts.base import TTSEngine, SpeechResult

logger = logging.getLogger(__name__)

# Maximum seconds for Ukrainian TTS synthesis
UK_TTS_TIMEOUT = 10


class UkrainianTTS(TTSEngine):
    """Ukrainian TTS using the ukrainian-tts package.

    Runs synthesis in a separate thread with timeout protection.
    """

    def __init__(self, voice: str = "Dmytro", stress: str = "Dictionary", device: str = "cpu"):
        self._voice_name = voice
        self._stress_name = stress
        self._device = device
        self._tts = None
        self._voices_enum = None
        self._stress_enum = None
        self._init_error: Optional[str] = None
        self._initialize()

    def _initialize(self):
        """Initialize the TTS engine with timeout protection."""
        result_q = queue.Queue()

        def _init_worker():
            try:
                from ukrainian_tts.tts import TTS, Voices, Stress
                tts = TTS(device=self._device)
                result_q.put(("ok", tts, Voices, Stress))
            except ImportError:
                result_q.put(("import_error", None, None, None))
            except Exception as e:
                result_q.put(("error", str(e), None, None))

        t = threading.Thread(target=_init_worker, daemon=True)
        t.start()

        try:
            status, *args = result_q.get(timeout=60)
        except queue.Empty:
            self._init_error = "Ukrainian TTS init timed out (60s). Model may be downloading."
            logger.warning(self._init_error)
            return

        if status == "import_error":
            raise TTSError(
                "ukrainian-tts not installed. Run: "
                "pip install git+https://github.com/robinhad/ukrainian-tts.git"
            )
        elif status == "error":
            raise TTSError(f"Failed to initialize Ukrainian TTS: {args[0]}")
        else:
            self._tts = args[0]
            self._voices_enum = args[1]
            self._stress_enum = args[2]
            logger.info(
                f"Ukrainian TTS initialized: voice={self._voice_name}, "
                f"stress={self._stress_name}, device={self._device}"
            )

    def synthesize(self, text: str) -> SpeechResult:
        """Synthesize Ukrainian text to WAV audio (with timeout)."""
        if not text.strip():
            return SpeechResult(audio_data=b"", sample_rate=22050)

        if self._tts is None:
            if self._init_error:
                logger.warning(f"Ukrainian TTS unavailable: {self._init_error}")
            return SpeechResult(audio_data=b"", sample_rate=22050)

        result_q = queue.Queue()
        voice_name = self._voice_name
        stress_name = self._stress_name
        voices_enum = self._voices_enum
        stress_enum = self._stress_enum
        tts = self._tts

        def _synth_worker():
            try:
                voice_val = getattr(voices_enum, voice_name).value
                stress_val = getattr(stress_enum, stress_name).value
                wav_buffer = io.BytesIO()
                _, output_text = tts.tts(text, voice_val, stress_val, wav_buffer)
                wav_data = wav_buffer.getvalue()
                result_q.put(("ok", wav_data))
            except Exception as e:
                result_q.put(("error", str(e)))

        t = threading.Thread(target=_synth_worker, daemon=True)
        t.start()

        try:
            status, data = result_q.get(timeout=UK_TTS_TIMEOUT)
        except queue.Empty:
            logger.error(f"Ukrainian TTS timed out after {UK_TTS_TIMEOUT}s")
            return SpeechResult(audio_data=b"", sample_rate=22050)

        if status == "error":
            logger.error(f"Ukrainian TTS synthesis failed: {data}")
            return SpeechResult(audio_data=b"", sample_rate=22050)

        logger.debug(f"Ukrainian TTS: '{text[:50]}...' -> {len(data)} bytes")
        return SpeechResult(audio_data=data, sample_rate=22050, format="wav")

    def get_available_voices(self) -> list[str]:
        if self._voices_enum:
            return [v.name for v in self._voices_enum]
        return ["Oleksa", "Tetiana", "Dmytro", "Lada", "Mykyta"]

    def set_voice(self, voice_id: str) -> None:
        if self._voices_enum and hasattr(self._voices_enum, voice_id):
            self._voice_name = voice_id
        else:
            logger.warning(f"Unknown Ukrainian voice: {voice_id}")

    def cleanup(self) -> None:
        self._tts = None
