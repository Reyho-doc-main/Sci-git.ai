# --- FILE: ui/elements.py ---
import pygame
import math
import json
from settings import UITheme
from state_manager import state

class VersionTree:
    def __init__(self):
        self.nodes = []  
        self.connections =[]
        self.extra_links = {}
        self.node_radius = 18
        self.camera_offset = pygame.Vector2(60, 300)
        self.zoom_level = 1.0
        self.is_panning = False
        self.dragged_node_id = None
        self.font = pygame.font.SysFont("Consolas", 12, bold=True)
        self._search_filter = "" 
        self.minimap_rect = None
        self.minimap_btn_rect = None
        self.minimap_internals = {}

    @property
    def search_filter(self): return self._search_filter

    @search_filter.setter
    def search_filter(self, value):
        self._search_filter = value
        if value:
            for node in self.nodes:
                if value.lower() in node["name"].lower():
                    self.center_on_node(node["id"])
                    break

    def handle_zoom(self, direction):
        old_zoom = self.zoom_level
        if direction == "in": self.zoom_level = min(2.0, self.zoom_level + 0.1)
        else: self.zoom_level = max(0.4, self.zoom_level - 0.1)
        if old_zoom != self.zoom_level:
            center = pygame.Vector2(400, 300)
            self.camera_offset = center - (center - self.camera_offset) * (self.zoom_level / old_zoom)

    def center_on_node(self, node_id):
        for node in self.nodes:
            if node["id"] == node_id:
                target_center = pygame.Vector2(400, 300)
                self.camera_offset = target_center - (node["pos"] * self.zoom_level)
                break

    def update_tree(self, db_rows):
        old_offsets = {n["id"]: n.get("manual_offset", pygame.Vector2(0,0)) for n in self.nodes}
        self.nodes = []
        self.connections =[]
        self.extra_links = {} # Reset extra links
        pos_map = {}
        branch_slots = {"main": 0}
        next_slot_y = 100 

        for row in db_rows:
            node_id, parent_id, branch, name = row[0], row[1], row[2], row[3]
            if len(row) > 4 and row[4]:
                try: self.extra_links[node_id] = json.loads(row[4])
                except: pass
            
            gen_x = pos_map[parent_id]['gen'] + 1 if (parent_id and parent_id in pos_map) else 0
            if branch not in branch_slots:
                branch_slots[branch] = len(branch_slots) * next_slot_y
            
            base_pos = pygame.Vector2(gen_x * 160, branch_slots[branch])
            manual_off = old_offsets.get(node_id, pygame.Vector2(0,0))
            final_pos = base_pos + manual_off
            
            pos_map[node_id] = {'pos': final_pos, 'gen': gen_x}
            
            self.nodes.append({
                "id": node_id, "pos": final_pos, "base_pos": base_pos,
                "manual_offset": manual_off, "parent_id": parent_id, 
                "name": name, "branch": branch
            })
            
            if parent_id in pos_map:
                self.connections.append((pos_map[parent_id]['pos'], final_pos))

        # Add custom linkages
        for src, targets in self.extra_links.items():
            if src in pos_map:
                for tgt in targets:
                    if tgt in pos_map:
                        self.connections.append((pos_map[src]['pos'], pos_map[tgt]['pos']))

    def draw_arrow_head(self, surface, tip, direction, color):
        if direction.length() == 0: return
        direction = direction.normalize()
        size = 8
        angle = math.atan2(direction.y, direction.x)
        p1 = tip
        p2 = tip - pygame.Vector2(size, size/2).rotate_rad(angle)
        p3 = tip - pygame.Vector2(size, -size/2).rotate_rad(angle)
        pygame.draw.polygon(surface, color, [p1, p2, p3])

    def draw_n8n_curve(self, surface, start, end, color):
        dist = (end.x - start.x) / 2
        if abs(dist) < 10: dist = 40
        cp1 = start + pygame.Vector2(dist, 0)
        cp2 = end - pygame.Vector2(dist, 0)
        
        points = [start]
        for t in range(1, 21):
            t /= 20
            p = (1-t)**3 * start + 3*(1-t)**2 * t * cp1 + 3*(1-t) * t**2 * cp2 + t**3 * end
            points.append(p)
        
        pygame.draw.lines(surface, color, False, points, 2)
        direction = end - cp2
        if direction.length() == 0: direction = pygame.Vector2(1, 0)
        self.draw_arrow_head(surface, end, direction, color)

    def draw(self, surface, mouse_pos):
        surface.fill((0, 0, 0, 0))
        current_radius = int(self.node_radius * self.zoom_level)
        screen_w, screen_h = surface.get_size()

        # FIXED: When dragging, we must rebuild BOTH parent connections AND extra links
        if self.dragged_node_id is not None:
            self.connections =[]
            pos_lookup = {n["id"]: n["pos"] for n in self.nodes}
            
            # Rebuild standard parent-child links
            for n in self.nodes:
                if n["parent_id"] in pos_lookup:
                    self.connections.append((pos_lookup[n["parent_id"]], n["pos"]))
                    
            # Rebuild custom extra links
            for src, targets in self.extra_links.items():
                if src in pos_lookup:
                    for tgt in targets:
                        if tgt in pos_lookup:
                            self.connections.append((pos_lookup[src], pos_lookup[tgt]))

        for start, end in self.connections:
            s = (start * self.zoom_level) + self.camera_offset
            e = (end * self.zoom_level) + self.camera_offset
            port_out = s + pygame.Vector2(current_radius, 0)
            port_in = e - pygame.Vector2(current_radius, 0)

            if max(s.x, e.x) < -50 or min(s.x, e.x) > screen_w + 50: continue
            if max(s.y, e.y) < -50 or min(s.y, e.y) > screen_h + 50: continue

            self.draw_n8n_curve(surface, port_out, port_in, (100, 100, 110))
            pygame.draw.circle(surface, (150, 150, 160), port_out, 3)
            pygame.draw.circle(surface, (150, 150, 160), port_in, 3)

        for node in self.nodes:
            draw_pos = (node["pos"] * self.zoom_level) + self.camera_offset
            ix, iy = int(draw_pos.x), int(draw_pos.y)
            
            if not (-50 < ix < screen_w + 50) or not (-50 < iy < screen_h + 50): continue

            is_match = self.search_filter.lower() in node["name"].lower() if self.search_filter else False
            is_light = UITheme.BG_DARK[0] > 150
            search_color = (255, 255, 0) if not is_light else (180, 140, 0)
            
            if is_match and state.status_msg != "MATCH FOUND": state.status_msg = "MATCH FOUND"

            base_color = UITheme.NODE_MAIN if node["branch"] == "main" else UITheme.NODE_BRANCH
            
            if node["id"] in state.selected_ids:
                idx = state.selected_ids.index(node["id"])
                hl_color = UITheme.ACCENT_ORANGE if idx == 0 else (0, 255, 255)
                pygame.draw.circle(surface, hl_color, (ix, iy), current_radius + 4, 3)
            
            if is_match and self.search_filter:
                pygame.draw.circle(surface, search_color, (ix, iy), current_radius + 8, 3)

            pygame.draw.circle(surface, UITheme.PANEL_GREY, (ix, iy), current_radius)
            pygame.draw.circle(surface, base_color, (ix, iy), current_radius, 2)
            
            if node["id"] in state.inconsistent_nodes:
                badge_pos = (ix + current_radius - 5, iy - current_radius + 5)
                pygame.draw.circle(surface, (255, 50, 50), badge_pos, 8)
                excl = self.font.render("!", True, (255, 255, 255))
                surface.blit(excl, (badge_pos[0] - excl.get_width()//2, badge_pos[1] - excl.get_height()//2))

            if self.zoom_level > 0.6:
                id_txt = self.font.render(str(node["id"]), True, UITheme.TEXT_OFF_WHITE)
                surface.blit(id_txt, id_txt.get_rect(center=(ix, iy)))
                
                name_trunc = node["name"][:15] + ".." if len(node["name"]) > 15 else node["name"]
                name_col = search_color if is_match else UITheme.TEXT_DIM
                name_txt = self.font.render(name_trunc, True, name_col)
                surface.blit(name_txt, (ix - 30, iy + current_radius + 5))


    def draw_minimap(self, surface, panel_rect, icons=None):
        if not self.nodes: return
        map_w, map_h = 160, 120
        dest_x = panel_rect.w - map_w - 10
        dest_y = panel_rect.h - map_h - 10
        
        if state.minimap_collapsed:
            self.minimap_rect = None
            self.minimap_btn_rect = pygame.Rect(panel_rect.w - 30, panel_rect.h - 30, 20, 20)
            if icons and icons.get('expand'): surface.blit(icons['expand'], (self.minimap_btn_rect.x, self.minimap_btn_rect.y))
            else:
                pygame.draw.rect(surface, UITheme.PANEL_GREY, self.minimap_btn_rect)
                pygame.draw.rect(surface, UITheme.ACCENT_ORANGE, self.minimap_btn_rect, 1)
                surface.blit(self.font.render("+", True, UITheme.ACCENT_ORANGE), (self.minimap_btn_rect.x + 6, self.minimap_btn_rect.y + 2))
            return

        self.minimap_rect = pygame.Rect(dest_x, dest_y, map_w, map_h)
        self.minimap_btn_rect = pygame.Rect(dest_x + map_w - 20, dest_y - 20, 20, 20)
        
        if icons and icons.get('collapse'): surface.blit(icons['collapse'], (self.minimap_btn_rect.x, self.minimap_btn_rect.y))
        else:
            pygame.draw.rect(surface, (50, 20, 20), self.minimap_btn_rect)
            surface.blit(self.font.render("_", True, (255, 255, 255)), (self.minimap_btn_rect.x + 6, self.minimap_btn_rect.y - 4))

        s = pygame.Surface((map_w, map_h))
        s.set_alpha(220)
        s.fill((15, 15, 20))
        surface.blit(s, (dest_x, dest_y))
        pygame.draw.rect(surface, UITheme.ACCENT_ORANGE, self.minimap_rect, 1)

        all_x =[n["pos"].x for n in self.nodes]
        all_y = [n["pos"].y for n in self.nodes]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        padding = 100
        min_x -= padding; min_y -= padding; max_x += padding; max_y += padding
        world_w = max_x - min_x; world_h = max_y - min_y
        if world_w < 1: world_w = 1
        if world_h < 1: world_h = 1

        scale_x = map_w / world_w
        scale_y = map_h / world_h
        scale = min(scale_x, scale_y)
        
        self.minimap_internals = {"min_x": min_x, "min_y": min_y, "scale": scale, "dest_x": dest_x, "dest_y": dest_y}

        for node in self.nodes:
            mx = dest_x + (node["pos"].x - min_x) * scale
            my = dest_y + (node["pos"].y - min_y) * scale
            col = UITheme.ACCENT_ORANGE if node["id"] in state.selected_ids else (100, 100, 100)
            if node["branch"] != "main": col = UITheme.NODE_BRANCH
            if self.minimap_rect.collidepoint(mx, my): pygame.draw.circle(surface, col, (mx, my), 2)

        view_world_x = -self.camera_offset.x / self.zoom_level
        view_world_y = -self.camera_offset.y / self.zoom_level
        view_world_w = panel_rect.w / self.zoom_level
        view_world_h = panel_rect.h / self.zoom_level
        vx = dest_x + (view_world_x - min_x) * scale
        vy = dest_y + (view_world_y - min_y) * scale
        vw = view_world_w * scale
        vh = view_world_h * scale
        view_rect = pygame.Rect(vx, vy, vw, vh)
        clipped_rect = view_rect.clip(self.minimap_rect)
        if clipped_rect.w > 0 and clipped_rect.h > 0: pygame.draw.rect(surface, (255, 255, 255), clipped_rect, 1)

    def handle_click(self, mouse_pos, panel_rect):
        local_x = mouse_pos[0] - panel_rect[0]
        local_y = mouse_pos[1] - panel_rect[1]
        local_mouse = pygame.Vector2(local_x, local_y)

        if self.minimap_btn_rect and self.minimap_btn_rect.collidepoint(local_x, local_y):
            state.minimap_collapsed = not state.minimap_collapsed
            return None

        if not state.minimap_collapsed and self.minimap_rect and self.minimap_rect.collidepoint(local_x, local_y):
            data = self.minimap_internals
            if not data: return None
            click_map_x = local_x - data["dest_x"]
            click_map_y = local_y - data["dest_y"]
            target_world_x = (click_map_x / data["scale"]) + data["min_x"]
            target_world_y = (click_map_y / data["scale"]) + data["min_y"]
            screen_center = pygame.Vector2(panel_rect[2]/2, panel_rect[3]/2)
            self.camera_offset = screen_center - (pygame.Vector2(target_world_x, target_world_y) * self.zoom_level)
            return None

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
            self.dragged_node_id = clicked_node
            return list(state.selected_ids) 
        return None

    def update_drag(self, mouse_pos, panel_rect):
        if self.dragged_node_id is None: return
        local_x = mouse_pos[0] - panel_rect[0]
        local_y = mouse_pos[1] - panel_rect[1]
        tree_mouse = (pygame.Vector2(local_x, local_y) - self.camera_offset) / self.zoom_level
        tree_mouse.x = max(-2000, min(5000, tree_mouse.x))
        tree_mouse.y = max(-2000, min(5000, tree_mouse.y))
        for node in self.nodes:
            if node["id"] == self.dragged_node_id:
                node["pos"] = tree_mouse
                node["manual_offset"] = node["pos"] - node["base_pos"]
                break