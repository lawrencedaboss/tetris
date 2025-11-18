import pygame
import os
import sys
import random

# Initialize pygame
pygame.init()

# Game window dimensions
WIDTH, HEIGHT = 620, 600
GRID_SIZE = 30
GRID_WIDTH, GRID_HEIGHT = 10, 20
TOP_MARGIN = HEIGHT - GRID_HEIGHT * GRID_SIZE
LEFT_MARGIN = (WIDTH - GRID_WIDTH * GRID_SIZE) // 2

# (removed stray global UI variables)
# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)

# Speed settings
FALL_SPEED_NORMAL = 500  # milliseconds
FALL_SPEED_FAST = 50  # milliseconds

# Define tetromino shapes
TETROMINOS = {
    'I': [[(0, 1), (1, 1), (2, 1), (3, 1)],
          [(1, 0), (1, 1), (1, 2), (1, 3)]],
    'O': [[(0, 0), (1, 0), (0, 1), (1, 1)]],
    'T': [[(1, 0), (0, 1), (1, 1), (2, 1)],
          [(1, 0), (1, 1), (2, 1), (1, 2)],
          [(0, 1), (1, 1), (2, 1), (1, 2)],
          [(1, 0), (0, 1), (1, 1), (1, 2)]],
    'S': [[(1, 0), (2, 0), (0, 1), (1, 1)],
          [(0, 0), (0, 1), (1, 1), (1, 2)]],
    'Z': [[(0, 0), (1, 0), (1, 1), (2, 1)],
          [(2, 0), (1, 1), (2, 1), (1, 2)]],
    'J': [[(0, 0), (0, 1), (1, 1), (2, 1)],
          [(1, 0), (2, 0), (1, 1), (1, 2)],
          [(0, 1), (1, 1), (2, 1), (2, 2)],
          [(1, 0), (1, 1), (0, 2), (1, 2)]],
    'L': [[(2, 0), (0, 1), (1, 1), (2, 1)],
          [(1, 0), (1, 1), (1, 2), (2, 2)],
          [(0, 1), (1, 1), (2, 1), (0, 2)],
          [(0, 0), (1, 0), (1, 1), (1, 2)]],
}

# Tetromino colors
COLORS = {
    'I': (0, 255, 255),
    'O': (255, 255, 0),
    'T': (128, 0, 128),
    'S': (0, 255, 0),
    'Z': (255, 0, 0),
    'J': (0, 0, 255),
    'L': (255, 165, 0),
}

class Tetromino:
    def __init__(self, x, y, shape_name):
        self.x = x
        self.y = y
        self.shape_name = shape_name
        self.shape = TETROMINOS[shape_name]
        self.color = COLORS[shape_name]
        self.rotation = 0

    def get_shape(self):
        return self.shape[self.rotation]

    def rotate(self):
        self.rotation = (self.rotation + 1) % len(self.shape)

class Tetris:
    def __init__(self, screen):
        self.screen = screen
        self.grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.level = 1
        self.fall_time = 0
        self.fall_speed = FALL_SPEED_NORMAL  # milliseconds
        self.piece_queue = []
        self.hold_piece = None
        self.can_hold = True
        self.active_piece = self.get_next_piece()
        self.game_over = False
        self.down_press_time = None
        # Try to load and play background music (if present in assets)
        try:
            self.load_background_music()
        except Exception:
            # Don't crash if mixer or music fails
            pass

    def load_background_music(self, assets_subdir="assets", volume=0.5):

        # Initialize mixer safely
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            # If mixer can't init, abort gracefully
            return

        cwd_candidates = [
            os.path.join(os.getcwd(), assets_subdir),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", assets_subdir)),
            os.path.abspath(os.path.join(os.path.dirname(__file__), assets_subdir)),
        ]

        audio_exts = ('.mp3', '.ogg', '.wav')
        found = None
        for path in cwd_candidates:
            if path and os.path.isdir(path):
                for fname in os.listdir(path):
                    if fname.lower().endswith(audio_exts):
                        found = os.path.join(path, fname)
                        break
            if found:
                break

        if not found:
            # No music found; silently continue
            return

        try:
            pygame.mixer.music.load(found)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)  # loop indefinitely
        except Exception:
            # If loading/playing fails, don't crash the game
            return

    def get_next_piece(self):
        if len(self.piece_queue)<7:
            self.refill_queue()
        shape_name = self.piece_queue.pop(0)
        return Tetromino(GRID_WIDTH // 2 - 2, 0, shape_name)

    def refill_queue(self):
        bag = list(TETROMINOS.keys())
        random.shuffle(bag)
        self.piece_queue.extend(bag)

    def draw_grid(self):
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                pygame.draw.rect(self.screen, self.grid[y][x],
                                 (LEFT_MARGIN + x * GRID_SIZE, TOP_MARGIN + y * GRID_SIZE, GRID_SIZE, GRID_SIZE), 0)
                pygame.draw.rect(self.screen, GRAY,
                                 (LEFT_MARGIN + x * GRID_SIZE, TOP_MARGIN + y * GRID_SIZE, GRID_SIZE, GRID_SIZE), 1)

    def draw_piece(self, piece, offset_x=0, offset_y=0):
        shape = piece.get_shape()
        for x, y in shape:
            pygame.draw.rect(self.screen, piece.color,
                             (LEFT_MARGIN + (piece.x + x + offset_x) * GRID_SIZE, TOP_MARGIN + (piece.y + y + offset_y) * GRID_SIZE, GRID_SIZE, GRID_SIZE), 0)

    def get_restart_button_rect(self):
        # Position the restart button below the hold box on the left side
        x = LEFT_MARGIN - 150
        y = TOP_MARGIN + 200
        w = 120
        h = 40
        return pygame.Rect(x, y, w, h)


    def draw_sidebar(self):
        # Draw next pieces
        font = pygame.font.Font(None, 30)
        text = font.render("NEXT", True, BLACK)
        self.screen.blit(text, (LEFT_MARGIN + GRID_WIDTH * GRID_SIZE + 20, TOP_MARGIN + 20))
        for i, shape_name in enumerate(self.piece_queue[:7]):
            temp_piece = Tetromino(0, 0, shape_name)
            for x, y in temp_piece.get_shape():
                pygame.draw.rect(self.screen, temp_piece.color,
                                 (LEFT_MARGIN + GRID_WIDTH * GRID_SIZE + 20 + (x * GRID_SIZE), TOP_MARGIN + 50 + i * (4 * GRID_SIZE) + (y * GRID_SIZE), GRID_SIZE, GRID_SIZE), 0)
        
        # Draw hold piece
        text = font.render("HOLD", True, BLACK)
        self.screen.blit(text, (LEFT_MARGIN - 150, TOP_MARGIN + 20))
        if self.hold_piece:
            temp_piece = self.hold_piece
            for x, y in temp_piece.get_shape():
                pygame.draw.rect(self.screen, temp_piece.color,
                                 (LEFT_MARGIN - 150 + (x * GRID_SIZE), TOP_MARGIN + 60 + (y * GRID_SIZE), GRID_SIZE, GRID_SIZE), 0)
                
        # Draw scoreboard
        text = font.render("Score:", True, BLACK)
        self.screen.blit(text, (LEFT_MARGIN - 150, TOP_MARGIN + 300))
        scoreboard = (self.score)
        text = font.render(str(scoreboard), True, BLACK)
        self.screen.blit(text, (LEFT_MARGIN - 150, TOP_MARGIN + 350))

        # Draw restart button below the hold area
        btn_rect = self.get_restart_button_rect()
        pygame.draw.rect(self.screen, GRAY, btn_rect, 0)
        pygame.draw.rect(self.screen, BLACK, btn_rect, 2)
        btn_font = pygame.font.Font(None, 28)
        btn_text = btn_font.render("Restart", True, BLACK)
        text_rect = btn_text.get_rect(center=btn_rect.center)
        self.screen.blit(btn_text, text_rect)




    def check_collision(self, piece, dx=0, dy=0):
        for x, y in piece.get_shape():
            new_x = piece.x + x + dx
            new_y = piece.y + y + dy

            # First check bounds
            if not (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT):
                return True

            # Then check if cell is occupied
            if self.grid[new_y][new_x] != BLACK:
                return True
        return False


    def lock_piece(self, piece):
        for x, y in piece.get_shape():
            self.grid[piece.y + y][piece.x + x] = piece.color
        self.check_lines()
        self.can_hold = True

    def check_lines(self):
        lines_cleared = 0
        new_grid = [row for row in self.grid if any(cell == BLACK for cell in row)]
        lines_cleared = GRID_HEIGHT - len(new_grid)

        if lines_cleared > 0:
            empty_rows = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(lines_cleared)]
            self.grid = empty_rows + new_grid
            
            # Scoring logic for multiple lines
            if lines_cleared == 1:
                self.score += 100 * self.level
            elif lines_cleared == 2:
                self.score += 300 * self.level
            elif lines_cleared == 3:
                self.score += 500 * self.level
            elif lines_cleared == 4:
                self.score += 800 * self.level

            if self.score // (1000 * self.level) > self.level:
                self.level += 1
                self.fall_speed = max(100, 500 - (self.level - 1) * 50)

    def update(self, dt):
        self.fall_time += dt
        if self.fall_time >= self.fall_speed:
            self.fall_time = 0
            if not self.check_collision(self.active_piece, dy=1):
                self.active_piece.y += 1
            else:
                self.lock_piece(self.active_piece)
                self.active_piece = self.get_next_piece()
                if self.check_collision(self.active_piece):
                    self.game_over = True

    def handle_input(self, events, keys):

        # Process event-based one-shot actions and mouse clicks
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    old_rotation = self.active_piece.rotation
                    self.active_piece.rotate()
                    if self.check_collision(self.active_piece):
                        self.active_piece.rotation = old_rotation
                elif event.key == pygame.K_SPACE:
                    while not self.check_collision(self.active_piece, dy=1):
                        self.active_piece.y += 1
                    self.lock_piece(self.active_piece)
                    self.active_piece = self.get_next_piece()
                    if self.check_collision(self.active_piece):
                        self.game_over = True
                elif event.key == pygame.K_s and self.can_hold:
                    if self.hold_piece:
                        self.hold_piece, self.active_piece = self.active_piece, self.hold_piece
                        self.active_piece.x = GRID_WIDTH // 2 - 2
                        self.active_piece.y = 0
                        self.active_piece.rotation = 0
                    else:
                        self.hold_piece = self.active_piece
                        self.active_piece = self.get_next_piece()
                        self.hold_piece.x = 0
                        self.hold_piece.y = 0
                        self.hold_piece.rotation = 0
                    self.can_hold = False

                elif event.key == pygame.K_DOWN:
                    # Single-step down on press
                    if not self.check_collision(self.active_piece, dy=1):
                        self.active_piece.y += 1
                    self.down_press_time = pygame.time.get_ticks()

                elif event.key == pygame.K_LEFT and not self.check_collision(self.active_piece, dx=-1):
                    self.active_piece.x -= 1
                elif event.key == pygame.K_RIGHT and not self.check_collision(self.active_piece, dx=1):
                    self.active_piece.x += 1

                elif event.key == pygame.K_r:
                    # Keyboard shortcut to restart
                    self.restart()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    self.down_press_time = None
                    self.fall_speed = FALL_SPEED_NORMAL

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Left mouse click: check restart button
                btn_rect = self.get_restart_button_rect()
                if btn_rect.collidepoint(event.pos):
                    self.restart()

        # Continuous key handling (hold-down behavior)
        if keys[pygame.K_DOWN]:
            if self.down_press_time is not None:
                hold_duration = pygame.time.get_ticks() - self.down_press_time
                if hold_duration >= 1000:
                    self.fall_speed = FALL_SPEED_FAST
        else:
            self.fall_speed = FALL_SPEED_NORMAL
    def Game_end(self):
        font = pygame.font.Font(None, 50)
        game_over_text = font.render("GAME OVER", True, BLACK)
        text_rect = game_over_text.get_rect(center=(WIDTH/2, HEIGHT/2))
        self.screen.blit(game_over_text, text_rect)

    def restart(self):
        self.grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.level = 1
        self.fall_time = 0
        self.fall_speed = FALL_SPEED_NORMAL
        self.piece_queue = []
        self.refill_queue()
        self.hold_piece = None
        self.can_hold = True
        self.active_piece = self.get_next_piece()
        self.game_over = False
        self.down_press_time = None





def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()
    game = Tetris(screen)
    
    # Disable key repeat initially. We handle movement with a mix of KEYDOWN and get_pressed.
    pygame.key.set_repeat(0)

    while True:
        # Poll events once per frame and pass them to the game input handler
        events = pygame.event.get()
        keys_pressed = pygame.key.get_pressed()
        game.handle_input(events, keys_pressed)

        # Update game when not over
        dt = clock.tick(60)
        if not game.game_over:
            game.update(dt)

        # Drawing (always draw sidebar so restart button is visible)
        screen.fill(WHITE)
        game.draw_grid()
        game.draw_piece(game.active_piece)
        game.draw_sidebar()
        if game.game_over:
            game.Game_end()

        pygame.display.flip()

main()