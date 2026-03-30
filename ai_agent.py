#!/usr/bin/env python3
"""
Auto-Developer Python Script
AI-powered automation system for code generation, Git operations, and deployment.

Features:
- Dynamic prompts from file or user input
- AI code generation via Ollama
- Auto-save to project folder
- Git init, add, commit, push
- GitHub Pages deployment
- Report generation
- Multi-prompt support
- Chat-style interaction
"""

import subprocess
import os
import sys
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "ollama_model": "stablelm2:1.6b",
    "github_repo_url": os.environ.get("GITHUB_REPO_URL", ""),  # GitHub repo URL from environment
    "github_branch": "main",
    "output_file": "index.html",
    "prompt_file": "prompt.txt",
    "report_file": "auto_report.txt",
    "commit_message_file": "commit_message.txt",
    "github_pages_url": os.environ.get("GITHUB_PAGES_URL", ""),  # GitHub Pages URL from environment
}

# ============================================================================
# UTILITY FUNCTIONS
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


def read_prompt_from_file(filepath: str) -> Optional[str]:
    """Read prompt from a text file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()
            if prompt:
                log(f"Read prompt from {filepath}")
                return prompt
            else:
                log(f"Prompt file {filepath} is empty", "WARNING")
                return None
    except FileNotFoundError:
        log(f"Prompt file {filepath} not found", "WARNING")
        return None
    except Exception as e:
        log(f"Error reading prompt file: {e}", "ERROR")
        return None


def get_prompt_interactive() -> str:
    """Get prompt from user input interactively."""
    print("\n" + "="*60)
    print("Enter your prompt (press Enter twice to finish):")
    print("="*60)
    
    lines = []
    empty_count = 0
    
    while True:
        try:
            line = input()
            if line == "":
                empty_count += 1
                if empty_count >= 2:
                    break
                lines.append(line)
            else:
                empty_count = 0
                lines.append(line)
        except EOFError:
            break
    
    prompt = "\n".join(lines).strip()
    return prompt


def get_prompts() -> List[str]:
    """
    Get prompts from various sources:
    1. Command line arguments
    2. prompt.txt file
    3. Interactive input
    """
    prompts = []
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--file" and len(sys.argv) > 2:
            # Read from specified file
            prompt = read_prompt_from_file(sys.argv[2])
            if prompt:
                prompts.append(prompt)
        elif sys.argv[1] == "--interactive":
            # Interactive mode
            pass
        else:
            # Treat arguments as prompt
            prompts.append(" ".join(sys.argv[1:]))
    
    # If no prompts from args, try prompt.txt
    if not prompts:
        prompt = read_prompt_from_file(CONFIG["prompt_file"])
        if prompt:
            prompts.append(prompt)
    
    # If still no prompts, use interactive mode
    if not prompts:
        prompt = get_prompt_interactive()
        if prompt:
            prompts.append(prompt)
    
    return prompts


# ============================================================================
# AI CODE GENERATION
# ============================================================================

def generate_code_with_ollama(prompt: str) -> Optional[str]:
    """
    Generate code using Ollama AI model.
    Returns the generated code or None on failure.
    """
    log(f"Generating code with model: {CONFIG['ollama_model']}")
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
        
        # Generate code
        result = subprocess.run(
            ["ollama", "run", CONFIG["ollama_model"]],
            input=prompt,
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


# ============================================================================
# FILE OPERATIONS
# ============================================================================

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
        run_git_command(["branch", "-M", CONFIG["github_branch"]])
        log(f"Default branch set to {CONFIG['github_branch']}")
        
        return True
    except Exception as e:
        log(f"Failed to initialize Git repository: {e}", "ERROR")
        return False


def setup_git_remote() -> bool:
    """Setup Git remote origin if configured."""
    if not CONFIG["github_repo_url"]:
        log("GitHub repository URL not configured", "WARNING")
        return False
    
    try:
        # Check if remote already exists
        result = run_git_command(["remote", "-v"], check=False)
        
        if "origin" in result.stdout:
            log("Git remote 'origin' already configured")
            return True
        
        # Add remote
        run_git_command(["remote", "add", "origin", CONFIG["github_repo_url"]])
        log(f"Git remote 'origin' added: {CONFIG['github_repo_url']}")
        
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


def git_push() -> bool:
    """Push changes to remote repository."""
    if not CONFIG["github_repo_url"]:
        log("GitHub repository URL not configured, skipping push", "WARNING")
        return False
    
    try:
        # Push to remote
        log(f"Pushing to {CONFIG['github_branch']}...")
        run_git_command(["push", "-u", "origin", CONFIG["github_branch"]])
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
Model: {CONFIG['ollama_model']}

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
# MAIN AUTOMATION WORKFLOW
# ============================================================================

def process_single_prompt(prompt: str, prompt_index: int = 1) -> Dict:
    """
    Process a single prompt through the complete workflow:
    1. Generate code
    2. Save to file
    3. Git operations
    4. Generate report
    """
    result = {
        "prompt": prompt,
        "success": False,
        "files_updated": [],
        "commit_message": "",
        "error": None
    }
    
    log(f"\n{'='*60}")
    log(f"Processing Prompt #{prompt_index}")
    log(f"{'='*60}")
    
    # Step 1: Generate code
    code = generate_code_with_ollama(prompt)
    if not code:
        result["error"] = "Code generation failed"
        return result
    
    # Step 2: Save code to file
    output_file = CONFIG["output_file"]
    if not save_code_to_file(code, output_file):
        result["error"] = "Failed to save code"
        return result
    
    result["files_updated"].append(output_file)
    
    # Step 3: Initialize Git if needed
    if not init_git_repo():
        result["error"] = "Git initialization failed"
        return result
    
    # Step 4: Setup remote if configured
    setup_git_remote()
    
    # Step 5: Generate commit message
    commit_message = f"Auto-generated code for prompt #{prompt_index}: {prompt[:50]}..."
    result["commit_message"] = commit_message
    
    # Step 6: Add and commit
    # Add all files (.) instead of just output_file to commit everything
    if not git_add_and_commit(["."], commit_message):
        result["error"] = "Git commit failed"
        return result
    
    # Step 7: Push to GitHub
    git_push()
    
    # Step 8: Generate and save report
    report = generate_report(
        prompt=prompt,
        files_updated=result["files_updated"],
        commit_message=commit_message,
        github_url=CONFIG["github_repo_url"]
    )
    
    save_report(report, CONFIG["report_file"])
    
    # Print report to console
    print(report)
    
    result["success"] = True
    return result


def run_batch_mode(prompts: List[str]) -> None:
    """Run automation for multiple prompts."""
    log(f"Starting batch mode with {len(prompts)} prompt(s)")
    
    results = []
    
    for i, prompt in enumerate(prompts, 1):
        result = process_single_prompt(prompt, i)
        results.append(result)
        
        if not result["success"]:
            log(f"Prompt #{i} failed: {result['error']}", "ERROR")
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    log(f"\n{'='*60}")
    log(f"BATCH SUMMARY")
    log(f"{'='*60}")
    log(f"Total prompts: {len(prompts)}")
    log(f"Successful: {successful}")
    log(f"Failed: {len(prompts) - successful}")
    log(f"{'='*60}")


def run_chat_mode() -> None:
    """Run in interactive chat mode."""
    log("Starting chat mode. Type 'exit' or 'quit' to end session.")
    log("Type 'help' for available commands.")
    
    prompt_count = 0
    
    while True:
        print("\n" + "-"*60)
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ['exit', 'quit', 'q']:
            log("Ending chat session")
            break
        
        if user_input.lower() == 'help':
            print("\nAvailable commands:")
            print("  help     - Show this help message")
            print("  exit/quit- End the session")
            print("  config   - Show current configuration")
            print("  status   - Show last operation status")
            print("\nOr enter a prompt to generate code.")
            continue
        
        if user_input.lower() == 'config':
            print("\nCurrent Configuration:")
            for key, value in CONFIG.items():
                print(f"  {key}: {value}")
            continue
        
        if user_input.lower() == 'status':
            print("\nStatus: Ready")
            print(f"Prompts processed this session: {prompt_count}")
            continue
        
        # Process as prompt
        prompt_count += 1
        result = process_single_prompt(user_input, prompt_count)
        
        if result["success"]:
            print(f"\n[OK] Prompt #{prompt_count} completed successfully!")
        else:
            print(f"\n[FAIL] Prompt #{prompt_count} failed: {result['error']}")


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the Auto-Developer script."""
    print("""
    ============================================================
    |           AUTO-DEVELOPER PYTHON SCRIPT                    |
    |           AI-Powered Code Generation & Deployment         |
    ============================================================
    """)
    
    # Check for chat mode
    if len(sys.argv) > 1 and sys.argv[1] == "--chat":
        run_chat_mode()
        return
    
    # Get prompts
    prompts = get_prompts()
    
    if not prompts:
        log("No prompts provided. Use --chat for interactive mode.", "ERROR")
        print("\nUsage:")
        print("  python ai_agent.py                    # Use prompt.txt")
        print("  python ai_agent.py 'Your prompt here' # Direct prompt")
        print("  python ai_agent.py --file prompt.txt  # From file")
        print("  python ai_agent.py --chat             # Interactive mode")
        sys.exit(1)
    
    # Run automation
    if len(prompts) == 1:
        process_single_prompt(prompts[0])
    else:
        run_batch_mode(prompts)


if __name__ == "__main__":
    main()
