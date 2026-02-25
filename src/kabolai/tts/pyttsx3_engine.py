"""pyttsx3-based TTS for English — fresh engine per call for reliability.

pyttsx3 uses Windows SAPI5 COM objects. The runAndWait() call hangs
permanently in persistent daemon threads. The ONLY reliable fix is to
create a FRESH pyttsx3 engine + fresh COM apartment for each synthesis
request. This adds ~0.3-0.5s overhead but never hangs.
"""

import logging
import queue
import tempfile
import threading
from pathlib import Path

from kabolai.core.exceptions import TTSError
from kabolai.tts.base import TTSEngine, SpeechResult

logger = logging.getLogger(__name__)

# Maximum seconds to wait for a single TTS synthesis
TTS_TIMEOUT = 8


class Pyttsx3TTS(TTSEngine):
    """English TTS using pyttsx3 (Windows SAPI5).

    Creates a fresh COM apartment + fresh pyttsx3 engine for each call.
    This prevents the permanent runAndWait() hang that occurs when reusing
    a single engine across multiple calls from daemon threads.
    """

    def __init__(self, rate: int = 175, volume: float = 0.9):
        self._rate = rate
        self._volume = volume
        self._voice_id = None
        # Quick sanity check that pyttsx3 is importable
        try:
            import pyttsx3  # noqa: F401
        except ImportError:
            raise TTSError("pyttsx3 not installed. Run: pip install pyttsx3")

    def synthesize(self, text: str) -> SpeechResult:
        """Synthesize text to WAV audio bytes (thread-safe, never hangs).

        Each call creates a fresh thread + fresh pyttsx3 engine + fresh
        COM apartment. This is the nuclear option but it WORKS.
        """
        if not text.strip():
            return SpeechResult(audio_data=b"", sample_rate=22050)

        # Create temp file for pyttsx3 output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        result_q = queue.Queue()
        rate = self._rate
        volume = self._volume
        voice_id = self._voice_id

        def _tts_worker():
            """Run in a fresh thread with fresh COM apartment."""
            # Explicit COM initialization — this is the critical fix
            try:
                import pythoncom
                pythoncom.CoInitialize()
                has_pythoncom = True
            except ImportError:
                # Fallback: use ctypes for COM init
                try:
                    import ctypes
                    ctypes.windll.ole32.CoInitialize(None)
                except Exception:
                    pass
                has_pythoncom = False

            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty("rate", rate)
                engine.setProperty("volume", volume)
                if voice_id:
                    engine.setProperty("voice", voice_id)

                engine.save_to_file(text, tmp_path)
                engine.runAndWait()
                engine.stop()
                del engine

                wav_data = Path(tmp_path).read_bytes()
                Path(tmp_path).unlink(missing_ok=True)
                result_q.put(("ok", wav_data))
            except Exception as e:
                Path(tmp_path).unlink(missing_ok=True)
                result_q.put(("error", str(e)))
            finally:
                # Clean up COM apartment
                if has_pythoncom:
                    try:
                        import pythoncom
                        pythoncom.CoUninitialize()
                    except Exception:
                        pass

        # Launch worker thread (NOT daemon — let it finish even if main dies)
        t = threading.Thread(target=_tts_worker, name="pyttsx3-oneshot")
        t.start()

        # Wait with timeout — prevents infinite hang
        try:
            status, data = result_q.get(timeout=TTS_TIMEOUT)
        except queue.Empty:
            Path(tmp_path).unlink(missing_ok=True)
            logger.error(f"pyttsx3 timed out after {TTS_TIMEOUT}s — thread stuck")
            raise TTSError(f"TTS synthesis timed out after {TTS_TIMEOUT}s")

        if status == "error":
            raise TTSError(f"pyttsx3 synthesis failed: {data}")

        return SpeechResult(audio_data=data, sample_rate=22050, format="wav")

    def get_available_voices(self) -> list:
        """Get available SAPI voices (creates temporary engine)."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            result = [v.id for v in voices] if voices else []
            engine.stop()
            del engine
            return result
        except Exception:
            return []

    def set_voice(self, voice_id: str) -> None:
        self._voice_id = voice_id

    def set_speed(self, speed: float) -> None:
        # speed 1.0 = 175 wpm
        self._rate = int(175 * speed)

    def cleanup(self) -> None:
        pass  # No persistent resources to clean up
