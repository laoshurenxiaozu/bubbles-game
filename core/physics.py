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
        radius = getattr(self, "radius", 0)
        prev_top = previous_y - radius
        prev_bottom = previous_y + radius
        curr_top = self.y - radius
        curr_bottom = self.y + radius
        for wall in walls:
            if self.x + radius < wall.rect.left:
                continue
            if self.x - radius > wall.rect.right:
                continue
            if not self.rect.colliderect(wall.rect):
                continue
            if prev_bottom <= wall.rect.top and curr_bottom > wall.rect.top:
                self.y = wall.rect.top - radius
                return
            if prev_top >= wall.rect.bottom and curr_top < wall.rect.bottom:
                self.y = wall.rect.bottom + radius
                return

    def resolve_horizontal_wall_collisions(self, walls, previous_x):
        if not hasattr(self, "rect"):
            return
        radius = getattr(self, "radius", 0)
        prev_left = previous_x - radius
        prev_right = previous_x + radius
        curr_left = self.x - radius
        curr_right = self.x + radius
        for wall in walls:
            if self.y + radius < wall.rect.top:
                continue
            if self.y - radius > wall.rect.bottom:
                continue
            if not self.rect.colliderect(wall.rect):
                continue
            if prev_right <= wall.rect.left and curr_right > wall.rect.left:
                self.x = wall.rect.left - radius
                return
            if prev_left >= wall.rect.right and curr_left < wall.rect.right:
                self.x = wall.rect.right + radius
                return
