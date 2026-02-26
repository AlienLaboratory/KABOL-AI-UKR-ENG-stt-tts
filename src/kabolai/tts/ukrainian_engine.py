"""Ukrainian TTS using robinhad/ukrainian-tts (ESPnet v2).

First run downloads stanza + TTS model (~1-2 min). After that it's fast.
Has timeout protection and lazy retry if first init fails.
"""

import io
import logging
import queue
import threading
from typing import Optional

from kabolai.core.exceptions import TTSError
from kabolai.tts.base import TTSEngine, SpeechResult

logger = logging.getLogger(__name__)

# Maximum seconds for synthesis of a single utterance
UK_TTS_TIMEOUT = 15

# Maximum seconds for initial model loading (first run downloads ~200MB)
UK_INIT_TIMEOUT = 180


class UkrainianTTS(TTSEngine):
    """Ukrainian TTS using the ukrainian-tts package.

    On first run, downloads stanza Ukrainian models + TTS model (~200MB).
    This can take 1-2 minutes. After that, init takes ~5 seconds.

    If init fails/times out, it retries on next synthesize() call.
    """

    def __init__(self, voice: str = "Dmytro", stress: str = "Dictionary", device: str = "cpu"):
        self._voice_name = voice
        self._stress_name = stress
        self._device = device
        self._tts = None
        self._voices_enum = None
        self._stress_enum = None
        self._init_attempted = False
        self._init_lock = threading.Lock()

    def _ensure_initialized(self) -> bool:
        """Lazy init — only loads model when first needed. Returns True if ready."""
        if self._tts is not None:
            return True

        with self._init_lock:
            # Double-check after acquiring lock
            if self._tts is not None:
                return True

            if self._init_attempted:
                return False  # Already failed, don't retry every call

            self._init_attempted = True
            return self._do_init()

    def _do_init(self) -> bool:
        """Actually initialize TTS. Returns True on success."""
        logger.info(
            "Initializing Ukrainian TTS (first run downloads models, may take 1-2 min)..."
        )
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
            status, *args = result_q.get(timeout=UK_INIT_TIMEOUT)
        except queue.Empty:
            logger.error(
                f"Ukrainian TTS init timed out after {UK_INIT_TIMEOUT}s. "
                f"Model may still be downloading. Try again later."
            )
            self._init_attempted = False  # Allow retry
            return False

        if status == "import_error":
            logger.error(
                "ukrainian-tts not installed. "
                "Run: pip install git+https://github.com/robinhad/ukrainian-tts.git"
            )
            return False
        elif status == "error":
            logger.error(f"Ukrainian TTS init failed: {args[0]}")
            self._init_attempted = False  # Allow retry
            return False
        else:
            self._tts = args[0]
            self._voices_enum = args[1]
            self._stress_enum = args[2]
            logger.info(
                f"✓ Ukrainian TTS ready: voice={self._voice_name}, "
                f"stress={self._stress_name}, device={self._device}"
            )
            return True

    def synthesize(self, text: str) -> SpeechResult:
        """Synthesize Ukrainian text to WAV audio (with timeout)."""
        if not text.strip():
            return SpeechResult(audio_data=b"", sample_rate=22050)

        if not self._ensure_initialized():
            logger.warning("[Ukrainian TTS] Not available — returning silence.")
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
            logger.error(f"Ukrainian TTS synthesis timed out after {UK_TTS_TIMEOUT}s")
            return SpeechResult(audio_data=b"", sample_rate=22050)

        if status == "error":
            logger.error(f"Ukrainian TTS synthesis failed: {data}")
            return SpeechResult(audio_data=b"", sample_rate=22050)

        if len(data) < 100:
            logger.warning(f"Ukrainian TTS returned suspiciously small audio: {len(data)} bytes")
            return SpeechResult(audio_data=b"", sample_rate=22050)

        logger.info(f"[Ukrainian TTS] '{text[:40]}' -> {len(data)} bytes")
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
