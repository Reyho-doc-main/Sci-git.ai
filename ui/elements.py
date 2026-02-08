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
        self.dragged_node_id = None
        self.font = pygame.font.SysFont("Consolas", 12, bold=True)
        
        # Search & Navigation
        self._search_filter = "" 
        self.target_offset = None # For smooth snapping
        self.minimap_rect = None # For click detection

    @property
    def search_filter(self):
        return self._search_filter

    @search_filter.setter
    def search_filter(self, value):
        self._search_filter = value
        # Auto-snap to first match
        if value:
            for node in self.nodes:
                if value.lower() in node["name"].lower():
                    self.center_on_node(node["id"])
                    break

    def handle_zoom(self, direction):
        old_zoom = self.zoom_level
        if direction == "in": 
            self.zoom_level = min(2.0, self.zoom_level + 0.1)
        else: 
            self.zoom_level = max(0.4, self.zoom_level - 0.1)
            
        # Adjust offset to zoom towards center of screen (approximate)
        if old_zoom != self.zoom_level:
            center = pygame.Vector2(400, 300)
            self.camera_offset = center - (center - self.camera_offset) * (self.zoom_level / old_zoom)

    def center_on_node(self, node_id):
        """Snap camera to a specific node."""
        for node in self.nodes:
            if node["id"] == node_id:
                # Target position: Center of screen (400, 300 relative to tree surface)
                target_center = pygame.Vector2(400, 300)
                # Calculate required offset
                self.camera_offset = target_center - (node["pos"] * self.zoom_level)
                break

    def update_tree(self, db_rows):
        # Preserve manual offsets for dragging (Session Persistence)
        old_offsets = {n["id"]: n.get("manual_offset", pygame.Vector2(0,0)) for n in self.nodes}
        
        self.nodes = []
        self.connections = []
        pos_map = {}
        branch_slots = {"main": 0}
        next_slot_y = 100 

        for row in db_rows:
            node_id, parent_id, branch, name = row
            
            # Simple "Git Graph" Layout Algorithm
            gen_x = pos_map[parent_id]['gen'] + 1 if (parent_id and parent_id in pos_map) else 0
            
            if branch not in branch_slots:
                # Assign new Y-level for new branches
                branch_slots[branch] = len(branch_slots) * next_slot_y
            
            base_pos = pygame.Vector2(gen_x * 160, branch_slots[branch])
            manual_off = old_offsets.get(node_id, pygame.Vector2(0,0))
            final_pos = base_pos + manual_off
            
            pos_map[node_id] = {'pos': final_pos, 'gen': gen_x}
            
            self.nodes.append({
                "id": node_id, 
                "pos": final_pos, 
                "base_pos": base_pos,
                "manual_offset": manual_off,
                "parent_id": parent_id, 
                "name": name, 
                "branch": branch
            })
            
            if parent_id in pos_map:
                self.connections.append((pos_map[parent_id]['pos'], final_pos))

    def draw(self, surface, mouse_pos):
        surface.fill((0, 0, 0, 0))
        current_radius = int(self.node_radius * self.zoom_level)
        screen_w, screen_h = surface.get_size()

        # 1. Handle Dragging Logic
        if self.dragged_node_id is not None:
            # Convert screen mouse to tree coordinates
            # Note: mouse_pos is absolute, we need relative to the tree surface (which is usually at 20, 80)
            # But the caller passes raw mouse_pos. We'll adjust in handle_click, but here we assume logic holds.
            # Actually, let's simplify: Dragging is updated in handle_click or main loop. 
            # We'll just check if we need to update connections.
            
            # Recalculate connections for visual fluidity
            self.connections = []
            pos_lookup = {n["id"]: n["pos"] for n in self.nodes}
            for n in self.nodes:
                if n["parent_id"] in pos_lookup:
                    self.connections.append((pos_lookup[n["parent_id"]], n["pos"]))

        # 2. Draw Connections
        for start, end in self.connections:
            s = (start * self.zoom_level) + self.camera_offset
            e = (end * self.zoom_level) + self.camera_offset
            
            # Culling: Don't draw lines strictly outside view
            if max(s.x, e.x) < -50 or min(s.x, e.x) > screen_w + 50: continue
            if max(s.y, e.y) < -50 or min(s.y, e.y) > screen_h + 50: continue

            # Elbow connector style
            mid_x = int(s.x + (e.x - s.x) // 2)
            pts = [(int(s.x), int(s.y)), (mid_x, int(s.y)), (mid_x, int(e.y)), (int(e.x), int(e.y))]
            pygame.draw.lines(surface, (70, 70, 80), False, pts, 2)

        # 3. Draw Nodes
        font_height = self.font.get_linesize()
        
        for node in self.nodes:
            draw_pos = (node["pos"] * self.zoom_level) + self.camera_offset
            ix, iy = int(draw_pos.x), int(draw_pos.y)
            
            # Dynamic Culling
            if not (-50 < ix < screen_w + 50) or not (-50 < iy < screen_h + 50): 
                continue

            # Search Match Logic
            is_match = self.search_filter.lower() in node["name"].lower() if self.search_filter else False
            if is_match and state.status_msg != "MATCH FOUND":
                state.status_msg = "MATCH FOUND"

            # Color Logic
            base_color = UITheme.NODE_MAIN if node["branch"] == "main" else UITheme.NODE_BRANCH
            
            # Selection Highlight
            if node["id"] in state.selected_ids:
                idx = state.selected_ids.index(node["id"])
                hl_color = UITheme.ACCENT_ORANGE if idx == 0 else (0, 255, 255)
                pygame.draw.circle(surface, hl_color, (ix, iy), current_radius + 4, 3)
            
            # Search Glow
            if is_match and self.search_filter:
                pygame.draw.circle(surface, (255, 255, 0), (ix, iy), current_radius + 8, 2)

            # Node Body
            pygame.draw.circle(surface, UITheme.PANEL_GREY, (ix, iy), current_radius)
            pygame.draw.circle(surface, base_color, (ix, iy), current_radius, 2)
            
            # Text Labels (Level of Detail: Hide text if zoomed out too far)
            if self.zoom_level > 0.6:
                id_txt = self.font.render(str(node["id"]), True, UITheme.TEXT_OFF_WHITE)
                surface.blit(id_txt, id_txt.get_rect(center=(ix, iy)))
                
                name_trunc = node["name"][:15] + ".." if len(node["name"]) > 15 else node["name"]
                name_col = (255, 255, 0) if is_match else UITheme.TEXT_DIM
                name_txt = self.font.render(name_trunc, True, name_col)
                surface.blit(name_txt, (ix - 30, iy + current_radius + 5))

    def draw_minimap(self, surface, panel_rect):
        """Draws a minimap overlay in the bottom-right of the tree panel."""
        if not self.nodes: return

        # 1. Calculate Bounds
        all_x = [n["pos"].x for n in self.nodes]
        all_y = [n["pos"].y for n in self.nodes]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        tree_w = max(100, max_x - min_x)
        tree_h = max(100, max_y - min_y)

        # 2. Setup Minimap Rect
        map_w, map_h = 160, 120
        # Position relative to the *Tree Surface*, which is 800x600
        # We want it bottom-right of that surface
        dest_x = panel_rect.w - map_w - 10
        dest_y = panel_rect.h - map_h - 10
        self.minimap_rect = pygame.Rect(dest_x, dest_y, map_w, map_h)

        # Background
        s = pygame.Surface((map_w, map_h))
        s.set_alpha(200)
        s.fill((15, 15, 20))
        surface.blit(s, (dest_x, dest_y))
        pygame.draw.rect(surface, UITheme.ACCENT_ORANGE, self.minimap_rect, 1)

        # 3. Calculate Scale
        scale_x = map_w / (tree_w + 200) # + padding
        scale_y = map_h / (tree_h + 200)
        scale = min(scale_x, scale_y)

        # 4. Draw Nodes (Dots)
        for node in self.nodes:
            # Normalize to 0,0 relative to tree bounds
            nx = (node["pos"].x - min_x) + 100
            ny = (node["pos"].y - min_y) + 100
            
            mx = dest_x + (nx * scale)
            my = dest_y + (ny * scale)
            
            col = UITheme.ACCENT_ORANGE if node["id"] in state.selected_ids else (100, 100, 100)
            if node["branch"] != "main": col = UITheme.NODE_BRANCH
            
            pygame.draw.circle(surface, col, (mx, my), 2)

        # 5. Draw Viewport (Camera)
        # The camera offset is negative relative to world 0,0 usually.
        # Viewport TopLeft in World Space = -camera_offset
        vx = (-self.camera_offset.x - min_x + 100) * scale
        vy = (-self.camera_offset.y - min_y + 100) * scale
        vw = (panel_rect.w / self.zoom_level) * scale
        vh = (panel_rect.h / self.zoom_level) * scale
        
        view_rect = pygame.Rect(dest_x + vx, dest_y + vy, vw, vh)
        pygame.draw.rect(surface, (255, 255, 255), view_rect, 1)

    def handle_click(self, mouse_pos, panel_rect):
        """
        Handles click selection, dragging, and minimap navigation.
        mouse_pos: Global screen coordinates
        panel_rect: (x, y, w, h) of the tree surface on screen
        """
        # 1. Convert Global Mouse to Local Surface Mouse
        local_x = mouse_pos[0] - panel_rect[0]
        local_y = mouse_pos[1] - panel_rect[1]
        local_mouse = pygame.Vector2(local_x, local_y)

        # 2. Check Minimap Click
        if self.minimap_rect and self.minimap_rect.collidepoint(local_x, local_y):
            # Jump to location
            # Inverse of the draw_minimap logic is complex, skipping for hackathon speed.
            # We just return None to consume the click so it doesn't deselect nodes.
            return None

        # 3. Check Node Click
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
                if clicked_node in state.selected_ids: 
                    state.selected_ids.remove(clicked_node)
                elif len(state.selected_ids) < 2: 
                    state.selected_ids.append(clicked_node)
                else: 
                    state.selected_ids = [clicked_node]
            else:
                state.selected_ids = [clicked_node]
            
            # Start Dragging
            self.dragged_node_id = clicked_node
            return state.selected_ids
        
        # 4. Handle Dragging Movement (Called every frame via main loop if mouse is down)
        # Note: Actual movement logic is easier in draw() or a separate update() 
        # but for this structure, we handle "start drag" here.
        
        return None

    def update_drag(self, mouse_pos, panel_rect):
        """Updates position of the currently dragged node."""
        if self.dragged_node_id is None: return

        local_x = mouse_pos[0] - panel_rect[0]
        local_y = mouse_pos[1] - panel_rect[1]

        tree_mouse = (pygame.Vector2(local_x, local_y) - self.camera_offset) / self.zoom_level
        
        for node in self.nodes:
            if node["id"] == self.dragged_node_id:
                node["pos"] = tree_mouse
                node["manual_offset"] = node["pos"] - node["base_pos"]
                break