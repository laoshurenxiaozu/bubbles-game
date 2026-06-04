from config import FLOAT_SPEED, SCREEN_HEIGHT


class FloatBody:
    def __init__(self, x, y, bubble_count=1, seed_count=0):
        self.x = x
        self.y = y
        self.bubble_count = bubble_count
        self.seed_count = seed_count

    @property
    def net_value(self):
        return self.bubble_count - self.seed_count

    @property
    def vertical_state(self):
        if self.net_value > 0:
            return "floating"
        if self.net_value < 0:
            return "sinking"
        return "hovering"

    def update_vertical_motion(self, dt):
        old_y = self.y
        if self.net_value > 0:
            self.y -= FLOAT_SPEED * dt
        elif self.net_value < 0:
            self.y += FLOAT_SPEED * dt
        self.clamp_vertical()
        return old_y

    def clamp_vertical(self):
        radius = getattr(self, "radius", 0)
        if self.y < radius:
            self.y = radius
        if self.y > SCREEN_HEIGHT - radius:
            self.y = SCREEN_HEIGHT - radius

    def resolve_vertical_wall_collisions(self, walls, previous_y):
        if not hasattr(self, "rect"):
            return
        for wall in walls:
            if hasattr(wall, "blocks_vertical_motion") and not wall.blocks_vertical_motion():
                continue
            if self.rect.colliderect(wall.rect):
                self.y = previous_y
                self.clamp_vertical()
                return

    def resolve_horizontal_wall_collisions(self, walls, previous_x):
        if not hasattr(self, "rect"):
            return
        for wall in walls:
            if hasattr(wall, "blocks_horizontal_motion") and not wall.blocks_horizontal_motion():
                continue
            if self.rect.colliderect(wall.rect):
                self.x = previous_x
                return
