"""
AI Agent Web — Auto Developer
A professional Tkinter application that uses OpenRouter API (Kimi K2) to generate HTML websites
and automatically commits them to GitHub with live deployment.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from groq import Groq
import json
import os
import threading
import datetime
import subprocess
import webbrowser
import time
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = "moonshotai/kimi-k2-instruct-0905"
BASE_URL = "https://api.groq.com"
REMOTE_URL = "https://github.com/iftekharirab11-stack/ai-agent.git"
LIVE_URL = "https://iftekharirab11-stack.github.io/ai-agent/"
OUTPUT_FILE = "index.html"
MEMORY_DIR = "memory"
MEMORY_INDEX = os.path.join(MEMORY_DIR, "index.json")
REPORT_FILE = "auto_report.txt"

SYSTEM_PROMPT = """You are an expert HTML and CSS developer. When given a task, respond with ONLY a complete valid HTML file. Rules:
- Always start with <!DOCTYPE html>
- Always end with </html>
- Include ALL sections mentioned in the prompt
- Write ALL CSS inside a <style> tag in <head>
- The <body> must contain ALL HTML content, never leave it empty
- Use Google Fonts via @import in CSS
- Make it visually stunning with gradients and animations
- Do NOT explain anything
- Do NOT use markdown code fences
- Return ONLY the raw complete HTML file"""

# ============================================================================
# MEMORY SYSTEM
# ============================================================================

def ensure_memory_dir():
    """Create memory directory if it doesn't exist."""
    if not os.path.exists(MEMORY_DIR):
        os.makedirs(MEMORY_DIR)

def load_memory_index():
    """Load the memory index file."""
    ensure_memory_dir()
    if os.path.exists(MEMORY_INDEX):
        try:
            with open(MEMORY_INDEX, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"sessions": []}
    return {"sessions": []}

def save_memory_index(index_data):
    """Save the memory index file."""
    ensure_memory_dir()
    with open(MEMORY_INDEX, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

def save_memory(prompt, code, commit_message):
    """Save a memory session after successful generation."""
    ensure_memory_dir()
    timestamp = datetime.datetime.now()
    filename = timestamp.strftime("%Y-%m-%d_%H-%M-%S") + ".json"
    filepath = os.path.join(MEMORY_DIR, filename)
    
    memory_data = {
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "prompt": prompt,
        "model": MODEL,
        "output_file": OUTPUT_FILE,
        "code_length": len(code),
        "code_preview": code[:300] if len(code) > 300 else code,
        "commit_message": commit_message,
        "github_url": REMOTE_URL,
        "live_url": LIVE_URL,
        "status": "success"
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(memory_data, f, indent=2, ensure_ascii=False)
    
    # Update index
    index_data = load_memory_index()
    index_data["sessions"].append({
        "filename": filename,
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
    })
    save_memory_index(index_data)

def load_last_sessions(count=5):
    """Load the last N sessions from memory."""
    index_data = load_memory_index()
    sessions = index_data.get("sessions", [])
    return sessions[-count:] if len(sessions) > count else sessions

def get_last_prompt():
    """Get the prompt from the last session for context injection."""
    sessions = load_last_sessions(1)
    if sessions:
        filename = sessions[0]["filename"]
        filepath = os.path.join(MEMORY_DIR, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("prompt", "")
            except:
                pass
    return ""

def clear_memory():
    """Delete all memory files."""
    ensure_memory_dir()
    if os.path.exists(MEMORY_DIR):
        for filename in os.listdir(MEMORY_DIR):
            filepath = os.path.join(MEMORY_DIR, filename)
            if os.path.isfile(filepath):
                os.remove(filepath)

# ============================================================================
# CODE GENERATION
# ============================================================================

def validate_html(html_code):
    """Validate that the HTML code is complete and valid."""
    if not html_code:
        return False, "Empty response"
    
    if "<!DOCTYPE" not in html_code and "<!doctype" not in html_code.lower():
        return False, "Missing DOCTYPE declaration"
    
    if "<body" not in html_code.lower():
        return False, "Missing <body> tag"
    
    if "</body>" not in html_code.lower():
        return False, "Missing </body> tag"
    
    if "</html>" not in html_code.lower():
        return False, "Missing </html> tag"
    
    if len(html_code) < 1000:
        return False, f"Code too short ({len(html_code)} chars, minimum 1000)"
    
    return True, "Valid"

def generate_code(prompt, status_callback=None):
    """Generate HTML code using OpenRouter API with Kimi K2 model."""
    try:
        # Context injection from last session
        last_prompt = get_last_prompt()
        if last_prompt:
            full_prompt = f"Previous task: {last_prompt}. New task: {prompt}"
        else:
            full_prompt = prompt
        
        if status_callback:
            status_callback("Connecting to OpenRouter API...")
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/iftekharirab11-stack/ai-agent",
            "X-Title": "AI Agent Web"
        }
        
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 16000
        }
        
        # DEBUG: Log request details
        print(f"[DEBUG] API Key (first 10 chars): {GROQ_API_KEY[:10]}...")
        print(f"[DEBUG] Model: {MODEL}")
        print(f"[DEBUG] Base URL: {BASE_URL}")
        print(f"[DEBUG] Headers: {headers}")
        print(f"[DEBUG] Payload: {json.dumps(payload, indent=2)}")
        
        if status_callback:
            status_callback("Sending request to AI...")
        
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=120)
        
        # DEBUG: Log response details
        print(f"[DEBUG] Response Status Code: {response.status_code}")
        print(f"[DEBUG] Response Headers: {dict(response.headers)}")
        print(f"[DEBUG] Response Body: {response.text[:500]}...")
        
        if status_callback:
            status_callback("Processing AI response...")
        
        if response.status_code != 200:
            error_msg = f"API Error {response.status_code}: {response.text}"
            print(f"[DEBUG] Full error response: {response.text}")
            return None, error_msg
        
        data = response.json()
        
        if "choices" not in data or len(data["choices"]) == 0:
            return None, "No response from AI model"
        
        code = data["choices"][0]["message"]["content"]
        
        # Clean up the response - remove markdown code fences if present
        code = code.strip()
        if code.startswith("```html"):
            code = code[7:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        code = code.strip()
        
        # Validate HTML
        is_valid, validation_msg = validate_html(code)
        if not is_valid:
            return None, f"AI returned incomplete HTML — {validation_msg}"
        
        if status_callback:
            status_callback("Code validated successfully!")
        
        return code, "Success"
        
    except requests.exceptions.Timeout:
        return None, "Request timed out — please try again"
    except requests.exceptions.ConnectionError:
        return None, "Connection error — check your internet connection"
    except Exception as e:
        return None, f"Error: {str(e)}"

# ============================================================================
# GIT OPERATIONS
# ============================================================================

def git_commit_push(code, prompt, status_callback=None):
    """Commit and push the generated code to GitHub."""
    try:
        # Save the code to file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(code)
        
        if status_callback:
            status_callback("Saved code to " + OUTPUT_FILE)
        
        # Generate commit message
        commit_message = f"AI Agent: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"
        
        # Git operations
        if status_callback:
            status_callback("Adding files to git...")
        
        result = subprocess.run(
            ["git", "add", "."],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode != 0:
            return False, f"Git add failed: {result.stderr}"
        
        if status_callback:
            status_callback("Committing changes...")
        
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode != 0:
            # Check if it's just "nothing to commit"
            if "nothing to commit" in result.stdout.lower():
                return True, "No changes to commit"
            return False, f"Git commit failed: {result.stderr}"
        
        if status_callback:
            status_callback("Pushing to GitHub...")
        
        result = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode != 0:
            return False, f"Git push failed: {result.stderr}"
        
        if status_callback:
            status_callback("Successfully pushed to GitHub!")
        
        # Save memory
        save_memory(prompt, code, commit_message)
        
        # Generate report
        generate_report(prompt, code, commit_message)
        
        return True, commit_message
        
    except Exception as e:
        return False, f"Git error: {str(e)}"

def generate_report(prompt, code, commit_message):
    """Generate an auto report file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = f"""AI Agent Web — Auto Report
Generated: {timestamp}
Model: {MODEL}
GitHub: {REMOTE_URL}
Live: {LIVE_URL}

PROMPT:
{prompt}

COMMIT MESSAGE:
{commit_message}

CODE LENGTH: {len(code)} characters

CODE PREVIEW:
{code[:500]}...

---
Report generated automatically by AI Agent Web
"""
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)

# ============================================================================
# MAIN APPLICATION UI
# ============================================================================

class AIAgentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Agent Web — Auto Developer")
        self.root.geometry("1000x700")
        self.root.minsize(850, 600)
        self.root.configure(bg="#0d0d0d")
        
        # Status animation
        self.status_animation_id = None
        self.status_dots = 0
        
        # Session count
        self.session_count = len(load_memory_index().get("sessions", []))
        
        # Build UI
        self.setup_ui()
        
        # Load memory on startup
        self.root.after(100, self.load_startup_memory)
    
    def setup_ui(self):
        """Setup the complete UI."""
        # Top header bar
        self.setup_header()
        
        # Chat area
        self.setup_chat_area()
        
        # Buttons row
        self.setup_buttons_row()
        
        # Input area
        self.setup_input_area()
        
        # Bottom status bar
        self.setup_status_bar()
    
    def setup_header(self):
        """Setup the top header bar."""
        header_frame = tk.Frame(self.root, bg="#111111", height=50)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Left side - title
        title_label = tk.Label(
            header_frame,
            text="🤖 AI Agent Web",
            font=("Segoe UI", 16, "bold"),
            fg="#00ffff",
            bg="#111111"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Right side - status indicators
        status_frame = tk.Frame(header_frame, bg="#111111")
        status_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # API status
        self.api_status = tk.Label(
            status_frame,
            text="🟢 API Connected",
            font=("Segoe UI", 9),
            fg="#00ff88",
            bg="#111111"
        )
        self.api_status.pack(side=tk.LEFT, padx=10)
        
        # Git status
        self.git_status = tk.Label(
            status_frame,
            text="🟡 Git Ready",
            font=("Segoe UI", 9),
            fg="#ffaa00",
            bg="#111111"
        )
        self.git_status.pack(side=tk.LEFT, padx=10)
        
        # Memory status
        self.memory_status = tk.Label(
            status_frame,
            text="🔵 Memory Active",
            font=("Segoe UI", 9),
            fg="#4a9eff",
            bg="#111111"
        )
        self.memory_status.pack(side=tk.LEFT, padx=10)
        
        # Separator line
        separator = tk.Frame(self.root, bg="#333333", height=2)
        separator.pack(fill=tk.X, padx=0, pady=0)
    
    def setup_chat_area(self):
        """Setup the scrollable chat area."""
        chat_frame = tk.Frame(self.root, bg="#0a0a0a")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(chat_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Chat text area
        self.chat_area = tk.Text(
            chat_frame,
            bg="#0a0a0a",
            fg="#ffffff",
            font=("Consolas", 10),
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            state=tk.DISABLED,
            padx=15,
            pady=15,
            spacing1=2,
            spacing3=2
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.chat_area.yview)
        
        # Configure text tags for different message types
        self.chat_area.tag_configure("timestamp", foreground="#555555", font=("Consolas", 8))
        self.chat_area.tag_configure("user", foreground="#4a9eff", font=("Consolas", 10, "bold"))
        self.chat_area.tag_configure("agent", foreground="#00ff88", font=("Consolas", 10, "bold"))
        self.chat_area.tag_configure("system", foreground="#ffaa00", font=("Consolas", 10, "bold"))
        self.chat_area.tag_configure("error", foreground="#ff4444", font=("Consolas", 10, "bold"))
        self.chat_area.tag_configure("memory", foreground="#aa88ff", font=("Consolas", 10, "bold"))
        self.chat_area.tag_configure("success", foreground="#00ffcc", font=("Consolas", 10, "bold"))
    
    def setup_buttons_row(self):
        """Setup the buttons row above input."""
        buttons_frame = tk.Frame(self.root, bg="#0d0d0d")
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Memory button
        memory_btn = tk.Button(
            buttons_frame,
            text="📂 Memory",
            command=self.show_memory_popup,
            bg="#1a1a1a",
            fg="#aa88ff",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        memory_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear Memory button
        clear_btn = tk.Button(
            buttons_frame,
            text="🗑️ Clear Memory",
            command=self.clear_memory_action,
            bg="#1a1a1a",
            fg="#ff4444",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Last Report button
        report_btn = tk.Button(
            buttons_frame,
            text="📋 Last Report",
            command=self.show_report_popup,
            bg="#1a1a1a",
            fg="#ffaa00",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        report_btn.pack(side=tk.LEFT, padx=5)
        
        # View Live button
        live_btn = tk.Button(
            buttons_frame,
            text="🌐 View Live",
            command=self.open_live_url,
            bg="#1a1a1a",
            fg="#00ffcc",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        live_btn.pack(side=tk.LEFT, padx=5)
    
    def setup_input_area(self):
        """Setup the input area with send button."""
        input_frame = tk.Frame(self.root, bg="#0d0d0d")
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Input field
        self.input_field = tk.Text(
            input_frame,
            bg="#1a1a1a",
            fg="#ffffff",
            font=("Segoe UI", 11),
            height=3,
            wrap=tk.WORD,
            insertbackground="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Placeholder text
        self.input_field.insert("1.0", "Describe what you want to build...")
        self.input_field.bind("<FocusIn>", self.clear_placeholder)
        self.input_field.bind("<FocusOut>", self.add_placeholder)
        self.input_field.bind("<Return>", self.handle_enter_key)
        
        # Send button
        send_btn = tk.Button(
            input_frame,
            text="SEND",
            command=self.send_message,
            bg="#00ff88",
            fg="#000000",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        send_btn.pack(side=tk.RIGHT)
    
    def setup_status_bar(self):
        """Setup the bottom status bar."""
        status_frame = tk.Frame(self.root, bg="#111111", height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        # Left side - status text
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            font=("Segoe UI", 9),
            fg="#888888",
            bg="#111111"
        )
        self.status_label.pack(side=tk.LEFT, padx=20, pady=5)
        
        # Right side - session count
        self.session_label = tk.Label(
            status_frame,
            text=f"Sessions: {self.session_count}",
            font=("Segoe UI", 9),
            fg="#888888",
            bg="#111111"
        )
        self.session_label.pack(side=tk.RIGHT, padx=20, pady=5)
    
    # ========================================================================
    # UI HELPER METHODS
    # ========================================================================
    
    def clear_placeholder(self, event):
        """Clear placeholder text when input is focused."""
        if self.input_field.get("1.0", tk.END).strip() == "Describe what you want to build...":
            self.input_field.delete("1.0", tk.END)
            self.input_field.configure(fg="#ffffff")
    
    def add_placeholder(self, event):
        """Add placeholder text when input loses focus."""
        if not self.input_field.get("1.0", tk.END).strip():
            self.input_field.insert("1.0", "Describe what you want to build...")
            self.input_field.configure(fg="#666666")
    
    def handle_enter_key(self, event):
        """Handle Enter key press in input field."""
        if not event.state & 0x1:  # Check if Shift is not pressed
            self.send_message()
            return "break"
    
    def add_message(self, message, msg_type="system"):
        """Add a message to the chat area."""
        self.chat_area.configure(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.chat_area.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Add message prefix based on type
        prefixes = {
            "user": "▶ You: ",
            "agent": "🤖 Agent: ",
            "system": "⚙ System: ",
            "error": "✖ Error: ",
            "memory": "📂 Memory: ",
            "success": "✅ Done: "
        }
        
        prefix = prefixes.get(msg_type, "")
        if prefix:
            self.chat_area.insert(tk.END, prefix, msg_type)
        
        # Add message content
        self.chat_area.insert(tk.END, message + "\n\n")
        
        # Scroll to bottom
        self.chat_area.see(tk.END)
        self.chat_area.configure(state=tk.DISABLED)
    
    def update_status(self, text):
        """Update the status bar text with animation."""
        def update():
            self.status_label.configure(text=text)
        self.root.after(0, update)
    
    def start_status_animation(self, base_text):
        """Start animated status with dots."""
        def animate():
            self.status_dots = (self.status_dots + 1) % 4
            dots = "." * self.status_dots
            self.update_status(base_text + dots)
            self.status_animation_id = self.root.after(500, animate)
        animate()
    
    def stop_status_animation(self):
        """Stop the status animation."""
        if self.status_animation_id:
            self.root.after_cancel(self.status_animation_id)
            self.status_animation_id = None
    
    def update_session_count(self):
        """Update the session count display."""
        self.session_count = len(load_memory_index().get("sessions", []))
        self.session_label.configure(text=f"Sessions: {self.session_count}")
    
    # ========================================================================
    # ACTION METHODS
    # ========================================================================
    
    def load_startup_memory(self):
        """Load and display last 5 sessions on startup."""
        sessions = load_last_sessions(5)
        if sessions:
            self.add_message("Memory loaded — Last 5 sessions:", "memory")
            for i, session in enumerate(sessions, 1):
                prompt_preview = session.get("prompt", "Unknown")
                timestamp = session.get("timestamp", "Unknown")
                self.add_message(f"  {i}. [{timestamp}] {prompt_preview}", "memory")
        else:
            self.add_message("No previous sessions found in memory.", "memory")
    
    def send_message(self):
        """Handle sending a message."""
        # Get input text
        text = self.input_field.get("1.0", tk.END).strip()
        
        # Check for placeholder
        if not text or text == "Describe what you want to build...":
            return
        
        # Clear input
        self.input_field.delete("1.0", tk.END)
        
        # Add user message to chat
        self.add_message(text, "user")
        
        # Start generation in background thread
        thread = threading.Thread(target=self.generate_and_deploy, args=(text,))
        thread.daemon = True
        thread.start()
    
    def generate_and_deploy(self, prompt):
        """Generate code and deploy to GitHub (runs in background thread)."""
        # Start status animation
        self.root.after(0, lambda: self.start_status_animation("Generating"))
        
        # Generate code
        code, result = generate_code(
            prompt,
            status_callback=lambda msg: self.root.after(0, lambda: self.update_status(msg))
        )
        
        # Stop animation
        self.root.after(0, self.stop_status_animation)
        
        if code is None:
            # Error occurred
            self.root.after(0, lambda: self.add_message(result, "error"))
            self.root.after(0, lambda: self.update_status("Error occurred"))
            return
        
        # Success - show preview
        self.root.after(0, lambda: self.add_message(f"Generated {len(code)} characters of HTML code", "agent"))
        
        # Commit and push
        self.root.after(0, lambda: self.start_status_animation("Deploying"))
        
        success, commit_result = git_commit_push(
            code,
            prompt,
            status_callback=lambda msg: self.root.after(0, lambda: self.update_status(msg))
        )
        
        # Stop animation
        self.root.after(0, self.stop_status_animation)
        
        if success:
            self.root.after(0, lambda: self.add_message(f"Committed: {commit_result}", "success"))
            self.root.after(0, lambda: self.add_message(f"Live at: {LIVE_URL}", "success"))
            self.root.after(0, self.update_session_count)
        else:
            self.root.after(0, lambda: self.add_message(commit_result, "error"))
        
        self.root.after(0, lambda: self.update_status("Ready"))
    
    def show_memory_popup(self):
        """Show popup with all memory sessions."""
        popup = tk.Toplevel(self.root)
        popup.title("Memory Sessions")
        popup.geometry("600x400")
        popup.configure(bg="#0d0d0d")
        
        # Title
        title = tk.Label(
            popup,
            text="📂 All Memory Sessions",
            font=("Segoe UI", 14, "bold"),
            fg="#aa88ff",
            bg="#0d0d0d"
        )
        title.pack(pady=10)
        
        # Sessions list
        sessions = load_memory_index().get("sessions", [])
        
        if not sessions:
            no_sessions = tk.Label(
                popup,
                text="No sessions found in memory.",
                font=("Segoe UI", 10),
                fg="#888888",
                bg="#0d0d0d"
            )
            no_sessions.pack(pady=20)
        else:
            # Create scrollable frame
            frame = tk.Frame(popup, bg="#0d0d0d")
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            canvas = tk.Canvas(frame, bg="#0d0d0d", highlightthickness=0)
            scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="#0d0d0d")
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Add sessions
            for i, session in enumerate(reversed(sessions), 1):
                session_frame = tk.Frame(scrollable_frame, bg="#1a1a1a", padx=10, pady=5)
                session_frame.pack(fill=tk.X, pady=2)
                
                timestamp = session.get("timestamp", "Unknown")
                prompt = session.get("prompt", "Unknown")
                
                label = tk.Label(
                    session_frame,
                    text=f"{i}. [{timestamp}] {prompt}",
                    font=("Consolas", 9),
                    fg="#ffffff",
                    bg="#1a1a1a",
                    anchor="w"
                )
                label.pack(fill=tk.X)
            
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close button
        close_btn = tk.Button(
            popup,
            text="Close",
            command=popup.destroy,
            bg="#1a1a1a",
            fg="#ffffff",
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor="hand2"
        )
        close_btn.pack(pady=10)
    
    def clear_memory_action(self):
        """Clear all memory after confirmation."""
        result = messagebox.askyesno(
            "Clear Memory",
            "Are you sure you want to delete all memory sessions?\n\nThis action cannot be undone.",
            icon="warning"
        )
        
        if result:
            clear_memory()
            self.add_message("All memory sessions have been deleted.", "system")
            self.update_session_count()
    
    def show_report_popup(self):
        """Show popup with the last report."""
        popup = tk.Toplevel(self.root)
        popup.title("Last Report")
        popup.geometry("700x500")
        popup.configure(bg="#0d0d0d")
        
        # Title
        title = tk.Label(
            popup,
            text="📋 Last Auto Report",
            font=("Segoe UI", 14, "bold"),
            fg="#ffaa00",
            bg="#0d0d0d"
        )
        title.pack(pady=10)
        
        # Report content
        if os.path.exists(REPORT_FILE):
            with open(REPORT_FILE, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            text_area = scrolledtext.ScrolledText(
                popup,
                bg="#1a1a1a",
                fg="#ffffff",
                font=("Consolas", 10),
                wrap=tk.WORD,
                padx=15,
                pady=15
            )
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_area.insert("1.0", report_content)
            text_area.configure(state=tk.DISABLED)
        else:
            no_report = tk.Label(
                popup,
                text="No report found. Generate a website first.",
                font=("Segoe UI", 10),
                fg="#888888",
                bg="#0d0d0d"
            )
            no_report.pack(pady=20)
        
        # Close button
        close_btn = tk.Button(
            popup,
            text="Close",
            command=popup.destroy,
            bg="#1a1a1a",
            fg="#ffffff",
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor="hand2"
        )
        close_btn.pack(pady=10)
    
    def open_live_url(self):
        """Open the GitHub Pages URL in browser."""
        webbrowser.open(LIVE_URL)
        self.add_message(f"Opened {LIVE_URL} in browser", "system")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = AIAgentApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
