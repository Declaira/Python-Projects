# 🐍 Python Projects 

Welcome to my Python project showcase! This repository is a collection of my coding journey, featuring everything from interactive games to utility tools and audio scripts.

---

## 📂 Repository Content

This project is organized into three main categories:

### 🎮 Games
Classic and custom-built games developed with Python:
* **Snake**: The legendary arcade game.
* **Minesweeper**: A logic-based puzzle game.
* **Connect 4 Ultimate**: An enhanced version of the famous strategy game.

### 🧮 Tools & Calculators
Practical applications for mathematical operations:
* **Graphical Calculator**: A clean and efficient interface for everyday calculations.

### 🎵 Music & Audio
Experimental scripts focused on sound manipulation, music generation, or audio processing.

---

## 🚀 Getting Started

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/Declaira/Python-Projects.git](https://github.com/Declaira/Python-Projects.git)
   
## How to run

```bash
uv run main
```

## Development

### How to run pre-commit

```bash
uvx pre-commit run -a
```

Alternatively, you can install it so that it runs before every commit :

```bash
uvx pre-commit install
```

### How to run tests

```bash
uv sync --group test
uv run coverage run -m pytest -v
```

### How to run type checking

```bash
uvx pyright MyProjects --pythonpath .venv/bin/python
```

### How to build docs

```bash
uv sync --group docs
cd docs && uv run make html
```

#### How to run autobuild for docs

```bash
uv sync --group docs
cd docs && make livehtml
