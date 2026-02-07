import pygame
from settings import UITheme
from state_manager import state

class VersionTree:
    def __init__(self):
        self.nodes = []  
        self.connections = []
        self.node_radius = 18
        self.camera_offset = pygame.Vector2(60, 300)
        self.zoom_level = 1.0
        self.is_panning = False
        self.font = pygame.font.SysFont("Consolas", 12, bold=True)
        self.search_filter = "" # NEW: Search text

    def handle_zoom(self, direction):
        if direction == "in": self.zoom_level = min(2.0, self.zoom_level + 0.1)
        else: self.zoom_level = max(0.4, self.zoom_level - 0.1)

    def update_tree(self, db_rows):
        self.nodes = []
        self.connections = []
        pos_map = {}
        branch_slots = {"main": 0}
        next_slot_y = 100 

        for row in db_rows:
            node_id, parent_id, branch, name = row
            
            gen_x = pos_map[parent_id]['gen'] + 1 if (parent_id and parent_id in pos_map) else 0
            
            if branch not in branch_slots:
                branch_slots[branch] = len(branch_slots) * next_slot_y
            
            pos = pygame.Vector2(gen_x * 160, branch_slots[branch])
            pos_map[node_id] = {'pos': pos, 'gen': gen_x}
            
            self.nodes.append({"id": node_id, "pos": pos, "parent_id": parent_id, "name": name, "branch": branch})
            
            if parent_id in pos_map:
                self.connections.append((pos_map[parent_id]['pos'], pos))

        if self.nodes:
            max_x = max(n['pos'].x for n in self.nodes)
            self.camera_offset.x = 600 - (max_x * self.zoom_level)

    def draw(self, surface, mouse_pos):
        surface.fill((0, 0, 0, 0))

        # Connections
        for start, end in self.connections:
            s = (start * self.zoom_level) + self.camera_offset
            e = (end * self.zoom_level) + self.camera_offset
            mid_x = int(s.x + (e.x - s.x) // 2)
            pts = [(int(s.x), int(s.y)), (mid_x, int(s.y)), (mid_x, int(e.y)), (int(e.x), int(e.y))]
            pygame.draw.lines(surface, (70, 70, 80), False, pts, 2)

        # Nodes
        current_radius = int(self.node_radius * self.zoom_level)
        for node in self.nodes:
            draw_pos = (node["pos"] * self.zoom_level) + self.camera_offset
            ix, iy = int(draw_pos.x), int(draw_pos.y)
            if not (-100 < ix < 900): continue

            # Search Match Check
            is_match = self.search_filter.lower() in node["name"].lower() if self.search_filter else False

            # Colors
            base_color = UITheme.NODE_MAIN if node["branch"] == "main" else UITheme.NODE_BRANCH
            
            # Selection Highlight
            if node["id"] in state.selected_ids:
                idx = state.selected_ids.index(node["id"])
                hl_color = UITheme.ACCENT_ORANGE if idx == 0 else (0, 255, 255)
                pygame.draw.circle(surface, hl_color, (ix, iy), current_radius + 4, 3)
            
            # Search Highlight (Yellow Glow)
            if is_match and self.search_filter:
                pygame.draw.circle(surface, (255, 255, 0), (ix, iy), current_radius + 8, 2)

            pygame.draw.circle(surface, UITheme.PANEL_GREY, (ix, iy), current_radius)
            pygame.draw.circle(surface, base_color, (ix, iy), current_radius, 2)
            
            if self.zoom_level > 0.6:
                id_txt = self.font.render(str(node["id"]), True, UITheme.TEXT_OFF_WHITE)
                surface.blit(id_txt, id_txt.get_rect(center=(ix, iy)))
                name_txt = self.font.render(node["name"][:10], True, (255, 255, 0) if is_match else UITheme.TEXT_DIM)
                surface.blit(name_txt, (ix - 30, iy + current_radius + 5))

    def handle_click(self, mouse_pos, panel_rect):
        local_mouse = pygame.Vector2(mouse_pos[0] - panel_rect[0], mouse_pos[1] - panel_rect[1])
        current_radius = self.node_radius * self.zoom_level
        
        clicked_node = None
        for node in self.nodes:
            draw_pos = (node["pos"] * self.zoom_level) + self.camera_offset
            if draw_pos.distance_to(local_mouse) < current_radius + 5:
                clicked_node = node["id"]
                break
        
        if clicked_node:
            keys = pygame.key.get_pressed()
            is_ctrl = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
            if is_ctrl:
                if clicked_node in state.selected_ids: state.selected_ids.remove(clicked_node)
                elif len(state.selected_ids) < 2: state.selected_ids.append(clicked_node)
                else: state.selected_ids = [clicked_node]
            else:
                state.selected_ids = [clicked_node]
            return state.selected_ids
        return None