import math

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH


class RestartHintOverlay:
    def __init__(self, font):
        self.font = font

    def draw(
        self,
        screen,
        elapsed,
        duration,
        text,
        world_time,
        fading=False,
        fade_time=0.0,
        fade_duration=0.35,
    ):
        t = min(elapsed, duration)
        self.draw_background(screen, t)
        self.draw_icon(screen, t, world_time)
        self.draw_text(screen, text)

        if fading:
            alpha = int(255 * min(1.0, fade_time / max(0.01, fade_duration)))
            fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fade.fill((0, 16, 34, alpha))
            screen.blit(fade, (0, 0))

    def draw_background(self, screen, t):
        light = (116, 219, 236)
        deep = (24, 35, 92)
        bg_t = self.background_t(t)
        top = self.mix_color(light, deep, bg_t)
        bottom_light = (70, 158, 211)
        bottom_deep = (10, 22, 58)
        bottom = self.mix_color(bottom_light, bottom_deep, bg_t)
        for y in range(SCREEN_HEIGHT):
            vertical = y / SCREEN_HEIGHT
            color = self.mix_color(top, bottom, vertical)
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))

    def background_t(self, t):
        if t < 1.25:
            return self.smoothstep(t / 1.25)
        if t > 6.35:
            return 1.0 - self.smoothstep((t - 6.35) / 1.0)
        return 1.0

    def draw_icon(self, screen, t, world_time):
        icon_offset_x = 23
        center = (SCREEN_WIDTH / 2 + icon_offset_x, SCREEN_HEIGHT / 2 - 15)
        root = (center[0], center[1] + 38)
        leaf_root = (root[0] + 28, root[1])
        bubble_origin = self.leaf_stem_origin(leaf_root)
        leaf_path = self.leaf_path(leaf_root)
        motion = self.motion(root, 39, bubble_origin)

        if t < 1.7:
            progress = 1.0 - self.smoothstep(t / 1.7)
            color = self.mix_color(
                (88, 230, 142),
                (177, 154, 78),
                self.smoothstep(t / 1.45),
            )
            main_line_only_progress = 0.46
            if progress > main_line_only_progress:
                points = self.partial_polyline(leaf_path, progress)
            else:
                main_path = self.leaf_main_path(leaf_root)
                points = self.partial_polyline(
                    main_path,
                    progress / main_line_only_progress,
                )
            self.draw_glow_polyline(screen, points, color, 4, 74)

        if motion["rise_start"] <= t <= motion["landing_t"] + 0.55:
            self.draw_bubble(screen, t, root, bubble_origin)

        if motion["seed_start"] <= t <= motion["seed_ground_t"] + 0.12:
            self.draw_seed(screen, t, root, bubble_origin, world_time)

        if t >= motion["landing_t"]:
            self.draw_ground(screen, t, root, bubble_origin, leaf_root)

        if t >= motion["leaf_start"]:
            progress = max(
                0.025,
                self.smoothstep((t - motion["leaf_start"]) / 1.25),
            )
            color = self.mix_color((177, 154, 78), (91, 238, 146), progress)
            self.draw_glow_polyline(
                screen,
                self.partial_polyline(leaf_path, progress),
                color,
                4,
                82,
            )

    def draw_bubble(self, screen, t, root, bubble_origin=None):
        radius = 39
        center = self.bubble_center(t, root, radius, bubble_origin)
        motion = self.motion(root, radius, bubble_origin)
        color = (186, 246, 255)
        alpha = 215
        if t > motion["landing_t"] + 0.3:
            alpha = int(
                alpha
                * (
                    1.0
                    - self.smoothstep(
                        (t - (motion["landing_t"] + 0.3)) / 0.16
                    )
                )
            )
        if alpha <= 0:
            return

        erase = self.smoothstep((t - motion["landing_t"]) / 0.34)
        bubble_progress = 1.0
        if t < motion["draw_end"]:
            bubble_progress = self.smoothstep(
                (t - motion["rise_start"]) / motion["draw_duration"]
            )
            points = self.circle_points(
                center,
                radius,
                progress=bubble_progress,
                counterclockwise=True,
                start_angle=math.pi,
            )
        elif erase > 0:
            points = self.erased_bubble_points(center, radius, erase)
        else:
            swallow = self.smoothstep(
                (t - (motion["capture_t"] - 0.18)) / 0.52
            ) * (
                1.0
                - self.smoothstep(
                    (t - (motion["capture_t"] + 0.36)) / 0.42
                )
            )
            points = self.bubble_points(center, radius, swallow)

        if len(points) < 2:
            return

        self.draw_glow_polyline(
            screen,
            points,
            color,
            4,
            int(72 * alpha / 215),
            alpha=alpha,
        )
        highlight_alpha = int(min(alpha, 150) * bubble_progress)
        highlight_full = self.circle_points(
            (center[0] - 3, center[1] - 4),
            radius * 0.68,
            progress=0.18,
        )
        highlight_count = max(2, int(len(highlight_full) * bubble_progress))
        highlight = highlight_full[-highlight_count:]
        if len(highlight) >= 2 and erase <= 0 and highlight_alpha > 20:
            self.draw_glow_polyline(
                screen,
                highlight,
                (233, 255, 255),
                2,
                28,
                alpha=highlight_alpha,
            )

    def draw_seed(self, screen, t, root, bubble_origin=None, world_time=0.0):
        radius = 39
        motion = self.motion(root, radius, bubble_origin)
        bubble_center = self.bubble_center(t, root, radius, bubble_origin)
        seed_x = bubble_center[0] + 5
        appear = self.smoothstep((t - motion["seed_start"]) / 0.28)

        entry = 0.0
        if t < motion["capture_t"]:
            y = motion["seed_start_y"] + motion["seed_speed"] * (
                t - motion["seed_start"]
            )
        elif t < motion["landing_t"]:
            capture_span = max(
                0.01,
                motion["seed_settle_t"] - motion["capture_t"],
            )
            capture_entry = self.smoothstep(
                (t - motion["capture_t"]) / capture_span
            )
            outside_y = bubble_center[1] + motion["seed_capture_offset"]
            inside_y = bubble_center[1] + motion["carried_seed_offset"]
            y = self.lerp(outside_y, inside_y, capture_entry)
        else:
            entry_span = max(
                0.01,
                motion["seed_ground_t"] - motion["landing_t"],
            )
            entry = max(
                0.0,
                min(1.0, (t - motion["landing_t"]) / entry_span),
            )
            y = self.lerp(
                motion["landing_y"] + motion["carried_seed_offset"],
                motion["seed_ground_y"],
                entry,
            )

        fade = 1.0 - self.smoothstep(
            (t - (motion["seed_ground_t"] - 0.22)) / 0.22
        )
        alpha = int(230 * min(appear, max(0.0, fade)))
        if alpha <= 0:
            return

        pulse = 0.72 + 0.28 * math.sin(world_time * 8.0)
        seed_width = max(4, int(13 * (1.0 - 0.42 * entry)))
        seed_height = max(4, int(19 * (1.0 - 0.68 * entry)))
        glow = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.circle(
            glow,
            (
                95,
                255,
                149,
                int(58 * pulse * alpha / 230 * (1.0 - 0.35 * entry)),
            ),
            (35, 35),
            24,
        )
        screen.blit(glow, (seed_x - 35, y - 35))
        seed_rect = pygame.Rect(0, 0, seed_width, seed_height)
        seed_rect.center = (seed_x, y)
        pygame.draw.ellipse(screen, (110, 255, 156, alpha), seed_rect, 2)
        pygame.draw.arc(
            screen,
            (217, 255, 220, alpha),
            seed_rect.inflate(-4, -4),
            math.radians(110),
            math.radians(286),
            2,
        )

    def draw_ground(
        self,
        screen,
        t,
        root,
        bubble_origin=None,
        leaf_root=None,
    ):
        ground_y = root[1] + 50
        radius = 39
        motion = self.motion(root, radius, bubble_origin)
        cx = self.bubble_center(
            motion["landing_t"],
            root,
            radius,
            bubble_origin,
        )[0]
        leaf_x = (
            self.leaf_stem_origin(leaf_root)[0]
            if leaf_root is not None
            else cx - 40
        )
        line_t = self.smoothstep((t - motion["landing_t"]) / 0.24)
        shrink = 1.0 - self.smoothstep(
            (t - motion["leaf_start"]) / 0.3
        )
        half_width = 60 * line_t * shrink
        color = (205, 239, 219)
        if half_width > 1:
            pygame.draw.line(
                screen,
                color,
                (cx - half_width, ground_y),
                (cx + half_width, ground_y),
                2,
            )

        pulse_t = self.smoothstep(
            (t - (motion["landing_t"] + 0.04)) / 0.24
        )
        if 0 < pulse_t < 1:
            alpha = int(150 * (1.0 - pulse_t))
            gap = 4 + 5 * pulse_t
            span = 10 + 38 * pulse_t
            pulse = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT),
                pygame.SRCALPHA,
            )
            pulse_color = (234, 255, 232, alpha)
            pygame.draw.line(
                pulse,
                pulse_color,
                (cx - gap - span, ground_y),
                (cx - gap, ground_y),
                2,
            )
            pygame.draw.line(
                pulse,
                pulse_color,
                (cx + gap, ground_y),
                (cx + gap + span, ground_y),
                2,
            )
            pygame.draw.circle(
                pulse,
                (234, 255, 232, min(190, alpha + 35)),
                (int(cx), int(ground_y)),
                max(2, int(5 * (1.0 - pulse_t))),
            )
            screen.blit(pulse, (0, 0))

        green_front_t = self.smoothstep(
            (t - motion["green_start"]) / 0.26
        )
        green_tail_t = self.smoothstep(
            (t - (motion["green_start"] + 0.09)) / 0.26
        )
        if green_front_t > 0:
            front_x = self.lerp(cx, leaf_x, green_front_t)
            tail_x = self.lerp(cx, leaf_x, green_tail_t)
            green_alpha = int(
                230
                * (
                    1.0
                    - self.smoothstep(
                        (t - (motion["leaf_start"] + 0.12)) / 0.18
                    )
                )
            )
            if green_alpha > 0 and abs(front_x - tail_x) > 1:
                glow = pygame.Surface(
                    (SCREEN_WIDTH, SCREEN_HEIGHT),
                    pygame.SRCALPHA,
                )
                pygame.draw.line(
                    glow,
                    (95, 255, 149, int(100 * green_alpha / 230)),
                    (tail_x, ground_y),
                    (front_x, ground_y),
                    8,
                )
                pygame.draw.line(
                    glow,
                    (95, 255, 149, int(145 * green_alpha / 230)),
                    (tail_x, ground_y),
                    (front_x, ground_y),
                    4,
                )
                screen.blit(glow, (0, 0))
                pygame.draw.line(
                    screen,
                    (95, 255, 149, green_alpha),
                    (tail_x, ground_y),
                    (front_x, ground_y),
                    3,
                )
                pygame.draw.circle(
                    screen,
                    (165, 255, 184, min(255, green_alpha)),
                    (int(front_x), int(ground_y)),
                    4,
                )

    def draw_text(self, screen, text):
        lines = text.splitlines()
        line_height = self.font.get_linesize()
        start_y = (
            SCREEN_HEIGHT
            - 132
            - (len(lines) - 1) * line_height / 2
        )
        for index, line in enumerate(lines):
            rendered = self.font.render(line, True, (236, 249, 224))
            shadow = self.font.render(line, True, (15, 30, 54))
            center = (
                SCREEN_WIDTH / 2,
                start_y + index * line_height,
            )
            screen.blit(
                shadow,
                shadow.get_rect(center=(center[0] + 2, center[1] + 2)),
            )
            screen.blit(rendered, rendered.get_rect(center=center))

    def leaf_path(self, root):
        root = (float(root[0]), float(root[1]))
        joint = (root[0] - 36, root[1] - 22)
        tip = (root[0] + 108, root[1] + 22)
        stem_end = self.leaf_stem_origin(root)
        points = []
        points.extend(
            self.cubic_points(
                stem_end,
                (root[0] - 88, root[1] + 13),
                (root[0] - 68, root[1] - 21),
                joint,
                70,
            )
        )
        points.extend(
            self.cubic_points(
                joint,
                (root[0] + 18, root[1] - 13),
                (root[0] + 72, root[1] - 1),
                tip,
                88,
            )[1:]
        )
        points.extend(
            self.cubic_points(
                tip,
                (root[0] + 44, root[1] + 56),
                (root[0] - 44, root[1] + 36),
                joint,
                86,
            )[1:]
        )
        points.extend(
            self.cubic_points(
                joint,
                (root[0] - 13, root[1] - 72),
                (root[0] + 72, root[1] - 25),
                tip,
                90,
            )[1:]
        )
        return points

    def leaf_main_path(self, root):
        root = (float(root[0]), float(root[1]))
        joint = (root[0] - 36, root[1] - 22)
        tip = (root[0] + 108, root[1] + 22)
        stem_end = self.leaf_stem_origin(root)
        points = []
        points.extend(
            self.cubic_points(
                stem_end,
                (root[0] - 88, root[1] + 13),
                (root[0] - 68, root[1] - 21),
                joint,
                70,
            )
        )
        points.extend(
            self.cubic_points(
                joint,
                (root[0] + 18, root[1] - 13),
                (root[0] + 72, root[1] - 1),
                tip,
                88,
            )[1:]
        )
        return points

    def leaf_stem_origin(self, root):
        return (float(root[0]) - 90, float(root[1]) + 50)

    def motion(self, root, radius, bubble_origin=None):
        if bubble_origin is None:
            bubble_origin = root
        bubble_speed = 78.0
        seed_speed = 68.0
        rise_start = 1.68
        draw_duration = 0.83
        draw_end = rise_start + draw_duration
        seed_start = draw_end - 0.06
        seed_start_y = root[1] - 176
        start_y = bubble_origin[1]
        landing_y = root[1] + 10
        seed_capture_offset = -radius + 8
        carried_seed_offset = 7
        seed_ground_y = root[1] + 57
        capture_t = (
            start_y
            + seed_capture_offset
            - seed_start_y
            + bubble_speed * rise_start
            + seed_speed * seed_start
        ) / (bubble_speed + seed_speed)
        capture_y = start_y - bubble_speed * (capture_t - rise_start)
        landing_t = capture_t + (landing_y - capture_y) / bubble_speed
        seed_ground_t = (
            landing_t
            + (seed_ground_y - (landing_y + carried_seed_offset))
            / seed_speed
        )
        seed_settle_t = capture_t + 0.46
        green_start = seed_ground_t - 0.08
        leaf_start = green_start + 0.26
        return {
            "bubble_speed": bubble_speed,
            "seed_speed": seed_speed,
            "rise_start": rise_start,
            "draw_duration": draw_duration,
            "draw_end": draw_end,
            "seed_start": seed_start,
            "seed_start_y": seed_start_y,
            "start_y": start_y,
            "capture_t": capture_t,
            "capture_y": capture_y,
            "seed_settle_t": seed_settle_t,
            "landing_t": landing_t,
            "landing_y": landing_y,
            "seed_capture_offset": seed_capture_offset,
            "carried_seed_offset": carried_seed_offset,
            "seed_ground_t": seed_ground_t,
            "seed_ground_y": seed_ground_y,
            "green_start": green_start,
            "leaf_start": leaf_start,
        }

    def bubble_center(self, t, root, radius, bubble_origin=None):
        if bubble_origin is None:
            bubble_origin = root
        bubble_x = bubble_origin[0] + radius
        motion = self.motion(root, radius, bubble_origin)
        if t < motion["capture_t"]:
            rise_t = max(0.0, t - motion["rise_start"])
            return (
                bubble_x,
                motion["start_y"] - motion["bubble_speed"] * rise_t,
            )
        if t < motion["landing_t"]:
            sink_t = t - motion["capture_t"]
            return (
                bubble_x,
                motion["capture_y"] + motion["bubble_speed"] * sink_t,
            )
        return (bubble_x, motion["landing_y"])

    def bubble_points(self, center, radius, swallow):
        points = []
        for index in range(90):
            angle = math.tau * index / 89
            x = center[0] + math.cos(angle) * radius
            y = center[1] + math.sin(angle) * radius
            top_weight = max(
                0.0,
                1.0 - abs(angle - math.tau * 0.75) / 0.38,
            )
            if top_weight > 0:
                y += 9 * swallow * top_weight
                if swallow > 0.72 and top_weight > 0.93:
                    continue
            points.append((x, y))
        return points

    def erased_bubble_points(self, center, radius, erase):
        erase = max(0.0, min(1.0, erase))
        if erase >= 0.99:
            return []
        top_angle = -math.pi / 2
        start = top_angle + erase * math.pi
        end = top_angle + math.tau - erase * math.pi
        count = max(2, int(92 * (1.0 - erase)))
        return [
            (
                center[0]
                + math.cos(self.lerp(start, end, i / (count - 1)))
                * radius,
                center[1]
                + math.sin(self.lerp(start, end, i / (count - 1)))
                * radius,
            )
            for i in range(count)
        ]

    def circle_points(
        self,
        center,
        radius,
        progress=1.0,
        counterclockwise=False,
        start_angle=math.pi / 2,
    ):
        progress = max(0.0, min(1.0, progress))
        count = max(2, int(92 * progress))
        direction = -1 if counterclockwise else 1
        return [
            (
                center[0]
                + math.cos(
                    start_angle
                    + direction
                    * math.tau
                    * progress
                    * i
                    / (count - 1)
                )
                * radius,
                center[1]
                + math.sin(
                    start_angle
                    + direction
                    * math.tau
                    * progress
                    * i
                    / (count - 1)
                )
                * radius,
            )
            for i in range(count)
        ]

    def cubic_points(self, p0, p1, p2, p3, steps):
        points = []
        for index in range(steps + 1):
            t = index / steps
            one = 1.0 - t
            points.append(
                (
                    one * one * one * p0[0]
                    + 3 * one * one * t * p1[0]
                    + 3 * one * t * t * p2[0]
                    + t * t * t * p3[0],
                    one * one * one * p0[1]
                    + 3 * one * one * t * p1[1]
                    + 3 * one * t * t * p2[1]
                    + t * t * t * p3[1],
                )
            )
        return points

    def partial_polyline(self, points, progress):
        if not points or progress <= 0:
            return []
        if progress >= 1:
            return list(points)
        lengths = [0.0]
        total = 0.0
        for start, end in zip(points, points[1:]):
            total += math.dist(start, end)
            lengths.append(total)
        target = total * progress
        partial = [points[0]]
        for index in range(1, len(points)):
            if lengths[index] < target:
                partial.append(points[index])
                continue
            segment_length = lengths[index] - lengths[index - 1]
            local = (
                0.0
                if segment_length <= 0
                else (target - lengths[index - 1]) / segment_length
            )
            partial.append(
                (
                    self.lerp(
                        points[index - 1][0],
                        points[index][0],
                        local,
                    ),
                    self.lerp(
                        points[index - 1][1],
                        points[index][1],
                        local,
                    ),
                )
            )
            break
        return partial

    def draw_glow_polyline(
        self,
        screen,
        points,
        color,
        width,
        glow_alpha,
        alpha=255,
    ):
        if len(points) < 2:
            return
        int_points = [(int(x), int(y)) for x, y in points]
        glow = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        pygame.draw.lines(
            glow,
            (*color, glow_alpha),
            False,
            int_points,
            width + 8,
        )
        pygame.draw.lines(
            glow,
            (*color, min(255, glow_alpha + 20)),
            False,
            int_points,
            width + 4,
        )
        screen.blit(glow, (0, 0))
        pygame.draw.lines(
            screen,
            (*color, alpha),
            False,
            int_points,
            width,
        )
        cap_radius = max(2, width // 2)
        pygame.draw.circle(
            screen,
            (*color, alpha),
            int_points[0],
            cap_radius,
        )
        pygame.draw.circle(
            screen,
            (*color, alpha),
            int_points[-1],
            cap_radius,
        )

    def mix_color(self, first, second, t):
        t = max(0.0, min(1.0, t))
        return tuple(
            int(self.lerp(first[index], second[index], t))
            for index in range(3)
        )

    def smoothstep(self, t):
        t = max(0.0, min(1.0, t))
        return t * t * (3.0 - 2.0 * t)

    def lerp(self, start, end, t):
        return start + (end - start) * max(0.0, min(1.0, t))
