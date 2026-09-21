"""
SANVI background voice service.

Run this with pythonw.exe on Windows for a no-window/no-iframe experience.
It listens for a wake phrase, then captures one complete command and sends it
to the same native executor used by sanvi_desktop.py.
"""

from __future__ import annotations

import os
import re
import time

import speech_recognition as sr

from sanvi_desktop import execute, log, speak

WAKE = re.compile(r"^\s*(?:hey\s+sanvi|sanvi)\b[\s,.:;-]*(.*)$", re.I)
LANGUAGE = os.getenv("SANVI_VOICE_LANGUAGE", "en-IN")


def main() -> None:
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.7
    recognizer.non_speaking_duration = 0.3

    with sr.Microphone() as microphone:
        recognizer.adjust_for_ambient_noise(microphone, duration=1.0)
        log("SANVI background voice service is listening.")

        while True:
            try:
                audio = recognizer.listen(microphone, timeout=None, phrase_time_limit=12)
                heard = recognizer.recognize_google(audio, language=LANGUAGE).strip()
                match = WAKE.match(heard)
                if not match:
                    continue

                command = match.group(1).strip()
                if not command:
                    speak("Yes, I am listening.")
                    audio = recognizer.listen(microphone, timeout=8, phrase_time_limit=30)
                    command = recognizer.recognize_google(audio, language=LANGUAGE).strip()

                if not command:
                    continue

                log(f"VOICE: {command}")
                try:
                    result = execute(command)
                    log(result)
                    speak(result.splitlines()[-1][:250])
                except Exception as exc:
                    log(f"FAILED: {exc}")
                    speak(f"Task failed. {str(exc)[:180]}")

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError as exc:
                log(f"Speech service error: {exc}")
                time.sleep(3)
            except KeyboardInterrupt:
                break
            except Exception as exc:
                log(f"Voice service error: {exc}")
                time.sleep(2)


if __name__ == "__main__":
    main()
