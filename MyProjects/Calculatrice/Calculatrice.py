import sys
import os
import math
import csv
import io
import re
import base64
import tempfile
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sympy as sp    
from sympy import symbols, sympify, integrate
from sympy.parsing.sympy_parser import parse_expr

from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QShortcut,
    QPushButton, QLineEdit, QListWidget, QLabel, QMessageBox, QFileDialog,
    QListWidgetItem, QTextEdit, QStackedWidget, QComboBox, QTableWidget, QAction,
    QTableWidgetItem, QHeaderView, QSpinBox, QFormLayout, QGroupBox, QHBoxLayout,
    QSpacerItem, QSizePolicy, QMenu, QSplitter, QColorDialog, QDialog, QCheckBox
)
from PyQt5.QtGui import QPixmap, QFont, QIcon, QColor, QKeySequence
from PyQt5.QtCore import Qt

# -------------------------
# Fonctions utilitaires
# -------------------------
def safe_eval_math(expr):
    """Évaluation sécurisée d'expressions simples via math.*"""
    try:
        e = expr.replace('^', '**').replace('π', 'pi')
        e = e.replace('ln(', 'log(')
        allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("__")}
        allowed.update({'pi': math.pi, 'e': math.e, 'abs': abs, 'np': np})
        return eval(e, {"__builtins__": None}, allowed)
    except Exception as exc:
        raise

def integrale(type_integrale, fonction_str, bornes):
    """Réutilisation de ta fonction d'intégration (sympy)"""
    try:
        if type_integrale == "simple":
            variables = ['x']
        elif type_integrale == "double":
            variables = ['x', 'y']
        elif type_integrale == "triple":
            variables = ['x', 'y', 'z']
        else:
            return "Type d'intégrale non reconnu."

        syms = symbols(variables)
        context = {str(sym): sym for sym in syms}
        expr = parse_expr(fonction_str, local_dict=context)
        result = expr
        for var in reversed(variables):
            a = sympify(bornes[var]['min'], locals=context)
            b = sympify(bornes[var]['max'], locals=context)
            result = integrate(result, (context[var], a, b))
        return str(result)
    except Exception as e:
        return f"Erreur lors du calcul : {str(e)}"

# -------------------------
#%% TableurExcel
class TableurExcel(QWidget):
    def __init__(self, rows=20, cols=10):
        super().__init__()
        self.setWindowTitle("Tableur Excel PyQt5")
        self.resize(800, 600)
        self.rows = rows
        self.cols = cols
        self.cell_formulas = {}
        self.copied_text = ""
        self.drag_start_cell = None
        self.init_ui()
        self.current_canvas = None 
        self.undo_stack = []  # pile pour undo
        self.redo_stack = []  # pile pour redo

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Barre de formule
        self.formula_bar = QLineEdit()
        self.formula_bar.setPlaceholderText("Entrer une formule pour la cellule sélectionnée (ex: =A1+B1)")
        self.formula_bar.returnPressed.connect(self.apply_formula)
        layout.addWidget(self.formula_bar)

        # Import / Export CSV
        hl = QHBoxLayout()
        btn_import = QPushButton("Importer CSV")
        btn_import.clicked.connect(self.import_csv)
        btn_export = QPushButton("Exporter CSV")
        btn_export.clicked.connect(self.export_csv)
        hl.addWidget(btn_import)
        hl.addWidget(btn_export)
        layout.addLayout(hl)

        # Tableur
        self.table = QTableWidget(self.rows, self.cols)
        self.table.setHorizontalHeaderLabels([chr(65+i) for i in range(self.cols)])
        self.table.setVerticalHeaderLabels([str(i+1) for i in range(self.rows)])
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        self.table.cellClicked.connect(self.update_formula_bar)
        self.table.cellChanged.connect(self.on_cell_changed)
        self.table.viewport().installEventFilter(self)
        layout.addWidget(self.table, stretch=1)
        # Zone des graphiques sous le tableur
        self.graph_layout = QVBoxLayout()
        layout.addLayout(self.graph_layout)

        # ---------------- Raccourcis clavier ----------------
        QShortcut(QKeySequence("Ctrl+C"), self, self.copy_cell)
        QShortcut(QKeySequence("Ctrl+X"), self, self.cut_cell)
        QShortcut(QKeySequence("Ctrl+V"), self, self.paste_cell)
        QShortcut(QKeySequence("Delete"), self, self.delete_cells)
        QShortcut(QKeySequence("Ctrl+Z"), self, self.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self.redo)
        
    # ---------------- Barre de formule ----------------
    def update_formula_bar(self, row, col):
        """Affiche dans la barre soit la formule brute, soit le texte brut"""
        key = f"{row},{col}"
        if key in self.cell_formulas:
            self.formula_bar.setText(self.cell_formulas[key])
        else:
            item = self.table.item(row, col)
            self.formula_bar.setText(item.text() if item and item.text().strip() else "")
    
    def apply_formula(self):
        """Applique la formule entrée dans la barre à la cellule sélectionnée"""
        formula = self.formula_bar.text().strip()
        selected = self.table.selectedItems()
        if not selected:
            return
    
        cell = selected[0]
        row, col = cell.row(), cell.column()
        key = f"{row},{col}"
    
        if formula.startswith("="):
            # Stocke la formule brute
            self.cell_formulas[key] = formula
            val = self.evaluate_cell(formula, row, col)
            self.table.blockSignals(True)
            cell.setText(str(val))  # affiche la valeur
            self.table.blockSignals(False)
        else:
            # Pas de formule → valeur brute
            self.cell_formulas.pop(key, None)
            self.table.blockSignals(True)
            cell.setText(formula)
            self.table.blockSignals(False)
    
        # Mets à jour la barre pour rester alignée
        self.formula_bar.setText(formula)
    
        # Recalcul global
        self.recalculate_all()

    # ---------------- Évaluation formules ----------------
    def evaluate_cell(self, formula, row, col):
        expr = formula[1:]  # enlever '='
        expr = expr.replace("^", "**")  # support puissance
    
        # Remplacement des références simples A1, B2, etc.
        def repl_ref(match):
            ref = match.group(0)
            if ":" in ref:  # Cas plage, ex: A1:A5
                start, end = ref.split(":")
                start_col = ord(start[0].upper()) - 65
                start_row = int(start[1:]) - 1
                end_col = ord(end[0].upper()) - 65
                end_row = int(end[1:]) - 1
    
                values = []
                for r in range(start_row, end_row + 1):
                    for c in range(start_col, end_col + 1):
                        key = f"{r},{c}"
                        item = self.table.item(r, c)
                        if key in self.cell_formulas:
                            val = self.evaluate_cell(self.cell_formulas[key], r, c)
                        else:
                            val = float(item.text()) if item and item.text().strip() else 0
                        values.append(float(val))
                return str(values)
            else:
                c = ord(ref[0].upper()) - 65
                r = int(ref[1:]) - 1
                key = f"{r},{c}"
                item = self.table.item(r, c)
                if key in self.cell_formulas:
                    return str(self.evaluate_cell(self.cell_formulas[key], r, c))
                return item.text() if item else "0"
    
        # Remplacement des plages et références simples
        expr = re.sub(r"[A-Z][0-9]+(:[A-Z][0-9]+)?", repl_ref, expr)
    
        # Ajout fonctions autorisées
        local_dict = {
            "SIN": math.sin,
            "COS": math.cos,
            "TAN": math.tan,
            "LOG": math.log,
            "EXP": math.exp,
            "MOYENNE": lambda x: np.mean(np.array(x, dtype=float)),
            "ECARTYPE": lambda x: np.std(np.array(x, dtype=float), ddof=1),
            "math": math,
            "np": np
        }
    
        try:
            return eval(expr, {"__builtins__": None}, local_dict)
        except Exception as e:
            return "#ERR"
        
    def recalculate_all(self):
        """Recalcule toutes les formules du tableur"""
        for key, formula in self.cell_formulas.items():
            row, col = map(int, key.split(","))
            val = self.evaluate_cell(formula, row, col)
            self.table.blockSignals(True)
            self.table.setItem(row, col, QTableWidgetItem(str(val)))
            self.table.blockSignals(False)
    
    def on_cell_changed(self, row, col):
        """Quand l’utilisateur modifie directement une cellule"""
        key = f"{row},{col}"
        item = self.table.item(row, col)
    
        if not item or item.text().strip() == "":
            # Cellule vidée
            self.cell_formulas.pop(key, None)
            self.formula_bar.setText("")
            return
    
        text = item.text().strip()
        if text.startswith("="):
            # Formule entrée directement dans la cellule
            self.cell_formulas[key] = text
            val = self.evaluate_cell(text, row, col)
            self.table.blockSignals(True)
            item.setText(str(val))  # on affiche valeur
            self.table.blockSignals(False)
            self.formula_bar.setText(text)  # on affiche formule brute
        else:
            # Valeur brute
            self.cell_formulas.pop(key, None)
            self.formula_bar.setText(text)
    
        # Recalcule global
        self.recalculate_all()


    # ---------------- Drag & fill ----------------
    def eventFilter(self, source, event):
        if source == self.table.viewport():
            if event.type() == event.MouseButtonPress:
                idx = self.table.indexAt(event.pos())
                if idx.isValid():
                    self.drag_start_cell = (idx.row(), idx.column())
            elif event.type() == event.MouseButtonRelease:
                if self.drag_start_cell:
                    idx = self.table.indexAt(event.pos())
                    if idx.isValid():
                        self.drag_fill_to(idx.row(), idx.column())
                    self.drag_start_cell = None
        return super().eventFilter(source, event)

    def drag_fill_to(self, row, col):
        if not self.drag_start_cell:
            return
        self.save_state()
        start_row, start_col = self.drag_start_cell
        start_item = self.table.item(start_row, start_col)
        if not start_item:
            return
    
        key = f"{start_row},{start_col}"
        value = start_item.text()
        formula = self.cell_formulas.get(key)
    
        row_offset = row - start_row
        col_offset = col - start_col
    
        # Horizontal fill
        if row == start_row and col > start_col:
            for c in range(start_col + 1, col + 1):
                new_key = f"{row},{c}"
                if formula:
                    new_formula = self.shift_formula(formula, 0, c - start_col)
                    self.cell_formulas[new_key] = new_formula
                    val = self.evaluate_cell(new_formula, row, c)
                    self.table.setItem(row, c, QTableWidgetItem(str(val)))
                else:
                    self.table.setItem(row, c, QTableWidgetItem(value))
    
        # Vertical fill
        if col == start_col and row > start_row:
            for r in range(start_row + 1, row + 1):
                new_key = f"{r},{col}"
                if formula:
                    new_formula = self.shift_formula(formula, r - start_row, 0)
                    self.cell_formulas[new_key] = new_formula
                    val = self.evaluate_cell(new_formula, r, col)
                    self.table.setItem(r, col, QTableWidgetItem(str(val)))
                else:
                    self.table.setItem(r, col, QTableWidgetItem(value))
    
        self.recalculate_all()
    
    def shift_formula(self, formula, row_offset, col_offset):
        """Décale les références dans une formule selon les offsets"""
        def repl(match):
            ref = match.group(0)
            col = ord(ref[0].upper()) - 65 + col_offset
            row = int(ref[1:]) - 1 + row_offset
            return f"{chr(65+col)}{row+1}"
        return re.sub(r"[A-Z][0-9]+", repl, formula)


    # ---------------- Mise à jour dynamique quand on change manuellement la cellule ----------------
    def on_cell_changed(self, row, col):
        """Quand l’utilisateur modifie directement une cellule"""
        key = f"{row},{col}"
        item = self.table.item(row, col)
    
        if not item or item.text().strip() == "":
            # Cellule vidée → supprimer la formule et le contenu
            self.cell_formulas.pop(key, None)
            self.formula_bar.setText("")
            return
    
        text = item.text().strip()
        if text.startswith("="):
            # Si l’utilisateur tape une formule directement
            self.cell_formulas[key] = text
            val = self.evaluate_cell(text, row, col)
            self.table.blockSignals(True)
            item.setText(str(val))
            self.table.blockSignals(False)
        else:
            # Sinon → valeur brute
            self.cell_formulas.pop(key, None)
    
        # Mettre à jour la barre de formule avec ce qui est stocké
        if key in self.cell_formulas:
            self.formula_bar.setText(self.cell_formulas[key])
        else:
            self.formula_bar.setText(item.text())
    
        # Recalcul global
        self.recalculate_all()


    # ---------------- Menu contextuel ----------------
    def open_context_menu(self, pos):
        menu = QMenu()
        selected = self.table.selectedItems()
        row = selected[0].row() if selected else 0
        col = selected[0].column() if selected else 0
    
        menu.addAction(QAction("Ajouter ligne", self, triggered=lambda: self.table.insertRow(row+1)))
        menu.addAction(QAction("Ajouter colonne", self, triggered=lambda: self.table.insertColumn(col+1)))
        menu.addAction(QAction("Supprimer ligne", self, triggered=lambda: self.table.removeRow(row)))
        menu.addAction(QAction("Supprimer colonne", self, triggered=lambda: self.table.removeColumn(col)))
        menu.addSeparator()
        menu.addAction(QAction("Copier", self, triggered=self.copy_cell))
        menu.addAction(QAction("Couper", self, triggered=self.cut_cell))
        menu.addAction(QAction("Coller", self, triggered=self.paste_cell))
        menu.addAction(QAction("Supprimer", self, triggered=self.delete_cells))
        menu.addAction(QAction("Créer un graphique", self, triggered=self.create_graph))
        menu.exec_(self.table.viewport().mapToGlobal(pos))
    def copy_cell(self):
        """Copie une ou plusieurs cellules (valeurs et formules)"""
        selected = self.table.selectedRanges()
        if not selected:
            return
        self.save_state()
        sel = selected[0]  # premier bloc sélectionné
        self.copied_text = []
        self.copy_origin = (sel.topRow(), sel.leftColumn())  # sauvegarde position d'origine

        for r in range(sel.topRow(), sel.bottomRow() + 1):
            row_data = []
            for c in range(sel.leftColumn(), sel.rightColumn() + 1):
                key = f"{r},{c}"
                if key in self.cell_formulas:
                    row_data.append(self.cell_formulas[key])  # copie formule brute
                else:
                    item = self.table.item(r, c)
                    row_data.append(item.text() if item else "")
            self.copied_text.append(row_data)

    def cut_cell(self):
        """Coupe une ou plusieurs cellules (copie + efface contenu et formules)"""
        selected = self.table.selectedRanges()
        if not selected:
            return
        self.save_state()
        sel = selected[0]
        self.copied_text = []
        self.copy_origin = (sel.topRow(), sel.leftColumn())  # sauvegarde position d'origine

        for r in range(sel.topRow(), sel.bottomRow() + 1):
            row_data = []
            for c in range(sel.leftColumn(), sel.rightColumn() + 1):
                key = f"{r},{c}"
                if key in self.cell_formulas:
                    row_data.append(self.cell_formulas[key])
                    self.cell_formulas.pop(key, None)
                else:
                    item = self.table.item(r, c)
                    row_data.append(item.text() if item else "")
                self.table.setItem(r, c, QTableWidgetItem(""))  # efface affichage
            self.copied_text.append(row_data)

    def paste_cell(self):
        """Colle les cellules copiées dans la sélection avec ajustement des formules"""
        if not self.copied_text:
            return
        self.save_state()
        selected = self.table.selectedRanges()
        if not selected:
            return

        start_row = selected[0].topRow()
        start_col = selected[0].leftColumn()

        row_offset = start_row - self.copy_origin[0]
        col_offset = start_col - self.copy_origin[1]

        for r, row_data in enumerate(self.copied_text):
            for c, val in enumerate(row_data):
                row = start_row + r
                col = start_col + c
                key = f"{row},{col}"

                if val.startswith("="):
                    # Ajuste la formule copiée
                    new_formula = self.shift_formula(val, row_offset, col_offset)
                    self.cell_formulas[key] = new_formula
                    calc = self.evaluate_cell(new_formula, row, col)
                    self.table.setItem(row, col, QTableWidgetItem(str(calc)))
                else:
                    # sinon texte brut
                    self.cell_formulas.pop(key, None)
                    self.table.setItem(row, col, QTableWidgetItem(val))

        self.recalculate_all()

    def shift_formula(self, formula, row_offset, col_offset):
        """Décale les références dans une formule selon les offsets"""

        def repl(match):
            ref = match.group(0)
            col = ord(ref[0].upper()) - 65 + col_offset
            row = int(ref[1:]) - 1 + row_offset
            if col < 0 or row < 0:
                return ref  # éviter indices négatifs
            return f"{chr(65+col)}{row+1}"

        return re.sub(r"[A-Z][0-9]+", repl, formula)

    def delete_cells(self):
        """Supprime le contenu et les formules de la sélection"""
        self.save_state()
        selected = self.table.selectedRanges()
        if not selected:
            return

        for sel in selected:
            for r in range(sel.topRow(), sel.bottomRow() + 1):
                for c in range(sel.leftColumn(), sel.rightColumn() + 1):
                    key = f"{r},{c}"
                    self.cell_formulas.pop(key, None)
                    self.table.setItem(r, c, QTableWidgetItem(""))

        # Mettre à jour la barre de formule si une cellule est active
        current = self.table.currentItem()
        if current:
            self.formula_bar.setText("")

    def create_graph(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        cols = sorted(list(set(item.column() for item in selected)))
        if len(cols) != 2:
            return
        col_x, col_y = cols
    
        # Récupérer les valeurs X et Y
        x = [self.table.item(r, col_x).text() if self.table.item(r, col_x) else "" for r in range(self.table.rowCount())]
        y = [self.table.item(r, col_y).text() if self.table.item(r, col_y) else "" for r in range(self.table.rowCount())]
        try:
            x = [float(v) for v in x if v.strip() != ""]
            y = [float(v) for v in y if v.strip() != ""]
        except:
            return
    
        label_x = self.table.horizontalHeaderItem(col_x).text() if self.table.horizontalHeaderItem(col_x) else f"Col {col_x+1}"
        label_y = self.table.horizontalHeaderItem(col_y).text() if self.table.horizontalHeaderItem(col_y) else f"Col {col_y+1}"
    
        dlg = QDialog(self)
        dlg.setWindowTitle("Paramètres du graphique")
        layout = QVBoxLayout(dlg)
    
        # Titre
        hl_title = QHBoxLayout()
        hl_title.addWidget(QLabel("Titre:"))
        edit_title = QLineEdit("Graphique")
        hl_title.addWidget(edit_title)
        layout.addLayout(hl_title)
    
        # Labels axes
        hl_labels = QHBoxLayout()
        hl_labels.addWidget(QLabel("Label X:"))
        edit_x = QLineEdit(label_x)
        hl_labels.addWidget(edit_x)
        hl_labels.addWidget(QLabel("Label Y:"))
        edit_y = QLineEdit(label_y)
        hl_labels.addWidget(edit_y)
        layout.addLayout(hl_labels)
    
        # Légende
        hl_legend = QHBoxLayout()
        hl_legend.addWidget(QLabel("Légende:"))
        edit_legend = QLineEdit("")
        hl_legend.addWidget(edit_legend)
        layout.addLayout(hl_legend)
    
        # Couleur
        hl_color = QHBoxLayout()
        hl_color.addWidget(QLabel("Couleur:"))
        combo_color = QComboBox()
        base_colors = ["blue", "red", "green", "orange", "purple", "black", "+"]
        combo_color.addItems(base_colors)
        hl_color.addWidget(combo_color)
        layout.addLayout(hl_color)
    
        # Marker
        hl_marker = QHBoxLayout()
        hl_marker.addWidget(QLabel("Marker:"))
        combo_marker = QComboBox()
        combo_marker.addItems(["-", "+", "x"])
        hl_marker.addWidget(combo_marker)
        layout.addLayout(hl_marker)
    
        # Régression linéaire
        chk_linreg = QCheckBox("Ajouter régression linéaire")
        layout.addWidget(chk_linreg)
    
        # Bouton OK
        btn_ok = QPushButton("OK")
        layout.addWidget(btn_ok)
    
        def draw_graph():
            # Couleur
            color_name = combo_color.currentText()
            if color_name == "+":
                c = QColorDialog.getColor()
                if c.isValid():
                    color_name = c.name()
                    if combo_color.findText(color_name) == -1:
                        combo_color.addItem(color_name)
                    combo_color.setCurrentText(color_name)
    
            marker = combo_marker.currentText()
            linestyle = '-' if marker == '-' else ''
            plot_marker = None if marker == '-' else marker
    
            # Supprimer ancien graph
            if hasattr(self, 'current_canvas') and self.current_canvas:
                self.graph_layout.removeWidget(self.current_canvas)
                self.current_canvas.setParent(None)
                self.current_canvas = None
            if hasattr(self, 'btn_save_png') and self.btn_save_png:
                self.graph_layout.removeWidget(self.btn_save_png)
                self.btn_save_png.setParent(None)
                self.btn_save_png = None
    
            # Créer le graph
            fig = Figure(figsize=(3, 2))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            
            legend_text = edit_legend.text().strip() or None
            ax.plot(x, y, color=color_name, marker=plot_marker, linestyle=linestyle, label=legend_text)
            ax.set_title(edit_title.text())
            ax.set_xlabel(edit_x.text())
            ax.set_ylabel(edit_y.text())
            ax.grid(True)
    
            # Régression linéaire
            if chk_linreg.isChecked() and len(x) > 1:
                coeffs = np.polyfit(x, y, 1)
                a, b = coeffs
                y_fit = a * np.array(x) + b
                ax.plot(x, y_fit, linestyle='--', color='black', label=f"y={a:.2f}x+{b:.2f}")
    
            # Affichage de la légende si texte présent
            if legend_text or chk_linreg.isChecked():
                ax.legend()
    
            # Affichage sous le tableur
            self.current_canvas = FigureCanvas(fig)
            if not hasattr(self, 'graph_layout'):
                self.graph_layout = QVBoxLayout()
                self.layout().addLayout(self.graph_layout)
            self.graph_layout.addWidget(self.current_canvas)
    
            # Bouton save PNG
            self.btn_save_png = QPushButton("Enregistrer PNG")
            self.graph_layout.addWidget(self.btn_save_png)
            self.btn_save_png.clicked.connect(save_png)
    
        def save_png():
            if hasattr(self, 'current_canvas') and self.current_canvas:
                path, _ = QFileDialog.getSaveFileName(self, "Enregistrer PNG", "", "PNG Files (*.png)")
                if path:
                    self.current_canvas.figure.savefig(path)
    
        btn_ok.clicked.connect(lambda: [draw_graph(), dlg.accept()])
        dlg.exec_()

    def save_state(self):
        """Sauvegarde l'état actuel des cellules pour undo"""
        state = {}
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                key = f"{r},{c}"
                item = self.table.item(r, c)
                state[key] = {
                    "text": item.text() if item else "",
                    "formula": self.cell_formulas.get(key, None)
                }
        self.undo_stack.append(state)
        self.redo_stack.clear()  # vider redo à chaque nouvelle action

    def undo(self):
        if not self.undo_stack:
            return
        # sauvegarde état courant pour redo
        state_current = {}
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                key = f"{r},{c}"
                item = self.table.item(r, c)
                state_current[key] = {
                    "text": item.text() if item else "",
                    "formula": self.cell_formulas.get(key, None)
                }
        self.redo_stack.append(state_current)
    
        # restaurer dernier état
        state = self.undo_stack.pop()
        self.restore_state(state)
    
    def redo(self):
        if not self.redo_stack:
            return
        # sauvegarder état courant pour undo
        state_current = {}
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                key = f"{r},{c}"
                item = self.table.item(r, c)
                state_current[key] = {
                    "text": item.text() if item else "",
                    "formula": self.cell_formulas.get(key, None)
                }
        self.undo_stack.append(state_current)
    
        # restaurer état redo
        state = self.redo_stack.pop()
        self.restore_state(state)
    
    def restore_state(self, state):
        """Restaure un état complet des cellules"""
        self.table.blockSignals(True)
        self.cell_formulas.clear()
        for key, val in state.items():
            r, c = map(int, key.split(","))
            if val["formula"]:
                self.cell_formulas[key] = val["formula"]
            self.table.setItem(r, c, QTableWidgetItem(val["text"]))
        self.table.blockSignals(False)
        self.recalculate_all()



    # ---------------- Import / Export CSV ----------------
    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importer CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        with open(path, newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(max(len(r) for r in rows))
        self.table.setHorizontalHeaderLabels([chr(65+i) for i in range(self.table.columnCount())])
        self.table.setVerticalHeaderLabels([str(i+1) for i in range(self.table.rowCount())])
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(val))

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            for r in range(rows):
                writer.writerow([self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(cols)])
#%% API : logique métier
# -------------------------
class API:
    def __init__(self):
        self.pathA = "matriceA.csv"
        self.pathB = "matriceB.csv"
        self.path_resultat = "resultat.csv"
        self.matriceA = self.charger_matrice(self.pathA) or [[0,0],[0,0]]
        self.matriceB = self.charger_matrice(self.pathB) or [[0,0],[0,0]]
        self.matrice_resultat = self.charger_matrice(self.path_resultat) or [[0,0],[0,0]]

    # --- Calculatrice ---
    def calculer(self, expression):
        try:
            res = safe_eval_math(expression)
            return str(res)
        except Exception as e:
            return f"Erreur : {e}"

    # --- Matrices ---
    def charger_matrice(self, filename):
        if not os.path.exists(filename):
            return None
        with open(filename, newline='') as csvfile:
            reader = csv.reader(csvfile)
            return [[float(cell) for cell in row] for row in reader]

    def sauvegarder_matrice(self, matrix, filename):
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(matrix)

    def calcul_matrice(self, A, B, op):
        try:
            A = np.array(A, dtype=float)
            if B is not None and len(B):
                B = np.array(B, dtype=float)

            if op == '+': return (A + B).tolist()
            elif op == '-': return (A - B).tolist()
            elif op == '*': return (A @ B).tolist()
            elif op == 'trace': return float(np.trace(A))
            elif op == 'transpose': return A.T.tolist()
            elif op == 'inverse': return np.linalg.inv(A).tolist()
            elif op == 'det': return float(np.linalg.det(A))
            else: return "Opération non supportée"
        except Exception as e:
            return f"Erreur : {e}"

    # --- Tracé de fonctions ---
    def tracer_fonction(self, params, racines=None):
        # params: dict avec 'fonctions', 'labels', 'couleurs', 'styles', 'titre', 'xlabel', 'ylabel', 'xmin', 'xmax'
        fonctions = params.get('fonctions', [])
        labels = params.get('labels', [])
        couleurs = params.get('couleurs', [])
        styles = params.get('styles', [])
        titre = params.get('titre', '')
        xlabel = params.get('xlabel', '')
        ylabel = params.get('ylabel', '')
        xmin = params.get('xmin', -10)
        xmax = params.get('xmax', 10)
    
        x = np.linspace(xmin, xmax, 1000)
        plt.figure(figsize=(6,4))
        plt.clf()
    
        # Tracer les fonctions
        for i, f_str in enumerate(fonctions):
            try:
                allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("__")}
                allowed.update({
                    'np': np, 'x': x, 'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
                    'exp': np.exp, 'log': np.log, 'sqrt': np.sqrt, 'abs': np.abs
                })
                y = eval(f_str.replace('^','**'), {"__builtins__": None}, allowed)
                label = labels[i] if labels and i < len(labels) else f_str
                couleur = couleurs[i] if couleurs and i < len(couleurs) else 'blue'
                style = styles[i] if styles and i < len(styles) else '-'
                plt.plot(x, y, label=label, color=couleur, linestyle=style)
            except Exception as e:
                plt.plot([], [], label=f"{f_str} (Erreur)")
    
        # 🔹 Ajouter les racines si fournies
        if racines:
            racine_added = False
            for f_str, roots in racines.items():
                if isinstance(roots, (list, tuple, np.ndarray)):
                    for r in roots:
                        try:
                            if xmin <= r <= xmax:
                                plt.scatter(r, 0, color="red", s=60, zorder=5,
                                            label="Racine" if not racine_added else "")
                                racine_added = True
                        except Exception:
                            continue
                else:
                    try:
                        if xmin <= roots <= xmax:
                            plt.scatter(roots, 0, color="red", s=60, zorder=5,
                                        label="Racine" if not racine_added else "")
                            racine_added = True
                    except Exception:
                        pass
    
        plt.title(titre)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
    
        # Sauvegarde dans un buffer pour data URI
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_data = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()
    
        return f"data:image/png;base64,{img_data}"

    # --- Racines ---
    def trouver_racines(self, fonctions, xmin, xmax):
        x = sp.symbols('x')
        racines_resultat = {}
        for f_str in fonctions:
            try:
                f_expr = sp.sympify(f_str)
                f_lambdified = sp.lambdify(x, f_expr, modules=["numpy"])
                X = np.linspace(xmin, xmax, 2000)
                Y = f_lambdified(X)
                racines = []
                for i in range(len(X)-1):
                    if np.isnan(Y[i]) or np.isnan(Y[i+1]):
                        continue
                    if Y[i] * Y[i+1] <= 0:
                        racine = (X[i] + X[i+1]) / 2
                        racines.append(round(racine, 6))
                # dédupliquer proches
                dedup = []
                for r in racines:
                    if not any(abs(r - rr) < 1e-4 for rr in dedup):
                        dedup.append(r)
                racines_resultat[f_str] = dedup
            except Exception as e:
                racines_resultat[f_str] = [f"Erreur : {e}"]
        return racines_resultat

    # --- Régression linéaire ---
    def regression(self, x_list, y_list):
        try:
            x = np.array(x_list, dtype=float)
            y = np.array(y_list, dtype=float)
            A = np.vstack([x, np.ones(len(x))]).T
            m, c = np.linalg.lstsq(A, y, rcond=None)[0]
            # tracer
            plt.figure(figsize=(6,4))
            plt.scatter(x, y, label="données")
            plt.plot(x, m*x + c, label=f"régression: y={m:.4f}x+{c:.4f}")
            plt.legend()
            plt.grid(True)
            path = os.path.join(tempfile.gettempdir(), "os_regression.png")
            plt.savefig(path)
            plt.close()
            equation = f"y = {m:.6f} x + {c:.6f}"
            return equation, path
        except Exception as e:
            return f"Erreur : {e}", None

    # --- Suites récurrentes et export CSV ---
    def calculer_suite(self, termes_initiaux, recurrence, n):
        ordre = 1
        if 'un_2' in recurrence:
            ordre = 3
        elif 'un_1' in recurrence:
            ordre = 2
        if len(termes_initiaux) < ordre:
            return f"Erreur : il faut fournir au moins {ordre} terme(s) initial(aux)."
        suite = list(termes_initiaux[:ordre])
        for i in range(ordre, n):
            local_env = {
                "un": suite[i - 1],
                "un_1": suite[i - 2] if i >= 2 else 0,
                "un_2": suite[i - 3] if i >= 3 else 0,
                "n": i,
                "math": math
            }
            try:
                val = eval(recurrence, {"__builtins__": {}}, local_env)
                suite.append(val)
            except Exception as e:
                return f"Erreur d'évaluation à u{i} : {e}"
        return suite

    def exporter_suite_csv(self, suite, save_path):
        with open(save_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Index", "Valeur"])
            for i, val in enumerate(suite):
                writer.writerow([f"u{i}", val])
        return save_path

# -------------------------
#%% Interface PyQt (toutes pages)
# -------------------------

        
class MainWindow(QWidget):
    def __init__(self, api):
        super().__init__()
        self.api = api
        self.setWindowTitle("Outils Scientifiques")
        self.setWindowIcon(QIcon("calculatrice.ico"))
        self.init_ui()
        self.resize(1200, 800)       # taille initiale (largeur x hauteur)
        self.setMinimumSize(800, 600)  # taille minimale

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        # --- Sidebar ---
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(180)
        self.sidebar.setStyleSheet("""
            QWidget {
                background-color: #333;
            }
            QPushButton {
                background: none;
                border: none;
                color: white;
                padding: 12px 20px;
                text-align: left;
                font-size: 15px;
                border-left: 4px solid transparent;
            }
            QPushButton:hover {
                background-color: #555;
                border-left: 4px solid #4CAF50;
            }
            QPushButton:checked {
                background-color: #555;
                border-left: 4px solid #4CAF50;
            }
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0,20,0,0)
        sidebar_layout.setSpacing(0)  # pas d’espacement supplémentaire
        
        # Liste des pages
        self.pages = QStackedWidget()
        self.buttons = []
        
        onglets = [
            ("🧮 Calculatrice", self.page_calculatrice),
            ("📊 Tableur", self.page_tableur),
            ("📈 Graphe", self.page_graphe),
            ("🔢 Matrice", self.page_matrice),
            ("⏭️ Suite", self.page_suite),
            ("∫ Intégrale", self.page_integrale),
        ]
        
        for i, (txt, fn) in enumerate(onglets):
            btn = QPushButton(txt, checkable=True)
            btn.clicked.connect(lambda _, ix=i, b=btn: self.switch_page(ix, b))
            sidebar_layout.addWidget(btn)
            self.buttons.append(btn)
            self.pages.addWidget(fn())
        
        # 🟢 Important : ajouter un espace flexible en bas
        sidebar_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Premier bouton actif
        self.buttons[0].setChecked(True)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.pages)
        
    def switch_page(self, index, btn):
        # Changer de page
        self.pages.setCurrentIndex(index)
    
        # Désélectionner tous les autres
        for b in self.buttons:
            b.setChecked(False)
    
        # Garder seulement celui cliqué
        btn.setChecked(True)

#%% ---------------- Calculatrice ----------------
    def page_calculatrice(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        self.calc_expr = QLineEdit()
        self.calc_expr.setPlaceholderText("Entrez un calcul...")
        self.calc_expr.setFixedHeight(36)
        layout.addWidget(self.calc_expr)

        # boutons grille
        grid = QGridLayout()
        buttons = [
            '7','8','9','/',
            '4','5','6','*',
            '1','2','3','-',
            '.','0','e','+',
            '(' ,')','π','^',
            'sin(','cos(','tan(','←',
            'asin(','acos(','atan(','C',
            'log(','ln(','exp(','='
        ]
        positions = [(i,j) for i in range(8) for j in range(4)]
        for pos, txt in zip(positions, buttons):
            btn = QPushButton(txt)
            btn.setFixedHeight(38)
            if txt == '=':
                btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight:bold;")
            elif txt == 'C':
                btn.setStyleSheet("background-color: #f44336; color: white;")
            btn.clicked.connect(lambda ch, t=txt: self.handle_calc_button(t))
            grid.addWidget(btn, *pos)
        layout.addLayout(grid)

        # historique calculatrice
        hist_label = QLabel("Historique")
        hist_label.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(hist_label)
        self.calc_history = QListWidget()
        self.calc_history.itemDoubleClicked.connect(self.on_history_double)
        layout.addWidget(self.calc_history, stretch=1)

        self.calc_expr.returnPressed.connect(lambda: self.handle_calc_button('='))
        return w

    def handle_calc_button(self, token):
        if token == 'C':
            self.calc_expr.clear()
            return
        if token == '←':
            txt = self.calc_expr.text()
            self.calc_expr.setText(txt[:-1])
            return
        if token == '=':
            expr = self.calc_expr.text().strip()
            if not expr:
                return
            res = self.api.calculer(expr)
            display = f"{expr} = {res}"
            # ➝ ajouter dans l’historique uniquement
            self.calc_history.insertItem(0, display)
            # ➝ vider la barre d’entrée
            self.calc_expr.clear()
            return
        if token == 'log(':
            token = 'log10('

        # insérer le token au curseur
        cur = self.calc_expr.cursorPosition()
        txt = self.calc_expr.text()
        new = txt[:cur] + token + txt[cur:]
        self.calc_expr.setText(new)
        self.calc_expr.setCursorPosition(cur + len(token))

    def on_history_double(self, item):
        text = item.text()
        if '=' in text:
            # ➝ injecter uniquement le résultat
            res = text.split('=')[-1].strip()
            self.calc_expr.setText(res)
        else:
            self.calc_expr.setText(text)

#%% ---------------- Matrices ----------------
    def page_matrice(self):
        w = QWidget(); layout = QVBoxLayout(w)
    
        # --- Dimensions dynamiques ---
        dim_layout = QHBoxLayout()
        dim_layout.addWidget(QLabel("Lignes:"))
        self.rows_spin = QSpinBox(); self.rows_spin.setMinimum(1); self.rows_spin.setValue(2)
        dim_layout.addWidget(self.rows_spin)
        dim_layout.addWidget(QLabel("Colonnes:"))
        self.cols_spin = QSpinBox(); self.cols_spin.setMinimum(1); self.cols_spin.setValue(2)
        dim_layout.addWidget(self.cols_spin)
        btn_set_dim = QPushButton("Appliquer dimensions")
        btn_set_dim.clicked.connect(self.apply_matrix_dimensions)
        dim_layout.addWidget(btn_set_dim)
        layout.addLayout(dim_layout)
    
        # Table A / B
        box = QHBoxLayout()
    
        # Matrice A
        groupA = QGroupBox("Matrice A")
        vA = QVBoxLayout()
        self.tableA = QTableWidget(2,2)
        self.tableA.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableA.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        vA.addWidget(self.tableA)
        btn_loadA = QPushButton("Charger A (CSV)"); btn_loadA.clicked.connect(self.load_matrixA)
        btn_saveA = QPushButton("Sauvegarder A"); btn_saveA.clicked.connect(self.save_matrixA)
        vA.addWidget(btn_loadA); vA.addWidget(btn_saveA)
        groupA.setLayout(vA)
        box.addWidget(groupA)
    
        # Matrice B
        groupB = QGroupBox("Matrice B")
        vB = QVBoxLayout()
        self.tableB = QTableWidget(2,2)
        self.tableB.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableB.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        vB.addWidget(self.tableB)
        btn_loadB = QPushButton("Charger B (CSV)"); btn_loadB.clicked.connect(self.load_matrixB)
        btn_saveB = QPushButton("Sauvegarder B"); btn_saveB.clicked.connect(self.save_matrixB)
        vB.addWidget(btn_loadB); vB.addWidget(btn_saveB)
        groupB.setLayout(vB)
        box.addWidget(groupB)
    
        layout.addLayout(box)
    
        # Opérations
        ops_layout = QHBoxLayout()
        self.op_combo = QComboBox()
        self.op_combo.addItems(['+', '-', '*', 'transpose', 'inverse', 'det', 'trace'])
        ops_layout.addWidget(QLabel("Opération"))
        ops_layout.addWidget(self.op_combo)
        btn_calc = QPushButton("Calculer"); btn_calc.clicked.connect(self.compute_matrix_op)
        ops_layout.addWidget(btn_calc)
        layout.addLayout(ops_layout)
    
        # Résultat
        self.matrix_result = QTableWidget(2,2)
        self.matrix_result.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.matrix_result.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("Résultat"))
        layout.addWidget(self.matrix_result)
    
        # Remplir par défaut
        self.fill_table(self.tableA, self.api.matriceA)
        self.fill_table(self.tableB, self.api.matriceB)
        
        # Bouton sauvegarde résultat
        btn_save_result = QPushButton("Sauvegarder Résultat (CSV)")
        btn_save_result.clicked.connect(self.save_matrix_result)
        layout.addWidget(btn_save_result)
        

    
        return w
    
    # ---------------- Fonction de sauvegarde ----------------
    def save_matrix_result(self):
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer Résultat", "resultat.csv", "CSV Files (*.csv)")
        if path:
            rows = self.matrix_result.rowCount()
            cols = self.matrix_result.columnCount()
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                for i in range(rows):
                    row_data = []
                    for j in range(cols):
                        item = self.matrix_result.item(i, j)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Succès", "Matrice résultat sauvegardée avec succès !")    
    # ------------------------
    # Appliquer les dimensions
    # ------------------------
    def apply_matrix_dimensions(self):
        rows = self.rows_spin.value()
        cols = self.cols_spin.value()
        self.tableA.setRowCount(rows)
        self.tableA.setColumnCount(cols)
        self.tableB.setRowCount(rows)
        self.tableB.setColumnCount(cols)
    
    def fill_table(self, table: QTableWidget, matrix):
        rows = len(matrix)
        cols = len(matrix[0]) if rows else 0
        table.setRowCount(rows)
        table.setColumnCount(cols)
        for i in range(rows):
            for j in range(cols):
                table.setItem(i, j, QTableWidgetItem(str(matrix[i][j])))

    def read_table(self, table: QTableWidget):
        rows = table.rowCount()
        cols = table.columnCount()
        m = []
        for i in range(rows):
            row = []
            for j in range(cols):
                it = table.item(i, j)
                if it is None or it.text() == '':
                    row.append(0.0)
                else:
                    try:
                        row.append(float(it.text()))
                    except:
                        row.append(it.text())
                # note: we keep non-floats but API expects floats
            m.append(row)
        return m

    def load_matrixA(self):
        path, _ = QFileDialog.getOpenFileName(self, "Charger matrice A", "", "CSV Files (*.csv);;All Files (*)")
        if not path: return
        mat = []
        with open(path, newline='') as f:
            r = csv.reader(f)
            for row in r:
                mat.append([float(c) for c in row])
        self.fill_table(self.tableA, mat)

    def load_matrixB(self):
        path, _ = QFileDialog.getOpenFileName(self, "Charger matrice B", "", "CSV Files (*.csv);;All Files (*)")
        if not path: return
        mat = []
        with open(path, newline='') as f:
            r = csv.reader(f)
            for row in r:
                mat.append([float(c) for c in row])
        self.fill_table(self.tableB, mat)

    def save_matrixA(self):
        mat = self.read_table(self.tableA)
        path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder matrice A", "matriceA.csv", "CSV Files (*.csv)")
        if not path: return
        self.api.sauvegarder_matrice(mat, path)
        QMessageBox.information(self, "Sauvegarde", f"Matrice A sauvegardée : {path}")

    def save_matrixB(self):
        mat = self.read_table(self.tableB)
        path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder matrice B", "matriceB.csv", "CSV Files (*.csv)")
        if not path: return
        self.api.sauvegarder_matrice(mat, path)
        QMessageBox.information(self, "Sauvegarde", f"Matrice B sauvegardée : {path}")

    def compute_matrix_op(self):
        A = self.read_table(self.tableA)
        B = self.read_table(self.tableB)
        op = self.op_combo.currentText()
        res = self.api.calcul_matrice(A, B, op)
        if isinstance(res, str):
            QMessageBox.warning(self, "Erreur", str(res))
            return
        # afficher résultat
        if isinstance(res, (int, float)):
            # scalar result
            self.matrix_result.setRowCount(1)
            self.matrix_result.setColumnCount(1)
            self.matrix_result.setItem(0,0, QTableWidgetItem(str(res)))
        else:
            self.fill_table(self.matrix_result, res)

#%% ---------------- Intégrales ----------------
    def page_integrale(self):
        w = QWidget()
        layout = QVBoxLayout(w)
    
        # Type d'intégrale
        hl_type = QHBoxLayout()
        hl_type.addWidget(QLabel("Type d'intégrale :"))
        self.int_type = QComboBox()
        self.int_type.addItems(["simple", "double", "triple"])
        hl_type.addWidget(self.int_type)
        hl_type.addStretch()
        layout.addLayout(hl_type)
    
        # Bornes dynamiques avec affichage style intégrale
        self.bornes_group = QGroupBox("Bornes")
        self.bornes_layout = QVBoxLayout()
        self.bornes_group.setLayout(self.bornes_layout)
        layout.addWidget(self.bornes_group)
    
        self.int_type.currentTextChanged.connect(self.update_bornes_fields)
        self.update_bornes_fields("simple")
    
        # Bouton calcul
        btn_calc = QPushButton("Calculer")
        btn_calc.clicked.connect(self.compute_integrale)
        layout.addWidget(btn_calc)
    
        # Résultat
        layout.addWidget(QLabel("Résultat"))
        self.int_result = QTextEdit()
        self.int_result.setReadOnly(True)
        layout.addWidget(self.int_result)
    
        return w
    
    # ------------------------
    # Mise à jour bornes avec symbole ∫
    # ------------------------
    def update_bornes_fields(self, t):
        # clear
        for i in reversed(range(self.bornes_layout.count())):
            widget = self.bornes_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
    
        variables = []
        if t == "simple": variables = ['x']
        elif t == "double": variables = ['x','y']
        elif t == "triple": variables = ['x','y','z']
    
        self.borne_inputs = {}
    
        # Layout horizontal principal pour aligner toutes les intégrales
        hl_total = QHBoxLayout()
        hl_total.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    
        # Pour chaque variable, créer le symbole ∫ avec bornes
        for v in variables:
            vl = QVBoxLayout()
            max_in = QLineEdit(); max_in.setFixedWidth(60); max_in.setPlaceholderText("max")
            min_in = QLineEdit(); min_in.setFixedWidth(60); min_in.setPlaceholderText("min")
            lbl_int = QLabel("∫"); lbl_int.setAlignment(Qt.AlignHCenter)
            vl.addWidget(max_in)
            vl.addWidget(lbl_int)
            vl.addWidget(min_in)
            hl_total.addLayout(vl)
    
            # Stocker les entrées
            self.borne_inputs[v] = {'min': min_in, 'max': max_in}
    
        # Entrée fonction juste après les symboles ∫
        self.int_fonction = QLineEdit()
        self.int_fonction.setPlaceholderText("Fonction à intégrer")
        self.int_fonction.setFixedWidth(200)
        hl_total.addWidget(self.int_fonction)
    
        # Différentiels dx, dy, dz alignés à droite de la fonction
        for v in variables:
            lbl_dx = QLabel(f"d{v}")
            lbl_dx.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            hl_total.addWidget(lbl_dx)
    
        container = QWidget()
        container.setLayout(hl_total)
        self.bornes_layout.addWidget(container)

    
    def compute_integrale(self):
        t = self.int_type.currentText()
        f = self.int_fonction.text().strip()
        if not f:
            QMessageBox.warning(self, "Erreur", "Indiquez la fonction.")
            return
        bornes = {}
        for v, widgets in self.borne_inputs.items():
            a = widgets['min'].text().strip()
            b = widgets['max'].text().strip()
            if a == '' or b == '':
                QMessageBox.warning(self, "Erreur", f"Bornes manquantes pour {v}.")
                return
            bornes[v] = {'min': a, 'max': b}
        res = integrale(t, f, bornes)
        self.int_result.setText(str(res))


#%% ---------------- Graphes ----------------
    def page_graphe(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        # ------------------------
        # Paramètres généraux : titre, axes, xlim/ylim
        # ------------------------
        form = QFormLayout()
        self.g_title = QLineEdit("Titre du graphique")
        form.addRow("Titre :", self.g_title)
        self.g_xlabel = QLineEdit("X")
        form.addRow("Axe X :", self.g_xlabel)
        self.g_ylabel = QLineEdit("Y")
        form.addRow("Axe Y :", self.g_ylabel)
        
        hl_xlim = QHBoxLayout()
        self.g_xmin = QLineEdit("-10"); self.g_xmin.setFixedWidth(80)
        self.g_xmax = QLineEdit("10"); self.g_xmax.setFixedWidth(80)
        hl_xlim.addWidget(QLabel("xmin:")); hl_xlim.addWidget(self.g_xmin)
        hl_xlim.addWidget(QLabel("xmax:")); hl_xlim.addWidget(self.g_xmax)
        form.addRow("Limites X :", hl_xlim)
        
        hl_ylim = QHBoxLayout()
        self.g_ymin = QLineEdit("-10"); self.g_ymin.setFixedWidth(80)
        self.g_ymax = QLineEdit("10"); self.g_ymax.setFixedWidth(80)
        hl_ylim.addWidget(QLabel("ymin:")); hl_ylim.addWidget(self.g_ymin)
        hl_ylim.addWidget(QLabel("ymax:")); hl_ylim.addWidget(self.g_ymax)
        form.addRow("Limites Y :", hl_ylim)
        
        layout.addLayout(form)

        # ------------------------
        # Liste dynamique des fonctions
        # ------------------------
        self.func_entries_layout = QVBoxLayout()
        layout.addLayout(self.func_entries_layout)
        self.func_entries = []

        def add_function_entry(formula="", color="blue", marker="", label=""):
            entry_layout = QHBoxLayout()
            # bouton supprimer
            btn_remove = QPushButton("–"); btn_remove.setFixedWidth(30)
            entry_layout.addWidget(btn_remove)
            # formule
            le_formula = QLineEdit(formula); le_formula.setPlaceholderText("Ex: sin(x)")
            entry_layout.addWidget(le_formula)
            # couleur
            le_color = QLineEdit(color); le_color.setPlaceholderText("Couleur")
            le_color.setFixedWidth(80)
            entry_layout.addWidget(le_color)
            # marker
            le_marker = QLineEdit(marker); le_marker.setPlaceholderText("Marker")
            le_marker.setFixedWidth(60)
            entry_layout.addWidget(le_marker)
            # label
            le_label = QLineEdit(label); le_label.setPlaceholderText("Label")
            entry_layout.addWidget(le_label)

            container = QWidget()
            container.setLayout(entry_layout)
            self.func_entries_layout.addWidget(container)
            self.func_entries.append((container, le_formula, le_color, le_marker, le_label))

            btn_remove.clicked.connect(lambda: remove_function_entry(container))

        def remove_function_entry(container):
            for i, (c, *_) in enumerate(self.func_entries):
                if c == container:
                    self.func_entries_layout.removeWidget(c)
                    c.setParent(None)
                    self.func_entries.pop(i)
                    break

        # Ajouter première fonction par défaut
        add_function_entry()

        # Bouton ajouter fonction
        btn_add_func = QPushButton("Ajouter fonction +")
        btn_add_func.clicked.connect(lambda: add_function_entry())
        layout.addWidget(btn_add_func)

        # ------------------------
        # Boutons Tracer / Enregistrer
        # ------------------------
        hl_btns = QHBoxLayout()
        btn_plot = QPushButton("Tracer")
        btn_plot.clicked.connect(self.plot_graphs_dynamic)
        btn_save = QPushButton("Enregistrer image")
        btn_save.clicked.connect(self.save_current_plot)
        hl_btns.addWidget(btn_plot); hl_btns.addWidget(btn_save)
        layout.addLayout(hl_btns)

        # ------------------------
        # Graphique + Tableau avec QSplitter
        # ------------------------
        splitter = QSplitter(Qt.Horizontal)

        # Graphique
        self.graph_label = QLabel()
        self.graph_label.setAlignment(Qt.AlignCenter)
        self.graph_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.addWidget(self.graph_label)

        # Tableau racines
        table_container = QWidget()
        vbox = QVBoxLayout(table_container)
        vbox.addWidget(QLabel("Racines trouvées :"))

        self.roots_table = QTableWidget()
        self.roots_table.setColumnCount(2)
        self.roots_table.setHorizontalHeaderLabels(["Fonction", "Racines"])
        self.roots_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.roots_table.setMinimumWidth(200)  # largeur minimale pour lisibilité
        vbox.addWidget(self.roots_table)

        splitter.addWidget(table_container)
        splitter.setSizes([600, 200])  # taille initiale (graph / tableau)

        layout.addWidget(splitter, stretch=1)

        return w


    
    def update_roots_table(self, racines_dict):
        self.roots_table.setRowCount(0)
        for f, roots in racines_dict.items():
            row = self.roots_table.rowCount()
            self.roots_table.insertRow(row)
            self.roots_table.setItem(row, 0, QTableWidgetItem(f))
            if isinstance(roots, list):
                roots_str = ", ".join(str(r) for r in roots) if roots else "Aucune"
            else:
                roots_str = str(roots)
            self.roots_table.setItem(row, 1, QTableWidgetItem(roots_str))
    # ------------------------
    # Fonction pour tracer avec toutes les options
    # ------------------------
    def plot_graphs_dynamic(self):
        # Récupérer toutes les fonctions
        funcs_params = []
        for _, le_formula, le_color, le_marker, le_label in self.func_entries:
            formula = le_formula.text().strip()
            if not formula:
                continue
            color = le_color.text().strip() or "blue"
            marker = le_marker.text().strip()
            label = le_label.text().strip() or formula
            funcs_params.append({
                'fonction': formula,
                'couleur': color,
                'styles': '-', 
                'label': label,
                'marker': marker
            })
    
        if not funcs_params:
            QMessageBox.warning(self, "Erreur", "Aucune fonction fournie.")
            return
    
        # Récupérer les limites
        try:
            xmin = float(self.g_xmin.text()); xmax = float(self.g_xmax.text())
            ymin = float(self.g_ymin.text()); ymax = float(self.g_ymax.text())
        except Exception:
            QMessageBox.warning(self, "Erreur", "Les limites X ou Y sont invalides.")
            return
    
        # Préparer les paramètres pour l'API
        params = {
            'fonctions': [f['fonction'] for f in funcs_params],
            'labels': [f['label'] for f in funcs_params],
            'couleurs': [f['couleur'] for f in funcs_params],
            'styles': [f['styles'] for f in funcs_params],
            'titre': self.g_title.text().strip(),
            'xlabel': self.g_xlabel.text().strip(),
            'ylabel': self.g_ylabel.text().strip(),
            'xmin': xmin,
            'xmax': xmax,
            'ymin': ymin,
            'ymax': ymax
        }
    
        # 🔹 Calcul des racines
        racines_dict = {}
        try:
            racines_dict = self.api.trouver_racines(
                [f['fonction'] for f in funcs_params],
                xmin, xmax
            )
            self.update_roots_table(racines_dict)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de calculer les racines : {e}")
    
        # 🔹 Appeler l'API pour générer le graphique
        try:
            data_uri = self.api.tracer_fonction(params, racines=racines_dict)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la génération du graphique : {e}")
            return
    
        # Vérifier que le résultat est un data URI valide
        if not isinstance(data_uri, str) or not data_uri.startswith("data:image/png;base64,"):
            QMessageBox.warning(self, "Erreur", f"Impossible de générer le graphique : {data_uri}")
            return
    
        # Charger le pixmap depuis le data URI
        try:
            pix = QPixmap()
            pix.loadFromData(base64.b64decode(data_uri.split(",")[1]))
            self.graph_label.setPixmap(pix.scaled(
                self.graph_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du rendu du graphique : {e}")
            return

    def save_current_plot(self):
        pixmap = self.graph_label.pixmap()
        if not pixmap or pixmap.isNull():
            QMessageBox.warning(self, "Erreur", "Aucun plot à enregistrer.")
            return
    
        # Boîte de dialogue pour choisir le chemin d'enregistrement
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer image", "graphique.png", "PNG Files (*.png)"
        )
        if not save_path:
            return
    
        try:
            # Enregistrer directement le QPixmap affiché
            if not pixmap.save(save_path, "PNG"):
                raise Exception("Erreur lors de l'enregistrement")
            QMessageBox.information(self, "Enregistré", f"Graphique sauvegardé : {save_path}")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de sauvegarder l'image : {e}")


#%% ---------------- Tableur ----------------
    def page_tableur(self):
        return TableurExcel(rows=20, cols=10)
#%% ---------------- Suites récurrentes ----------------
    def page_suite(self):
        w = QWidget(); layout = QVBoxLayout(w)
        layout.addWidget(QLabel("Saisir termes initiaux (séparés par virgule), récurrence (en utilisant un, un_1, un_2) et n"))
        form = QFormLayout()
        self.s_init = QLineEdit("1,1")
        self.s_recur = QLineEdit("un + un_1")  # exemple
        self.s_n = QSpinBox(); self.s_n.setMinimum(1); self.s_n.setValue(10)
        form.addRow("Termes initiaux:", self.s_init)
        form.addRow("Récurrence:", self.s_recur)
        form.addRow("n:", self.s_n)
        layout.addLayout(form)
        btn_calc = QPushButton("Calculer suite")
        btn_calc.clicked.connect(self.compute_suite)
        btn_export = QPushButton("Exporter CSV")
        btn_export.clicked.connect(self.export_suite_csv)
        hl = QHBoxLayout(); hl.addWidget(btn_calc); hl.addWidget(btn_export)
        layout.addLayout(hl)
        self.suite_result = QTextEdit(); self.suite_result.setReadOnly(True)
        layout.addWidget(self.suite_result)
        return w

    def compute_suite(self):
        try:
            init = [float(x.strip()) for x in self.s_init.text().split(',') if x.strip()!='']
        except:
            QMessageBox.warning(self, "Erreur", "Termes initiaux invalides.")
            return
        rec = self.s_recur.text().strip()
        n = self.s_n.value()
        res = self.api.calculer_suite(init, rec, n)
        if isinstance(res, str) and res.startswith("Erreur"):
            QMessageBox.warning(self, "Erreur", res)
            return
        # afficher
        text = "\n".join([f"u{i} = {v}" for i,v in enumerate(res[:n])])
        self.suite_current = res
        self.suite_result.setText(text)

    def export_suite_csv(self):
        if not hasattr(self, 'suite_current') or not self.suite_current:
            QMessageBox.warning(self, "Erreur", "Aucune suite calculée à exporter.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exporter suite CSV", "suite.csv", "CSV Files (*.csv)")
        if not path: return
        self.api.exporter_suite_csv(self.suite_current, path)
        QMessageBox.information(self, "Export", f"Suite exportée : {path}")

# -------------------------
#%% Main
# -------------------------
def main():
    app = QApplication(sys.argv)
    api = API()
    w = MainWindow(api)
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
