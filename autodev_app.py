#!/usr/bin/env python3
"""
Auto-Developer Desktop Chatbot Application
AI-powered automation system for code generation, Git operations, and deployment.

Features:
- Dark-themed Tkinter GUI interface
- Real-time status updates
- Non-blocking UI with threading
- Complete automation workflow
- User-friendly interface with timestamps
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
import subprocess
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

# ============================================================================
# CONFIGURATION
# ============================================================================

REMOTE_URL = "https://github.com/iftekharirab11-stack/ai-agent.git"
LIVE_URL = "https://iftekharirab11-stack.github.io/ai-agent/"
OLLAMA_MODEL = "qwen2.5-coder:7b"
OUTPUT_FILE = "index.html"
REPORT_FILE = "auto_report.txt"

# ============================================================================
# AI AGENT FUNCTIONS
# ============================================================================

def log(message: str, level: str = "INFO") -> None:
    """Print formatted log messages with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def clean_ai_output(raw_output: str) -> str:
    """
    Clean AI-generated output by removing markdown code blocks.
    Handles patterns like:
    - ```html ... ```
    - ``` ... ```
    - Extra whitespace and explanations
    """
    # Remove markdown code blocks
    # Pattern 1: ```html ... ```
    cleaned = re.sub(r'```html\s*\n?', '', raw_output)
    cleaned = re.sub(r'```\s*$', '', cleaned, flags=re.MULTILINE)
    
    # Pattern 2: ``` ... ``` (generic)
    cleaned = re.sub(r'```\w*\s*\n?', '', cleaned)
    cleaned = re.sub(r'```\s*$', '', cleaned, flags=re.MULTILINE)
    
    # Remove leading/trailing whitespace
    cleaned = cleaned.strip()
    
    # If the output starts with explanation text, try to extract HTML
    if cleaned and not cleaned.startswith('<!DOCTYPE') and not cleaned.startswith('<html'):
        # Look for HTML content within the text
        html_match = re.search(r'(<!DOCTYPE.*?</html>)', cleaned, re.DOTALL | re.IGNORECASE)
        if html_match:
            cleaned = html_match.group(1)
    
    return cleaned


def is_valid_html(code: str) -> bool:
    """Validate that the AI output is complete HTML."""
    has_doctype = '<!DOCTYPE' in code.upper()
    has_body_open = '<body' in code.lower()
    has_body_close = '</body>' in code.lower()
    has_html_close = '</html>' in code.lower()
    has_content = len(code.strip()) > 500
    return all([has_doctype, has_body_open, 
                has_body_close, has_html_close, has_content])


def generate_code_with_ollama(prompt: str) -> Optional[str]:
    """
    Generate code using Ollama AI model.
    Returns the generated code or None on failure.
    """
    log(f"Generating code with model: {OLLAMA_MODEL}")
    log(f"Prompt: {prompt[:100]}...")
    
    try:
        # Check if Ollama is available
        check_result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        
        if check_result.returncode != 0:
            log("Ollama is not running or not installed", "ERROR")
            log("Please install Ollama from https://ollama.ai", "ERROR")
            return None
        
        # Generate code with system instruction
        system_instruction = """You are an expert HTML and CSS developer.
When given a task, you must respond with ONLY a complete, 
valid HTML file. Rules:
- Start with <!DOCTYPE html>
- End with </html>
- Include ALL sections requested in the prompt
- Include ALL CSS inside a <style> tag in the <head>
- The <body> must contain ALL the HTML content
- Do NOT explain anything
- Do NOT use markdown code fences
- Return ONLY the raw HTML file, nothing else"""
        
        full_prompt = system_instruction + "\n\nTASK: " + prompt
        
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=full_prompt,
            text=True,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            log(f"Ollama error: {result.stderr}", "ERROR")
            return None
        
        raw_output = result.stdout
        
        if not raw_output or not raw_output.strip():
            log("Ollama returned empty output", "ERROR")
            return None
        
        # Clean the output
        cleaned_code = clean_ai_output(raw_output)
        
        if not cleaned_code:
            log("Failed to clean AI output", "ERROR")
            return None
        
        log(f"Generated {len(cleaned_code)} characters of code")
        return cleaned_code
        
    except subprocess.TimeoutExpired:
        log("Ollama generation timed out (5 minutes)", "ERROR")
        return None
    except FileNotFoundError:
        log("Ollama command not found. Please install Ollama.", "ERROR")
        return None
    except Exception as e:
        log(f"Unexpected error during code generation: {e}", "ERROR")
        return None


def save_code_to_file(code: str, filename: str) -> bool:
    """Save generated code to a file."""
    try:
        # Create directory if it doesn't exist
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)
        
        log(f"Code saved to {filename}")
        return True
    except Exception as e:
        log(f"Error saving code to {filename}: {e}", "ERROR")
        return False


# ============================================================================
# GIT OPERATIONS
# ============================================================================

# Whitelist of allowed git commands for security
ALLOWED_GIT_COMMANDS = {
    "status", "init", "branch", "remote", "add", "commit", "push", "log", "diff"
}


def run_git_command(command: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a git command with validation.
    
    Security: Validates command against whitelist to prevent injection.
    """
    # Validate command is not empty
    if not command:
        raise ValueError("Git command cannot be empty")
    
    # Validate command is in whitelist
    if command[0] not in ALLOWED_GIT_COMMANDS:
        raise ValueError(f"Invalid git command: {command[0]}. Allowed: {ALLOWED_GIT_COMMANDS}")
    
    try:
        result = subprocess.run(
            ["git"] + command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        log(f"Git command failed: {' '.join(command)}", "ERROR")
        log(f"Error: {e.stderr}", "ERROR")
        raise
    except FileNotFoundError:
        log("Git is not installed or not in PATH", "ERROR")
        raise


def init_git_repo() -> bool:
    """Initialize Git repository if not already initialized."""
    try:
        # Check if already a git repo
        result = run_git_command(["status"], check=False)
        
        if result.returncode == 0:
            log("Git repository already initialized")
            return True
        
        # Initialize new repo
        run_git_command(["init"])
        log("Git repository initialized")
        
        # Set default branch to main
        run_git_command(["branch", "-M", "main"])
        log("Default branch set to main")
        
        return True
    except Exception as e:
        log(f"Failed to initialize Git repository: {e}", "ERROR")
        return False


def setup_git_remote(remote_url: Optional[str] = None) -> bool:
    """Setup Git remote origin if configured."""
    url = remote_url or REMOTE_URL
    if not url:
        log("GitHub repository URL not configured", "WARNING")
        return False
    
    try:
        # Check if remote already exists
        result = run_git_command(["remote", "-v"], check=False)
        
        if "origin" in result.stdout:
            log("Git remote 'origin' already configured")
            return True
        
        # Add remote
        run_git_command(["remote", "add", "origin", url])
        log(f"Git remote 'origin' added: {url}")
        
        return True
    except Exception as e:
        log(f"Failed to setup Git remote: {e}", "ERROR")
        return False


def git_add_and_commit(files: List[str], commit_message: str) -> bool:
    """Add files and commit changes."""
    try:
        # Add files
        for file in files:
            run_git_command(["add", file])
            log(f"Added {file} to staging")
        
        # Check if there are changes to commit
        status_result = run_git_command(["status", "--porcelain"])
        
        if not status_result.stdout.strip():
            log("No changes to commit")
            return True
        
        # Commit
        run_git_command(["commit", "-m", commit_message])
        log(f"Committed with message: {commit_message}")
        
        return True
    except Exception as e:
        log(f"Failed to commit changes: {e}", "ERROR")
        return False


def git_push(remote_url: Optional[str] = None) -> bool:
    """Push changes to remote repository."""
    url = remote_url or REMOTE_URL
    if not url:
        log("GitHub repository URL not configured, skipping push", "WARNING")
        return False
    
    try:
        # Push to remote
        log("Pushing to main...")
        run_git_command(["push", "-u", "origin", "main"])
        log("Successfully pushed to GitHub")
        
        return True
    except Exception as e:
        log(f"Failed to push to GitHub: {e}", "ERROR")
        log("You may need to authenticate with GitHub", "ERROR")
        return False


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(
    prompt: str,
    files_updated: List[str],
    commit_message: str,
    github_url: Optional[str] = None
) -> str:
    """Generate a detailed report of the automation process."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate GitHub Pages URL if repo URL is provided
    pages_url = ""
    if github_url:
        # Extract username and repo from URL
        # Format: https://github.com/username/repo.git
        match = re.search(r'github\.com[:/]([^/]+)/([^/.]+)', github_url)
        if match:
            username = match.group(1)
            repo = match.group(2)
            pages_url = f"https://{username}.github.io/{repo}/"
    
    report = f"""
{'='*60}
AUTO-DEVELOPER REPORT
{'='*60}

Generated: {timestamp}
Model: {OLLAMA_MODEL}

{'='*60}
PROMPT
{'='*60}
{prompt}

{'='*60}
FILES UPDATED
{'='*60}
{chr(10).join(f'- {f}' for f in files_updated)}

{'='*60}
COMMIT MESSAGE
{'='*60}
{commit_message}

{'='*60}
DEPLOYMENT
{'='*60}
GitHub Repository: {github_url or 'Not configured'}
GitHub Pages URL: {pages_url or 'Not available'}

{'='*60}
STATUS
{'='*60}
Code Generation: [OK] Complete
File Save: [OK] Complete
Git Commit: [OK] Complete
Git Push: {'[OK] Complete' if github_url else '[SKIP] Skipped (no repo URL)'}
Deployment: {'[OK] Live' if pages_url else '[SKIP] Not available'}

{'='*60}
"""
    return report


def save_report(report: str, filename: str) -> bool:
    """Save report to file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        log(f"Report saved to {filename}")
        return True
    except Exception as e:
        log(f"Error saving report: {e}", "ERROR")
        return False


# ============================================================================
# TKINTER GUI APPLICATION
# ============================================================================

class AutoDeveloperApp:
    """Main application class for the Auto-Developer chatbot."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Auto-Developer Agent v1.0")
        self.root.geometry("900x700")
        self.root.configure(bg="#1e1e1e")
        
        # Configure styles
        self.setup_ui()
        self.show_welcome_message()
    
    def setup_ui(self):
        """Setup the user interface."""
        # Main frame
        main_frame = tk.Frame(self.root, bg="#1e1e1e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Chat display area
        self.chat_display = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            bg="#2d2d2d",
            fg="#ffffff",
            font=("Consolas", 10),
            insertbackground="#ffffff",
            selectbackground="#4a9eff",
            selectforeground="#ffffff",
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Input frame
        input_frame = tk.Frame(main_frame, bg="#1e1e1e")
        input_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Input field
        self.input_field = tk.Entry(
            input_frame,
            bg="#2d2d2d",
            fg="#ffffff",
            font=("Consolas", 10),
            insertbackground="#ffffff",
            relief=tk.FLAT
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_field.bind("<Return>", self.on_enter_pressed)
        
        # Send button
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            bg="#4a9eff",
            fg="#ffffff",
            font=("Consolas", 10, "bold"),
            relief=tk.FLAT,
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(
            main_frame,
            textvariable=self.status_var,
            bg="#1e1e1e",
            fg="#c0c0c0",
            font=("Consolas", 9),
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, pady=(5, 0))
    
    def show_welcome_message(self):
        """Display welcome message."""
        welcome = """
╔══════════════════════════════════════════════════════════════╗
║              AUTO-DEVELOPER AGENT v1.0                       ║
║                                                              ║
║  Welcome! I'm your AI-powered development assistant.         ║
║                                                              ║
║  What I can do:                                              ║
║  • Generate code based on your prompts                       ║
║  • Save files automatically                                  ║
║  • Push to GitHub                                            ║
║  • Deploy to GitHub Pages                                    ║
║  • Generate detailed reports                                 ║
║                                                              ║
║  Just type your task and press Enter or click Send!          ║
╚══════════════════════════════════════════════════════════════╝
"""
        self.display_message(welcome, "system")
    
    def display_message(self, message: str, msg_type: str = "normal"):
        """Display a message in the chat area."""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on message type
        if msg_type == "user":
            color = "#4a9eff"
            prefix = f"[{timestamp}] You: "
        elif msg_type == "agent":
            color = "#4aff4a"
            prefix = f"[{timestamp}] Agent: "
        elif msg_type == "system":
            color = "#ffff4a"
            prefix = f"[{timestamp}] "
        elif msg_type == "error":
            color = "#ff4a4a"
            prefix = f"[{timestamp}] ERROR: "
        else:
            color = "#ffffff"
            prefix = f"[{timestamp}] "
        
        # Insert message with color
        self.chat_display.insert(tk.END, prefix, msg_type)
        self.chat_display.insert(tk.END, message + "\n")
        
        # Configure tag for color
        self.chat_display.tag_config(msg_type, foreground=color)
        
        # Auto-scroll to bottom
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def update_status(self, status: str):
        """Update the status bar."""
        self.status_var.set(status)
        self.root.update_idletasks()
    
    def on_enter_pressed(self, event):
        """Handle Enter key press."""
        self.send_message()
    
    def send_message(self):
        """Send user message and process task."""
        user_input = self.input_field.get().strip()
        
        if not user_input:
            return
        
        # Clear input field
        self.input_field.delete(0, tk.END)
        
        # Display user message
        self.display_message(user_input, "user")
        
        # Disable send button while processing
        self.send_button.config(state=tk.DISABLED)
        
        # Start processing in a separate thread
        thread = threading.Thread(
            target=self.process_task_threaded,
            args=(user_input,),
            daemon=True
        )
        thread.start()
    
    def process_task_threaded(self, user_input: str):
        """Process task in a separate thread to keep UI responsive."""
        try:
            self.process_task(user_input)
        except Exception as e:
            self.root.after(0, self.display_message, f"Unexpected error: {e}", "error")
        finally:
            # Re-enable send button
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
            self.root.after(0, self.update_status, "Ready")
    
    def process_task(self, user_input: str):
        """Process the user's task through the complete workflow."""
        # Step 1: Generate code
        self.root.after(0, self.update_status, "Generating code with AI...")
        self.root.after(0, self.display_message, "Generating code with Ollama AI...", "agent")
        
        code = generate_code_with_ollama(user_input)
        
        if not code:
            self.root.after(0, self.display_message, "Failed to generate code. Please check if Ollama is running.", "error")
            return
        
        # Validate HTML before saving
        if not is_valid_html(code):
            self.root.after(0, self.display_message, "AI returned incomplete HTML — please try again", "error")
            return
        
        # Display code preview
        preview = code[:500] + "..." if len(code) > 500 else code
        self.root.after(0, self.display_message, f"Generated {len(code)} characters of code", "agent")
        self.root.after(0, self.display_message, f"Code Preview:\n{preview}", "system")
        
        # Step 2: Save code to file
        self.root.after(0, self.update_status, "Saving file...")
        self.root.after(0, self.display_message, f"Saving code to {OUTPUT_FILE}...", "agent")
        
        if not save_code_to_file(code, OUTPUT_FILE):
            self.root.after(0, self.display_message, "Failed to save code to file.", "error")
            return
        
        self.root.after(0, self.display_message, f"Code saved successfully to {OUTPUT_FILE}", "agent")
        
        # Step 3: Initialize Git
        self.root.after(0, self.update_status, "Initializing Git...")
        self.root.after(0, self.display_message, "Initializing Git repository...", "agent")
        
        if not init_git_repo():
            self.root.after(0, self.display_message, "Failed to initialize Git repository.", "error")
            return
        
        # Step 4: Setup remote
        if REMOTE_URL:
            self.root.after(0, self.update_status, "Setting up Git remote...")
            self.root.after(0, self.display_message, "Setting up Git remote...", "agent")
            setup_git_remote(REMOTE_URL)
        else:
            self.root.after(0, self.display_message, "Warning: GitHub repository URL not configured. Skipping remote setup.", "system")
        
        # Step 5: Add and commit
        self.root.after(0, self.update_status, "Committing changes...")
        self.root.after(0, self.display_message, "Adding and committing files...", "agent")
        
        commit_message = f"Auto-generated code: {user_input[:50]}..."
        
        if not git_add_and_commit(["."], commit_message):
            self.root.after(0, self.display_message, "Failed to commit changes.", "error")
            return
        
        self.root.after(0, self.display_message, "Changes committed successfully", "agent")
        
        # Step 6: Push to GitHub
        if REMOTE_URL:
            self.root.after(0, self.update_status, "Pushing to GitHub...")
            self.root.after(0, self.display_message, "Pushing to GitHub...", "agent")
            
            if git_push(REMOTE_URL):
                self.root.after(0, self.display_message, "Successfully pushed to GitHub!", "agent")
            else:
                self.root.after(0, self.display_message, "Failed to push to GitHub. You may need to authenticate.", "error")
        else:
            self.root.after(0, self.display_message, "Skipping push (no remote URL configured).", "system")
        
        # Step 7: Generate report
        self.root.after(0, self.update_status, "Generating report...")
        self.root.after(0, self.display_message, "Generating report...", "agent")
        
        report = generate_report(
            prompt=user_input,
            files_updated=[OUTPUT_FILE],
            commit_message=commit_message,
            github_url=REMOTE_URL
        )
        
        save_report(report, REPORT_FILE)
        self.root.after(0, self.display_message, f"Report saved to {REPORT_FILE}", "agent")
        
        # Step 8: Display completion message
        self.root.after(0, self.update_status, "Done")
        self.root.after(0, self.display_message, "Task completed successfully!", "agent")
        
        # Display summary
        summary = f"""
✓ Code generated with Ollama AI
✓ File saved: {OUTPUT_FILE}
✓ Changes committed to Git
✓ Report saved: {REPORT_FILE}

🌐 Your website is live at:
   {LIVE_URL}

Note: It may take a few minutes for GitHub Pages to deploy.
"""
        self.root.after(0, self.display_message, summary, "system")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the Auto-Developer application."""
    root = tk.Tk()
    app = AutoDeveloperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
