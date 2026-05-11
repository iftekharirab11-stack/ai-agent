# AI Agent Web — Auto Developer

A professional Tkinter application that uses Mistral AI API (via OpenRouter) to generate HTML websites and automatically commits them to GitHub with live deployment.

## Features

- 🤖 AI-Powered Code Generation: Uses Mistral Large model via OpenRouter to generate complete HTML websites from natural language prompts
- 💾 Memory System: Remembers previous sessions for context-aware generation
- 🚀 One-Click Deployment: Automatically saves, commits, and pushes generated code to GitHub
- 🌐 Live Preview: View deployed websites instantly via GitHub Pages
- 📊 Auto Reporting: Generates detailed reports of each generation session
- 💫 Modern UI: Dark-themed interface with smooth animations and feedback
- 🔐 Secure: API keys stored in environment variables

## Project Structure

```
AI AGENT WEB/
├── autodev_app.py          # Main application file
├── index.html              # Generated HTML output
├── auto_report.txt         # Auto-generated report
├── .env                    # Environment variables (API keys)
├── .gitignore              # Git ignore rules
├── memory/                 # Session memory storage
│   └── index.json          # Memory index
├── plans/                  # Planning documents
├── .vscode/                # VS Code settings
└── README.md               # This file
```

## Setup Instructions

### Prerequisites

- Python 3.7+
- Git installed and configured
- Mistral API key (from OpenRouter)
- GitHub account for deployment

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/iftekharirab11-stack/ai-agent.git
   cd ai-agent
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with your Mistral API key:
   ```env
   MISTRAL_API_KEY=your_api_key_here
   ```

4. Configure GitHub remote (if not already set):
   ```bash
   git remote set-url origin https://github.com/yourusername/your-repo.git
   ```

## Usage

1. Run the application:
   ```bash
   python autodev_app.py
   ```

2. In the application window:
   - Describe what you want to build in the input field (e.g., "Create a modern portfolio website for a photographer")
   - Click "SEND" or press Enter
   - Watch as the AI generates HTML code, validates it, and deploys to GitHub
   - View your live site at the configured GitHub Pages URL

3. Use the buttons:
   - 📂 Memory: View previous generation sessions
   - 📋 Last Report: See details of the last generation
   - 🌐 View Live: Open your deployed site in browser
   - 🗑️ Clear Memory: Delete all session history (requires confirmation)

## How It Works

1. **Input Processing**: Your description is sent to Mistral AI via OpenRouter
2. **Code Generation**: The AI generates a complete HTML file with embedded CSS
3. **Validation**: The generated code is validated for completeness (DOCTYPE, html, body tags)
4. **Deployment**: Valid code is saved, committed with a descriptive message, and pushed to GitHub
5. **Memory**: Successful generations are stored in the `memory/` directory for context
6. **Reporting**: An auto-report is generated summarizing the session

## Configuration

Modify these constants in `autodev_app.py` to customize behavior:

- `MODEL`: AI model to use (default: "mistral-large-latest")
- `REMOTE_URL`: GitHub repository URL
- `LIVE_URL`: GitHub Pages live URL
- `OUTPUT_FILE`: Output HTML filename (default: "index.html")
- `SYSTEM_PROMPT`: Instructions for the AI generator

## Memory System

The application maintains a memory of past sessions:
- Stored in the `memory/` directory as JSON files
- Index tracked in `memory/index.json`
- Used to provide context for subsequent generations
- Can be viewed via the "Memory" button or cleared entirely

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Iftekhar  - [GitHub Profile](https://github.com/iftekharirab11-stack)

Project Link: [https://github.com/iftekharirab11-stack/ai-agent](https://github.com/iftekharirab11-stack/ai-agent)

## Acknowledgments

- Mistral AI for their powerful language models
- OpenRouter for providing API access
- Tkinter for the GUI framework
- dotenv for environment variable management
