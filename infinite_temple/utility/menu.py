import pygame
import random

from infinite_temple.utility.config import set_api_key, get_configured_providers
from infinite_temple.paths import get_assets_dir


# Shared title font (loaded on first use)
_title_font = None


def get_title_font(size=72):
    """Get the CloisterBlack font for game title."""
    global _title_font
    if _title_font is None:
        font_path = get_assets_dir() / "CloisterBlack.ttf"
        _title_font = pygame.font.Font(str(font_path), size)
    return _title_font


def draw_game_title(surface, y=60):
    """Draw 'Infinite Temple' title at top of screen."""
    font = get_title_font(72)
    title = font.render("Infinite Temple", True, (180, 180, 180))
    title_rect = title.get_rect(center=(surface.get_width() // 2, y))
    surface.blit(title, title_rect)


def draw_temple_name(surface, name, y=30):
    """Draw temple name at top of screen (for gameplay)."""
    font = pygame.font.Font(None, 28)
    title = font.render(name, True, (120, 120, 120))
    title_rect = title.get_rect(center=(surface.get_width() // 2, y))
    surface.blit(title, title_rect)


ATMOSPHERIC_WORDS = [
    # Cosmic (8 words)
    "void", "star", "eclipse", "nebula", "gravity", "orbit", "comet", "cosmos",
    # Structure (8 words)
    "temple", "spire", "vault", "chamber", "portal", "obelisk", "citadel", "monolith",
    # Mood (8 words)
    "shadow", "ancient", "whisper", "silent", "frozen", "forgotten", "hollow", "drift",
    # Elements (8 words)
    "crystal", "stone", "metal", "dust", "ash", "rust", "glass", "bone",
    # Texture (8 words)
    "sharp", "smooth", "jagged", "curved", "fractured", "twisted", "layered", "endless"
]


class TempleSelector:
    """
    Simple horizontal selector for temple navigation.

    Uses arrow keys to navigate, ENTER to select.
    """

    def __init__(self, surface, temples, on_temple_selected, on_update_background):
        """
        Initialize temple selector.

        Args:
            surface: Pygame surface for rendering
            temples: List of temple configurations
            on_temple_selected: Callback(temple_id) when temple chosen
            on_update_background: Callback(temple_id) when selection changes
        """
        self.surface = surface
        self.temples = temples
        self.on_temple_selected = on_temple_selected
        self.on_update_background = on_update_background

        # Build options
        self.options = [(t.narrative.title, t.temple_id) for t in temples]
        self.options.append(("Create New Temple", "CREATE_NEW"))

        self.current_index = 0
        self.font = pygame.font.Font(None, 24)

        # Colors
        self.text_color = (150, 150, 150)
        self.arrow_color = (100, 100, 100)

        # Trigger initial background
        if temples:
            self.on_update_background(temples[0].temple_id)

    def handle_event(self, event):
        """
        Handle keyboard events.

        Args:
            event: Pygame event

        Returns:
            True if event was handled
        """
        if event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_LEFT:
            self.current_index = (self.current_index - 1) % len(self.options)
            temple_id = self.options[self.current_index][1]
            self.on_update_background(temple_id)
            return True

        elif event.key == pygame.K_RIGHT:
            self.current_index = (self.current_index + 1) % len(self.options)
            temple_id = self.options[self.current_index][1]
            self.on_update_background(temple_id)
            return True

        elif event.key == pygame.K_RETURN:
            temple_id = self.options[self.current_index][1]
            self.on_temple_selected(temple_id)
            return True

        return False

    def draw(self):
        """Draw the selector with title at top, navigation at bottom."""
        # Draw game title at top
        draw_game_title(self.surface)

        # Get current option
        title, _ = self.options[self.current_index]

        # Render text
        text_surface = self.font.render(title, True, self.text_color)
        text_rect = text_surface.get_rect()

        # Position at bottom center
        x = self.surface.get_width() // 2
        y = self.surface.get_height() - 60

        # Draw arrows
        arrow_offset = text_rect.width // 2 + 20

        left_arrow = self.font.render("<", True, self.arrow_color)
        left_rect = left_arrow.get_rect()
        left_rect.center = (x - arrow_offset, y)
        self.surface.blit(left_arrow, left_rect)

        text_rect.center = (x, y)
        self.surface.blit(text_surface, text_rect)

        right_arrow = self.font.render(">", True, self.arrow_color)
        right_rect = right_arrow.get_rect()
        right_rect.center = (x + arrow_offset, y)
        self.surface.blit(right_arrow, right_rect)

        # Instructions at very bottom
        help_font = pygame.font.Font(None, 20)
        help_text = help_font.render("LEFT/RIGHT to browse  |  ENTER to select", True, (80, 80, 80))
        help_rect = help_text.get_rect(center=(x, self.surface.get_height() - 25))
        self.surface.blit(help_text, help_rect)


class WordPicker:
    """
    Three word selector for temple creation.

    Uses arrow keys to navigate words, ENTER to confirm, ESC to back.
    """

    def __init__(self, surface, on_generate_clicked, on_back_clicked):
        """
        Initialize word picker.

        Args:
            surface: Pygame surface
            on_generate_clicked: Callback(word1, word2, word3)
            on_back_clicked: Callback() when back pressed
        """
        self.surface = surface
        self.on_generate_clicked = on_generate_clicked
        self.on_back_clicked = on_back_clicked

        self.words = ATMOSPHERIC_WORDS
        self.selected_words = random.sample(range(len(self.words)), 3)  # Random default words
        self.current_slot = 0  # Which word slot (0, 1, or 2)

        self.font = pygame.font.Font(None, 24)
        self.text_color = (150, 150, 150)
        self.highlight_color = (200, 200, 200)
        self.arrow_color = (100, 100, 100)

    def handle_event(self, event):
        """
        Handle keyboard events.

        Returns:
            True if event was handled
        """
        if event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_LEFT:
            # Cycle word in current slot
            self.selected_words[self.current_slot] = (self.selected_words[self.current_slot] - 1) % len(self.words)
            return True

        elif event.key == pygame.K_RIGHT:
            # Cycle word in current slot
            self.selected_words[self.current_slot] = (self.selected_words[self.current_slot] + 1) % len(self.words)
            return True

        elif event.key == pygame.K_UP:
            # Move to previous slot
            self.current_slot = (self.current_slot - 1) % 3
            return True

        elif event.key == pygame.K_DOWN:
            # Move to next slot
            self.current_slot = (self.current_slot + 1) % 3
            return True

        elif event.key == pygame.K_RETURN:
            # Generate temple
            w1 = self.words[self.selected_words[0]]
            w2 = self.words[self.selected_words[1]]
            w3 = self.words[self.selected_words[2]]
            self.on_generate_clicked(w1, w2, w3)
            return True

        elif event.key == pygame.K_ESCAPE:
            # Back
            self.on_back_clicked()
            return True

        return False

    def draw(self):
        """Draw the word picker with title at top, words and instructions at bottom."""
        # Draw game title at top
        draw_game_title(self.surface)

        x = self.surface.get_width() // 2
        y_start = self.surface.get_height() - 130

        for i in range(3):
            word = self.words[self.selected_words[i]]
            color = self.highlight_color if i == self.current_slot else self.text_color

            # Render word
            text_surface = self.font.render(word, True, color)
            text_rect = text_surface.get_rect()
            y = y_start + (i * 30)
            text_rect.center = (x, y)

            # Draw arrows for current slot
            if i == self.current_slot:
                arrow_offset = text_rect.width // 2 + 20

                left_arrow = self.font.render("<", True, self.arrow_color)
                left_rect = left_arrow.get_rect()
                left_rect.center = (x - arrow_offset, y)
                self.surface.blit(left_arrow, left_rect)

                right_arrow = self.font.render(">", True, self.arrow_color)
                right_rect = right_arrow.get_rect()
                right_rect.center = (x + arrow_offset, y)
                self.surface.blit(right_arrow, right_rect)

            # Draw word
            self.surface.blit(text_surface, text_rect)

        # Instructions at very bottom
        help_font = pygame.font.Font(None, 20)
        help_text = help_font.render("UP/DOWN to select slot  |  LEFT/RIGHT to change word  |  ENTER to generate  |  ESC to back", True, (80, 80, 80))
        help_rect = help_text.get_rect(center=(x, self.surface.get_height() - 25))
        self.surface.blit(help_text, help_rect)


class EmptyStateMenu:
    """
    Simple menu for when no temples exist.

    Shows message and 'Create Temple' button.
    """

    def __init__(self, surface, on_create_clicked):
        """
        Initialize empty state menu.

        Args:
            surface: Pygame surface
            on_create_clicked: Callback() when create pressed
        """
        self.surface = surface
        self.on_create_clicked = on_create_clicked

        self.font = pygame.font.Font(None, 24)
        self.text_color = (150, 150, 150)

    def handle_event(self, event):
        """
        Handle keyboard events.

        Returns:
            True if event was handled
        """
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.on_create_clicked()
            return True
        return False

    def draw(self):
        """Draw the empty state menu with title at top, instructions at bottom."""
        # Draw game title at top
        draw_game_title(self.surface)

        x = self.surface.get_width() // 2

        # Instructions at bottom
        help_font = pygame.font.Font(None, 20)
        help_text = help_font.render("Press ENTER to create your first temple", True, (80, 80, 80))
        help_rect = help_text.get_rect(center=(x, self.surface.get_height() - 40))
        self.surface.blit(help_text, help_rect)


class GenerationProgressOverlay:
    """
    Renders temple generation progress over dark background.

    Replaces menu during generation, shows progress bar and parallel task statuses.
    """

    def __init__(self, surface):
        """
        Initialize progress overlay.

        Args:
            surface: Pygame surface to render on
        """
        self.surface = surface
        self.progress = 0
        self.message = ""
        self.task_statuses = None

    def update_progress(self, percent, message, task_statuses=None):
        """
        Callback for TempleGenerationPipeline.

        Args:
            percent: Progress percentage (0-100)
            message: Status message
            task_statuses: Optional dict of parallel task statuses
        """
        self.progress = percent
        self.message = message
        if task_statuses is not None:
            self.task_statuses = task_statuses

    def draw(self):
        """Render progress bar, main message, and parallel task statuses."""
        # Draw dark background
        self.surface.fill((0, 0, 0))

        # Calculate center position
        center_x = self.surface.get_width() // 2
        center_y = self.surface.get_height() // 2

        # Draw main progress bar (centered)
        bar_width = 600
        bar_height = 40
        bar_x = center_x - bar_width // 2
        bar_y = center_y - 100

        # Background bar
        pygame.draw.rect(self.surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))

        # Fill bar
        fill_width = int(bar_width * self.progress / 100)
        pygame.draw.rect(self.surface, (100, 100, 100), (bar_x, bar_y, fill_width, bar_height))

        # Draw percentage text on bar
        font = pygame.font.Font(None, 24)
        percent_text = font.render(f"{int(self.progress)}%", True, (200, 200, 200))
        percent_x = center_x - percent_text.get_width() // 2
        percent_y = bar_y + (bar_height - percent_text.get_height()) // 2
        self.surface.blit(percent_text, (percent_x, percent_y))

        # Draw main message above bar
        if self.message:
            message_text = font.render(self.message, True, (180, 180, 180))
            message_x = center_x - message_text.get_width() // 2
            message_y = bar_y - 40
            self.surface.blit(message_text, (message_x, message_y))

        # Draw parallel task statuses below bar
        if self.task_statuses:
            task_y = bar_y + bar_height + 40
            task_spacing = 30

            task_font = pygame.font.Font(None, 20)

            # Task display names
            task_names = {
                "map": "Room Layout",
                "music": "Ambient Music",
                "title_svg": "Title Screen",
                "gameover_svg": "Game Over Screen"
            }

            for task_id, task_info in self.task_statuses.items():
                display_name = task_names.get(task_id, task_id)
                status_msg = task_info["message"]

                # Choose color based on status
                if task_info["complete"]:
                    color = (100, 200, 100)  # Green
                elif task_info["error"]:
                    color = (200, 100, 100)  # Red
                elif "Generating" in status_msg or "Composing" in status_msg:
                    color = (200, 200, 100)  # Yellow (in progress)
                else:
                    color = (120, 120, 120)  # Gray (waiting)

                # Render task status
                task_text = task_font.render(f"{display_name}: {status_msg}", True, color)
                task_x = center_x - task_text.get_width() // 2
                self.surface.blit(task_text, (task_x, task_y))

                task_y += task_spacing


class ProviderSelector:
    """
    Simple selector for choosing LLM provider before generation.

    Shows available providers (those with API keys configured).
    """

    PROVIDERS = {
        "anthropic": {"name": "Anthropic (Claude)", "prefix": "sk-ant-"},
        "openai": {"name": "OpenAI (GPT)", "prefix": "sk-"},
    }

    def __init__(self, surface, on_provider_selected, on_back, on_add_key):
        """
        Initialize provider selector.

        Args:
            surface: Pygame surface
            on_provider_selected: Callback(provider_id) when provider chosen
            on_back: Callback() when user goes back
            on_add_key: Callback() when user wants to add a new API key
        """
        self.surface = surface
        self.on_provider_selected = on_provider_selected
        self.on_back = on_back
        self.on_add_key = on_add_key

        # Build options from configured providers
        self.configured = get_configured_providers()
        self.options = []

        # Anthropic first (recommended)
        if "anthropic" in self.configured:
            self.options.append(("anthropic", "Anthropic (Claude) - Recommended"))
        if "openai" in self.configured:
            self.options.append(("openai", "OpenAI (GPT)"))

        # Always show option to add new key
        self.options.append(("add_key", "+ Add API Key"))

        self.current_index = 0
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.text_color = (150, 150, 150)
        self.highlight_color = (200, 200, 200)

    def handle_event(self, event):
        """Handle keyboard events."""
        if event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_UP:
            self.current_index = (self.current_index - 1) % len(self.options)
            return True

        elif event.key == pygame.K_DOWN:
            self.current_index = (self.current_index + 1) % len(self.options)
            return True

        elif event.key == pygame.K_RETURN:
            provider_id, _ = self.options[self.current_index]
            if provider_id == "add_key":
                self.on_add_key()
            else:
                self.on_provider_selected(provider_id)
            return True

        elif event.key == pygame.K_ESCAPE:
            self.on_back()
            return True

        return False

    def draw(self):
        """Draw the provider selector."""
        self.surface.fill((0, 0, 0))

        center_x = self.surface.get_width() // 2
        center_y = self.surface.get_height() // 2

        # Title
        title = self.font.render("Select LLM Provider", True, self.text_color)
        title_rect = title.get_rect(center=(center_x, center_y - 80))
        self.surface.blit(title, title_rect)

        # Options
        y_start = center_y - 20
        for i, (provider_id, display_name) in enumerate(self.options):
            color = self.highlight_color if i == self.current_index else self.text_color

            # Draw selection indicator
            if i == self.current_index:
                indicator = self.font.render(">", True, color)
                self.surface.blit(indicator, (center_x - 150, y_start + i * 30))

            text = self.font.render(display_name, True, color)
            text_rect = text.get_rect(midleft=(center_x - 130, y_start + i * 30 + 8))
            self.surface.blit(text, text_rect)

        # Help text
        help_text = self.small_font.render("UP/DOWN to select  |  ENTER to confirm  |  ESC to cancel", True, (80, 80, 80))
        help_rect = help_text.get_rect(center=(center_x, center_y + 100))
        self.surface.blit(help_text, help_rect)


class APIKeyInputMenu:
    """
    Text input menu for API key configuration.

    Supports both OpenAI and Anthropic keys.
    """

    PROVIDERS = {
        "anthropic": {"name": "Anthropic", "prefix": "sk-ant-", "placeholder": "sk-ant-..."},
        "openai": {"name": "OpenAI", "prefix": "sk-", "placeholder": "sk-..."},
    }

    def __init__(self, surface, on_key_saved, on_back, provider: str = None):
        """
        Initialize API key input menu.

        Args:
            surface: Pygame surface
            on_key_saved: Callback(provider) when key is saved successfully
            on_back: Callback() when user cancels
            provider: Pre-selected provider, or None to show provider selection first
        """
        self.surface = surface
        self.on_key_saved = on_key_saved
        self.on_back = on_back
        self.provider = provider
        self.input_text = ""
        self.error_message = ""
        self.cursor_timer = 0

        # If no provider specified, default to anthropic
        if self.provider is None:
            self.provider = "anthropic"
            self.selecting_provider = True
            self.provider_index = 0
            self.provider_options = list(self.PROVIDERS.keys())
        else:
            self.selecting_provider = False

        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.text_color = (150, 150, 150)
        self.error_color = (200, 100, 100)
        self.input_color = (200, 200, 200)
        self.highlight_color = (200, 200, 200)

        # Enable text input mode
        pygame.key.start_text_input()

        # Initialize clipboard support
        if not pygame.scrap.get_init():
            pygame.scrap.init()

    def handle_event(self, event):
        """Handle keyboard and text input events."""
        if self.selecting_provider:
            return self._handle_provider_selection(event)
        else:
            return self._handle_key_input(event)

    def _handle_provider_selection(self, event):
        """Handle provider selection."""
        if event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
            self.provider_index = (self.provider_index + 1) % len(self.provider_options)
            self.provider = self.provider_options[self.provider_index]
            return True

        elif event.key == pygame.K_RETURN or event.key == pygame.K_DOWN:
            self.selecting_provider = False
            return True

        elif event.key == pygame.K_ESCAPE:
            pygame.key.stop_text_input()
            self.on_back()
            return True

        return False

    def _handle_key_input(self, event):
        """Handle API key text input."""
        if event.type == pygame.TEXTINPUT:
            self.input_text += event.text
            self.error_message = ""
            return True

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                self.error_message = ""
                return True

            elif event.key == pygame.K_UP:
                # Go back to provider selection
                self.selecting_provider = True
                return True

            elif event.key == pygame.K_RETURN:
                if self._validate_and_save():
                    pygame.key.stop_text_input()
                    self.on_key_saved(self.provider)
                return True

            elif event.key == pygame.K_ESCAPE:
                pygame.key.stop_text_input()
                self.on_back()
                return True

            elif event.key == pygame.K_v and (event.mod & pygame.KMOD_META or event.mod & pygame.KMOD_CTRL):
                # Handle paste
                self._paste_from_clipboard()
                return True

        return False

    def _paste_from_clipboard(self):
        """Paste text from system clipboard."""
        try:
            # Try pygame.scrap first
            clipboard = None

            # Try different scrap types (macOS uses different types)
            for scrap_type in [pygame.SCRAP_TEXT, "text/plain;charset=utf-8", "text/plain"]:
                try:
                    clipboard = pygame.scrap.get(scrap_type)
                    if clipboard:
                        break
                except:
                    continue

            if clipboard:
                if isinstance(clipboard, bytes):
                    clipboard = clipboard.decode('utf-8', errors='ignore').rstrip('\x00')
                self.input_text += clipboard.strip()
                self.error_message = ""
                return

            # Fallback: use subprocess to call pbpaste on macOS
            import sys
            if sys.platform == 'darwin':
                import subprocess
                result = subprocess.run(['pbpaste'], capture_output=True, text=True)
                if result.returncode == 0 and result.stdout:
                    self.input_text += result.stdout.strip()
                    self.error_message = ""
        except Exception:
            pass

    def _validate_and_save(self) -> bool:
        """Validate the API key and save if valid."""
        key = self.input_text.strip()
        provider_config = self.PROVIDERS[self.provider]

        if not key:
            self.error_message = "Please enter an API key"
            return False

        expected_prefix = provider_config["prefix"]
        if not key.startswith(expected_prefix):
            self.error_message = f"Key should start with {expected_prefix}"
            return False

        if len(key) < 20:
            self.error_message = "Key seems too short"
            return False

        # Save the key
        set_api_key(key, self.provider)
        return True

    def _mask_key(self, key: str) -> str:
        """Mask the API key for display (truncated to fit)."""
        if len(key) <= 10:
            return "*" * len(key)
        # Show prefix + asterisks + last 4 chars, max ~40 chars total
        prefix = key[:7]
        suffix = key[-4:]
        # Fixed number of asterisks to keep display compact
        return prefix + "****" + suffix

    def draw(self):
        """Draw the API key input screen."""
        self.surface.fill((0, 0, 0))

        center_x = self.surface.get_width() // 2
        center_y = self.surface.get_height() // 2

        provider_config = self.PROVIDERS[self.provider]

        # Title
        title = self.font.render("Configure API Key", True, self.text_color)
        title_rect = title.get_rect(center=(center_x, center_y - 100))
        self.surface.blit(title, title_rect)

        # Provider selection
        provider_y = center_y - 60
        provider_label = self.small_font.render("Provider:", True, (100, 100, 100))
        self.surface.blit(provider_label, (center_x - 150, provider_y))

        for i, p in enumerate(self.provider_options if hasattr(self, 'provider_options') else [self.provider]):
            p_config = self.PROVIDERS[p]
            is_selected = (p == self.provider)
            color = self.highlight_color if is_selected else self.text_color

            if is_selected and self.selecting_provider:
                # Draw selection arrows
                left_arrow = self.font.render("<", True, (100, 100, 100))
                self.surface.blit(left_arrow, (center_x - 60, provider_y - 3))
                right_arrow = self.font.render(">", True, (100, 100, 100))
                self.surface.blit(right_arrow, (center_x + 80, provider_y - 3))

            if is_selected:
                provider_text = self.font.render(p_config["name"], True, color)
                provider_rect = provider_text.get_rect(center=(center_x + 20, provider_y + 8))
                self.surface.blit(provider_text, provider_rect)

        # Input field
        field_y = center_y
        field_width = 400
        field_height = 30
        field_x = center_x - field_width // 2

        # Field label
        key_label = self.small_font.render("API Key:", True, (100, 100, 100))
        self.surface.blit(key_label, (field_x, field_y - 20))

        # Field background
        border_color = self.highlight_color if not self.selecting_provider else (60, 60, 60)
        pygame.draw.rect(self.surface, (30, 30, 30), (field_x, field_y, field_width, field_height))
        pygame.draw.rect(self.surface, border_color, (field_x, field_y, field_width, field_height), 1)

        # Masked input text
        if self.input_text:
            display_text = self._mask_key(self.input_text)
        else:
            display_text = provider_config["placeholder"]

        text_surface = self.font.render(display_text, True, self.input_color if self.input_text else (80, 80, 80))
        text_rect = text_surface.get_rect(midleft=(field_x + 10, field_y + field_height // 2))

        # Clip text to field bounds
        old_clip = self.surface.get_clip()
        self.surface.set_clip((field_x + 5, field_y, field_width - 10, field_height))
        self.surface.blit(text_surface, text_rect)
        self.surface.set_clip(old_clip)

        # Blinking cursor (inside field bounds)
        if not self.selecting_provider:
            self.cursor_timer = (self.cursor_timer + 1) % 60
            if self.cursor_timer < 30:
                cursor_x = min(text_rect.right + 2, field_x + field_width - 10) if self.input_text else field_x + 10
                pygame.draw.line(self.surface, self.input_color, (cursor_x, field_y + 5), (cursor_x, field_y + field_height - 5))

        # Error message
        if self.error_message:
            error_text = self.small_font.render(self.error_message, True, self.error_color)
            error_rect = error_text.get_rect(center=(center_x, field_y + 50))
            self.surface.blit(error_text, error_rect)

        # Help text
        if self.selecting_provider:
            help_msg = "LEFT/RIGHT to change provider  |  ENTER/DOWN to continue  |  ESC to cancel"
        else:
            help_msg = "ENTER to save  |  UP to change provider  |  ESC to cancel  |  Cmd/Ctrl+V to paste"
        help_text = self.small_font.render(help_msg, True, (80, 80, 80))
        help_rect = help_text.get_rect(center=(center_x, center_y + 100))
        self.surface.blit(help_text, help_rect)
