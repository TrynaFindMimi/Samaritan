import sys
import os
import time
import random
import re
import subprocess
import shutil
from typing import Optional


class SamaritanTUI:
    def __init__(self, voice: Optional[bool] = None, sfx: Optional[bool] = None):
        self.reset = '\033[0m'
        self.bold = '\033[1m'
        self.dim = '\033[2m'

        self.bright_red = '\033[91m'
        self.bright_green = '\033[92m'
        self.bright_yellow = '\033[93m'
        self.bright_cyan = '\033[96m'
        self.bright_white = '\033[97m'
        self.bone = '\033[38;2;220;220;210m'
        self.cyan_dim = '\033[38;2;80;200;220m'

        if voice is None:
            env_v = os.environ.get("SAMARITAN_VOICE", "").strip().lower()
            self.voice = env_v in ("1", "true", "yes", "on")
        else:
            self.voice = voice

        if sfx is None:
            env_s = os.environ.get("SAMARITAN_SFX", "").strip().lower()
            self.sfx = env_s in ("1", "true", "yes", "on")
        else:
            self.sfx = sfx

        self._voice_cmd = self._detect_tts()

    def _detect_tts(self):
        candidates = [
            ["spd-say", "-t", "male3", "-r", "-12"],
            ["spd-say", "-t", "male1"],
            ["espeak-ng", "-v", "en+m3", "-s", "155"],
            ["espeak", "-v", "en+m3", "-s", "155"],
        ]
        for cmd in candidates:
            if shutil.which(cmd[0]):
                return cmd
        return None

    def clear(self):
        print('\033[2J\033[H', end='')
        sys.stdout.flush()

    def cursor_hide(self):
        print('\033[?25l', end='')
        sys.stdout.flush()

    def cursor_show(self):
        print('\033[?25h', end='')
        sys.stdout.flush()

    def beep(self, freq=900, dur=0.03):
        if not self.sfx:
            return
        try:
            if shutil.which('play'):
                subprocess.Popen(['play', '-n', 'synth', f'{dur}', 'sin', f'{freq}', 'gain', '-20'],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            if shutil.which('sox'):
                subprocess.Popen(['play', '-n', 'synth', f'{dur}', 'sin', f'{freq}', 'gain', '-20'],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
        except Exception:
            pass
        sys.stdout.write('\a')
        sys.stdout.flush()

    def typewriter(self, text: str, delay: float = 0.008, end: str = '\n', sound: bool = True):
        if not text:
            print(end=end)
            return
        for i, char in enumerate(text):
            print(f"{self.bone}{char}{self.reset}", end='')
            sys.stdout.flush()
            if sound and char not in [' ', '\n']:
                if i % 4 == 0:
                    self.beep(880 + random.randint(-15, 15), 0.01)
            if char in ['.', ',', ';', ':']:
                time.sleep(delay * 2.5)
            elif char == '\n':
                time.sleep(delay * 1.5)
            else:
                time.sleep(delay)
        print(end=end)

    def thinking(self):
        print(f"{self.bright_cyan}> {self.reset}", end='')
        sys.stdout.flush()
        frames = ['.', '..', '...']
        for _ in range(4):
            for f in frames:
                sys.stdout.write(f'\r{self.bright_cyan}> {self.bone}ANALYZING{f}{self.reset}   ')
                sys.stdout.flush()
                self.beep(800, 0.008)
                time.sleep(0.04)
        sys.stdout.write('\r' + ' ' * 28 + '\r')
        sys.stdout.flush()

    def boot(self):
        self.clear()
        self.cursor_hide()
        try:
            logo = [
                "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓",
                "┃          ▓  S A M A R I T A N  ▓           ┃",
                "┃      AUTONOMOUS TACTICAL RESPONSE UNIT     ┃",
                "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛",
            ]
            for line in logo:
                print(f"{self.bright_cyan}{line}{self.reset}")
                self.beep(950, 0.02)
                time.sleep(0.05)

            print()
            init_steps = [
                f"{self.cyan_dim}[CORE]{self.reset} {self.bone}INITIALIZING",
                f"{self.cyan_dim}[NET]{self.reset}  {self.bone}SECURE CHANNEL",
                f"{self.cyan_dim}[ACL]{self.reset}  {self.bone}ACCESS CONTROL",
                f"{self.cyan_dim}[ID]{self.reset}   {self.bone}PRIORITY: ADMIN",
            ]
            for step in init_steps:
                print(step, end=' ')
                sys.stdout.flush()
                time.sleep(0.12)
                print(f"{self.bright_green}OK{self.reset}")
                self.beep(820, 0.015)

            print()
            print(f"{self.bright_green}{self.bold}> SAMARITAN ONLINE{self.reset}")
            print()
            self.beep(1100, 0.04)
            time.sleep(0.2)
            self.speak("SAMARITAN ONLINE")
        finally:
            self.cursor_show()

    def prompt(self):
        return f"{self.bright_cyan}>{self.reset} "

    def respond(self, text: str):
        print()
        print(f"{self.bright_cyan}>{self.reset} ", end='')
        sys.stdout.flush()
        self.beep(900, 0.02)
        self.typewriter(text, delay=0.01, end='\n')
        print()
        self.beep(740, 0.015)
        self.speak(text)

    def speak(self, text: str):
        if not self.voice or not self._voice_cmd:
            return
        try:
            clean = re.sub(r'\[[^\]]*\]', '', text)
            clean = re.sub(r'[\[\]{}()<>|┏┓┗┛━┃▓▒░>]', ' ', clean)
            clean = re.sub(r'\s+', ' ', clean).strip()
            if not clean:
                return
            if len(clean) > 200:
                clean = clean[:197] + "..."
            cmd = list(self._voice_cmd)
            if cmd[0] == 'spd-say':
                cmd.append(clean)
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif cmd[0] in ['espeak-ng', 'espeak']:
                cmd.append(clean)
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def main():
    tui = SamaritanTUI()
    tui.boot()


if __name__ == '__main__':
    main()
