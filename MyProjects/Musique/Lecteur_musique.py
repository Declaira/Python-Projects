import sys, os
import numpy as np
import sounddevice as sd
import soundfile as sf
import keyboard
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,QFrame,
    QPushButton, QFileDialog, QListWidget, QLabel, QSlider, QListWidgetItem, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QSize,QObject, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QIcon,QPainter, QPainterPath
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

from Editeur_musique import Editor

class KeyboardSignals(QObject):
    play_pause = pyqtSignal()
    prev_track = pyqtSignal()
    next_track = pyqtSignal()

class MusicPlayerModern(QMainWindow):
    song_finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.song_finished.connect(self.next_song)
        self.setWindowTitle("Musique")
        self.setWindowIcon(QIcon(r"icon.png"))
        self.setGeometry(100, 100, 1000, 600)
        # ----------------- Style global -----------------
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #1d2b64, stop:1 #f8cdda);
                font-family: 'Poppins', sans-serif;
                color: #fff;
            }

            QLabel {
                color: #fff;
                font-family: 'Poppins', sans-serif;
            }

            QPushButton {
                background-color: rgba(255,255,255,0.15);
                color: #fff;
                border-radius: 12px;
                padding: 10px 16px;
                font-family: 'Poppins', sans-serif;
                font-weight: 600;
                transition: 0.3s;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.25);
            }

            QListWidget {
                background: rgba(0,0,0,0.3);
                color: #fff;
                border-radius: 12px;
                padding: 6px;
                font-family: 'Poppins', sans-serif;
            }
            QListWidget::item:selected {
                background: rgba(255,255,255,0.2);
                border-radius: 8px;
            }

            QSlider::groove:horizontal {
                border: none;
                height: 8px;
                background: rgba(255,255,255,0.3);
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #fff;
                border: none;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #1d2b64, stop:1 #f8cdda);
                border-radius: 4px;
            }
                                            
            QListWidget {
            background: rgba(0,0,0,0.3);   /* fond sombre */
            color: #fff;
            border-radius: 12px;
            padding: 6px;
            font-family: 'Poppins', sans-serif;
            font-weight: bold;   
            }
            
            QListWidget::item:selected {
                background: rgba(255,255,255,0.2);
                border-radius: 8px;
            }
            
            /* Scrollbar verticale */
            QScrollBar:vertical {
                background: transparent;       /* supprime le fond blanc */
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.3);  /* couleur de la poignée */
                min-height: 20px;
                border-radius: 6px;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;    /* supprime les flèches */
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;   /* supprime la zone blanche derrière la poignée */
            }
            
            /* Scrollbar horizontale (si présente) */
            QScrollBar:horizontal {
                background: transparent;
                height: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal {
                background: rgba(255,255,255,0.3);
                min-width: 20px;
                border-radius: 6px;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
            
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)

        # Variables audio
        self.current_file = None
        self.audio_data = None
        self.sr = None
        self.stream = None
        self.play_pos = 0
        self.is_playing = False
        self.volume = 0.3
        self.base_folder = os.getcwd()  # chemin par défaut
        self.songs = []

        # ----------------- Layout -----------------
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QHBoxLayout(main_widget)
        self.main_layout.setContentsMargins(10,10,10,10)

        # ----------------- Navigation Gauche (Dossiers + Musiques) -----------------
        self.left_container = QWidget()
        self.left_layout = QVBoxLayout(self.left_container)
        self.left_layout.setContentsMargins(0,0,0,0)
        
        # 1. Label Dossiers
        self.lbl_folders = QLabel("🎶 Mes Playlists")
        self.lbl_folders.setFont(QFont("Poppins", 11, QFont.Bold))
        self.left_layout.addWidget(self.lbl_folders)

        # 2. Liste des dossiers
        self.folder_list_widget = QListWidget()
        self.folder_list_widget.setFixedHeight(150) 
        self.folder_list_widget.itemClicked.connect(self.on_folder_selected)
        self.left_layout.addWidget(self.folder_list_widget)

        # 3. Bouton Parcourir
        self.btn_browse = QPushButton("Parcourir un autre dossier...")
        self.btn_browse.setFixedHeight(40)
        self.btn_browse.clicked.connect(self.browse_custom_folder)
        self.left_layout.addWidget(self.btn_browse)

        # 4. Ligne de séparation
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: rgba(255,255,255,0.1); margin: 5px 0px;")
        self.left_layout.addWidget(line)

        # 5. Label Musiques
        self.lbl_songs = QLabel("🎵 Musiques")
        self.lbl_songs.setFont(QFont("Poppins", 11, QFont.Bold))
        self.left_layout.addWidget(self.lbl_songs)

        # 6. Liste des musiques
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(40, 40))
        self.list_widget.itemClicked.connect(self.select_song)
        self.left_layout.addWidget(self.list_widget)

        # 7. Bouton Gérer
        self.btn_manage = QPushButton("Gérer les fichiers")
        self.btn_manage.setFixedHeight(40)
        self.btn_manage.clicked.connect(self.open_manage_window)
        self.left_layout.addWidget(self.btn_manage)

        self.main_layout.addWidget(self.left_container, 2)
        # ----------------- Player droite -----------------
        self.right_layout = QVBoxLayout()

                # Layout horizontal pour les deux boutons
        top_buttons_layout = QHBoxLayout()

        
        # Bouton pour masquer la liste
        self.btn_toggle_list = QPushButton("🡸 Masquer la liste")
        self.btn_toggle_list.setFixedHeight(40)
        self.btn_toggle_list.clicked.connect(self.toggle_list)
        top_buttons_layout.addWidget(self.btn_toggle_list, alignment=Qt.AlignLeft)
        
        top_buttons_layout.addStretch(1)
        
        # Bouton pour ouvrir l’éditeur
        self.btn_open_editor = QPushButton("Éditer la musique")
        self.btn_open_editor.setFixedHeight(40)
        self.btn_open_editor.clicked.connect(self.on_open_editor_clicked)
        top_buttons_layout.addWidget(self.btn_open_editor, alignment=Qt.AlignRight)
        
        # Ajouter ce layout en haut de la partie droite
        self.right_layout.addLayout(top_buttons_layout)
        
        # Cover
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(250, 250)
        self.cover_label.setScaledContents(True)
        self.cover_label.setStyleSheet("border: 2px solid #444; border-radius:15px;")
        self.right_layout.addWidget(self.cover_label, alignment=Qt.AlignCenter)

        # Titre / artiste
        self.info_label = QLabel("Titre\nArtiste")
        self.info_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.info_label.setAlignment(Qt.AlignCenter)
        self.right_layout.addWidget(self.info_label)

        # Spacer
        self.right_layout.addSpacerItem(QSpacerItem(20,20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Slider + temps
        slider_layout = QHBoxLayout()
        self.time_elapsed = QLabel("0:00"); self.time_elapsed.setFixedWidth(50)
        self.time_elapsed.setFont(QFont("Arial", 12, QFont.Bold))
        slider_layout.addWidget(self.time_elapsed)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0); self.slider.setMaximum(1000)
        self.slider.sliderReleased.connect(self.slider_moved)
        slider_layout.addWidget(self.slider)

        self.time_total = QLabel("0:00"); self.time_total.setFixedWidth(50)
        self.time_total.setFont(QFont("Arial", 12, QFont.Bold))
        slider_layout.addWidget(self.time_total)
        self.right_layout.addLayout(slider_layout)

        slider_layout = QHBoxLayout()

        # Création du nouveau layout boutons
        btn_layout = QHBoxLayout()
        
        # Bouton précédent
        self.btn_prev = QPushButton("⏮ Précédent")
        self.btn_prev.setFont(QFont("Arial", 12, QFont.Bold))
        self.btn_prev.clicked.connect(self.previous_song)
        btn_layout.addWidget(self.btn_prev)
        
        # Bouton lire/pause (un seul)
        self.to_play = None
        self.btn_play_pause = QPushButton("⏸ Pause")
        self.btn_play_pause.setFont(QFont("Arial", 12, QFont.Bold))
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        btn_layout.addWidget(self.btn_play_pause)
        
        # Bouton suivant
        self.btn_next = QPushButton("Suivant ⏭")
        self.btn_next.setFont(QFont("Arial", 12, QFont.Bold))
        self.btn_next.clicked.connect(self.next_song)
        btn_layout.addWidget(self.btn_next)
        
        self.right_layout.addLayout(btn_layout)

        # Slider volume (sous les boutons)
        volume_layout = QHBoxLayout()
        vol_label = QLabel("Volume"); vol_label.setFixedWidth(60)
        vol_label.setFont(QFont("Arial", 9, QFont.Bold))
        volume_layout.addWidget(vol_label)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0); self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(int(self.volume*100))
        self.volume_slider.sliderMoved.connect(self.change_volume)
        volume_layout.addWidget(self.volume_slider)
        self.right_layout.addLayout(volume_layout)

        self.main_layout.addLayout(self.right_layout, 3)

        # Timer pour slider et temps
        self.timer = QTimer(); self.timer.setInterval(200); self.timer.timeout.connect(self.update_slider)
        self.timer.start()
        self.update_folder_list()

        # ----------------- Raccourcis globaux -----------------
        self.kb_signals = KeyboardSignals()
        self.kb_signals.play_pause.connect(self.toggle_play_pause)
        self.kb_signals.prev_track.connect(self.previous_song)
        self.kb_signals.next_track.connect(self.next_song)

        # Raccourcis via une fonction lambda qui émet le signal
        keyboard.on_press_key("f9", lambda e: self.kb_signals.play_pause.emit())
        keyboard.on_press_key("f8", lambda e: self.kb_signals.prev_track.emit())
        keyboard.on_press_key("f10", lambda e: self.kb_signals.next_track.emit())
    # ----------------- Fonctions principales -----------------
    
    def update_folder_list(self):
        self.folder_list_widget.clear()
        if os.path.exists(self.base_folder):
            # Lister les sous-dossiers
            for name in os.listdir(self.base_folder):
                path = os.path.join(self.base_folder, name)
                if os.path.isdir(path):
                    item = QListWidgetItem(f"📁 {name}")
                    # On stocke le chemin complet dans le "UserRole" pour le récupérer au clic
                    item.setData(Qt.UserRole, path)
                    self.folder_list_widget.addItem(item)

    def on_folder_selected(self, item):
        path = item.data(Qt.UserRole)
        self.lbl_songs.setText(f"🎵 {os.path.basename(path)}")
        self.load_music_from_path(path)

    def browse_custom_folder(self):
        # Ouvre l'explorateur pour choisir un nouveau dossier racine
        new_folder = QFileDialog.getExistingDirectory(self, "Choisir un nouveau dossier racine", self.base_folder)
        
        if new_folder:
            # 1. On change le dossier de base par le nouveau
            self.base_folder = new_folder
            
            # 2. On met à jour l'affichage de la liste des dossiers (Playlists)
            # Note : assurez-vous d'avoir ajouté la méthode update_folder_list() citée précédemment
            self.update_folder_list()
            
            # 3. Optionnel : On change le label pour indiquer où on se trouve
            self.lbl_folders.setText(f"🎶 Dossier : {os.path.basename(new_folder)}")
            
            # 4. On vide la liste des musiques en attendant qu'un sous-dossier soit cliqué
            self.list_widget.clear()
            self.lbl_songs.setText("🎵 Musiques")

    def load_music_from_path(self, folder):
        self.list_widget.clear()
        self.songs.clear()
        self.stop_audio()
        for f in os.listdir(folder):
            if f.lower().endswith(".mp3"):
                filepath = os.path.join(folder, f)
                title, artist, icon = f, "Inconnu", QIcon()
                try:
                    audio = MP3(filepath, ID3=ID3)
                    title = str(audio.get("TIT2", f))
                    artist = str(audio.get("TPE1", "Inconnu"))
                    apic = next((tag for tag in audio.tags.values() if tag.FrameID=="APIC"), None)
                    if apic:
                        pixmap = QPixmap(); pixmap.loadFromData(apic.data)
                        icon = QIcon(pixmap.scaled(40,40,Qt.KeepAspectRatio, Qt.SmoothTransformation))
                except Exception as e:
                    print("Erreur lecture MP3:", e)
                self.songs.append((filepath,title,artist))
                item = QListWidgetItem(f"{title} - {artist}"); item.setIcon(icon)
                self.list_widget.addItem(item)
        if self.songs:
            self.list_widget.setCurrentRow(0)
            self.select_song(self.list_widget.currentItem())


    def select_song(self, item):
        idx = self.list_widget.currentRow()
        filepath, title, artist = self.songs[idx]
        self.current_file = filepath
        self.play_pos = 0
        self.is_playing = False
        self.stop_audio()
    
        # Cover grande
        try:
            audio = MP3(filepath, ID3=ID3)
            apic = next((tag for tag in audio.tags.values() if tag.FrameID=="APIC"), None)
            if apic:
                pixmap = QPixmap()
                pixmap.loadFromData(apic.data)
                self.cover_label.setPixmap(self.rounded_pixmap(pixmap, radius=15))
            else:
                self.cover_label.clear()
        except:
            self.cover_label.clear()
    
        self.info_label.setText(f"{title}\n{artist}")
    
        # Charger audio
        self.audio_data, self.sr = sf.read(filepath, dtype='float32')
        if self.audio_data.ndim > 1:
            self.audio_data = np.mean(self.audio_data, axis=1)
    
        # Durée totale
        total_sec = int(len(self.audio_data)/self.sr)
        min_, sec = divmod(total_sec, 60)
        self.time_total.setText(f"{min_}:{sec:02d}")
    
        # Lancer la lecture immédiatement
        self.play_audio()
    
    def rounded_pixmap(self, pixmap, radius=15):
        size = self.cover_label.size()
        # Redimensionner en remplissant tout en gardant les proportions
        scaled = pixmap.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    
        # Créer une surface transparente
        rounded = QPixmap(size)
        rounded.fill(Qt.transparent)
    
        # Calcul pour centrer l’image
        x = (size.width() - scaled.width()) // 2
        y = (size.height() - scaled.height()) // 2
    
        # Dessiner avec un masque arrondi
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, size.width(), size.height(), radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(x, y, scaled)
        painter.end()
    
        return rounded
    
    def open_manage_window(self):
        try:
            from Gestion_musique import ExplorerWindow
            self.manage_window = ExplorerWindow()
            self.manage_window.show()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible d’ouvrir la fenêtre de gestion:\n{e}")
    
    def open_editor(self, file_path):
        # Crée une instance de l'éditeur et montre-la
        self.editor_window = Editor(file_path)
        self.editor_window.show()

    def on_open_editor_clicked(self):
        # Récupérer la musique sélectionnée
        file_path = self.current_file
        if file_path == None:
            QMessageBox.warning(self, "Attention", "Aucune musique sélectionnée")
            return
        self.open_editor(file_path)
    
        
    def previous_song(self):
        if not self.songs:
            return
        idx = self.list_widget.currentRow()
        idx = max(0, idx-1)
        self.list_widget.setCurrentRow(idx)
        self.select_song(self.list_widget.currentItem())
    
    def next_song(self):
        if not self.songs:
            return
        idx = self.list_widget.currentRow()
        idx = min(len(self.songs)-1, idx+1)
        self.list_widget.setCurrentRow(idx)
        self.select_song(self.list_widget.currentItem())
    
    def toggle_list(self):
        if self.left_container.isVisible():
            self.left_container.hide()
            self.btn_toggle_list.setText("🡺 Afficher la liste")
            self.main_layout.setStretch(0, 0)
            self.main_layout.setStretch(1, 1)
            self.resize(650, self.height())
        else:
            self.left_container.show()
            self.btn_toggle_list.setText("🡸 Masquer la liste")
            self.main_layout.setStretch(0, 2)
            self.main_layout.setStretch(1, 3)
            self.resize(1000, self.height())


    # ----------------- Audio -----------------
    def play_audio(self):
        if self.audio_data is None:
            return
        self.is_playing = True
        self.btn_play_pause.setText("⏸ Pause")
    
        if self.to_play is None or len(self.to_play) == 0:
            self.to_play = self.audio_data[self.play_pos:].copy()
    
        if self.stream and self.stream.active:
            self.stream.stop()
            self.stream.close() 
    
        def callback(outdata, frames, time, status):
            if status:
                print(status)
            if self.play_pos >= len(self.audio_data):
                outdata[:] = 0
                self.is_playing = False
                raise sd.CallbackStop()
            else:
                chunk = self.audio_data[self.play_pos:self.play_pos+frames] * self.volume
                outdata[:len(chunk), 0] = chunk
                if len(chunk) < frames:
                    outdata[len(chunk):frames, 0] = 0
                    self.to_play = None
                    self.is_playing = False
                    # ✅ Utiliser le signal pour prévenir Qt
                    self.song_finished.emit()
                    raise sd.CallbackStop()
                self.play_pos += frames

        self.stream = sd.OutputStream(
            channels=1,
            samplerate=self.sr,
            callback=callback,
            blocksize=1024,
            latency='low'
        )
        self.stream.start()

    def pause_audio(self):
        if self.stream and self.stream.active:
            self.stream.stop()
            self.stream.close()
        self.is_playing = False
        self.btn_play_pause.setText("▶ Lire")

    def stop_audio(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.is_playing = False
        self.play_pos = 0
        self.slider.setValue(0)
        self.time_elapsed.setText("0:00")

    def change_volume(self):
        self.volume = self.volume_slider.value()/100.0

    # ----------------- Slider / temps -----------------
    def update_slider_style(self):
        if self.audio_data is None or len(self.audio_data) == 0:
            return
        value = self.slider.value()
        max_val = self.slider.maximum()
        percent = int((value / max_val) * 100)
    
        style = f"""
            QSlider::groove:horizontal {{
                border: none;
                height: 8px;
                background: rgba(255,255,255,0.3);
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: #fff;                  
                border: none;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #6a11cb, stop:1 #2575fc);
                border-radius: 4px;
            }}
        """
        self.slider.setStyleSheet(style)
        

            
    def update_slider(self):
        if self.audio_data is None or len(self.audio_data) == 0:
            return
    
        # Calcul de la position actuelle
        pos = int((self.play_pos / len(self.audio_data)) * 1000)
        self.slider.blockSignals(True)
        self.slider.setValue(pos)
        self.slider.blockSignals(False)
    
        # Mise à jour du temps écoulé
        elapsed_sec = int(self.play_pos / self.sr)
        min_, sec = divmod(elapsed_sec, 60)
        self.time_elapsed.setText(f"{min_}:{sec:02d}")   
    
        # Style du slider
        self.update_slider_style()
    
        # ✅ Vérifier si on a atteint la fin de la musique
        if self.play_pos >= len(self.audio_data) and self.is_playing:
            self.is_playing = False
            self.song_finished.emit()

    def slider_moved(self):
        if self.audio_data is not None:
            val = self.slider.value()/1000
            self.play_pos = int(val*len(self.audio_data))

    # ----------------- Raccourcis globaux -----------------
    def toggle_play_pause(self):
        if self.is_playing:
            self.pause_audio()
        else:
            self.play_audio()

    def skip_forward(self, seconds=5):
        if self.audio_data is not None:
            self.play_pos += int(seconds*self.sr)
            if self.play_pos > len(self.audio_data)-1:
                self.play_pos = len(self.audio_data)-1

    def skip_backward(self, seconds=5):
        if self.audio_data is not None:
            self.play_pos -= int(seconds*self.sr)
            if self.play_pos < 0:
                self.play_pos = 0

    # ----------------- Fermeture -----------------
    def closeEvent(self, event):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        # Arrêter tous les raccourcis globaux keyboard
        keyboard.unhook_all()
        # Quitter l’application
        event.accept()

if __name__=="__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Poppins", 10)) 
    player = MusicPlayerModern()
    player.show()
    sys.exit(app.exec_())
