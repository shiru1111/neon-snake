"""
Procedural 8-bit Sound Generator for Snake Game.
Synthesizes retro chimes, blips, and buzzes directly into memory using Python's
built-in `wave` and `struct` modules—no external audio files required.
"""

import io
import math
import struct
import wave
import pygame


def _synthesize_wav(samples: list[int], sample_rate: int = 44100) -> pygame.mixer.Sound:
    """Pack 16-bit signed integer samples into an in-memory WAV buffer and return a Pygame Sound."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        clamped = [max(-32767, min(32767, int(s))) for s in samples]
        wf.writeframes(struct.pack(f"<{len(clamped)}h", *clamped))
    buf.seek(0)
    return pygame.mixer.Sound(file=buf)


class SoundManager:
    """Manages playback of retro game sound effects."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.eat_sound = None
        self.bonus_sound = None
        self.game_over_sound = None
        self.click_sound = None
        self.bomb_sound = None
        self.spawn_sound = None
        self.victory_sound = None

        if not self.enabled:
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self._generate_sounds()
        except Exception as err:
            print(f"[SoundManager] Audio initialization notice: {err}. Audio will be muted.")
            self.enabled = False

    def _generate_sounds(self):
        sample_rate = 44100

        # 1. Eat Food: Crisp rising sweep (520Hz -> 980Hz, 85ms)
        eat_duration = 0.085
        eat_samples_len = int(sample_rate * eat_duration)
        eat_samples = []
        for i in range(eat_samples_len):
            t = i / sample_rate
            progress = i / eat_samples_len
            freq = 520 + (980 - 520) * progress
            # Sine wave with smooth decay envelope
            amp = 14000 * (1 - progress)
            sample = amp * math.sin(2 * math.pi * freq * t)
            eat_samples.append(sample)
        self.eat_sound = _synthesize_wav(eat_samples, sample_rate)
        self.eat_sound.set_volume(0.4)

        # 2. Bonus Golden Food: 3-note cheerful arpeggio (E5 -> G#5 -> B5 -> E6)
        bonus_duration = 0.18
        bonus_samples_len = int(sample_rate * bonus_duration)
        bonus_samples = []
        notes = [659.25, 830.61, 987.77, 1318.51]  # E5, G#5, B5, E6
        step_len = bonus_samples_len // len(notes)
        for i in range(bonus_samples_len):
            note_idx = min(i // step_len, len(notes) - 1)
            freq = notes[note_idx]
            sub_t = (i % step_len) / sample_rate
            note_progress = (i % step_len) / step_len
            amp = 15000 * (1.0 - note_progress * 0.7)
            # Add a bit of second harmonic for brightness
            sample = amp * (0.8 * math.sin(2 * math.pi * freq * sub_t) + 0.2 * math.sin(4 * math.pi * freq * sub_t))
            bonus_samples.append(sample)
        self.bonus_sound = _synthesize_wav(bonus_samples, sample_rate)
        self.bonus_sound.set_volume(0.5)

        # 3. Game Over: Descending distorted crunch/buzz (280Hz down to 60Hz)
        go_duration = 0.35
        go_samples_len = int(sample_rate * go_duration)
        go_samples = []
        for i in range(go_samples_len):
            progress = i / go_samples_len
            freq = 280 * (1.0 - progress * 0.75)
            t = i / sample_rate
            amp = 16000 * (1 - progress)
            # Mixed square/saw wave for retro crunch
            val = math.sin(2 * math.pi * freq * t)
            clipped = 1.0 if val > 0.15 else (-1.0 if val < -0.15 else val)
            go_samples.append(amp * clipped)
        self.game_over_sound = _synthesize_wav(go_samples, sample_rate)
        self.game_over_sound.set_volume(0.5)

        # 4. Click / UI selection blip
        click_duration = 0.03
        click_samples_len = int(sample_rate * click_duration)
        click_samples = []
        for i in range(click_samples_len):
            progress = i / click_samples_len
            amp = 10000 * (1 - progress)
            sample = amp * math.sin(2 * math.pi * 880 * (i / sample_rate))
            click_samples.append(sample)
        self.click_sound = _synthesize_wav(click_samples, sample_rate)
        self.click_sound.set_volume(0.3)

        # 5. Bomb / Tail explosion: punchy low-frequency thud with noise crunch (0.22s)
        bomb_duration = 0.22
        bomb_samples_len = int(sample_rate * bomb_duration)
        bomb_samples = []
        for i in range(bomb_samples_len):
            progress = i / bomb_samples_len
            freq = 160 * (1.0 - progress * 0.75)
            amp = 20000 * ((1 - progress) ** 1.8)
            # Bass wave + slight distortion noise
            sine = math.sin(2 * math.pi * freq * (i / sample_rate))
            noise = ((i * 1103515245 + 12345) % 65536 / 32768.0) - 1.0
            sample = amp * (0.75 * sine + 0.25 * noise)
            bomb_samples.append(sample)
        self.bomb_sound = _synthesize_wav(bomb_samples, sample_rate)
        self.bomb_sound.set_volume(0.6)

        # 6. Food Spawner: crisp high rising pop (0.06s)
        spawn_duration = 0.06
        spawn_samples_len = int(sample_rate * spawn_duration)
        spawn_samples = []
        for i in range(spawn_samples_len):
            progress = i / spawn_samples_len
            freq = 500 + (1100 - 500) * (progress ** 0.5)
            amp = 12000 * (1.0 - progress)
            sample = amp * math.sin(2 * math.pi * freq * (i / sample_rate))
            spawn_samples.append(sample)
        self.spawn_sound = _synthesize_wav(spawn_samples, sample_rate)
        self.spawn_sound.set_volume(0.4)

        # 7. Victory Fanfare: Triumphant rising arpeggio (C5 -> E5 -> G5 -> C6 -> E6 -> G6)
        vic_duration = 0.32
        vic_samples_len = int(sample_rate * vic_duration)
        vic_samples = []
        vic_notes = [523.25, 659.25, 783.99, 1046.50, 1318.51, 1567.98]
        vic_step_len = vic_samples_len // len(vic_notes)
        for i in range(vic_samples_len):
            note_idx = min(i // vic_step_len, len(vic_notes) - 1)
            freq = vic_notes[note_idx]
            sub_t = (i % vic_step_len) / sample_rate
            note_progress = (i % vic_step_len) / vic_step_len
            amp = 16000 * (1.0 - note_progress * 0.5)
            sample = amp * (0.8 * math.sin(2 * math.pi * freq * sub_t) + 0.2 * math.sin(4 * math.pi * freq * sub_t))
            vic_samples.append(sample)
        self.victory_sound = _synthesize_wav(vic_samples, sample_rate)
        self.victory_sound.set_volume(0.6)

    def play_eat(self):
        if self.enabled and self.eat_sound:
            self.eat_sound.play()

    def play_bonus(self):
        if self.enabled and self.bonus_sound:
            self.bonus_sound.play()

    def play_game_over(self):
        if self.enabled and self.game_over_sound:
            self.game_over_sound.play()

    def play_click(self):
        if self.enabled and self.click_sound:
            self.click_sound.play()

    def play_bomb(self):
        if self.enabled and self.bomb_sound:
            self.bomb_sound.play()

    def play_spawn(self):
        if self.enabled and self.spawn_sound:
            self.spawn_sound.play()

    def play_victory(self):
        if self.enabled and self.victory_sound:
            self.victory_sound.play()

