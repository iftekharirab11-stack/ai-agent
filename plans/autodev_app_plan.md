# Auto-Developer Desktop Chatbot App - Implementation Plan

## Overview
Create a Tkinter-based desktop chatbot application that integrates with the existing `ai_agent.py` functionality to provide a GUI interface for AI code generation, Git operations, and GitHub Pages deployment.

## Architecture

### 1. Configuration Section (Top of File)
```python
# ============================================================================
# CONFIGURATION - EDIT THESE VALUES
# ============================================================================
REMOTE_URL = "https://github.com/iftekharirab11-stack/ai-agent.git"
LIVE_URL = "https://iftekharirab11-stack.github.io/ai-agent/"
OLLAMA_MODEL = "stablelm2:1.6b"
OUTPUT_FILE = "index.html"
REPORT_FILE = "auto_report.txt"
```

### 2. Main Components

#### A. AutoDeveloperApp Class
- Main application class managing the Tkinter GUI
- Handles all UI components and user interactions
- Manages threading for non-blocking operations

#### B. UI Components
1. **Main Window**
   - Dark theme (#1e1e1e background, #ffffff text)
   - Title: "Auto-Developer Agent"
   - Minimum size: 800x600

2. **Chat Display Area**
   - ScrolledText widget (read-only)
   - Color-coded messages:
     - User messages: #4a9eff (blue)
     - AI responses: #4aff4a (green)
     - System messages: #ffff4a (yellow)
     - Errors: #ff4a4a (red)

3. **Input Area**
   - Text entry field
   - Send button
   - Enter key binding

4. **Status Bar**
   - Label showing current state
   - States: Ready, Generating..., Pushing to GitHub..., Done, Error

#### C. Core Methods

1. **`__init__()`**
   - Initialize Tkinter window
   - Setup UI components
   - Configure tags for colored text
   - Show welcome message

2. **`setup_ui()`**
   - Create chat display
   - Create input frame
   - Create status bar
   - Apply dark theme styling

3. **`send_message()`**
   - Get text from input
   - Clear input field
   - Display user message in chat
   - Start processing thread

4. **`process_task_threaded()`**
   - Run in separate thread to prevent UI freeze
   - Call `process_task()`
   - Handle exceptions
   - Update UI when complete

5. **`process_task()`**
   - Main workflow:
     1. Update status to "Generating..."
     2. Call Ollama to generate code
     3. Display AI response in chat
     4. Save code to index.html
     5. Update status to "Pushing to GitHub..."
     6. Run Git operations (add, commit, push)
     7. Generate and save report
     8. Display success message with live URL
     9. Update status to "Done"

6. **`display_message()`**
   - Add message to chat with appropriate color tag
   - Auto-scroll to bottom

7. **`update_status()`**
   - Update status bar text

### 3. Integration with ai_agent.py

Import and use these functions from ai_agent.py:
- `clean_ai_output()` - Clean markdown from AI output
- `generate_code_with_ollama()` - Generate code via Ollama
- `save_code_to_file()` - Save code to file
- `init_git_repo()` - Initialize Git repository
- `setup_git_remote()` - Setup Git remote
- `git_add_and_commit()` - Add and commit files
- `git_push()` - Push to GitHub
- `generate_report()` - Generate report
- `save_report()` - Save report to file

### 4. Bug Fixes Implementation

#### Bug 1: Ollama subprocess might hang
- **Fix**: Use 300-second timeout (already in ai_agent.py)
- **Additional**: Show timeout error in chat if it occurs

#### Bug 2: Git push might fail if remote not set
- **Fix**: Check if remote URL is configured before pushing
- **Additional**: Show warning in chat if remote not configured

#### Bug 3: UI must NOT freeze while Ollama is generating
- **Fix**: Use threading.Thread for process_task()
- **Additional**: Use root.after() for UI updates from thread

#### Bug 4: If index.html already exists, overwrite cleanly
- **Fix**: Use 'w' mode in file open (already in ai_agent.py)
- **Additional**: Show message that file was overwritten

#### Bug 5: If Git has nothing new to commit, skip commit gracefully
- **Fix**: Check git status before committing (already in ai_agent.py)
- **Additional**: Show message that no changes were detected

#### Bug 6: If Ollama returns empty response, show clear error
- **Fix**: Check for empty output (already in ai_agent.py)
- **Additional**: Display error message in chat

#### Bug 7: Make sure all file writes use UTF-8 encoding
- **Fix**: Use encoding='utf-8' in all file operations (already in ai_agent.py)

### 5. Error Handling

- Try-except blocks around all critical operations
- Display errors in red in chat
- Update status bar to "Error" on failure
- Log errors to console for debugging

### 6. Threading Strategy

```
Main Thread (Tkinter UI)
    ↓
    ├─ send_message() → starts thread
    ↓
Worker Thread
    ├─ process_task()
    │   ├─ generate_code_with_ollama()
    │   ├─ save_code_to_file()
    │   ├─ init_git_repo()
    │   ├─ setup_git_remote()
    │   ├─ git_add_and_commit()
    │   ├─ git_push()
    │   ├─ generate_report()
    │   └─ save_report()
    ↓
    └─ root.after() → update UI from main thread
```

### 7. Message Flow

1. User types message and presses Enter/Send
2. Message displayed in blue bubble
3. Status changes to "Generating..."
4. Worker thread starts
5. Ollama generates code
6. AI response displayed in green bubble
7. Status changes to "Saving file..."
8. File saved
9. Status changes to "Pushing to GitHub..."
10. Git operations executed
11. Success message displayed with live URL
12. Status changes to "Done"
13. Ready for next message

### 8. File Structure

```
autodev_app.py
├── Configuration (lines 1-30)
├── Imports (lines 31-40)
├── AutoDeveloperApp Class (lines 41-400)
│   ├── __init__ (lines 42-60)
│   ├── setup_ui (lines 62-120)
│   ├── display_message (lines 122-140)
│   ├── update_status (lines 142-150)
│   ├── send_message (lines 152-170)
│   ├── process_task_threaded (lines 172-190)
│   └── process_task (lines 192-350)
└── Main Entry Point (lines 352-370)
```

## Testing Checklist

- [ ] Window opens with dark theme
- [ ] Chat display shows welcome message
- [ ] Can type in input field
- [ ] Enter key sends message
- [ ] Send button sends message
- [ ] User messages appear in blue
- [ ] AI responses appear in green
- [ ] System messages appear in yellow
- [ ] Errors appear in red
- [ ] Status bar updates correctly
- [ ] UI doesn't freeze during generation
- [ ] Code is saved to index.html
- [ ] Git operations work correctly
- [ ] Report is generated
- [ ] Live URL is displayed
- [ ] Can send multiple messages
- [ ] Scrollbar works
- [ ] Window is resizable

## Manual Steps for User

1. Ensure Ollama is running with stablelm2:1.6b model
2. Ensure Git is configured with correct credentials
3. Run: `python autodev_app.py`

Note: GitHub URLs are already configured for your repository.
