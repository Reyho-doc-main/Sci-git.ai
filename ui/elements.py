import pygame
from settings import UITheme

class VersionTree:
    def __init__(self):
        self.nodes = []  
        self.connections = []
        self.node_radius = 18
        # Camera offset: X is how far we've scrolled, Y is the vertical center
        self.camera_offset = pygame.Vector2(60, 300)
        self.selected_node_id = None
        self.font = pygame.font.SysFont("Consolas", 12, bold=True)

    def update_tree(self, db_rows):
        """
        Processes DB rows into a visual map.
        db_rows: (id, parent_id, branch_name, name)
        """
        self.nodes = []
        self.connections = []
        pos_map = {}
        
        # Track branch Y-levels to keep them separated
        branch_slots = {"main": 0}
        next_slot_y = 100 # Distance between branches

        for row in db_rows:
            node_id, parent_id, branch, name = row
            
            # 1. Calculate X (Generation/Time)
            if parent_id is None or parent_id not in pos_map:
                gen_x = 0
            else:
                gen_x = pos_map[parent_id]['gen'] + 1
            
            # 2. Calculate Y (Branching)
            if branch not in branch_slots:
                # Find a new vertical slot for the new branch
                branch_slots[branch] = len(branch_slots) * next_slot_y
            
            y_pos = branch_slots[branch]
            
            pos = pygame.Vector2(gen_x * 160, y_pos)
            pos_map[node_id] = {'pos': pos, 'gen': gen_x}
            
            self.nodes.append({
                "id": node_id,
                "pos": pos,
                "parent_id": parent_id,
                "name": name,
                "branch": branch
            })
            
            # 3. Create Connection (with elbow logic)
            if parent_id in pos_map:
                parent_pos = pos_map[parent_id]['pos']
                self.connections.append((parent_pos, pos))

        # 4. Auto-Scroll: Keep the latest node (highest gen_x) in view
        if self.nodes:
            max_x = max(n['pos'].x for n in self.nodes)
            if max_x > 600: # If tree goes past the middle of the 800px panel
                self.camera_offset.x = 600 - max_x
    def draw(self, surface, mouse_pos):
            # 1. Clear the surface
            surface.fill((0, 0, 0, 0))

            # 2. Draw Connections (Elbow style)
            for start, end in self.connections:
                s = start + self.camera_offset
                e = end + self.camera_offset
                
                color = (70, 70, 80)
                # Use // for integer division to avoid floats
                mid_x = int(s.x + (e.x - s.x) // 2)
                
                # CRITICAL FIX: Pygame-CE needs a list of (int, int) tuples
                pts = [
                    (int(s.x), int(s.y)), 
                    (mid_x, int(s.y)), 
                    (mid_x, int(e.y)), 
                    (int(e.x), int(e.y))
                ]
                pygame.draw.lines(surface, color, False, pts, 2)

            # 3. Draw Nodes
            for node in self.nodes:
                # Calculate position and cast to int
                draw_pos = node["pos"] + self.camera_offset
                ix, iy = int(draw_pos.x), int(draw_pos.y)
                
                if not (-50 < ix < 850): continue

                base_color = UITheme.NODE_MAIN if node["branch"] == "main" else UITheme.NODE_BRANCH
                
                # Fix distance check (mouse_pos is already relative to the panel in main.py)
                dist = pygame.Vector2(ix, iy).distance_to(mouse_pos)
                if node["id"] == self.selected_node_id or dist < self.node_radius:
                    pygame.draw.circle(surface, UITheme.ACCENT_ORANGE, (ix, iy), self.node_radius + 4, 2)

                # Draw Node Body (using integer coordinates)
                pygame.draw.circle(surface, UITheme.PANEL_GREY, (ix, iy), self.node_radius)
                pygame.draw.circle(surface, base_color, (ix, iy), self.node_radius, 3)
                
                # Node ID Text
                id_txt = self.font.render(str(node["id"]), True, UITheme.TEXT_OFF_WHITE)
                surface.blit(id_txt, id_txt.get_rect(center=(ix, iy)))

                # Name Label
                name_txt = self.font.render(node["name"][:12], True, UITheme.TEXT_DIM)
                surface.blit(name_txt, (ix - 30, iy + 25))

    def handle_click(self, mouse_pos, panel_rect):
        """Corrected click detection accounting for panel position and camera."""
        # mouse_pos is global. Subtract panel top-left to get local surface coords.
        local_x = mouse_pos[0] - panel_rect[0]
        local_y = mouse_pos[1] - panel_rect[1]
        local_mouse = pygame.Vector2(local_x, local_y)
        
        for node in self.nodes:
            draw_pos = node["pos"] + self.camera_offset
            if draw_pos.distance_to(local_mouse) < self.node_radius + 5:
                self.selected_node_id = node["id"]
                return node["id"]
        return None