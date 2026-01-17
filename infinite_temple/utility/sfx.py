import pygame
import random
import os
import glob


class SoundEffectsPlayer:
    """Manages and plays sound effects during gameplay."""

    def __init__(self):
        self.sounds = {}
        self.enabled = True

    def load_sounds(self, asset_dir="assets"):
        """
        Load all sound effect files from the assets directory.

        Args:
            asset_dir: Directory containing sound effect files
        """
        # Initialize pygame mixer if not already done
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

        # Ensure we have enough channels for music + sound effects
        # Reserve at least 16 channels total (music voices + sfx)
        current_channels = pygame.mixer.get_num_channels()
        if current_channels < 16:
            pygame.mixer.set_num_channels(16)

        # Load impact sounds (all variations)
        impact_files = glob.glob(os.path.join(asset_dir, "impact*.wav"))
        self.sounds['impact'] = []
        for file in impact_files:
            try:
                sound = pygame.mixer.Sound(file)
                self.sounds['impact'].append(sound)
            except Exception as e:
                print(f"Warning: Could not load {file}: {e}")

        # Load collapse sounds (all variations)
        collapse_files = glob.glob(os.path.join(asset_dir, "collapse*.wav"))
        self.sounds['collapse'] = []
        for file in collapse_files:
            try:
                sound = pygame.mixer.Sound(file)
                self.sounds['collapse'].append(sound)
            except Exception as e:
                print(f"Warning: Could not load {file}: {e}")

        # Load priest sounds (all variations)
        priest_files = glob.glob(os.path.join(asset_dir, "priest*.wav"))
        self.sounds['priest'] = []
        for file in priest_files:
            try:
                sound = pygame.mixer.Sound(file)
                self.sounds['priest'].append(sound)
            except Exception as e:
                print(f"Warning: Could not load {file}: {e}")

        # Load vision sounds (all variations)
        vision_files = glob.glob(os.path.join(asset_dir, "vision*.wav"))
        self.sounds['vision'] = []
        for file in vision_files:
            try:
                sound = pygame.mixer.Sound(file)
                self.sounds['vision'].append(sound)
            except Exception as e:
                print(f"Warning: Could not load {file}: {e}")

        # Load explosion sounds (all variations)
        explosion_files = glob.glob(os.path.join(asset_dir, "explosion*.wav"))
        self.sounds['explosion'] = []
        for file in explosion_files:
            try:
                sound = pygame.mixer.Sound(file)
                self.sounds['explosion'].append(sound)
            except Exception as e:
                print(f"Warning: Could not load {file}: {e}")

        print(f"Loaded {len(self.sounds['impact'])} impact sounds")
        print(f"Loaded {len(self.sounds['collapse'])} collapse sounds")
        print(f"Loaded {len(self.sounds['priest'])} priest sounds")
        print(f"Loaded {len(self.sounds['vision'])} vision sounds")
        print(f"Loaded {len(self.sounds['explosion'])} explosion sounds")

    def play_random(self, sound_type, volume=1.0):
        """
        Play a random sound of the given type.

        Args:
            sound_type: Type of sound ('impact', 'collapse', 'priest', 'vision')
            volume: Volume level (0.0 to 1.0)
        """
        if not self.enabled:
            return

        if sound_type not in self.sounds or len(self.sounds[sound_type]) == 0:
            return

        # Pick random sound from the type
        sound_list = self.sounds[sound_type]
        sound_index = random.randint(0, len(sound_list) - 1)
        sound = sound_list[sound_index]
        sound.set_volume(volume)

        # Find an available channel and play
        channel = pygame.mixer.find_channel()
        if channel:
            channel.play(sound)

    def play_impact(self, volume=0.5):
        """Play a random impact sound."""
        self.play_random('impact', volume)

    def play_collapse(self, volume=0.5):
        """Play a random collapse sound."""
        self.play_random('collapse', volume)

    def play_priest(self, volume=0.4):
        """Play a random priest sound."""
        self.play_random('priest', volume)

    def play_vision(self, volume=0.4):
        """Play a random vision sound."""
        self.play_random('vision', volume)

    def play_explosion(self, volume=0.6):
        """Play the explosion sound."""
        self.play_random('explosion', volume)

    def set_enabled(self, enabled):
        """Enable or disable sound effects."""
        self.enabled = enabled


# Global sound effects player instance
_sfx_player = SoundEffectsPlayer()


def load_sound_effects(asset_dir="assets"):
    """Load all sound effects from the assets directory."""
    _sfx_player.load_sounds(asset_dir)


def play_impact_sound(volume=0.5):
    """Play a random impact sound effect."""
    _sfx_player.play_impact(volume)


def play_collapse_sound(volume=0.5):
    """Play a random collapse sound effect."""
    _sfx_player.play_collapse(volume)


def play_priest_sound(volume=0.4):
    """Play a random priest sound effect."""
    _sfx_player.play_priest(volume)


def play_vision_sound(volume=0.4):
    """Play a random vision sound effect."""
    _sfx_player.play_vision(volume)


def play_explosion_sound(volume=0.6):
    """Play the explosion sound effect."""
    _sfx_player.play_explosion(volume)


def set_sfx_enabled(enabled):
    """Enable or disable sound effects."""
    _sfx_player.set_enabled(enabled)
