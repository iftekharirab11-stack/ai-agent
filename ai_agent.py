import subprocess

# Example prompt
prompt = "Create a simple HTML portfolio page with a header, 3 sections, and a footer"

# Call Ollama to generate code
result = subprocess.run(
    ["ollama", "run", "stablelm2:1.6b"],
    input=prompt,
    text=True,
    capture_output=True
)

code = result.stdout

# Save code to a file
with open("index.html", "w", encoding="utf-8") as f:
    f.write(code)

print("Code generated and saved to index.html")