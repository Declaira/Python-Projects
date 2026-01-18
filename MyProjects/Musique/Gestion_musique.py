import sys
import os
import shutil
import re
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTreeView, QFileSystemModel,
    QFileDialog, QVBoxLayout, QWidget, QPushButton, QLineEdit,
    QHBoxLayout, QMessageBox, QMenu, QInputDialog, QTextEdit,
    QDockWidget, QCheckBox, QLabel
)
from PyQt5.QtCore import QDir, Qt, QPoint
from PyQt5.QtGui import QIcon
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from Editeur_musique import Editor

# ----------------- Gestion des MP3 -----------------
def get_track_number(filepath, n):
    try:
        audio = EasyID3(filepath)
        track = audio.get("tracknumber", [str(n[0])])[0]
        return int(track.split("/")[0])
    except (ID3NoHeaderError, ValueError, IndexError):
        return n[0]

def corriger_doublons(fichiers_avec_numero):
    numeros_vus = set()
    for i, (track_num, nom_fichier) in enumerate(fichiers_avec_numero):
        while track_num in numeros_vus:
            track_num += 1
        numeros_vus.add(track_num)
        fichiers_avec_numero[i] = (track_num, nom_fichier)
    return fichiers_avec_numero

def nettoyer_nom(nom_sans_ext):
    pattern = r"^\s*(?:\(\s*\d+\s*\)|\[\s*\d+\s*\]|\d+)\s*(?:[-–—._])?\s*"
    return re.sub(pattern, "", nom_sans_ext, count=1)

def renommer_par_numero_de_piste(dossier, extension=".mp3", padding=2):
    import tempfile
    log_messages = []
    fichiers = [f for f in os.listdir(dossier) if f.lower().endswith(extension)]
    if not fichiers:
        return ["❌ Aucun fichier trouvé."]

    # 1. Identifier les fichiers déjà bien nommés (ex: "01 - Titre.mp3") 
    # pour connaître le dernier numéro utilisé
    fichiers_a_traiter = []
    numeros_existants = []
    
    # Pattern pour détecter un début comme "01 - " ou "01. "
    pattern_num = r"^(\d+)\s*[-.]"

    for f in fichiers:
        match = re.match(pattern_num, f)
        if match:
            numeros_existants.append(int(match.group(1)))
        fichiers_a_traiter.append(f)

    # Déterminer le prochain numéro disponible
    prochain_num = max(numeros_existants) + 1 if numeros_existants else 1
    
    mapping_final = {}

    # 2. Préparer le renommage pour les fichiers qui n'ont pas encore le bon format
    # On trie par date de création pour que les derniers téléchargés soient les derniers numérotés
    fichiers_a_traiter.sort(key=lambda x: os.path.getctime(os.path.join(dossier, x)))

    for nom_fichier in fichiers_a_traiter:
        # Si le fichier est déjà numéroté, on vérifie s'il faut le renommer ou pas
        # Ici, on décide de ne renommer QUE ceux qui ne commencent pas par un chiffre
        if not re.match(pattern_num, nom_fichier):
            nom_sans_ext = os.path.splitext(nom_fichier)[0]
            nom_propre = nettoyer_nom(nom_sans_ext)
            
            prefixe = str(prochain_num).zfill(padding)
            nouveau_nom = f"{prefixe} - {nom_propre}{extension}"
            
            mapping_final[nom_fichier] = (nouveau_nom, prochain_num)
            prochain_num += 1

    if not mapping_final:
        return ["info: Tous les fichiers sont déjà numérotés."]

    # 3. Application du renommage (avec noms temporaires pour éviter les conflits)
    for ancien_nom, (nouveau_nom, track_num) in mapping_final.items():
        ancien_chemin = os.path.join(dossier, ancien_nom)
        temp_nom = f"temp_{next(tempfile._get_candidate_names())}{extension}"
        temp_chemin = os.path.join(dossier, temp_nom)
        
        try:
            os.rename(ancien_chemin, temp_chemin)
            nouveau_chemin = os.path.join(dossier, nouveau_nom)
            
            # Mise à jour du tag ID3
            try:
                audio = EasyID3(temp_chemin)
            except ID3NoHeaderError:
                audio = EasyID3()
            
            audio["tracknumber"] = str(track_num)
            audio.save(temp_chemin)
            
            os.rename(temp_chemin, nouveau_chemin)
            log_messages.append(f"✅ {ancien_nom} → {nouveau_nom}")
        except Exception as e:
            log_messages.append(f"❌ Erreur pour {ancien_nom} : {e}")

    return log_messages



# ----------------- Téléchargement YouTube -----------------
# ----------------- Téléchargement via yt-dlp (Intégré) -----------------
import yt_dlp
class MyLogger:
    """Capture les logs de yt-dlp pour les afficher dans l'interface"""
    def __init__(self):
        self.logs = []

    def debug(self, msg):
        # On filtre les messages trop verbeux si besoin, ou on garde tout
        if not msg.startswith('[debug] '):
            self.logs.append(msg)

    def warning(self, msg):
        self.logs.append(f"⚠️ {msg}")

    def error(self, msg):
        self.logs.append(f"❌ {msg}")

def lancer_batch_yt_dlp(batch_path, url, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # On récupère le nom du dossier pour l'utiliser comme "Genre/Style"
    nom_style = os.path.basename(os.path.normpath(output_dir))
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_path = os.path.join(script_dir, "ffmpeg.exe")
    
    logger = MyLogger()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'logger': logger,
        'writethumbnail': True,
        'nocheckcertificate': True,
        'ffmpeg_location': ffmpeg_path,
        'postprocessors': [
            {
                'key': 'FFmpegThumbnailsConvertor',
                'format': 'jpg',
            },
            {
                'key': 'ExecAfterDownload',
                'exec_cmd': f'"{ffmpeg_path}" -i "%(thumbnails.-1.filepath)s" -vf "crop=ih:ih" -y "%(thumbnails.-1.filepath)s"',
            },
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            },
            {
                'key': 'EmbedThumbnail',
            },
        ],
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
    }

    try:
        with yt_dlp.YoutubeDL({'rm_cachedir': True}) as ydl_clean:
            ydl_clean.cache.remove()
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Récupérer les infos avant téléchargement pour connaître le nom du fichier final
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # yt-dlp change l'extension en .mp3 à la fin, on s'adapte
            mp3_path = os.path.splitext(filename)[0] + ".mp3"

        # --- AJOUT : Application du style (nom du dossier) ---
        if os.path.exists(mp3_path):
            try:
                audio = EasyID3(mp3_path)
                audio['genre'] = nom_style
                audio.save()
                logger.logs.append(f"🏷️ Style appliqué : {nom_style}")
            except Exception as e:
                logger.logs.append(f"⚠️ Impossible d'appliquer le style : {e}")
        
        logger.logs.append("✅ Terminé ! MP3 créé avec pochette carrée et style mis à jour.")
    except Exception as e:
        logger.logs.append(f"❌ Erreur : {e}")

    return logger.logs
    
def lancer_batch_yt_dlp2(batch_path, url, output_dir):
    if not os.path.exists(batch_path):
        return [f"❌ Batch non trouvé : {batch_path}"]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    try:
        # Construire la commande : batch_path "url" "output_dir"
        cmd = f'"{batch_path}" "{url}" "{output_dir}"'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

        logs = []
        if result.stdout:
            logs.append(result.stdout)
        if result.stderr:
            logs.append(result.stderr)
        return logs
    except Exception as e:
        return [f"❌ Erreur lors de l'exécution du batch : {e}"]
# ----------------- Modèle avec Track # -----------------
class MusicFileSystemModel(QFileSystemModel):
    def columnCount(self, parent=None):
        return super().columnCount(parent) + 1  # Colonne supplémentaire Track #

    def data(self, index, role=Qt.DisplayRole):
        if index.column() == super().columnCount() and role == Qt.DisplayRole:
            path = self.filePath(index)
            if path.lower().endswith(".mp3"):
                try:
                    audio = EasyID3(path)
                    track = audio.get("tracknumber", [""])[0]
                    return track.split("/")[0]
                except ID3NoHeaderError:
                    return ""
            else:
                return ""
        return super().data(index, role)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return "Nom"
            elif section == 1:
                return "Taille"
            elif section == 2:
                return "Type"
            elif section == 3:
                return "Date de modification"
            elif section == super().columnCount():
                return "Numéro"
        return super().headerData(section, orientation, role)

# ----------------- Explorateur -----------------
class ExplorerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestion de Musique")
        self.setWindowIcon(QIcon(r"icon.png"))
        self.setGeometry(200, 100, 1200, 700)

        # Historique
        self.history = []
        self.history_index = -1
        self.clipboard_path = None

        # Modèle et vue
        self.model = MusicFileSystemModel()
        self.model.setRootPath(QDir.rootPath())

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.rootPath()))
        self.tree.setColumnWidth(0, 350)
        self.tree.setColumnWidth(1, 100)
        self.tree.setColumnWidth(2, 100)
        self.tree.setColumnWidth(3, 150)
        self.tree.setColumnWidth(4, 60)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        self.tree.doubleClicked.connect(self.open_item)  # Double-clic dossier

        # Chemin
        self.path_edit = QLineEdit()
        self.path_edit.returnPressed.connect(self.set_path_from_text)

        # Boutons
        self.back_button = QPushButton("⬅ Retour")
        self.back_button.clicked.connect(self.go_back)
        self.forward_button = QPushButton("➡ Suivant")
        self.forward_button.clicked.connect(self.go_forward)
        self.open_button = QPushButton("Ouvrir un dossier")
        self.open_button.clicked.connect(self.open_folder)
        self.menu_button = QPushButton("☰")
        self.menu_button.setFixedWidth(40)
        self.menu_button.clicked.connect(self.show_current_dir_menu)
        self.log_button = QPushButton("Afficher les logs")
        self.log_button.clicked.connect(self.toggle_logs)

        # YouTube
        self.download_link_edit = QLineEdit()
        self.download_link_edit.setPlaceholderText("Entrez le lien YouTube ici...")
        self.auto_rename_checkbox = QCheckBox("Renommage auto")
        self.auto_rename_checkbox.setChecked(True)
        self.download_button = QPushButton("Télécharger")
        self.download_button.clicked.connect(self.download_music)

        download_layout = QHBoxLayout()
        download_layout.addWidget(QLabel("Lien YouTube :"))
        download_layout.addWidget(self.download_link_edit)
        download_layout.addWidget(self.auto_rename_checkbox)
        download_layout.addWidget(self.download_button)

        # Top layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.back_button)
        top_layout.addWidget(self.forward_button)
        top_layout.addWidget(self.path_edit)
        top_layout.addWidget(self.menu_button)
        top_layout.addWidget(self.open_button)
        top_layout.addWidget(self.log_button)

        # Layout principal
        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addLayout(download_layout)
        layout.addWidget(self.tree)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Logs
        self.log_dock = QDockWidget("Logs", self)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_dock.setWidget(self.log_text)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)
        self.log_dock.hide()

        # Chemin initial
        chemin_de_base = os.getcwd()
        if not os.path.exists(chemin_de_base):
            os.makedirs(chemin_de_base)
        self.set_path(chemin_de_base)

    # -----------------------
    # Navigation
    # -----------------------
    def set_path(self, path, add_to_history=True):
        if QDir(path).exists():
            self.tree.setRootIndex(self.model.index(path))
            self.path_edit.setText(path)
            if add_to_history:
                self.history = self.history[: self.history_index + 1]
                self.history.append(path)
                self.history_index += 1
            self.update_buttons()
        else:
            QMessageBox.warning(self, "Erreur", f"Le chemin n'existe pas :\n{path}")

    def set_path_from_text(self):
        path = self.path_edit.text().strip()
        self.set_path(path)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier", QDir.homePath())
        if folder:
            self.set_path(folder)

    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.set_path(self.history[self.history_index], add_to_history=False)

    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.set_path(self.history[self.history_index], add_to_history=False)

    def update_buttons(self):
        self.back_button.setEnabled(self.history_index > 0)
        self.forward_button.setEnabled(self.history_index < len(self.history) - 1)

    # -----------------------
    # Double clic pour ouvrir dossier
    # -----------------------
    def open_item(self, index):
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self.set_path(path)

    # -----------------------
    # Logs
    # -----------------------
    def append_log(self, messages):
        if isinstance(messages, str):
            self.log_text.append(messages)
        elif isinstance(messages, list):
            for m in messages:
                self.log_text.append(m)
        self.log_text.ensureCursorVisible()

    def toggle_logs(self):
        if self.log_dock.isVisible():
            self.log_dock.hide()
        else:
            self.log_dock.show()

    # -----------------------
    # Menu contextuel et fonctions
    # -----------------------
    def show_current_dir_menu(self):
        pos = self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft())
        self.open_context_menu_in_dir(pos)

    def open_context_menu(self, position: QPoint):
        index = self.tree.indexAt(position)
        if index.isValid():
            file_path = self.model.filePath(index)
            self.open_context_menu_for_file(file_path, self.tree.viewport().mapToGlobal(position))
        else:
            self.open_context_menu_in_dir(self.tree.viewport().mapToGlobal(position))

    def open_context_menu_for_file(self, file_path, position):
        menu = QMenu()
        copy_action = menu.addAction("Copier")
        paste_action = menu.addAction("Coller")
        rename_action = menu.addAction("Renommer")
        delete_action = menu.addAction("Supprimer")
        number_action = menu.addAction("Modifier le numéro (fichier + tag)")
        editor_action = menu.addAction("Éditer musique")
        # Si c'est un dossier, ajouter l'option de renommage automatique
        batch_rename_action = None
        if os.path.isdir(file_path):
            batch_rename_action = menu.addAction("Renommer les musiques (auto)")

        paste_action.setEnabled(self.clipboard_path is not None)
        action = menu.exec_(position)

        if action == copy_action:
            self.clipboard_path = file_path
        elif action == paste_action and self.clipboard_path:
            self.paste_file(file_path)
        elif action == rename_action:
            self.rename_file(file_path)
        elif action == delete_action:
            self.delete_file(file_path)
        elif action == number_action:
            self.change_track_number(file_path)
        elif action == editor_action:
            self.open_editor(file_path)
        elif batch_rename_action and action == batch_rename_action:
            self.auto_rename_folder(file_path)

    def open_context_menu_in_dir(self, global_pos):
        menu = QMenu()
        paste_action = menu.addAction("Coller")
        download_action = menu.addAction("Télécharger playlist")
        new_folder_action = menu.addAction("Nouveau dossier")
        rename_folder_action = menu.addAction("Renommer les musiques (auto)")
        paste_action.setEnabled(self.clipboard_path is not None)

        action = menu.exec_(global_pos)
        current_dir = self.path_edit.text().strip()

        if action == paste_action and self.clipboard_path:
            self.paste_file(current_dir)
        elif action == download_action:
            self.download_playlist()
        elif action == new_folder_action:
            self.create_new_folder(current_dir)
        elif action == rename_folder_action:
            self.auto_rename_folder(current_dir)

    # -----------------------
    # Fonctions fichiers
    # -----------------------
    def paste_file(self, target_path):
        try:
            target_dir = target_path
            if os.path.isfile(target_path):
                target_dir = os.path.dirname(target_path)

            base_name = os.path.basename(self.clipboard_path)
            dest_path = os.path.join(target_dir, base_name)

            if os.path.abspath(self.clipboard_path) == os.path.abspath(dest_path) or os.path.exists(dest_path):
                name, ext = os.path.splitext(base_name)
                counter = 1
                new_name = f"{name} - copie{ext}"
                dest_path = os.path.join(target_dir, new_name)
                while os.path.exists(dest_path):
                    counter += 1
                    new_name = f"{name} - copie ({counter}){ext}"
                    dest_path = os.path.join(target_dir, new_name)

            if os.path.isfile(self.clipboard_path):
                shutil.copy(self.clipboard_path, dest_path)
            else:
                shutil.copytree(self.clipboard_path, dest_path)

            self.append_log([f"📋 Collé : {dest_path}"])
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de coller :\n{e}")

    def rename_file(self, file_path):
        new_name, ok = QInputDialog.getText(self, "Renommer", "Nouveau nom :", text=os.path.basename(file_path))
        if ok and new_name:
            new_path = os.path.join(os.path.dirname(file_path), new_name)
            try:
                os.rename(file_path, new_path)
                self.append_log([f"✏️ Renommé : {file_path} → {new_path}"])
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de renommer :\n{e}")

    def delete_file(self, file_path):
        reply = QMessageBox.question(
            self, "Supprimer",
            f"Voulez-vous vraiment supprimer :\n{file_path} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                else:
                    shutil.rmtree(file_path)
                self.append_log([f"🗑️ Supprimé : {file_path}"])
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de supprimer :\n{e}")

    def change_track_number(self, file_path):
        base_name = os.path.basename(file_path)
        dir_name = os.path.dirname(file_path)

        match = re.match(r"^(\d+)\s*[-_ ]*\s*(.*)", base_name)
        if match:
            current_num, rest = match.groups()
        else:
            current_num, rest = "", base_name

        track_num = None
        if file_path.lower().endswith(".mp3"):
            try:
                audio = EasyID3(file_path)
                if "tracknumber" in audio:
                    track_num = audio["tracknumber"][0].split("/")[0]
            except ID3NoHeaderError:
                pass

        if track_num and track_num.isdigit():
            current_num = track_num

        new_num, ok = QInputDialog.getInt(self, "Modifier le numéro",
                                          "Nouveau numéro :",
                                          int(current_num) if current_num.isdigit() else 1,
                                          1, 999)
        if ok:
            new_name = f"{new_num:02d} - {rest}"
            new_path = os.path.join(dir_name, new_name)

            try:
                os.rename(file_path, new_path)
                if new_path.lower().endswith(".mp3"):
                    try:
                        audio = EasyID3(new_path)
                    except ID3NoHeaderError:
                        audio = EasyID3()
                        audio.save(new_path)
                        audio = EasyID3(new_path)
                    audio["tracknumber"] = str(new_num)
                    audio.save()
                self.append_log([f"🔢 Numéro modifié : {file_path} → {new_name}"])
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de modifier le numéro :\n{e}")
                
    def open_editor(self, file_path):

        # Crée une instance de l'éditeur et montre-la
        self.editor_window = Editor(file_path)
        self.editor_window.show()

    def auto_rename_folder(self, folder_path):
        log = renommer_par_numero_de_piste(folder_path)
        self.append_log(log)
        QMessageBox.information(self, "Renommage terminé", "\n".join(log))

    def create_new_folder(self, parent_dir):
        folder_name, ok = QInputDialog.getText(self, "Nouveau dossier", "Nom du dossier :")
        if ok and folder_name:
            new_path = os.path.join(parent_dir, folder_name)
            counter = 1
            original_new_path = new_path
            while os.path.exists(new_path):
                new_path = f"{original_new_path} ({counter})"
                counter += 1
            try:
                os.makedirs(new_path)
                self.append_log([f"📂 Nouveau dossier créé : {new_path}"])
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de créer le dossier :\n{e}")

    # -----------------------
    # Téléchargement musique
    # -----------------------
    def download_music(self):
        url = self.download_link_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Attention", "Veuillez entrer un lien YouTube.")
            return

        current_dir = self.path_edit.text().strip()
        batch_path = r"telecharger_musique.bat"

        logs = lancer_batch_yt_dlp(batch_path, url, current_dir)
        self.append_log(logs)

        if self.auto_rename_checkbox.isChecked():
            self.append_log("\n📌 Renommage automatique des MP3 téléchargés...\n")
            logs = renommer_par_numero_de_piste(current_dir)
            self.append_log(logs)
        else:
            self.append_log("ℹ️ Renommage automatique désactivé.")

    def download_playlist(self):
            """Télécharger toutes les musiques d'un fichier texte contenant des liens YouTube."""
            txt_file, _ = QFileDialog.getOpenFileName(self, "Choisir un fichier .txt contenant les liens YouTube", QDir.homePath(), "Fichiers texte (*.txt)")
            if not txt_file:
                return
    
            current_dir = self.path_edit.text().strip()
            batch_path = r"telecharger_musique.bat"
    
            try:
                with open(txt_file, "r", encoding="utf-8") as f:
                    urls = [line.strip() for line in f if line.strip()]
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de lire le fichier :\n{e}")
                return
    
            if not urls:
                QMessageBox.warning(self, "Attention", "Le fichier ne contient aucun lien.")
                return
    
            self.append_log([f"📥 Téléchargement de {len(urls)} musiques depuis la playlist..."])
    
            for i, url in enumerate(urls, start=1):
                self.append_log([f"▶️ ({i}/{len(urls)}) Téléchargement : {url}"])
                logs = lancer_batch_yt_dlp(batch_path, url, current_dir)
                self.append_log(logs)
    
            if self.auto_rename_checkbox.isChecked():
                self.append_log("\n📌 Renommage automatique des MP3 téléchargés...\n")
                logs = renommer_par_numero_de_piste(current_dir)
                self.append_log(logs)
    
            QMessageBox.information(self, "Téléchargement terminé", f"{len(urls)} musiques téléchargées.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExplorerWindow()
    window.show()
    sys.exit(app.exec_())
