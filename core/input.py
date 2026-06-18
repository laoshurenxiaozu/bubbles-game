import pygame


SDL_SCANCODE_A = 4
SDL_SCANCODE_D = 7
SDL_SCANCODE_M = 16
SDL_SCANCODE_N = 17
SDL_SCANCODE_Q = 20
SDL_SCANCODE_R = 21
SDL_SCANCODE_S = 22
SDL_SCANCODE_W = 26
SDL_SCANCODE_Y = 28


def key_value(key_or_event):
    return getattr(key_or_event, "key", key_or_event)


def key_matches(key_or_event, keys=(), scancodes=()):
    return key_value(key_or_event) in keys or getattr(key_or_event, "scancode", None) in scancodes


def is_left(key_or_event):
    return key_matches(key_or_event, (pygame.K_a, pygame.K_LEFT), (SDL_SCANCODE_A,))


def is_right(key_or_event):
    return key_matches(key_or_event, (pygame.K_d, pygame.K_RIGHT), (SDL_SCANCODE_D,))


def is_up(key_or_event):
    return key_matches(key_or_event, (pygame.K_w, pygame.K_UP), (SDL_SCANCODE_W,))


def is_down(key_or_event):
    return key_matches(key_or_event, (pygame.K_s, pygame.K_DOWN), (SDL_SCANCODE_S,))


def is_save(key_or_event):
    return key_matches(key_or_event, (pygame.K_s,), (SDL_SCANCODE_S,))


def is_confirm(key_or_event):
    return key_matches(key_or_event, (pygame.K_RETURN, pygame.K_SPACE))


def is_cancel(key_or_event):
    return key_matches(key_or_event, (pygame.K_ESCAPE, pygame.K_BACKSPACE))


def is_restart(key_or_event):
    return key_matches(key_or_event, (pygame.K_r,), (SDL_SCANCODE_R,))


def is_map(key_or_event):
    return key_matches(key_or_event, (pygame.K_m,), (SDL_SCANCODE_M,))


def is_yes(key_or_event):
    return key_matches(key_or_event, (pygame.K_y,), (SDL_SCANCODE_Y,))


def is_no(key_or_event):
    return key_matches(key_or_event, (pygame.K_n,), (SDL_SCANCODE_N,))


def is_quit(key_or_event):
    return key_matches(key_or_event, (pygame.K_q,), (SDL_SCANCODE_Q,))
