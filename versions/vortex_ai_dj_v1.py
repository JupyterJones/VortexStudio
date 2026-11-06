#!/usr/bin/env python3
"""
Vortex AI DJ - Intelligent Algorithmic Beat Generator powered by Ollama.
Created by Jack Northrup & Esperanza AI Companion.
Supports: Southern Blues, Reggae, Acid House, Amen Jungle, Synthwave, Dubstep, etc.
"""

import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

# Ollama endpoint & timeout settings (300-500 seconds for SSD/CPU models)
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
REQUEST_TIMEOUT = 500

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_DIR = os.path.join(BASE_DIR, "saved_beats")
NOTES_DIR = os.path.join(BASE_DIR, "beat_notes")
NOTES_FILE = os.path.join(NOTES_DIR, "my_favorite_beats.txt")

os.makedirs(SAVED_DIR, exist_ok=True)
os.makedirs(NOTES_DIR, exist_ok=True)

# Curated priority list of models for beat generation (fastest CPU models first)
PREFERRED_MODELS = [
    "llama3.2-1b-local",
    "llama3.2:3b",
    "deepseek-r1:1.5b",
    "deepseek-coder:1.3b",
    "qwen2.5-coder:7b",
    "esperanza:latest",
    "mistral:7b-instruct",
]

SYSTEM_PROMPT = """Output ONLY executable Python code for the Vortex music engine. No markdown, no conversation, no explanations.

SYNTAX:
p("channel", s("mini_notation") >> speed("1") >> room(0.3))

SAMPLES:
- Drums: bd, snare, cp, realclaps, hh, ch, 808bd, 808sd, 808oh, clubkick, gabba, amencutup
- Melodic/Bass: bass1, arpy, birds, piano, sax, sitar
- Effects: speed("..."), room(0.0-1.0), vowel("a e i o u"), crush(1-16)

MINI-NOTATION:
- Space splits beat: "bd sn bd sn"
- Repeat: "bd*4"
- Rest: "~" (e.g. "~ ~ bd ~", "[~ cp]*2")
- Subdivide: "[bd bd] sn"

FEW-SHOT EXAMPLES:

User: "90s acid house beat"
Code:
p("drums", s("gabba*4") >> room(0.2))
p("hats", s("hh*8") >> room(0.1))
p("acid", s("bass1*8") >> speed("0.8 1 1.25 0.9") >> room(0.4))

User: "reggae beats with synth voice"
Code:
p("drums", s("~ ~ bd ~") >> room(0.3))
p("skank", s("[~ ch]*4") >> room(0.4))
p("synth", s("birds*4") >> speed("0.8 1.0 1.2") >> vowel("a e o i") >> room(0.6))

User: "slow southern blues shuffle"
Code:
p("drums", s("[bd ~ bd] [snare] [bd ~ bd] [snare]") >> speed("0.85") >> room(0.35))
p("bass", s("bass1*4") >> speed("0.6 0.7 0.8 0.65") >> room(0.4))
"""


def check_ollama_available():
    """Check if Ollama server is reachable and return list of available models."""
    try:
        url = f"{OLLAMA_HOST}/api/tags"
        req = urllib.request.Request(url, headers={"User-Agent": "Vortex-AI-DJ"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            return models
    except Exception:
        return []


def select_best_model(available_models, user_choice=None):
    """Pick requested model or best match from preferred list."""
    if user_choice:
        for am in available_models:
            if user_choice.lower() in am.lower():
                return am

    # Match preferred
    for pm in PREFERRED_MODELS:
        for am in available_models:
            if pm.lower() in am.lower():
                return am

    return available_models[0] if available_models else "llama3.2:3b"


def query_ollama(prompt, model_name):
    """Query Ollama API with generous 300-500s timeout."""
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": 0.4,
            "top_p": 0.9,
        }
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json", "User-Agent": "Vortex-AI-DJ"},
    )

    print(f"⏳ Generating beat with model \033[1;36m{model_name}\033[0m (timeout={REQUEST_TIMEOUT}s)...", flush=True)
    start_t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            raw_text = res_json.get("response", "")
            elapsed = time.time() - start_t
            print(f"✓ Generated in {elapsed:.1f}s!\n")
            return clean_generated_code(raw_text)
    except urllib.error.URLError as e:
        print(f"\n❌ Error contacting Ollama ({e}). Ensure Ollama is running at {OLLAMA_HOST}")
        return None


def clean_generated_code(text):
    """Extract and format Python code from model response."""
    # If wrapped in markdown ```python ... ```
    match = re.search(r"```(?:python)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        code = match.group(1).strip()
    else:
        # Strip leading/trailing explanations
        lines = []
        for line in text.splitlines():
            if line.startswith("p(") or line.startswith("s(") or line.startswith("#") or line.startswith("hush()") or line.startswith(" ") or line.startswith(")") or line.startswith(">>") or "=" in line:
                lines.append(line)
        code = "\n".join(lines).strip()

    code = code or text.strip()
    # Ensure separate pattern statements start on newlines
    code = re.sub(r"\)\s*(p\()", ")\n\\1", code)
    return code


def play_code_live(code):
    """Audition the code live through SuperDirt audio engine!"""
    print("▶ \033[1;32mAuditioning live on SuperDirt (port 57120)...\033[0m")
    try:
        from vortex import vortex_dsl
        with vortex_dsl() as dsl_module:
            exec(code, vars(dsl_module))
            print("✓ Playing! Press [Enter] or choose [H] to hush.")
            return True
    except Exception as e:
        print(f"⚠️ Live audition error: {e}")
        return False


def hush_live():
    """Hush all live streams."""
    try:
        from vortex import vortex_dsl
        with vortex_dsl() as dsl_module:
            hush_func = getattr(dsl_module, "hush", None)
            if hush_func:
                hush_func()
        print("🛑 All live audio silenced.")
    except Exception as e:
        print(f"Error executing hush: {e}")


def save_to_beat_notes(code, prompt_title):
    """Append the generated beat to beat_notes/my_favorite_beats.txt."""
    os.makedirs(NOTES_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n\n# --- AI GENERATED BEAT: {prompt_title.upper()} ({timestamp}) ---\n{code}\n"

    try:
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"💾 \033[1;32mSaved beat to Beat Notes:\033[0m {NOTES_FILE}")
        print("💡 Open Vortex Studio's 'Beat Notes' tab to view or insert it anytime!")
    except Exception as e:
        print(f"⚠️ Error saving to notes: {e}")


def save_as_python_script(code, prompt_title):
    """Save beat as a dedicated .py file in saved_beats/."""
    os.makedirs(SAVED_DIR, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9_]+", "_", prompt_title.lower()).strip("_")[:30]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ai_{safe_name}_{timestamp}.py"
    path = os.path.join(SAVED_DIR, filename)

    header = f"# 🎵 Vortex Beat by Jack Northrup & Esperanza AI Companion\n# Prompt: {prompt_title}\n\n"
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(header + code + "\n\n# Stop\nhush()\n")
        print(f"💾 \033[1;32mSaved script as:\033[0m {path}")
    except Exception as e:
        print(f"⚠️ Error saving script: {e}")


def display_code_banner(code):
    """Print the code with terminal colors."""
    print("━" * 60)
    for line in code.splitlines():
        if line.strip().startswith("#"):
            print(f"\033[1;30m{line}\033[0m")
        elif "p(" in line or "s(" in line:
            print(f"\033[1;32m{line}\033[0m")
        elif ">>" in line:
            print(f"\033[1;34m{line}\033[0m")
        else:
            print(f"\033[0;37m{line}\033[0m")
    print("━" * 60)


def interactive_menu(code, prompt_title):
    """Action menu after generating a beat."""
    while True:
        print("\nWhat would you like to do with this beat?")
        print("  [\033[1;32mP\033[0m] Play / Audition live on speakers")
        print("  [\033[1;33mS\033[0m] Save to Beat Notes (my_favorite_beats.txt)")
        print("  [\033[1;34mF\033[0m] Save as new .py script file in saved_beats/")
        print("  [\033[1;31mH\033[0m] Hush sound")
        print("  [\033[1;37mN\033[0m] New beat prompt")
        print("  [\033[1;37mQ\033[0m] Quit")

        try:
            choice = input("Select [P/S/F/H/N/Q] > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = "q"

        if choice == "p":
            play_code_live(code)
        elif choice == "s":
            save_to_beat_notes(code, prompt_title)
        elif choice == "f":
            save_as_python_script(code, prompt_title)
        elif choice == "h":
            hush_live()
        elif choice in ("n", ""):
            break
        elif choice == "q":
            hush_live()
            print("👋 Peace out, DJ Jack!")
            sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Vortex AI DJ - Algorithmic Beat Generator via Ollama")
    parser.add_argument("prompt", nargs="*", help="Description of beat (e.g., 'slow southern blues', 'reggae with synth voice')")
    parser.add_argument("--model", "-m", default=None, help="Ollama model name (e.g. qwen2.5-coder:7b, llama3.2:3b)")
    parser.add_argument("--play", "-p", action="store_true", help="Immediately play the generated beat")
    args = parser.parse_args()

    print("==========================================================")
    print("      🎧 VORTEX AI DJ — BEAT GENERATOR 🎵               ")
    print("     by Jack Northrup & Esperanza AI Companion           ")
    print("==========================================================")

    # Check Ollama
    available_models = check_ollama_available()
    if not available_models:
        print(f"❌ Error: Cannot connect to Ollama at {OLLAMA_HOST}.")
        print("Please ensure Ollama is running: 'ollama serve'")
        sys.exit(1)

    active_model = select_best_model(available_models, args.model)
    print(f"🤖 Connected to Ollama! Active Model: \033[1;33m{active_model}\033[0m")
    print(f"⚙️ Timeout limit: {REQUEST_TIMEOUT}s (plenty of time for SSD loading)")
    print("----------------------------------------------------------\n")

    # If single-shot prompt passed via CLI
    if args.prompt:
        prompt_str = " ".join(args.prompt)
        print(f"🎯 Beat Prompt: \"\033[1;35m{prompt_str}\033[0m\"")
        code = query_ollama(prompt_str, active_model)
        if code:
            display_code_banner(code)
            if args.play:
                play_code_live(code)
            interactive_menu(code, prompt_str)
        return

    # Interactive Loop
    while True:
        try:
            print("\nEnter your musical beat idea:")
            print("Examples:")
            print("  • 'create slow southern blues beat with walking bass'")
            print("  • 'create reggae beats with synth voice'")
            print("  • 'fast 90s acid house with screaming 303 bass'")
            print("  • 'chill ambient sci-fi arpeggios'")
            user_prompt = input("\n🎵 AI DJ > ").strip()

            if not user_prompt:
                continue
            if user_prompt.lower() in ("exit", "quit", "q"):
                hush_live()
                print("👋 Bye Jack!")
                break

            code = query_ollama(user_prompt, active_model)
            if code:
                display_code_banner(code)
                interactive_menu(code, user_prompt)

        except KeyboardInterrupt:
            hush_live()
            print("\n👋 Session ended.")
            break


if __name__ == "__main__":
    main()
