import json
import tempfile
import os

from tomita.legacy import pysynth_c as synthesizer
import pygame
from pedalboard import Pedalboard, Delay, Chorus, Reverb, Gain
from pedalboard.io import AudioFile
import numpy as np

from infinite_temple.schema.audio import AmbientMusic

class MusicPlayer:
    """Non-blocking music player that can be stopped and managed."""

    # Effect level constants
    EFFECT_NONE = 0
    EFFECT_MEDIUM = 1
    EFFECT_HEAVY = 2

    def __init__(self):
        self.temp_dir = None
        self.wav_files = {
            self.EFFECT_NONE: [],
            self.EFFECT_MEDIUM: [],
            self.EFFECT_HEAVY: []
        }
        self.sounds = []
        self.channels = []
        self.is_playing = False
        self.current_effect_level = self.EFFECT_NONE
        self.loop = True

    def _apply_effects(self, input_path, output_path, effect_level):
        """Apply Pedalboard effects to a WAV file."""
        with AudioFile(input_path) as f:
            audio = f.read(f.frames)
            sample_rate = f.samplerate

        if effect_level == self.EFFECT_MEDIUM:
            board = Pedalboard([
                Chorus(rate_hz=0.5, depth=0.3, mix=0.3),
                Delay(delay_seconds=0.3, feedback=0.2, mix=0.25),
            ])
        elif effect_level == self.EFFECT_HEAVY:
            board = Pedalboard([
                Chorus(rate_hz=0.8, depth=0.5, mix=0.5),
                Delay(delay_seconds=0.4, feedback=0.4, mix=0.4),
                Reverb(room_size=0.6, wet_level=0.3),
            ])
        else:
            return

        effected = board(audio, sample_rate)

        with AudioFile(output_path, 'w', sample_rate, effected.shape[0]) as f:
            f.write(effected)

    def stop(self):
        """Stop all playing music and clean up resources."""
        if self.is_playing:
            pygame.mixer.stop()
            self.is_playing = False

        # Clean up temporary files
        for level_files in self.wav_files.values():
            for wav_file in level_files:
                try:
                    os.remove(wav_file)
                except:
                    pass

        if self.temp_dir:
            try:
                os.rmdir(self.temp_dir)
            except:
                pass

        self.wav_files = {
            self.EFFECT_NONE: [],
            self.EFFECT_MEDIUM: [],
            self.EFFECT_HEAVY: []
        }
        self.sounds = []
        self.channels = []
        self.temp_dir = None
        self.current_effect_level = self.EFFECT_NONE

    def set_effect_level(self, level):
        """
        Switch to a different effect level.

        Args:
            level: EFFECT_NONE, EFFECT_MEDIUM, or EFFECT_HEAVY
        """
        if level == self.current_effect_level:
            return

        if not self.is_playing or not self.wav_files[level]:
            return

        self.current_effect_level = level

        # Stop current sounds and switch to new effect level
        for channel in self.channels:
            channel.stop()

        self.sounds = []
        self.channels = []

        # Load and play the new effect level files
        for i, wav_file in enumerate(self.wav_files[level]):
            sound = pygame.mixer.Sound(wav_file)
            sound.set_volume(0.4)
            self.sounds.append(sound)

            channel = pygame.mixer.Channel(i)
            channel.play(sound, loops=-1 if self.loop else 0)
            self.channels.append(channel)

    def play(self, music_dict, loop=True):
        """
        Start playing music without blocking.

        Args:
            music_dict: Dictionary with music data or JSON string
            loop: Whether to loop the music indefinitely (default: True)
        """
        # Stop any currently playing music
        self.stop()
        self.loop = loop

        # Handle both dict and JSON string
        if isinstance(music_dict, str):
            music_dict = json.loads(music_dict)

        print(f"Playing: {music_dict['title']}")
        print(f"Key: {music_dict['key']} | Tempo: {music_dict['tempo_bpm']} BPM")
        print(f"Mood: {music_dict['mood']}")
        print(f"Voices: {len(music_dict['voices'])}")

        # Create temporary directory for WAV files
        self.temp_dir = tempfile.mkdtemp()

        # Generate WAV file for each voice using Tomita, then create effect versions
        for i, voice in enumerate(music_dict['voices']):
            # Convert to Tomita/PySynth format: list of tuples
            notes = [(note['pitch'], note['duration']) for note in voice['notes']]

            # Base WAV (no effects)
            base_wav = os.path.join(self.temp_dir, f"voice_{i}_{voice['name']}_base.wav")
            synthesizer.make_wav(notes, fn=base_wav, bpm=music_dict['tempo_bpm'])
            self.wav_files[self.EFFECT_NONE].append(base_wav)

            # Medium effects version
            med_wav = os.path.join(self.temp_dir, f"voice_{i}_{voice['name']}_med.wav")
            self._apply_effects(base_wav, med_wav, self.EFFECT_MEDIUM)
            self.wav_files[self.EFFECT_MEDIUM].append(med_wav)

            # Heavy effects version
            heavy_wav = os.path.join(self.temp_dir, f"voice_{i}_{voice['name']}_heavy.wav")
            self._apply_effects(base_wav, heavy_wav, self.EFFECT_HEAVY)
            self.wav_files[self.EFFECT_HEAVY].append(heavy_wav)

        # Initialize pygame mixer for playback (if not already initialized)
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

        # Ensure we have enough channels for music voices + sound effects
        # Set to at least 16 total, or music voices + 12, whichever is larger
        num_voices = len(self.wav_files[self.EFFECT_NONE])
        required_channels = max(16, num_voices + 12)
        pygame.mixer.set_num_channels(required_channels)

        # Load and play base version (no effects)
        for i, wav_file in enumerate(self.wav_files[self.EFFECT_NONE]):
            sound = pygame.mixer.Sound(wav_file)
            sound.set_volume(0.4)
            self.sounds.append(sound)

            channel = pygame.mixer.Channel(i)
            channel.play(sound, loops=-1 if loop else 0)
            self.channels.append(channel)

        self.is_playing = True
        self.current_effect_level = self.EFFECT_NONE
        print(f"Music playing in background...")

# Global music player instance
_music_player = MusicPlayer()


def play_music_from_dict(music_dict, loop=True):
    """
    Play ambient music directly from a dictionary (no file needed).
    Non-blocking - returns immediately while music plays in background.

    Args:
        music_dict: Dictionary with music data (from LLM JSON response) or JSON string
        loop: Whether to loop the music indefinitely (default: True)
    """
    _music_player.play(music_dict, loop=loop)


def play_music_file(file: str):
    with open(file, "r") as f:
        audio_json = json.loads(f.read())
    audio_model = AmbientMusic.model_validate(audio_json)
    play_music_from_dict(audio_model.model_dump())


def stop_music():
    """Stop all playing music."""
    _music_player.stop()


def set_music_effect_level(difficulty: int):
    """
    Set music effect level based on game difficulty.

    Args:
        difficulty: Current difficulty level (0-10)
    """
    if difficulty >= 6:
        level = MusicPlayer.EFFECT_HEAVY
    elif difficulty >= 3:
        level = MusicPlayer.EFFECT_MEDIUM
    else:
        level = MusicPlayer.EFFECT_NONE

    _music_player.set_effect_level(level)