from pydantic import BaseModel, Field, computed_field
import pygame

class GameConfig(BaseModel):
    """Clean, validated game configuration"""
    display_width: int = Field(default=1000, description="Screen width in pixels")
    display_height: int = Field(default=1000, description="Screen height in pixels")
    player_size: int = Field(default=10, description="Player sprite size")

    # Non-serialized pygame objects
    surface: pygame.Surface | None = Field(default=None, exclude=True, repr=False)
    vec: type | None = Field(default=None, exclude=True, repr=False)

    model_config = {"arbitrary_types_allowed": True}

    def model_post_init(self, __context):
        """Initialize pygame objects after model validation"""
        self.surface = pygame.display.set_mode((self.display_width, self.display_height))
        self.vec = pygame.math.Vector2

    @computed_field
    @property
    def center(self) -> tuple[int, int]:
        """Center point of the screen"""
        return self.display_width // 2, self.display_height // 2

    @computed_field
    @property
    def size(self) -> tuple[int, int]:
        """Screen dimensions as tuple"""
        return self.display_width, self.display_height