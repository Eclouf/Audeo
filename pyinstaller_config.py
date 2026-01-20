# Audeo Build Configuration for PyInstaller
# This file contains optimization and exclusion settings

block_cipher = None

# Libraries to exclude (reduce size)
EXCLUDE_MODULES = [
    # Testing libraries
    'pytest',
    'unittest2',
    'mock',
    
    # Development tools
    'matplotlib',
    'numpy',
    'pandas',
    
    # Documentation
    'pydoc',
    'doctest',
]

# Hidden imports (must include)
HIDDEN_IMPORTS = [
    'toga',
    'toga.style',
    'toga.style.pack',
    'yt_dlp',
    'yt_dlp.extractor',
    'pillow',
    'imageio_ffmpeg',
]

# Optimize for size
OPTIMIZE_SIZE = True

# Collect data files
DATA_FILES = [
    ('src/audeo2', 'src/audeo2/ressources', 'audeo2/ressources'),
]

# Binary excludes (reduce size by ~30-40%)
BINARY_EXCLUDES = [
    'libcrypto',
    'libssl',
    'libc++',
    'libstdc++',
]
