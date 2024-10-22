from setuptools import setup

setup(
    app=['main.py'],
    data_files=['ai.py', 'icon.png', 'icon.ico'],
    setup_requires=['py2app'],
    options={
        'py2app': {
            'packages': ['openai', 'PIL', 'pynput', 'asyncio', 'anyio'],
            'includes': [
                'ai',
                'asyncio',
                'anyio',
                'pillow',
                'PIL',
                'pynput',
            ],
            'iconfile': 'icon.icns',
            'excludes': ['tkinter'],  # Exclude tkinter if you're not using it
            'argv_emulation': True,
        }
    },
)