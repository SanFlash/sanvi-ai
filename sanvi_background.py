"""
SANVI background voice service.

Keeps a microphone listener alive in the background. Say "Hey Sanvi" or
"Sanvi" to start a continuous conversational session. Once active, SANVI
accepts command after command and keeps asking for the next command until
"Good night" is spoken.
"""

from __future__ import annotations

import os
import re
import time
import traceback

import speech_recognition as sr

from sanvi_desktop import (
    _is_good_night,
    _strip_wake_phrase,
    log,
    run_command,
    speak,
)

WAKE = re.compile(r"^\s*(?:hey\s+sanvi|sanvi)\b[\s,.:;-]*(.*)$", re.I)
LANGUAGE = os.getenv("SANVI_VOICE_LANGUAGE", "en-IN")


def listen_command(recognizer: sr.Recognizer, microphone, timeout=None, phrase_time_limit=30) -> str:
    audio = recognizer.listen(
        microphone,
        timeout=timeout,
        phrase_time_limit=phrase_time_limit,
    )
    last_error = None
    for language in dict.fromkeys([LANGUAGE, "en-US", "hi-IN"]):
        try:
            result = recognizer.recognize_google(audio, language=language).strip()
            if result:
                log(f"Speech recognized ({language}): {result}")
                return result
        except sr.UnknownValueError as exc:
            last_error = exc
            continue
        except sr.RequestError:
            raise
    if last_error:
        raise last_error
    return ""


def conversation_loop(
    recognizer: sr.Recognizer,
    microphone,
    first_command: str = "",
) -> None:
    """Stay in command mode until Good night."""
    command = first_command.strip()

    if not command:
        speak("Yes, I am listening.")

    while True:
        if _is_good_night(command):
            speak("Good night. Conversation ended.")
            log("Good night. SANVI conversation ended; waiting for Hey Sanvi.")
            return

        if command:
            log(f"VOICE COMMAND: {command}")
            success = run_command(command)
            if success:
                speak("What should I do next?")

        try:
            command = listen_command(
                recognizer,
                microphone,
                timeout=None,
                phrase_time_limit=90,
            )
            command = _strip_wake_phrase(command)
            if not command:
                speak("Yes, I am listening.")
        except sr.UnknownValueError:
            log("ERROR: Speech could not be understood; waiting for the next command.")
            speak("Voice error. Retry.")
            command = ""
        except sr.RequestError as exc:
            log(f"Speech service error: {exc}")
            speak("Speech recognition is temporarily unavailable.")
            time.sleep(2)
            command = ""
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            log(f"Conversation voice error: {exc}")
            speak("I could not hear the command. Please try again.")
            command = ""


def main() -> None:
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.7
    recognizer.non_speaking_duration = 0.3

    try:
        with sr.Microphone() as microphone:
            log("Calibrating SANVI microphone...")
            recognizer.adjust_for_ambient_noise(microphone, duration=1.5)
            recognizer.energy_threshold = max(250, recognizer.energy_threshold)
            log("SANVI background voice service is ready. Say 'Hey Sanvi'.")

            while True:
                try:
                    heard = listen_command(
                        recognizer,
                        microphone,
                        timeout=None,
                        phrase_time_limit=20,
                    )
                    match = WAKE.match(heard)
                    if not match:
                        continue

                    command = match.group(1).strip()
                    if _is_good_night(command):
                        speak("Good night.")
                        continue

                    log("Wake phrase detected.")
                    conversation_loop(recognizer, microphone, command)

                except sr.UnknownValueError:
                    continue
                except sr.RequestError as exc:
                    log(f"ERROR: Speech service error: {exc}")
                    traceback.print_exc()
                    speak("Voice error. Retry.")
                    time.sleep(3)
                except KeyboardInterrupt:
                    break
                except Exception as exc:
                    log(f"ERROR: Background voice service: {exc}")
                    traceback.print_exc()
                    speak("Voice error. Retry.")
                    time.sleep(2)
    finally:
        log("SANVI background voice service stopped.")


if __name__ == "__main__":
    main()
