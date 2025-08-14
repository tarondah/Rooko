# Rooko

Rooko is a lightweight and user-friendly chess launcher that tracks playtime, stats, and ELO graph. It’s designed to be simple to use and customizable.

---

## Features

- Tracks your total playtime.
- Integrates a stat bar into chess.com
- Shows ELO graph of your chess games.
- Fullscreen toggle option.
- Lightweight and easy to launch.

---

## Installation

1. Download the latest **RookoInstaller.exe** from the [releases page].
2. Run the installer.
3. Choose installation directory and optional desktop shortcut.
4. Launch Rooko from Start Menu or Desktop shortcut.
5. Enjoy!

---

## Building from Source

To compile Rooko yourself:

### Requirements

- Python 3.11+ installed.
- [PyInstaller](https://www.pyinstaller.org/) (`pip install pyinstaller`).
- [Inno Setup](https://jrsoftware.org/isinfo.php) (for creating the installer).

### Steps

1. Clone the repository:
```
git clone https://github.com/yourusername/rooko.git
cd rooko
```

2. Install dependecies
```
pip install -r requirements.txt
```

3. Build the executable using PyInstaller
```
pyinstaller --onefile --windowed --add-data "config.jsonc;." --name "Rooko" --icon "logo.ico" main.py
```

4. Run Rooko.exe

(Optional: Run RookoInstaller.iss using InnoSetup)

## Contributing

We welcome contributions to Rooko! Here’s how you can help:

1. Fork the repository.
2. Create a feature branch by running:
```
git checkout -b feature/my-feature
```
4. Make your changes and commit them:
```
git commit -am "Add new feature"
```
6. Push to your branch:
```
git push origin feature/my-feature
```
9. Open a Pull Request on GitHub.

Please ensure your changes are tested and follow the existing code style. Every contribution, big or small, is appreciated!

---

## Contact

Have questions, suggestions, or issues? Reach out to us:

- **Website:** [https://www.rooko.vercel.app](https://www.rooko.vercel.app)  
- **GitHub Issues:** [https://github.com/tarondah/rooko/issues](https://github.com/tarondah/rooko/issues)
