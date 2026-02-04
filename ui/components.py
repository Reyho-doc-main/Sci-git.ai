import pygame
from settings import UITheme

class Button:
    def __init__(self, x, y, w, h, text, color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.is_hovered = False

    def draw(self, surface, font):
        draw_color = self.color if not self.is_hovered else (min(self.color[0]+40, 255), min(self.color[1]+40, 255), min(self.color[2]+40, 255))
        pygame.draw.rect(surface, UITheme.PANEL_GREY, self.rect)
        pygame.draw.rect(surface, draw_color, self.rect, 2)
        
        txt_surf = font.render(self.text, True, UITheme.TEXT_OFF_WHITE)
        surface.blit(txt_surf, (self.rect.x + (self.rect.w - txt_surf.get_width())//2, self.rect.y + (self.rect.h - txt_surf.get_height())//2))

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

def draw_loading_overlay(surface, font):
    """Draws a semi-transparent 'Processing' screen."""
    overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
    overlay.fill((10, 10, 12, 200)) # Dark transparent
    
    # Pulsing text logic could go here, but let's keep it simple
    msg = font.render(">> EXECUTING_ANALYSIS_PROTOCOL...", True, UITheme.ACCENT_ORANGE)
    surface.blit(overlay, (0,0))
    surface.blit(msg, (1280//2 - msg.get_width()//2, 720//2))