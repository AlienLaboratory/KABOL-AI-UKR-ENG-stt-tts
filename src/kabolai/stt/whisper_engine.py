"""faster-whisper based speech-to-text engine (GPU accelerated).

Whisper large-v3 on RTX 4070: ~3GB VRAM, ~2-3% WER, supports 99 languages.
Uses VAD filter + initial_prompt to improve command recognition accuracy.
"""

import logging
from typing import Optional

import numpy as np

from kabolai.core.exceptions import STTError
from kabolai.stt.base import STTEngine, TranscriptionResult

logger = logging.getLogger(__name__)


class WhisperSTT(STTEngine):
    """faster-whisper GPU speech recognition engine.

    Much more accurate than VOSK (~3-4% WER vs ~15-20% WER).
    Supports both English and Ukrainian natively.
    """

    def __init__(
        self,
        model_size: str = "medium",
        device: str = "cuda",
        compute_type: str = "float16",
    ):
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model = None

    def load_model(self, model_path: str = None) -> None:
        """Load faster-whisper model. Downloads automatically on first use."""
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise STTError(
                "faster-whisper not installed. Run: pip install faster-whisper"
            )

        # Auto-detect GPU if requested but not available
        device = self._device
        compute_type = self._compute_type
        if device == "cuda":
            try:
                import ctranslate2
                if ctranslate2.get_cuda_device_count() == 0:
                    logger.warning("CUDA requested but no GPU found. Falling back to CPU.")
                    device = "cpu"
                    compute_type = "int8"
            except Exception:
                logger.warning("Cannot check CUDA. Falling back to CPU.")
                device = "cpu"
                compute_type = "int8"

        logger.info(
            f"Loading Whisper '{self._model_size}' on {device} ({compute_type})... "
            f"This may take a few minutes on first run (model download)."
        )
        self._model = WhisperModel(
            self._model_size,
            device=device,
            compute_type=compute_type,
        )
        logger.info(
            f"✓ Whisper '{self._model_size}' loaded on {device} ({compute_type}). "
            f"Ready for speech recognition."
        )

    def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """Transcribe audio using faster-whisper.

        Uses VAD filter to skip silence segments and improve accuracy.
        """
        if self._model is None:
            raise STTError("Whisper model not loaded. Call load_model() first.")

        # faster-whisper expects float32 normalized audio
        if audio_data.dtype == np.int16:
            audio_float = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype in (np.float32, np.float64):
            audio_float = audio_data.astype(np.float32)
        else:
            audio_float = audio_data.astype(np.float32)

        # Log audio quality info for debugging
        duration = len(audio_float) / sample_rate
        rms = float(np.sqrt(np.mean(audio_float ** 2)))
        logger.debug(
            f"[Whisper] Input: {duration:.1f}s, RMS={rms:.4f}, "
            f"model={self._model_size}, lang={language}"
        )

        # Map language codes
        whisper_lang = {"en": "en", "uk": "uk"}.get(language)

        # Initial prompt biases Whisper toward common voice commands
        # This dramatically improves accuracy for short utterances
        if whisper_lang == "uk":
            initial_prompt = (
                "відкрий ютуб, відкрий гугл, грай музику, яка погода, "
                "котра година, гучність, відкрий браузер, пошук"
            )
        else:
            initial_prompt = (
                "open YouTube, open Google, play music, what time is it, "
                "search for, volume up, volume down, open browser, "
                "what's the weather, open Chrome, play a song"
            )

        try:
            segments, info = self._model.transcribe(
                audio_float,
                language=whisper_lang,
                beam_size=5,
                initial_prompt=initial_prompt,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=300,
                    speech_pad_ms=200,
                ),
            )

            # Collect all text segments
            texts = []
            for seg in segments:
                text = seg.text.strip()
                if text:
                    texts.append(text)

            full_text = " ".join(texts)
            detected_lang = info.language if info else (language or "en")
            confidence = info.language_probability if info else 0.0

        except Exception as e:
            logger.error(f"Whisper transcription error: {e}", exc_info=True)
            return TranscriptionResult(
                text="", language=language or "en",
                confidence=0.0, is_final=True,
            )

        return TranscriptionResult(
            text=full_text,
            language=detected_lang,
            confidence=confidence,
            is_final=True,
        )

    def supports_language(self, lang_code: str) -> bool:
        # Whisper supports 99 languages natively
        return lang_code in ("en", "uk")

    def cleanup(self) -> None:
        self._model = None
