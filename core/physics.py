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
            if prev_bottom <= wall.rect.top and curr_bottom > wall.rect.top:
                self.y = wall.rect.top - radius
                return
            if prev_top >= wall.rect.bottom and curr_top < wall.rect.bottom:
                self.y = wall.rect.bottom + radius
                return
            if self.rect.colliderect(wall.rect):
                self.resolve_embedded_vertical_wall_collision(wall, previous_y)
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
            if prev_right <= wall.rect.left and curr_right > wall.rect.left:
                self.x = wall.rect.left - radius
                return
            if prev_left >= wall.rect.right and curr_left < wall.rect.right:
                self.x = wall.rect.right + radius
                return
            if self.rect.colliderect(wall.rect):
                self.resolve_embedded_horizontal_wall_collision(wall, previous_x)
                return

    def resolve_embedded_vertical_wall_collision(self, wall, previous_y):
        radius = getattr(self, "radius", 0)
        curr_top = self.y - radius
        curr_bottom = self.y + radius
        moving_down = self.y >= previous_y
        was_above_or_entering_top = previous_y <= wall.rect.centery or self.y <= wall.rect.centery
        was_below_or_entering_bottom = previous_y >= wall.rect.centery or self.y >= wall.rect.centery

        if moving_down and was_above_or_entering_top:
            self.y = wall.rect.top - radius
            return
        if not moving_down and was_below_or_entering_bottom:
            self.y = wall.rect.bottom + radius
            return

        push_up = curr_bottom - wall.rect.top
        push_down = wall.rect.bottom - curr_top
        if push_up <= push_down:
            self.y = wall.rect.top - radius
        else:
            self.y = wall.rect.bottom + radius

    def resolve_embedded_horizontal_wall_collision(self, wall, previous_x):
        radius = getattr(self, "radius", 0)
        curr_left = self.x - radius
        curr_right = self.x + radius
        moving_right = self.x >= previous_x
        was_left_or_entering_left = previous_x <= wall.rect.centerx or self.x <= wall.rect.centerx
        was_right_or_entering_right = previous_x >= wall.rect.centerx or self.x >= wall.rect.centerx

        if moving_right and was_left_or_entering_left:
            self.x = wall.rect.left - radius
            return
        if not moving_right and was_right_or_entering_right:
            self.x = wall.rect.right + radius
            return

        push_left = curr_right - wall.rect.left
        push_right = wall.rect.right - curr_left
        if push_left <= push_right:
            self.x = wall.rect.left - radius
        else:
            self.x = wall.rect.right + radius
