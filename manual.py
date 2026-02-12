import gradio as gr
import os
import datetime
import socket
import io
from pathlib import Path
import base64  # ADD THIS WITH OTHER IMPORTS
import tempfile  # ADD THIS WITH OTHER IMPORTS
import re



# GET IP ADDRESS TO DISPLAY IN EMAILS
def get_IP():
    # Auto-detect LAN IP address
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            if local_ip.startswith("127.") or ":" in local_ip:
                local_ip = "YOUR_LOCAL_IP"
                return local_ip
        except:
            local_ip = "YOUR_LOCAL_IP"    
            return local_ip

MYLOCALIP = get_IP()
manual_file = "manual.md"  # ✅ Fixed typo
try:
    with open(manual_file, 'r', encoding='utf-8') as f:
        usermanual = f.read()
except FileNotFoundError:
    # ✅ Fallback content if file missing (prevents startup crash)
    usermanual = """# 📘 FGS/ESD Master Override Register - User Manual
⚠️ **manual.md not found**  
Place your user manual in Markdown format at `manual.md` in the application directory.
"""

# ======================
# GRADIO INTERFACE
# ======================
    
with gr.Blocks(title="📚 User Manual") as demo:
    with gr.Row():
        gr.Markdown(usermanual)
    with gr.Row():
        gr.Markdown("---")
    with gr.Row():    
        with gr.Column(scale=1):
            gr.Image("logo.png", height=50, container=False, buttons=[], scale=1)
        with gr.Column(scale=2):
            gr.Markdown("All rights reserved (C)\ncreated by fabio.matricardi@key-solution.eu for NGUYA FLNG Project\nvisit [Key Solution SRL](key-solution.eu)")
            gr.Markdown(f"#### Network IP: {MYLOCALIP}")

if __name__ == "__main__":
	demo.launch()