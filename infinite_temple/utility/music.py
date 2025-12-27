import json
import tempfile
import os

from tomita.legacy import pysynth_c as synthesizer
import pygame

from infinite_temple.schema.audio import AmbientMusic

class MusicPlayer:
    """Non-blocking music player that can be stopped and managed."""

    def __init__(self):
        self.temp_dir = None
        self.wav_files = []
        self.sounds = []
        self.channels = []
        self.is_playing = False

    def stop(self):
        """Stop all playing music and clean up resources."""
        if self.is_playing:
            pygame.mixer.stop()
            self.is_playing = False

        # Clean up temporary files
        for wav_file in self.wav_files:
            try:
                os.remove(wav_file)
            except:
                pass

        if self.temp_dir:
            try:
                os.rmdir(self.temp_dir)
            except:
                pass

        self.wav_files = []
        self.sounds = []
        self.channels = []
        self.temp_dir = None

    def play(self, music_dict, loop=True):
        """
        Start playing music without blocking.

        Args:
            music_dict: Dictionary with music data or JSON string
            loop: Whether to loop the music indefinitely (default: True)
        """
        # Stop any currently playing music
        self.stop()

        # Handle both dict and JSON string
        if isinstance(music_dict, str):
            music_dict = json.loads(music_dict)

        print(f"Playing: {music_dict['title']}")
        print(f"Key: {music_dict['key']} | Tempo: {music_dict['tempo_bpm']} BPM")
        print(f"Mood: {music_dict['mood']}")
        print(f"Voices: {len(music_dict['voices'])}")

        # Create temporary directory for WAV files
        self.temp_dir = tempfile.mkdtemp()

        # Generate WAV file for each voice using Tomita
        for i, voice in enumerate(music_dict['voices']):
            # Convert to Tomita/PySynth format: list of tuples
            notes = [(note['pitch'], note['duration']) for note in voice['notes']]

            temp_wav = os.path.join(self.temp_dir, f"voice_{i}_{voice['name']}.wav")

            # Generate WAV using Tomita's synthesizer
            synthesizer.make_wav(notes, fn=temp_wav, bpm=music_dict['tempo_bpm'])
            self.wav_files.append(temp_wav)

        # Initialize pygame mixer for playback (if not already initialized)
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

        pygame.mixer.set_num_channels(len(self.wav_files))

        # Load and play all voices simultaneously
        for i, wav_file in enumerate(self.wav_files):
            sound = pygame.mixer.Sound(wav_file)
            self.sounds.append(sound)

            channel = pygame.mixer.Channel(i)
            channel.play(sound, loops=-1 if loop else 0)
            self.channels.append(channel)

        self.is_playing = True
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