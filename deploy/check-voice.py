"""Real native TTS/local-STT round trip; not a substitute for human voice-note tests."""
import json
import os
from pathlib import Path
import sys


def main():
    from tools.tts_tool import text_to_speech_tool
    from tools.transcription_tools import transcribe_audio
    directory = Path(os.environ["HERMES_HOME"]) / "voice-acceptance"
    directory.mkdir(mode=0o700, exist_ok=True)
    audio = directory / "roundtrip.mp3"
    phrase = "Bailey voice test. My meeting is tomorrow at ten in the morning."
    raw = text_to_speech_tool(text=phrase, output_path=str(audio))
    result = json.loads(raw) if isinstance(raw, str) else raw
    if result.get("success") is False or not audio.is_file() or audio.stat().st_size == 0:
        raise RuntimeError("Native speech generation failed")
    audio.chmod(0o600)
    result = transcribe_audio(str(audio))
    text = result.get("transcript") or result.get("transcription") or result.get("text") or ""
    if result.get("success") is False or not all(word in text.lower() for word in ("meeting", "tomorrow", "morning")):
        raise RuntimeError("Native local transcription did not preserve the test meaning")
    corrupt = directory / "unsupported.mp3"
    corrupt.write_bytes(b"Bailey acceptance fixture: not an audio file")
    corrupt.chmod(0o600)
    invalid = transcribe_audio(str(corrupt))
    if invalid.get("success") is not False and not invalid.get("error"):
        raise RuntimeError("Invalid audio was not rejected")
    print("Native Edge TTS, local Whisper meaning check and corrupt-audio rejection passed. Human messaging/audio playback remain unverified.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Voice check failed ({type(exc).__name__}); inspect privately on the box.", file=sys.stderr)
        sys.exit(1)
