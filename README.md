<img align="right" alt="logo" width="200px" src="https://raw.githubusercontent.com/CaptainATW/academic-victim/refs/heads/main/icon.png" />

# Academic Victim

If you're reading this, thats probably what you look like ->

## Installation

To install this project, you need to clone or download the repository. Unlike traditional executables, you will need to run the project from source.

### Requirements
- You **will need an OpenAI API key** if you want to utilize GPT-4o, or other OpenAI GPT models.

### Installation via GitHub Desktop and VSCode

1. Open GitHub Desktop and navigate to `File > Clone Repository > URL`.
    - Paste in the following repository URL:

   ```bash
   https://github.com/CaptainATW/academic-victim
   ```

2. Once cloned, open the cloned repository in Visual Studio Code.

3. Inside VSCode, press:
   - **On Windows**: `Ctrl+Shift+P`
   - **On Mac**: `Cmd+Shift+P`

4. In the command palette, search for and select `Python: Create Environment`.
5. Choose:
   - `Venv > Create > Use Python 3.x`.

6. Select "Install dependencies using requirements.txt" OR go make sure the environment is selected and run:

   ```bash
   pip install -r requirements.txt
   ```

8. Now, you can run the main Python file by executing:

   ```bash
   python main.py
   ```

### Building with Gradle

Alternatively, you can build the project using Gradle.

1. First, clone the project by installing [Git](https://git-scm.com/) and running the following commands:

   ```bash
   git clone https://github.com/CaptainATW/academic-victim
   git submodule update --init --recursive
   ```

2. Next, depending on your platform, build the project:

   - **On Unix-like Systems (Linux/macOS)**:

     ```bash
     cd academic-victim
     chmod +x ./gradlew
     ./gradlew agent
     ```

   - **On Windows**:

     ```cmd
     cd academic-victim
     .\gradlew.bat agent
     ```

## Contributing

We welcome contributions from anyone interested in improving **Academic Victim**. If you find a bug, have an idea for a new feature, or just want to help with documentation, feel free to submit a pull request.

### Guidelines

- Create a new branch for each feature or bug fix.
- Make sure your code follows the existing style.
- Write tests where applicable.
- Submit your pull request with a clear description of what you've done.

---

Thank you for contributing!
