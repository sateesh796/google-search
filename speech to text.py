"""
JARVIS — Speech-to-Text (STT) Service
Modular service to convert spoken microphone audio to text.
Uses Gemini's native multimodal audio ingestion.
Can easily be swapped or extended with other STT providers (e.g. Whisper, LiveKit) in the future.
"""

import logging
import os
import google.generativeai as genai
from fastapi import HTTPException

logger = logging.getLogger("jarvis.voice.stt")


class SpeechToTextService:
    """Modular Speech-to-Text service for JARVIS."""

    def __init__(self):
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        self._model = None

    def _get_model(self) -> genai.GenerativeModel:
        if self._model is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY is not set for STT service.")

            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=(
                    "You are the high-precision Speech-to-Text engine for the JARVIS AI assistant. "
                    "Transcribe the user's spoken audio accurately. "
                    "Return ONLY the plain transcribed speech text. "
                    "Do NOT add any conversational prefixes, quotes, explanations, or metadata. "
                    "If the audio is silent or unintelligible, return an empty string."
                ),
            )
        return self._model

    async def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
        """
        Transcribe raw audio bytes to text.

        Args:
            audio_bytes: Raw binary audio from microphone.
            mime_type: Audio MIME type (audio/webm, audio/wav, audio/mp3, audio/ogg).

        Returns:
            The verbatim transcribed text string.
        """
        if not audio_bytes or len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio payload received.")

        # Normalize common browser mime types
        clean_mime = mime_type.split(";")[0].strip().lower()
        if not clean_mime or clean_mime == "application/octet-stream":
            clean_mime = "audio/webm"

        logger.info(
            "Transcribing audio: %d bytes (mime_type=%s, clean_mime=%s)",
            len(audio_bytes),
            mime_type,
            clean_mime,
        )

        model = self._get_model()

        audio_part = {
            "mime_type": clean_mime,
            "data": audio_bytes,
        }

        prompt = "Transcribe the exact words spoken in this audio accurately."

        try:
            response = model.generate_content([prompt, audio_part])
            transcript = response.text.strip() if response.text else ""
            logger.info("STT Transcription complete: '%s'", transcript)
            return transcript
        except Exception as exc:
            logger.error("STT transcription failed: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=502,
                detail=f"Speech-to-Text transcription failed: {str(exc)}",
            )


# Singleton instance
stt_service = SpeechToTextService()

