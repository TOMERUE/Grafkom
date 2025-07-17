import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np

class GraphicsApp:
    def __init__(self):
        # Inisialisasi pygame dan OpenGL
        pygame.init()
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Aplikasi Grafika 2D Interaktif - PyOpenGL")
        
        # Setup OpenGL viewport
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.width, 0, self.height)
        glMatrixMode(GL_MODELVIEW)
        
        # State variables
        self.current_tool = 'point'  # point, line, rectangle, ellipse
        self.current_color = [1.0, 1.0, 1.0]  # RGB white
        self.line_width = 1.0
        self.objects = []  # List untuk menyimpan objek yang digambar
        self.temp_points = []  # Untuk menyimpan titik sementara
        self.selected_object = None
        self.selection_mode = False  # Mode untuk memilih objek
        self.transform_mode = None  # translate, rotate, scale
        self.window_bounds = None  # [x1, y1, x2, y2]
        self.window_defining = False
        
        # Transformation parameters untuk objek yang dipilih
        self.object_transformations = {}  # Dictionary untuk menyimpan transformasi per objek
        
    def screen_to_opengl(self, x, y):
        """Konversi koordinat layar pygame ke koordinat OpenGL"""
        return x, self.height - y
    
    def distance_point_to_point(self, p1, p2):
        """Hitung jarak antara dua titik"""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def distance_point_to_line(self, px, py, x1, y1, x2, y2):
        """Hitung jarak dari titik ke garis"""
        # Rumus jarak titik ke garis: |ax + by + c| / sqrt(a² + b²)
        A = y2 - y1
        B = x1 - x2
        C = x2 * y1 - x1 * y2
        
        distance = abs(A * px + B * py + C) / math.sqrt(A * A + B * B)
        
        # Cek apakah proyeksi titik berada dalam segmen garis
        dot_product = (px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)
        squared_length = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1)
        
        if squared_length == 0:
            return self.distance_point_to_point((px, py), (x1, y1))
        
        t = dot_product / squared_length
        
        if t < 0:
            return self.distance_point_to_point((px, py), (x1, y1))
        elif t > 1:
            return self.distance_point_to_point((px, py), (x2, y2))
        else:
            return distance
    
    def point_in_rectangle(self, px, py, x1, y1, x2, y2):
        """Cek apakah titik berada dalam rectangle"""
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        return min_x <= px <= max_x and min_y <= py <= max_y
    
    def find_object_at_point(self, x, y):
        """Cari objek yang berada di dekat titik klik"""
        tolerance = 10  # Toleransi untuk seleksi
        
        for i, obj in enumerate(reversed(self.objects)):  # Cek dari objek teratas
            actual_index = len(self.objects) - 1 - i
            
            if obj['type'] == 'point':
                px, py = obj['points'][0]
                if self.distance_point_to_point((x, y), (px, py)) <= tolerance:
                    return actual_index
            
            elif obj['type'] == 'line':
                x1, y1, x2, y2 = obj['points'][0][0], obj['points'][0][1], obj['points'][1][0], obj['points'][1][1]
                if self.distance_point_to_line(x, y, x1, y1, x2, y2) <= tolerance:
                    return actual_index
            
            elif obj['type'] == 'rectangle':
                x1, y1, x2, y2 = obj['points'][0][0], obj['points'][0][1], obj['points'][1][0], obj['points'][1][1]
                # Cek apakah titik dekat dengan salah satu sisi rectangle
                if (self.distance_point_to_line(x, y, x1, y1, x2, y1) <= tolerance or
                    self.distance_point_to_line(x, y, x2, y1, x2, y2) <= tolerance or
                    self.distance_point_to_line(x, y, x2, y2, x1, y2) <= tolerance or
                    self.distance_point_to_line(x, y, x1, y2, x1, y1) <= tolerance):
                    return actual_index
            
            elif obj['type'] == 'ellipse':
                # Untuk ellipse, cek apakah titik berada dalam bounding rectangle
                x1, y1, x2, y2 = obj['points'][0][0], obj['points'][0][1], obj['points'][1][0], obj['points'][1][1]
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                rx, ry = abs(x2 - x1) / 2, abs(y2 - y1) / 2
                
                # Rumus ellipse: (x-cx)²/rx² + (y-cy)²/ry² = 1
                # Cek apakah titik dekat dengan ellipse
                if rx > 0 and ry > 0:
                    ellipse_eq = ((x - cx)**2 / rx**2) + ((y - cy)**2 / ry**2)
                    if abs(ellipse_eq - 1) <= 0.3:  # Toleransi untuk ellipse
                        return actual_index
        
        return None
    
    def get_object_transformation(self, obj_index):
        """Dapatkan transformasi untuk objek tertentu"""
        if obj_index not in self.object_transformations:
            self.object_transformations[obj_index] = {
                'translation': [0, 0],
                'rotation': 0,
                'scale': 1.0
            }
        return self.object_transformations[obj_index]
    
    def draw_point(self, x, y, color, size=5):
        """Menggambar titik"""
        glColor3f(*color)
        glPointSize(size)
        glBegin(GL_POINTS)
        glVertex2f(x, y)
        glEnd()
    
    def draw_line(self, x1, y1, x2, y2, color, width=1):
        """Menggambar garis"""
        glColor3f(*color)
        glLineWidth(width)
        glBegin(GL_LINES)
        glVertex2f(x1, y1)
        glVertex2f(x2, y2)
        glEnd()
    
    def draw_rectangle(self, x1, y1, x2, y2, color, width=1):
        """Menggambar persegi menggunakan GL_LINE_LOOP"""
        glColor3f(*color)
        glLineWidth(width)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x1, y1)
        glVertex2f(x2, y1)
        glVertex2f(x2, y2)
        glVertex2f(x1, y2)
        glEnd()
    
    def draw_ellipse(self, cx, cy, rx, ry, color, width=1):
        """
        Menggambar ellipse menggunakan parametric equation
        x = cx + rx * cos(t)
        y = cy + ry * sin(t)
        """
        glColor3f(*color)
        glLineWidth(width)
        glBegin(GL_LINE_LOOP)
        for i in range(360):
            angle = math.radians(i)
            x = cx + rx * math.cos(angle)
            y = cy + ry * math.sin(angle)
            glVertex2f(x, y)
        glEnd()
    
    def apply_transformation_to_object(self, obj, obj_index):
        """Menerapkan transformasi geometri pada objek tertentu"""
        if obj_index not in self.object_transformations:
            return obj['points']
        
        transform = self.object_transformations[obj_index]
        translation = transform['translation']
        rotation = transform['rotation']
        scale = transform['scale']
        
        transformed_points = []
        
        # Hitung pusat objek untuk rotasi dan scaling
        if obj['type'] == 'point':
            center = obj['points'][0]
        else:
            # Hitung centroid
            sum_x = sum(p[0] for p in obj['points'])
            sum_y = sum(p[1] for p in obj['points'])
            center = (sum_x / len(obj['points']), sum_y / len(obj['points']))
        
        for px, py in obj['points']:
            # 1. Translasi
            px += translation[0]
            py += translation[1]
            
            # 2. Rotasi terhadap pusat objek
            if rotation != 0:
                angle = math.radians(rotation)
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                cx, cy = center[0] + translation[0], center[1] + translation[1]
                px_new = cx + (px - cx) * cos_a - (py - cy) * sin_a
                py_new = cy + (px - cx) * sin_a + (py - cy) * cos_a
                px, py = px_new, py_new
            
            # 3. Scaling terhadap pusat objek
            if scale != 1.0:
                cx, cy = center[0] + translation[0], center[1] + translation[1]
                px = cx + (px - cx) * scale
                py = cy + (py - cy) * scale
            
            transformed_points.append((px, py))
        
        return transformed_points
    
    def draw_selection_highlight(self, obj, obj_index):
        """Gambar highlight untuk objek yang dipilih"""
        points = self.apply_transformation_to_object(obj, obj_index)
        
        glColor3f(1.0, 1.0, 0.0)  # Yellow highlight
        glLineWidth(3)
        
        if obj['type'] == 'point':
            # Gambar lingkaran kecil di sekitar titik
            x, y = points[0]
            glBegin(GL_LINE_LOOP)
            for i in range(20):
                angle = 2 * math.pi * i / 20
                glVertex2f(x + 8 * math.cos(angle), y + 8 * math.sin(angle))
            glEnd()
        
        elif obj['type'] == 'line':
            # Gambar garis dengan warna highlight
            glBegin(GL_LINES)
            glVertex2f(points[0][0], points[0][1])
            glVertex2f(points[1][0], points[1][1])
            glEnd()
        
        elif obj['type'] == 'rectangle':
            # Gambar rectangle dengan warna highlight
            glBegin(GL_LINE_LOOP)
            glVertex2f(points[0][0], points[0][1])
            glVertex2f(points[1][0], points[0][1])
            glVertex2f(points[1][0], points[1][1])
            glVertex2f(points[0][0], points[1][1])
            glEnd()
        
        elif obj['type'] == 'ellipse':
            # Gambar ellipse dengan warna highlight
            cx, cy = (points[0][0] + points[1][0]) / 2, (points[0][1] + points[1][1]) / 2
            rx, ry = abs(points[1][0] - points[0][0]) / 2, abs(points[1][1] - points[0][1]) / 2
            glBegin(GL_LINE_LOOP)
            for i in range(360):
                angle = math.radians(i)
                x = cx + rx * math.cos(angle)
                y = cy + ry * math.sin(angle)
                glVertex2f(x, y)
            glEnd()
    
    def cohen_sutherland_clip(self, x1, y1, x2, y2, xmin, ymin, xmax, ymax):
        """
        Algoritma Cohen-Sutherland untuk line clipping
        Region codes: 
        1001 | 1000 | 1010
        0001 | 0000 | 0010  
        0101 | 0100 | 0110
        """
        def compute_code(x, y):
            code = 0
            if x < xmin: code |= 1    # Left
            if x > xmax: code |= 2    # Right
            if y < ymin: code |= 4    # Bottom
            if y > ymax: code |= 8    # Top
            return code
        
        code1 = compute_code(x1, y1)
        code2 = compute_code(x2, y2)
        
        while True:
            # Kedua titik di dalam window
            if code1 == 0 and code2 == 0:
                return True, x1, y1, x2, y2
            
            # Kedua titik di luar window pada sisi yang sama
            if code1 & code2 != 0:
                return False, 0, 0, 0, 0
            
            # Pilih titik yang di luar window
            if code1 != 0:
                code_out = code1
            else:
                code_out = code2
            
            # Hitung intersection point
            if code_out & 8:  # Top
                x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1)
                y = ymax
            elif code_out & 4:  # Bottom
                x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1)
                y = ymin
            elif code_out & 2:  # Right
                y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
                x = xmax
            elif code_out & 1:  # Left
                y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
                x = xmin
            
            # Update titik dan code
            if code_out == code1:
                x1, y1 = x, y
                code1 = compute_code(x1, y1)
            else:
                x2, y2 = x, y
                code2 = compute_code(x2, y2)
    
    def point_in_window(self, x, y):
        """Cek apakah titik berada dalam window"""
        if not self.window_bounds:
            return False
        xmin, ymin, xmax, ymax = self.window_bounds
        return xmin <= x <= xmax and ymin <= y <= ymax
    
    def draw_window(self):
        """Menggambar window clipping"""
        if self.window_bounds:
            x1, y1, x2, y2 = self.window_bounds
            glColor3f(1.0, 1.0, 0.0)  # Yellow
            glLineWidth(2)
            glBegin(GL_LINE_LOOP)
            glVertex2f(x1, y1)
            glVertex2f(x2, y1)
            glVertex2f(x2, y2)
            glVertex2f(x1, y2)
            glEnd()
    
    def render(self):
        """Render semua objek"""
        glClear(GL_COLOR_BUFFER_BIT)
        
        # Gambar semua objek
        for i, obj in enumerate(self.objects):
            color = obj['color']
            
            # Terapkan transformasi pada objek
            points = self.apply_transformation_to_object(obj, i)
            
            # Cek apakah objek dalam window (untuk perubahan warna)
            if self.window_bounds:
                in_window = False
                if obj['type'] == 'point':
                    x, y = points[0]
                    in_window = self.point_in_window(x, y)
                elif obj['type'] == 'line':
                    # Cek apakah salah satu titik dalam window
                    for x, y in points:
                        if self.point_in_window(x, y):
                            in_window = True
                            break
                
                # Ubah warna jika dalam window
                if in_window:
                    color = [0.0, 1.0, 0.0]  # Green
            
            # Gambar objek berdasarkan tipe
            if obj['type'] == 'point':
                self.draw_point(points[0][0], points[0][1], color)
            elif obj['type'] == 'line':
                if self.window_bounds:
                    # Terapkan clipping
                    x1, y1, x2, y2 = points[0][0], points[0][1], points[1][0], points[1][1]
                    xmin, ymin, xmax, ymax = self.window_bounds
                    clipped, cx1, cy1, cx2, cy2 = self.cohen_sutherland_clip(
                        x1, y1, x2, y2, xmin, ymin, xmax, ymax)
                    if clipped:
                        self.draw_line(cx1, cy1, cx2, cy2, color, obj['width'])
                else:
                    self.draw_line(points[0][0], points[0][1], points[1][0], points[1][1], 
                                 color, obj['width'])
            elif obj['type'] == 'rectangle':
                self.draw_rectangle(points[0][0], points[0][1], points[1][0], points[1][1], 
                                  color, obj['width'])
            elif obj['type'] == 'ellipse':
                cx, cy = (points[0][0] + points[1][0]) / 2, (points[0][1] + points[1][1]) / 2
                rx, ry = abs(points[1][0] - points[0][0]) / 2, abs(points[1][1] - points[0][1]) / 2
                self.draw_ellipse(cx, cy, rx, ry, color, obj['width'])
            
            # Gambar highlight jika objek dipilih
            if self.selected_object == i:
                self.draw_selection_highlight(obj, i)
        
        # Gambar window clipping
        self.draw_window()
        
        # Gambar objek sementara
        if len(self.temp_points) == 1 and self.current_tool in ['line', 'rectangle', 'ellipse'] and not self.selection_mode:
            mouse_pos = pygame.mouse.get_pos()
            mx, my = self.screen_to_opengl(*mouse_pos)
            
            glColor3f(*self.current_color)
            glLineWidth(self.line_width)
            
            if self.current_tool == 'line':
                glBegin(GL_LINES)
                glVertex2f(self.temp_points[0][0], self.temp_points[0][1])
                glVertex2f(mx, my)
                glEnd()
            elif self.current_tool == 'rectangle':
                glBegin(GL_LINE_LOOP)
                glVertex2f(self.temp_points[0][0], self.temp_points[0][1])
                glVertex2f(mx, self.temp_points[0][1])
                glVertex2f(mx, my)
                glVertex2f(self.temp_points[0][0], my)
                glEnd()
        
        # Tampilkan status di title bar
        status = f"Mode: {'SELECT' if self.selection_mode else self.current_tool.upper()}"
        if self.selected_object is not None:
            status += f" | Selected: Object {self.selected_object + 1}"
        if self.transform_mode:
            status += f" | Transform: {self.transform_mode.upper()}"
        
        pygame.display.set_caption(f"Aplikasi Grafika 2D - {status}")
        pygame.display.flip()
    
    def handle_mouse_click(self, pos):
        """Handle mouse click events"""
        x, y = self.screen_to_opengl(*pos)
        
        if self.window_defining:
            self.temp_points.append((x, y))
            if len(self.temp_points) == 2:
                x1, y1 = self.temp_points[0]
                x2, y2 = self.temp_points[1]
                self.window_bounds = [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
                self.temp_points = []
                self.window_defining = False
            return
        
        # Mode seleksi objek
        if self.selection_mode:
            selected_index = self.find_object_at_point(x, y)
            if selected_index is not None:
                self.selected_object = selected_index
                print(f"Selected object {selected_index + 1} ({self.objects[selected_index]['type']})")
            else:
                self.selected_object = None
                print("No object selected")
            return
        
        # Mode menggambar objek
        if self.current_tool == 'point':
            obj = {
                'type': 'point',
                'points': [(x, y)],
                'color': self.current_color.copy(),
                'width': self.line_width
            }
            self.objects.append(obj)
        
        elif self.current_tool in ['line', 'rectangle', 'ellipse']:
            self.temp_points.append((x, y))
            if len(self.temp_points) == 2:
                obj = {
                    'type': self.current_tool,
                    'points': self.temp_points.copy(),
                    'color': self.current_color.copy(),
                    'width': self.line_width
                }
                self.objects.append(obj)
                self.temp_points = []
    
    def handle_keyboard(self, key):
        """Handle keyboard events"""
        # Selection mode toggle
        if key == K_v:  # 'V' untuk selection mode
            self.selection_mode = not self.selection_mode
            if not self.selection_mode:
                self.selected_object = None
            print(f"Selection mode: {'ON' if self.selection_mode else 'OFF'}")
            return
        
        # Tool selection (hanya jika tidak dalam selection mode)
        if not self.selection_mode:
            if key == K_1: self.current_tool = 'point'
            elif key == K_2: self.current_tool = 'line'
            elif key == K_3: self.current_tool = 'rectangle'
            elif key == K_4: self.current_tool = 'ellipse'
        
        # Color selection
        if key == K_r: self.current_color = [1.0, 0.0, 0.0]  # Red
        elif key == K_g: self.current_color = [0.0, 1.0, 0.0]  # Green
        elif key == K_b: self.current_color = [0.0, 0.0, 1.0]  # Blue
        elif key == K_w: self.current_color = [1.0, 1.0, 1.0]  # White
        
        # Line width
        elif key == K_PLUS or key == K_EQUALS:
            self.line_width = min(10, self.line_width + 1)
        elif key == K_MINUS:
            self.line_width = max(1, self.line_width - 1)
        
        # Window definition
        elif key == K_SPACE:
            self.window_defining = True
            self.temp_points = []
            print("Click two points to define window")
        
        # Transformation mode (hanya jika ada objek yang dipilih)
        elif self.selected_object is not None:
            if key == K_t: 
                self.transform_mode = 'translate'
                print("Transform mode: TRANSLATE (use arrow keys)")
            elif key == K_o: 
                self.transform_mode = 'rotate'
                print("Transform mode: ROTATE (use Q/E)")
            elif key == K_s: 
                self.transform_mode = 'scale'
                print("Transform mode: SCALE (use Z/X)")
            
            # Apply transformations to selected object
            elif self.transform_mode == 'translate':
                transform = self.get_object_transformation(self.selected_object)
                if key == K_UP:
                    transform['translation'][1] += 10
                elif key == K_DOWN:
                    transform['translation'][1] -= 10
                elif key == K_LEFT:
                    transform['translation'][0] -= 10
                elif key == K_RIGHT:
                    transform['translation'][0] += 10
            
            elif self.transform_mode == 'rotate':
                transform = self.get_object_transformation(self.selected_object)
                if key == K_q:
                    transform['rotation'] += 5
                elif key == K_e:
                    transform['rotation'] -= 5
            
            elif self.transform_mode == 'scale':
                transform = self.get_object_transformation(self.selected_object)
                if key == K_z:
                    transform['scale'] *= 1.1
                elif key == K_x:
                    transform['scale'] *= 0.9
        
        # Reset transformations for selected object
        if key == K_BACKSPACE and self.selected_object is not None:
            if self.selected_object in self.object_transformations:
                del self.object_transformations[self.selected_object]
            print("Reset transformations for selected object")
        
        # Clear all
        elif key == K_c:
            self.objects = []
            self.object_transformations = {}
            self.selected_object = None
            self.window_bounds = None
        
        # Delete selected object
        elif key == K_DELETE and self.selected_object is not None:
            # Hapus objek dan transformasinya
            del self.objects[self.selected_object]
            if self.selected_object in self.object_transformations:
                del self.object_transformations[self.selected_object]
            
            # Update indeks transformasi untuk objek lain
            new_transformations = {}
            for obj_idx, transform in self.object_transformations.items():
                if obj_idx > self.selected_object:
                    new_transformations[obj_idx - 1] = transform
                elif obj_idx < self.selected_object:
                    new_transformations[obj_idx] = transform
            
            self.object_transformations = new_transformations
            self.selected_object = None
            print("Deleted selected object")
    
    def run(self):
        """Main game loop"""
        clock = pygame.time.Clock()
        running = True
        
        print("=== KONTROL APLIKASI ===")
        print("Selection: V = Toggle selection mode")
        print("Tools: 1=Point, 2=Line, 3=Rectangle, 4=Ellipse")
        print("Colors: R=Red, G=Green, B=Blue, W=White")
        print("Line Width: +/- untuk mengubah ketebalan")
        print("Window: SPACE untuk mendefinisikan window clipping")
        print("")
        print("=== TRANSFORMASI (pilih objek dulu dengan V) ===")
        print("Transform Mode: T=Translate, O=Rotate, S=Scale")
        print("  - Translate: Arrow keys")
        print("  - Rotate: Q/E")
        print("  - Scale: Z/X")
        print("Reset: BACKSPACE (reset transformasi objek terpilih)")
        print("Delete: DELETE (hapus objek terpilih)")
        print("Clear All: C")
        print("========================")
        
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self.handle_mouse_click(event.pos)
                elif event.type == KEYDOWN:
                    self.handle_keyboard(event.key)
            
            self.render()
            clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    app = GraphicsApp()
    app.run()
