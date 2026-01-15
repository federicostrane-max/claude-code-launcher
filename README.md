# 🚀 Claude Code Launcher

A Windows GUI application to launch Claude Code with project session management, screenshot helper, and file upload support.

## Features

- **Project Browser**: Lists all your Claude Code projects with session history
- **Session Choice**: Start a new session or resume from previous conversations
- **Screenshot Helper**: Paste screenshots (Ctrl+V) to share with Claude
- **File Upload**: Browse and select files to share with Claude
- **Clipboard Integration**: Copy commands ready to paste in terminal
- **Windows Terminal**: Opens Claude Code in Windows Terminal with proper setup

## Screenshot

![Claude Launcher Interface](screenshot.png)

## Installation

### Option 1: Run from source
```bash
# Clone the repository
git clone https://github.com/federicostrane-max/claude-code-launcher.git
cd claude-code-launcher

# Install dependencies
pip install -r requirements.txt

# Run
python claude_launcher_v6.py
```

### Option 2: Build executable
```bash
# Run the build script
build_launcher_v6.bat

# The executable will be in dist/Claude_Launcher_v6.exe
```

## Requirements

- Windows 10/11
- Python 3.8+
- Windows Terminal
- Claude Code CLI installed (`claude` command available)

## Usage

1. **Launch the app** - Run the executable or Python script
2. **Select a project** - Choose from the list of your Claude Code projects
3. **Choose session type**:
   - 🆕 **New Session** - Start fresh conversation
   - 📂 **Resume Session** - Pick from previous sessions
4. **Use the helper** (optional):
   - Paste screenshots with Ctrl+V
   - Add files via the file browser
   - Write your message
   - Copy and paste into the terminal

## How it works

The launcher reads your Claude Code session history from `~/.claude/projects/` and provides a GUI to:
- Browse projects by last modified date
- Launch Claude Code in the correct directory
- Prepare multi-file inputs for Claude

## License

MIT License

## Author

Created by [federicostrane-max](https://github.com/federicostrane-max)
