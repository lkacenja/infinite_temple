import pygame
import random


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
        """Draw the selector at bottom center of screen."""
        # Get current option
        title, _ = self.options[self.current_index]

        # Render text
        text_surface = self.font.render(title, True, self.text_color)
        text_rect = text_surface.get_rect()

        # Position at bottom center
        x = self.surface.get_width() // 2
        y = self.surface.get_height() - 40
        text_rect.center = (x, y)

        # Draw arrows if not at edges (or if wrapping)
        arrow_offset = text_rect.width // 2 + 20

        # Left arrow
        left_arrow = self.font.render("<", True, self.arrow_color)
        left_rect = left_arrow.get_rect()
        left_rect.center = (x - arrow_offset, y)
        self.surface.blit(left_arrow, left_rect)

        # Text
        self.surface.blit(text_surface, text_rect)

        # Right arrow
        right_arrow = self.font.render(">", True, self.arrow_color)
        right_rect = right_arrow.get_rect()
        right_rect.center = (x + arrow_offset, y)
        self.surface.blit(right_arrow, right_rect)


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
        """Draw the word picker at bottom center of screen."""
        x = self.surface.get_width() // 2
        y_start = self.surface.get_height() - 100

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
        """Draw the empty state menu at bottom center of screen."""
        x = self.surface.get_width() // 2
        y = self.surface.get_height() - 60

        # Message
        message = self.font.render("No temples exist - Press ENTER to create", True, self.text_color)
        message_rect = message.get_rect()
        message_rect.center = (x, y)
        self.surface.blit(message, message_rect)


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
