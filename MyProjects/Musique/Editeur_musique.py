import sys
import numpy as np
import librosa
import sounddevice as sd
import soundfile as sf
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.widgets import SpanSelector

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QTextEdit, QMessageBox, QLineEdit, QLabel, QSlider, QInputDialog
)
from PyQt5.QtCore import QTimer, Qt
from mutagen.id3 import ID3, TIT2, TRCK, TPE1, APIC, TCON
from PyQt5.QtGui import QPixmap, QIcon
class Editor(QMainWindow):
    def __init__(self, filepath=None):
        super().__init__()
        self.setWindowTitle("Éditeur de Musique")
        self.setWindowIcon(QIcon(r"icon.png"))
        self.setGeometry(100, 100, 1000, 950)

        # Variables audio
        self.current_file = filepath
        self.samples = None
        self.sr = None
        self.cover_data = None  # image brute en bytes
        
        # Variables toujours initialisées
        self.selected_region = None
        self.to_play = None
        self.play_pos = 0
        self.stream = None
        self.selection_rect = None
        self.total_duration = 0.0
        self.time_axis = None
        self.is_looping = False
        self.cursor_text = "Curseur souris: 0:00"

        # --- Layout principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # --- Bloc fichier/actions ---
        file_layout = QHBoxLayout()
        self.btn_open = QPushButton("Ouvrir MP3")
        self.btn_open.clicked.connect(self.select_file)
        file_layout.addWidget(self.btn_open)
        
        self.btn_prev = QPushButton("⏮ Précédent")
        self.btn_prev.clicked.connect(self.load_previous)
        file_layout.addWidget(self.btn_prev)

        self.btn_next = QPushButton("⏭ Suivant")
        self.btn_next.clicked.connect(self.load_next)
        file_layout.addWidget(self.btn_next)

        self.btn_delete = QPushButton("Supprimer sélection")
        self.btn_delete.clicked.connect(self.delete_selection)
        file_layout.addWidget(self.btn_delete)

        self.btn_save = QPushButton("Sauvegarder MP3")
        self.btn_save.clicked.connect(self.save_audio)
        file_layout.addWidget(self.btn_save)
        
        self.btn_batch_vol = QPushButton("Normaliser Batch (-20dB)")
        self.btn_batch_vol.clicked.connect(self.batch_normalize_volumes)
        file_layout.addWidget(self.btn_batch_vol)

        layout.addLayout(file_layout)

        # --- Bloc titre/artiste + image ---
        info_layout = QHBoxLayout()
        text_layout = QVBoxLayout()

        self.title_input = QLineEdit()
        self.artist_input = QLineEdit()
        self.album_input = QLineEdit()
        self.genre_input = QLineEdit()
        self.track_input = QLineEdit()
        text_layout.addWidget(QLabel("Titre:"))
        text_layout.addWidget(self.title_input)
        text_layout.addWidget(QLabel("Artiste:"))
        text_layout.addWidget(self.artist_input)
        text_layout.addWidget(QLabel("Album:"))
        text_layout.addWidget(self.album_input)
        text_layout.addWidget(QLabel("Style / Genre:"))
        text_layout.addWidget(self.genre_input)
        text_layout.addWidget(QLabel("Numéro de piste:"))
        text_layout.addWidget(self.track_input)

        info_layout.addLayout(text_layout)

        # Zone image
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(200, 200)
        self.cover_label.setStyleSheet("border: 1px solid gray;")
        self.cover_label.setScaledContents(True)

        self.btn_change_cover = QPushButton("Changer image")
        self.btn_change_cover.clicked.connect(self.change_cover)

        img_layout = QVBoxLayout()
        img_layout.addWidget(self.cover_label)
        img_layout.addWidget(self.btn_change_cover)
        info_layout.addLayout(img_layout)

        layout.addLayout(info_layout)
    

        # --- Bloc lecture compact : boutons + slider + label ---
        playback_layout = QHBoxLayout()
        self.btn_play = QPushButton("Lire")
        self.btn_play.clicked.connect(lambda: self.play_audio(loop=False))
        playback_layout.addWidget(self.btn_play)
    
        self.btn_pause = QPushButton("Pause")
        self.btn_pause.clicked.connect(self.pause_audio)
        playback_layout.addWidget(self.btn_pause)
    
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.stop_audio)
        playback_layout.addWidget(self.btn_stop)
    
        self.playback_slider = QSlider(Qt.Horizontal)
        self.playback_slider.setMinimum(0)
        self.playback_slider.setMaximum(1000)
        self.playback_slider.sliderReleased.connect(self.slider_released)
        playback_layout.addWidget(self.playback_slider, stretch=1)
    
        self.time_label = QLabel("0:00 / 0:00")
        playback_layout.addWidget(self.time_label)
    
        layout.addLayout(playback_layout)

        # Zone sélection / curseur
        self.cursor_time_text = QTextEdit()
        self.cursor_time_text.setReadOnly(True)
        self.cursor_time_text.setMaximumHeight(50)
        layout.addWidget(self.cursor_time_text)
    
        # Label volume et bouton modifier
        self.volume_label = QLabel("Volume moyen : 0.0 dB")
        layout.addWidget(self.volume_label)
        self.btn_adjust_volume = QPushButton("Modifier volume moyen (dB)")
        self.btn_adjust_volume.clicked.connect(self.adjust_volume_db)
        layout.addWidget(self.btn_adjust_volume)
    
        # Graphe
        self.fig = Figure(figsize=(12,5))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas, stretch=1)
    
        # Timer pour mise à jour temps
        self.timer = QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.update_durations)
        self.timer.start()
    
        # Connexion souris
        self.canvas.mpl_connect("motion_notify_event", self.mouse_move)
    
        # Initialiser le texte du curseur (après avoir défini toutes les variables)
        self.update_cursor_text()
    
        self.canvas.mpl_connect("scroll_event", self.on_scroll)
        self.canvas.mpl_connect("button_press_event", self.on_click)
        # Si un fichier est fourni à l'ouverture
        if filepath:
            self.load_file(filepath)


    # ---------- Sélection fichier ----------
    def select_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Ouvrir un MP3", "", "MP3 Files (*.mp3)")
        if filepath:
            self.load_file(filepath)
            
    def load_file(self, filepath):
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3
        import soundfile as sf
        import os
        self.current_file = os.path.abspath(filepath)
        
        #self.current_file = filepath
        self.setWindowTitle(f"Éditeur de Musique - {filepath}")
    
        # Charger audio avec soundfile
        try:
            self.samples, self.sr = sf.read(filepath, dtype="float32")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger le fichier MP3 : {e}")
            return
    
        self.time_axis = np.arange(len(self.samples)) / self.sr
        self.total_duration = len(self.samples) / self.sr
    
        self.plot_audio()
        self.update_durations()
        self.update_volume_label_db()
    
        # Charger métadonnées
        try:
            audio = MP3(filepath, ID3=ID3)
            if audio.tags is not None:
                # Titre et artiste
                self.title_input.setText(str(audio.get("TIT2", filepath.split("/")[-1])))
                self.artist_input.setText(str(audio.get("TPE1", "Inconnu")))
                self.album_input.setText(str(audio.get("TALB", "Inconnu")))
                self.genre_input.setText(str(audio.get("TCON", "Inconnu")))
                if "TRCK" in audio.tags:
                    self.track_input.setText(str(audio.tags["TRCK"].text[0]))
                else:
                    self.track_input.setText("")  # vide si absent
    
                # Récupérer l’image (champ APIC, peut avoir différents IDs)
                apic = None
                for tag in audio.tags.values():
                    if tag.FrameID == "APIC":
                        apic = tag
                        break
    
                if apic:
                    self.cover_data = apic.data
                    pixmap = QPixmap()
                    if pixmap.loadFromData(self.cover_data):
                        self.cover_label.setPixmap(pixmap)
                    else:
                        self.cover_label.clear()
                else:
                    self.cover_data = None
                    self.cover_label.clear()
            else:
                self.title_input.setText(filepath.split("/")[-1])
                self.artist_input.setText("Inconnu")
                self.cover_label.clear()
        except Exception as e:
            print("Erreur lecture tags:", e)
            self.cover_label.clear()
            
    def get_playlist(self):
        """Récupère la liste des MP3 dans le dossier du fichier actuel."""
        if not self.current_file:
            return [], -1
        
        import os
        directory = os.path.dirname(self.current_file)
        files = [os.path.join(directory, f) for f in os.listdir(directory) 
                 if f.lower().endswith(".mp3")]
        files.sort() # Tri alphabétique
        
        try:
            current_index = files.index(os.path.abspath(self.current_file))
        except ValueError:
            # En cas de chemin relatif/absolu mixé
            current_index = files.index(self.current_file)
            
        return files, current_index

    def load_previous(self):
        files, index = self.get_playlist()
        if index > 0:
            self.stop_audio() # Arrêter la lecture avant de changer
            self.load_file(files[index - 1])
        else:
            QMessageBox.information(self, "Navigation", "C'est la première musique du dossier.")

    def load_next(self):
        files, index = self.get_playlist()
        if index < len(files) - 1:
            self.stop_audio() # Arrêter la lecture avant de changer
            self.load_file(files[index + 1])
        else:
            QMessageBox.information(self, "Navigation", "C'est la dernière musique du dossier.")
            
    def change_cover(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Choisir une image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if filepath:
            with open(filepath, "rb") as f:
                self.cover_data = f.read()
            pixmap = QPixmap()
            pixmap.loadFromData(self.cover_data)
            self.cover_label.setPixmap(pixmap)

    # ---------- Graphe en dB ----------
    def samples_to_db(self, samples):
        eps = 1e-9
        return 20 * np.log10(np.abs(samples) + eps)

    def plot_audio(self):
        self.ax.clear()
        self.ax.plot(self.time_axis, self.samples, linewidth=0.5)
        self.ax.set_xlabel("Temps (s)")
        self.ax.set_ylabel("Amplitude")
        self.ax.set_title("Oscillogramme")
        # Laisser matplotlib ajuster automatiquement l'axe y
        self.span = SpanSelector(
            self.ax, self.onselect_time, 'horizontal', useblit=True,
            props=dict(alpha=0.3, facecolor='red')
        )
        self.canvas.draw()
    
    def on_scroll(self, event):
        """Zoom avec molette sans sortir des limites de la musique"""
        if event.inaxes != self.ax or self.total_duration <= 0:
            return
    
        base_scale = 1.2
        if event.button == 'up':
            scale_factor = 1 / base_scale  # zoom in
        elif event.button == 'down':
            scale_factor = base_scale      # zoom out
        else:
            return
    
        xlim = self.ax.get_xlim()
        center = event.xdata
        width = (xlim[1] - xlim[0]) * scale_factor
        new_left = center - width / 2
        new_right = center + width / 2
    
        # Clamp les limites pour rester dans [0, total_duration]
        if new_left < 0:
            new_left = 0
            new_right = width
        if new_right > self.total_duration:
            new_right = self.total_duration
            new_left = self.total_duration - width
            if new_left < 0:
                new_left = 0  # si on est très petit fichier
        self.ax.set_xlim(new_left, new_right)
        self.canvas.draw_idle()
    
    def on_click(self, event):
        """Reset zoom sur clic molette (milieu)"""
        if event.button == 2 and event.inaxes == self.ax:  # bouton du milieu
            if self.total_duration > 0:
                self.ax.set_xlim(0, self.total_duration)
                self.canvas.draw_idle()

    # ---------- Mise à jour des durées ----------
    def update_durations(self):
        if self.samples is None or self.sr is None:
            elapsed = 0
        else:
            elapsed = self.play_pos / self.sr if self.to_play is not None else 0
    
        total_min = int(self.total_duration) // 60
        total_sec = int(self.total_duration) % 60
    
        elapsed_min = int(elapsed) // 60
        elapsed_sec = int(elapsed) % 60
    
        # Durée sélection
        sel_duration = 0
        if self.selected_region:
            start, end = self.selected_region
            sel_duration = (end - start) / self.sr
    
        sel_min = int(sel_duration) // 60
        sel_sec = int(sel_duration) % 60
    
        # Mettre à jour le QTextEdit du curseur
        self.cursor_time_text.setPlainText(
            f"Sélection: {sel_min}:{sel_sec:02d} / {total_min}:{total_sec:02d}\n{self.cursor_text}"
        )
    
        # Mettre à jour slider
        if self.total_duration > 0:
            pos = int((elapsed / self.total_duration) * 1000)
            self.playback_slider.blockSignals(True)
            self.playback_slider.setValue(pos)
            self.playback_slider.blockSignals(False)
    
        # Mettre à jour label temps
        self.time_label.setText(f"{elapsed_min}:{elapsed_sec:02d} / {total_min}:{total_sec:02d}")
    
        # Mettre à jour curseur sur le graphe si nécessaire
        if hasattr(self, "cursor_line"):
            self.cursor_line.set_xdata(elapsed)
            self.canvas.draw_idle()


    # ---------- Sélection ----------
    def onselect_time(self, tmin, tmax):
        start_idx = int(tmin * self.sr)
        end_idx = int(tmax * self.sr)
        if start_idx < 0: start_idx = 0
        if end_idx > len(self.samples): end_idx = len(self.samples)
        if start_idx >= end_idx:
            return
        self.selected_region = (start_idx, end_idx)

        if self.selection_rect:
            self.selection_rect.remove()
        width = tmax - tmin
        self.selection_rect = self.ax.add_patch(
            plt.Rectangle((tmin, np.min(self.samples)), width,
                          np.max(self.samples)-np.min(self.samples),
                          color='blue', alpha=0.3)
        )
        self.canvas.draw()
        self.update_durations()

    # ---------- Suppression ----------
    def delete_selection(self):
        if self.samples is None or self.selected_region is None:
            QMessageBox.warning(self, "Attention", "Aucune sélection")
            return
        start, end = self.selected_region
        self.samples = np.concatenate([self.samples[:start], self.samples[end:]])
        self.selected_region = None
        if self.selection_rect:
            self.selection_rect.remove()
            self.selection_rect = None

        self.time_axis = np.arange(len(self.samples)) / self.sr
        self.total_duration = len(self.samples) / self.sr
        self.plot_audio()
        self.update_durations()
        self.update_volume_label_db()

    # ---------- Sauvegarde ----------
    def save_audio(self):
        import lameenc
        import numpy as np
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3, TIT2, TRCK, TPE1, TALB, APIC, ID3NoHeaderError
        from PIL import Image
        import io
        from PyQt5.QtWidgets import QMessageBox, QFileDialog

        if self.samples is None or self.sr is None:
            QMessageBox.warning(self, "Attention", "Aucun audio à sauvegarder")
            return

        # 1. Détecter le nombre de canaux (1 si 1D, 2 si 2D)
        num_channels = 1 if self.samples.ndim == 1 else self.samples.shape[1]

        # Nom par défaut
        default_path = (self.current_file or "audio_modifie.mp3")
        if not default_path.endswith(".mp3"):
            default_path += ".mp3"

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder MP3", default_path, "MP3 Files (*.mp3)"
        )
        if not filepath:
            return

        # 2. Préparer les données audio
        data_to_save = self.samples.copy()
        
        # Normalisation si nécessaire (éviter la saturation)
        max_val = np.max(np.abs(data_to_save))
        if max_val > 1:
            data_to_save = data_to_save / max_val

        # 3. Conversion en PCM 16-bit entrelacé
        # .flatten() est crucial pour le stéréo : il met les échantillons L et R côte à côte
        if num_channels > 1:
            pcm_data = (data_to_save * 32767).astype(np.int16).flatten().tobytes()
        else:
            pcm_data = (data_to_save * 32767).astype(np.int16).tobytes()

        # 4. Configuration de l'encodeur LAME
        encoder = lameenc.Encoder()
        encoder.set_bit_rate(192)
        encoder.set_in_sample_rate(self.sr)
        encoder.set_channels(num_channels)
        encoder.set_quality(2)

        try:
            mp3_data = encoder.encode(pcm_data)
            mp3_data += encoder.flush()

            with open(filepath, "wb") as f:
                f.write(mp3_data)

            # 5. Ajouter les métadonnées (Tags ID3)
            try:
                try:
                    audio = MP3(filepath, ID3=ID3)
                except ID3NoHeaderError:
                    audio = MP3(filepath)
                    audio.add_tags()
            
                if audio.tags is None:
                    audio.add_tags()
            
                track_number = self.track_input.text().strip()
                title = self.title_input.text() or "Titre inconnu"
                artist = self.artist_input.text() or "Artiste inconnu"
                album = self.album_input.text() or "Album inconnu"
                genre = self.genre_input.text() or "Inconnu"
            
                audio.tags.add(TRCK(encoding=3, text=track_number))
                audio.tags.add(TIT2(encoding=3, text=title))
                audio.tags.add(TPE1(encoding=3, text=artist))
                audio.tags.add(TALB(encoding=3, text=album))
                audio.tags.add(TCON(encoding=3, text=genre))
            
                # Ajout de la couverture
                if getattr(self, "cover_data", None):
                    img = Image.open(io.BytesIO(self.cover_data))
                    mime = Image.MIME.get(img.format, "image/jpeg")
            
                    audio.tags.add(APIC(
                        encoding=3,
                        mime=mime,
                        type=3,  # Front cover
                        desc="Cover",
                        data=self.cover_data
                    ))
            
                audio.save(v2_version=3)
                QMessageBox.information(self, "Succès", "Fichier sauvegardé avec succès.")
            
            except Exception as e:
                print("Erreur tags:", e)
                QMessageBox.warning(self, "Erreur Métadonnées", f"Audio sauvé mais erreur tags : {e}")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de l'encodage : {e}")
    # ---------- Slider ----------
    def slider_released(self):
        if self.samples is None:
            return
        pos = self.playback_slider.value()
        new_time = (pos / 1000) * self.total_duration
        new_index = int(new_time * self.sr)
        if new_index >= len(self.samples):
            new_index = len(self.samples)-1
        self.play_pos = new_index
        if self.to_play is not None:
            self.to_play = self.samples[self.play_pos:].copy()

    # ---------- Temps ----------
    def update_cursor_text(self):
        # Sélection
        sel_text = "Sélection: "
        if self.selected_region:
            sel_duration = (self.selected_region[1] - self.selected_region[0]) / self.sr
            sel_min = int(sel_duration) // 60
            sel_sec = int(sel_duration) % 60
            sel_text += f"{sel_min}:{sel_sec:02d}"
        else:
            sel_text += "0:00"
    
        # Lecture actuelle
        if self.play_pos != 0:
            elapsed = self.play_pos / self.sr
            elapsed_min = int(elapsed) // 60
            elapsed_sec = int(elapsed) % 60
            total_min = int(self.total_duration) // 60
            total_sec = int(self.total_duration) % 60
        
            # Concaténer avec texte souris
            self.cursor_time_text.setPlainText(f"{sel_text} / {total_min}:{total_sec:02d}\n{self.cursor_text}")
    
    def mouse_move(self, event):
        if event.inaxes != self.ax:
            return
        t = event.xdata
        if t is not None:
            t = max(0, min(t, self.total_duration))
            t_min = int(t) // 60
            t_sec = int(t) % 60
            self.cursor_text = f"Curseur souris: {t_min}:{t_sec:02d}"
            self.update_cursor_text()
    
    def update_progress(self):
        # Mise à jour de la lecture
        if self.samples is None:
            return
        self.update_cursor_text()
        # mettre à jour slider et curseur vert
        elapsed = self.play_pos / self.sr
        pos = int((elapsed / self.total_duration) * 1000)
        self.playback_slider.blockSignals(True)
        self.playback_slider.setValue(pos)
        self.playback_slider.blockSignals(False)
        if hasattr(self, "cursor_line"):
            self.cursor_line.set_xdata(elapsed)
            self.canvas.draw_idle()
    # ---------- Lecture ----------
    def play_audio(self, loop=False):
        if self.samples is None:
            return

        self.is_looping = loop
        
        # Détecter le nombre de canaux (1 si 1D, sinon samples.shape[1])
        num_channels = 1 if self.samples.ndim == 1 else self.samples.shape[1]

        if self.selected_region:
            start, end = self.selected_region
            if self.play_pos < start or self.play_pos >= end:
                self.play_pos = start
            self.to_play = self.samples[self.play_pos:end].copy()
        else:
            if self.to_play is None or len(self.to_play) == 0:
                self.to_play = self.samples[self.play_pos:].copy()

        if self.stream and self.stream.active:
            self.stream.stop()
            self.stream.close()

        def callback(outdata, frames, time, status):
            if status:
                print(status)
            n = min(len(self.to_play), frames)
            
            # Copie adaptée au nombre de canaux
            if num_channels == 1:
                outdata[:n, 0] = self.to_play[:n]
            else:
                outdata[:n, :] = self.to_play[:n, :]
                
            if n < frames:
                outdata[n:frames, :] = 0
                if self.is_looping:
                    # Gestion du loop simplifiée pour l'exemple
                    raise sd.CallbackStop # Ou logique de reset
                else:
                    raise sd.CallbackStop
            self.to_play = self.to_play[n:]
            self.play_pos += n

        # Utiliser num_channels ici
        self.stream = sd.OutputStream(channels=num_channels, samplerate=self.sr, 
                                      callback=callback, blocksize=1024, latency='low')
        self.stream.start()

    def pause_audio(self):
        if self.stream and self.stream.active:
            self.stream.stop()
            self.stream.close()

    def stop_audio(self):
        self.is_looping = False
        if self.stream and self.stream.active:
            self.stream.stop()
            self.stream.close()
        self.play_pos = 0
        self.update_durations()

    # ---------- Volume en dB ----------
    def update_volume_label_db(self):
        if self.samples is not None:
            rms = np.sqrt(np.mean(self.samples**2))
            db = 20 * np.log10(rms + 1e-9)
            self.volume_label.setText(f"Volume moyen : {db:.1f} dB")

    def adjust_volume_db(self):
        if self.samples is None:
            return

        # Calcul RMS compatible Mono et Stéréo
        rms = np.sqrt(np.mean(self.samples**2))
        current_db = 20 * np.log10(rms + 1e-9)
        
        db_shift, ok = QInputDialog.getDouble(
            self, "Modifier volume (dB)",
            f"Volume actuel = {current_db:.1f} dB\nAjouter (+/-) :", 
            value=0.0, decimals=1
        )
        if ok:
            factor = 10 ** (db_shift / 20)
            self.samples *= factor # NumPy applique cela à tous les canaux automatiquement
            self.plot_audio()
            self.update_volume_label_db()
            
    def batch_normalize_volumes(self):
        # 1. Sélection des fichiers
        files, _ = QFileDialog.getOpenFileNames(
            self, "Sélectionner les MP3 à normaliser", "", "MP3 Files (*.mp3)"
        )
        if not files:
            return
    
        target_db = -20.0 # Cible de volume moyen
        
        # Dossier de sortie pour ne pas écraser les originaux par erreur
        output_dir = QFileDialog.getExistingDirectory(self, "Choisir le dossier d'exportation")
        if not output_dir:
            return
    
        import os
        import lameenc
        success_count = 0
    
        for filepath in files:
            try:
                # A. Charger l'audio
                samples, sr = sf.read(filepath, dtype="float32")
                
                # B. Calculer le gain nécessaire
                # RMS actuel
                rms = np.sqrt(np.mean(samples**2))
                if rms < 1e-9: continue # Éviter division par zéro
                
                current_db = 20 * np.log10(rms)
                gain_db = target_db - current_db
                factor = 10 ** (gain_db / 20)
                
                # C. Appliquer le gain
                samples *= factor
                
                # Limiteur simple pour éviter le "clipping" au-dessus de 0dB
                max_val = np.max(np.abs(samples))
                if max_val > 1.0:
                    samples /= max_val
    
                # D. Préparer l'encodage MP3 (Copie de votre logique save_audio)
                num_channels = 1 if samples.ndim == 1 else samples.shape[1]
                if num_channels > 1:
                    pcm_data = (samples * 32767).astype(np.int16).flatten().tobytes()
                else:
                    pcm_data = (samples * 32767).astype(np.int16).tobytes()
    
                encoder = lameenc.Encoder()
                encoder.set_bit_rate(192)
                encoder.set_in_sample_rate(sr)
                encoder.set_channels(num_channels)
                
                mp3_data = encoder.encode(pcm_data) + encoder.flush()
    
                # E. Sauvegarde et transfert des Tags originaux
                filename = os.path.basename(filepath)
                out_path = os.path.join(output_dir, filename)
                
                with open(out_path, "wb") as f:
                    f.write(mp3_data)
    
                # Copie des métadonnées ID3 de l'original vers le nouveau
                from mutagen.mp3 import MP3
                original_audio = MP3(filepath)
                new_audio = MP3(out_path)
                if original_audio.tags:
                    new_audio.tags = original_audio.tags
                    new_audio.save()
    
                success_count += 1
                
            except Exception as e:
                print(f"Erreur sur {filepath}: {e}")
    
        QMessageBox.information(self, "Terminé", f"{success_count} fichiers ont été normalisés dans le dossier cible.")
        
    def closeEvent(self, event):
        # Arrêter la lecture si elle est en cours
        if self.stream and self.stream.active:
            self.stream.stop()
            self.stream.close()
        event.accept()  # fermer la fenêtre normalement

if __name__ == "__main__":
    app = QApplication(sys.argv)
    filepath = None
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    window = Editor(filepath)
    window.show()
    sys.exit(app.exec_())


