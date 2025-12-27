import cairosvg
from io import BytesIO
import pygame


class SVGLoader:
    """Handles loading and caching SVG files as pygame surfaces"""

    def __init__(self):
        self.cache = {}

    def load_svg(self, svg_path, width=None, height=None):
        """
        Load an SVG file and convert it to a pygame surface.

        Args:
            svg_path: Path to the SVG file
            width: Target width (optional, maintains aspect ratio if only width given)
            height: Target height (optional, maintains aspect ratio if only height given)

        Returns:
            pygame.Surface or None if file doesn't exist
        """
        # Check cache first
        cache_key = f"{svg_path}_{width}_{height}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Read SVG file
            with open(svg_path, 'r') as f:
                svg_data = f.read()

            # Convert to PNG bytes
            png_data = cairosvg.svg2png(
                bytestring=svg_data.encode('utf-8'),
                output_width=width,
                output_height=height
            )

            # Load as pygame surface
            surface = pygame.image.load(BytesIO(png_data))

            # Cache it
            self.cache[cache_key] = surface

            return surface

        except FileNotFoundError:
            print(f"Warning: SVG file not found: {svg_path}")
            return None
        except Exception as e:
            print(f"Error loading SVG {svg_path}: {e}")
            return None

    def clear_cache(self):
        """Clear the surface cache"""
        self.cache.clear()


def draw_centered_surface(screen, surface, y_offset=0):
    """
    Draw a surface centered on the screen.

    Args:
        screen: pygame display surface
        surface: surface to draw
        y_offset: vertical offset from center (positive = down)
    """
    if surface:
        screen_rect = screen.get_rect()
        surface_rect = surface.get_rect()
        x = (screen_rect.width - surface_rect.width) // 2
        y = (screen_rect.height - surface_rect.height) // 2 + y_offset
        screen.blit(surface, (x, y))


def render_text_fallback(screen, text, font_size=48):
    """Fallback text rendering if SVG fails to load"""
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, (255, 255, 255))
    draw_centered_surface(screen, text_surface)