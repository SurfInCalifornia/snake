import sys
import random
import signal
import time
import os
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox, QLineEdit, QSpinBox, QStatusBar

signal.signal(signal.SIGINT, signal.SIG_IGN)
try:
    signal.signal(signal.SIGBREAK, signal.SIG_IGN)
except AttributeError:
    pass

DEFAULT_SPEED = 100

class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.snake = []
        self.food = (0, 0)
        self.grid_width = 20
        self.grid_height = 20

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cell_size = int(min(self.width() / self.grid_width, self.height() / self.grid_height))
        for x, y in self.snake[:-1]:
            painter.fillRect(int(x * cell_size), int(y * cell_size), cell_size, cell_size, QColor(0, 128, 0))
        if self.snake:
            hx, hy = self.snake[-1]
            painter.fillRect(int(hx * cell_size), int(hy * cell_size), cell_size, cell_size, QColor(144, 238, 144))
        fx, fy = self.food
        painter.fillRect(int(fx * cell_size), int(fy * cell_size), cell_size, cell_size, QColor(255, 0, 0))

class SnakeGame(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Snake")
        icon_path = os.path.join(os.path.dirname(sys.executable), "_internal", "logo2.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setMinimumWidth(1050)
        self.setMinimumHeight(600)
        self.resize(1050, 600)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.v_layout = QVBoxLayout(self.central_widget)
        self.controls_widget = QWidget()
        self.controls_layout = QHBoxLayout(self.controls_widget)
        self.v_layout.addWidget(self.controls_widget)
        self.canvas = Canvas()
        self.v_layout.addWidget(self.canvas, 1)
        self.lives_label_text = QLabel("Lives:")
        self.controls_layout.addWidget(self.lives_label_text)
        self.lives_start_label = QLabel("Starting Lives:")
        self.controls_layout.addWidget(self.lives_start_label)
        self.lives_input = QLineEdit("3")
        self.lives_input.setFixedWidth(40)
        self.last_valid_lives = 3
        self.lives_input.textChanged.connect(self.update_starting_lives)
        self.controls_layout.addWidget(self.lives_input)
        self.speed_label = QLabel("Move Interval (milliseconds per move):")
        self.controls_layout.addWidget(self.speed_label)
        self.speed_input = QSpinBox()
        self.speed_input.setMinimum(1)
        self.speed_input.setMaximum(999999999)
        self.speed_input.setValue(DEFAULT_SPEED)
        self.speed_input.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.controls_layout.addWidget(self.speed_input)
        self.ai_checkbox = QCheckBox("Enable AI")
        self.controls_layout.addWidget(self.ai_checkbox)
        self.infinite_lives_checkbox = QCheckBox("Infinite Lives")
        self.controls_layout.addWidget(self.infinite_lives_checkbox)
        self.restart_button = QPushButton("Restart")
        self.controls_layout.addWidget(self.restart_button)
        self.pause_button = QPushButton("Start")
        self.controls_layout.addWidget(self.pause_button)
        self.current_score_label = QLabel("Score: 0")
        self.controls_layout.addWidget(self.current_score_label)
        self.snake_length_label = QLabel("Snake Length: 1")
        self.controls_layout.addWidget(self.snake_length_label)
        self.restart_button.clicked.connect(self.reset_game)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.ai_checkbox.stateChanged.connect(self.restart_game_ai_toggle)
        self.infinite_lives_checkbox.stateChanged.connect(self.update_lives_visibility)
        self.speed_input.valueChanged.connect(self.update_speed)
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(DEFAULT_SPEED)
        self.next_move_timer = QTimer()
        self.next_move_timer.timeout.connect(self.update_next_move_label)
        self.next_move_timer.start(30)
        self.canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.canvas.keyPressEvent = self.keyPressEvent
        self.snake = []
        self.food = None
        self.direction = Qt.Key.Key_Right
        self.current_score = 0
        self.starting_lives = int(self.lives_input.text())
        self.current_lives = self.starting_lives
        self.lives_used = 0
        self.is_paused = True
        self.is_alive = True
        self.dead = False
        self.game_started = False
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.next_move_label = QLabel("")
        self.status.addWidget(self.next_move_label)
        self.setStyleSheet("QWidget {background-color:#2e2e2e;color:white;} QPushButton {background-color:black;color:white;border-radius:5px;} QLineEdit{background-color:#3a3a3a;color:white;border-radius:5px;} QCheckBox{color:white;} QSpinBox{background-color:#3a3a3a;color:white;border-radius:5px;}")
        self.reset_game()
        self.canvas.resizeEvent = lambda event:self.canvas.update()
        self.update_lives_visibility()
        self.last_move_timestamp = None
        self.set_button_grayed(self.restart_button, True)
        self.set_button_grayed(self.pause_button, False)

    def set_button_grayed(self, button, grayed):
        if grayed:
            button.setStyleSheet("background-color:#464646;color:white;border-radius:5px;")
            button.setEnabled(False)
        else:
            button.setStyleSheet("QPushButton {background-color:#000000;color:white;border-radius:5px;} QPushButton:hover {background-color:#232323;} QPushButton:pressed {background-color:#333333;}")
            button.setEnabled(True)

    def update_starting_lives(self):
        text = self.lives_input.text()
        if text == "":
            self.set_button_grayed(self.pause_button, True)
            return
        try:
            val = int(text)
            if val < 0: raise ValueError
            if val != self.last_valid_lives: self.last_valid_lives = val
        except ValueError:
            if text != "0": self.lives_input.setText(str(self.last_valid_lives))
            return
        self.starting_lives = max(0, val)
        if self.starting_lives < 1 and not self.game_started:
            self.set_button_grayed(self.pause_button, True)
        else:
            if not self.game_started: self.set_button_grayed(self.pause_button, False)
        if not self.game_started:
            self.current_lives = self.starting_lives
            self.update_ui()

    def update_next_move_label(self):
        if self.game_started and not self.is_paused and self.last_move_timestamp:
            remaining = max(0, self.timer.interval() - int((time.time()-self.last_move_timestamp)*1000))
            self.next_move_label.setText(f"Next move in: {remaining} ms")
        else:
            self.next_move_label.setText("")

    def update_lives_visibility(self):
        infinite = self.infinite_lives_checkbox.isChecked()
        self.lives_input.setVisible(not infinite)
        self.lives_start_label.setVisible(not infinite)
        if self.game_started or self.dead:
            self.lives_input.setEnabled(False)
            self.lives_input.setStyleSheet("QLineEdit {background-color:#494949;color:white;border:1px solid #494949;border-radius:5px;}")
        else:
            self.lives_input.setEnabled(True)
            self.lives_input.setStyleSheet("background-color:#3a3a3a;color:white;border-radius:5px;")
        if infinite:
            self.lives_label_text.setText(f"Lives used: {self.lives_used}")
        else:
            self.lives_label_text.setText(f"Lives: {self.current_lives}")
        self.update_ui()

    def update_speed(self):
        self.timer.stop()
        self.timer.setInterval(self.speed_input.value())
        self.timer.start()

    def reset_game(self):
        self.direction = Qt.Key.Key_Right
        self.snake = [(5,5)]
        self.food = self.spawn_food()
        self.is_alive = True
        self.dead = False
        self.is_paused = True
        self.current_score = 0
        self.lives_used = 0
        self.game_started = False
        if not self.infinite_lives_checkbox.isChecked():
            self.current_lives = self.starting_lives
        self.snake_length_label.setText("Snake Length: 1")
        self.snake_length_label.setEnabled(False)
        self.update_canvas()
        self.update_ui()
        self.last_move_timestamp = None
        self.next_move_label.setText("")
        self.pause_button.setText("Start")
        if self.starting_lives < 1:
            self.set_button_grayed(self.pause_button, True)
        else:
            self.set_button_grayed(self.pause_button, False)
        self.set_button_grayed(self.restart_button, True)
        self.update_lives_visibility()

    def restart_game_ai_toggle(self):
        self.reset_game()

    def toggle_pause(self):
        if not self.game_started and not self.dead:
            self.is_paused = False
            self.pause_button.setText("Pause")
            self.game_started = True
            self.last_move_timestamp = time.time()
            self.set_button_grayed(self.restart_button, False)
            self.update_lives_visibility()
            return
        if self.is_paused:
            self.is_paused = False
            self.pause_button.setText("Pause")
            self.last_move_timestamp = time.time()
        else:
            self.is_paused = True
            self.pause_button.setText("Resume")

    def spawn_food(self):
        width, height = self.grid_width, self.grid_height
        while True:
            pos = (random.randint(0, width-1), random.randint(0, height-1))
            if pos not in self.snake: return pos

    def update_ui(self):
        if self.infinite_lives_checkbox.isChecked():
            self.lives_label_text.setText(f"Lives used: {self.lives_used}")
        else:
            self.lives_label_text.setText(f"Lives: {self.current_lives}")
        self.current_score_label.setText(f"Score: {self.current_score}")
        self.snake_length_label.setText(f"Snake Length: {len(self.snake)}")

    @property
    def grid_width(self): return max(10, self.canvas.width() // 20)
    @property
    def grid_height(self): return max(10, self.canvas.height() // 20)

    def update_canvas(self):
        self.canvas.snake = self.snake
        self.canvas.food = self.food
        self.canvas.grid_width = self.grid_width
        self.canvas.grid_height = self.grid_height
        self.canvas.update()

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier: return
        key = event.key()
        if key == Qt.Key.Key_Up and self.direction != Qt.Key.Key_Down: self.direction = Qt.Key.Key_Up
        elif key == Qt.Key.Key_Down and self.direction != Qt.Key.Key_Up: self.direction = Qt.Key.Key_Down
        elif key == Qt.Key.Key_Left and self.direction != Qt.Key.Key_Right: self.direction = Qt.Key.Key_Left
        elif key == Qt.Key.Key_Right and self.direction != Qt.Key.Key_Left: self.direction = Qt.Key.Key_Right

    def ai_move(self):
        head = self.snake[-1]
        fx, fy = self.food
        hx, hy = head
        dx, dy = fx - hx, fy - hy
        directions = []
        if dx != 0: directions.append(Qt.Key.Key_Right if dx > 0 else Qt.Key.Key_Left)
        if dy != 0: directions.append(Qt.Key.Key_Down if dy > 0 else Qt.Key.Key_Up)
        for d in directions:
            nx, ny = self.next_pos(d)
            if self.is_safe(nx, ny): return d
        for d in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]:
            nx, ny = self.next_pos(d)
            if self.is_safe(nx, ny): return d
        return self.direction

    def next_pos(self, direction):
        x, y = self.snake[-1]
        if direction == Qt.Key.Key_Up: y -= 1
        if direction == Qt.Key.Key_Down: y += 1
        if direction == Qt.Key.Key_Left: x -= 1
        if direction == Qt.Key.Key_Right: x += 1
        return x % self.grid_width, y % self.grid_height

    def is_safe(self, x, y):
        return (x, y) not in self.snake

    def game_loop(self):
        if self.is_paused or not self.is_alive: return
        if self.ai_checkbox.isChecked(): self.direction = self.ai_move()
        nx, ny = self.next_pos(self.direction)
        self.last_move_timestamp = time.time()
        if not self.is_safe(nx, ny):
            if self.infinite_lives_checkbox.isChecked():
                self.lives_used += 1
                self.snake = [(5,5)]
                self.food = self.spawn_food()
                self.snake_length_label.setText("Snake Length: 1")
            else:
                self.current_lives -= 1
                if self.current_lives > 0:
                    self.snake = [(5,5)]
                    self.food = self.spawn_food()
                    self.snake_length_label.setText("Snake Length: 1")
                else:
                    self.is_alive = False
                    self.dead = True
                    self.is_paused = True
                    self.pause_button.setText("Pause")
                    self.set_button_grayed(self.pause_button, True)
                    self.lives_input.setEnabled(False)
                    self.lives_input.setStyleSheet("QLineEdit {background-color:#494949;color:white;border:1px solid #494949;border-radius:5px;}")
            self.update_ui()
            return
        self.snake.append((nx, ny))
        if (nx, ny) == self.food:
            self.food = self.spawn_food()
            self.current_score += 1
        else:
            self.snake.pop(0)
        self.update_canvas()
        self.update_ui()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = SnakeGame()
    game.show()
    sys.exit(app.exec())
