import sys
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QFrame)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class ProjectDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Python Projects Hub')
        self.setFixedSize(450, 550)
        self.setStyleSheet("background-color: #1a1a1a;")

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header
        title = QLabel('PYTHON PROJECTS')
        title.setFont(QFont('Segoe UI', 20, QFont.Bold))
        title.setStyleSheet("color: #00d4ff;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #333;")
        layout.addWidget(line)

        # Boutons avec styles différents
        self.add_project_button(layout, "🎮 GAMES MENU", "Jeux", "JEUX.py", "#f04747")
        self.add_project_button(layout, "🧮 CALCULATOR", "Calculatrice", "Calculatrice.py", "#43b581")
        
        # Bouton Musique avec ton dégradé spécifique
        music_gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1d2b64, stop:1 #f8cdda)"
        self.add_project_button(layout, "🎵 MUSIC TOOLS", "Musique", "Music.py", music_gradient)

        # Footer
        footer = QLabel('Declaira - 2026')
        footer.setFont(QFont('Consolas', 9))
        footer.setStyleSheet("color: #444;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addStretch()
        layout.addWidget(footer)

        self.setLayout(layout)

    def add_project_button(self, layout, text, folder, filename, bg_style):
        btn = QPushButton(text)
        btn.setFont(QFont('Segoe UI', 11, QFont.Bold))
        btn.setCursor(Qt.PointingHandCursor)
        
        # Si bg_style commence par 'qlineargradient', on l'utilise directement, 
        # sinon on considère que c'est une couleur simple (hex).
        style = f"""
            QPushButton {{
                background: {bg_style};
                color: white;
                border-radius: 8px;
                padding: 15px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: white;
                color: #1a1a1a;
            }}
        """
        btn.setStyleSheet(style)
        btn.clicked.connect(lambda: self.launch_project(folder, filename))
        layout.addWidget(btn)

    def launch_project(self, folder, filename):
        path = os.path.join(os.path.dirname(__file__), folder, filename)
        if os.path.exists(path):
            try:
                subprocess.Popen(["python", path], cwd=os.path.dirname(path))
            except Exception as e:
                print(f"Error: {e}")
        else:
            print(f"File not found: {path}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ProjectDashboard()
    window.show()
    sys.exit(app.exec_())