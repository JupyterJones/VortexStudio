#!/usr/bin/env python3
"""
Vortex AI DJ - Algorithmic Beat Generator powered by Ollama.
Created by Jack Northrup & Esperanza AI Companion.
Features:
- Autonomous self-healing grammar & syntax validator
- Dynamic retry loop with LLM error feedback
- Full JSON error & benchmark logging (model_errors.json & model_benchmark.json)
- Live SuperDirt audio auditioning & pattern export
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
ERROR_LOG_FILE = os.path.join(BASE_DIR, "model_errors.json")
BENCHMARK_LOG_FILE = os.path.join(BASE_DIR, "model_benchmark.json")

os.makedirs(SAVED_DIR, exist_ok=True)
os.makedirs(NOTES_DIR, exist_ok=True)

# Curated priority list of models for beat generation (fastest CPU models first)
PREFERRED_MODELS = [
    "llama3.2-1b-local",
    "llama3.2:3b",
    "deepseek-coder:1.3b",
    "deepseek-r1:1.5b",
    "granite4.1:3b",
    "qwen2.5-coder:7b",
    "esperanza:latest",
    "mistral:7b-instruct",
]

SYSTEM_PROMPT = """Output ONLY executable Python code for the Vortex music engine. No markdown, no conversation, no explanations.

SYNTAX:
p("channel", s("mini_notation") >> speed("1") >> room(0.3))

SAMPLES:
- Drums: bd, snare, cp, realclaps, hh, ch, clubkick, gabba, amencutup, tabla, perc, drum
- Melodic/Bass: bass1, arpy, birds, piano, sax, sitar, flute, fiddle, brass
- Effects: speed("..."), room(0.0-1.0), vowel("a e i o u"), crush(1-16), shape(0.0-1.0)

MINI-NOTATION:
- Space splits beat: "bd sn bd sn"
- Repeat: "bd*4"
- Rest: "~" (e.g. "~ ~ bd ~", "[~ cp]*2")
- Subdivide: "[bd bd] sn"

CRITICAL RULES:
- Sample names must NEVER start with numbers (use 'bd' NOT '808bd', 'bass1' NOT '303bass').
- Output ONLY raw Python code calling p("channel", s("...")).
- NO markdown formatting, NO python imports, NO def functions, NO comments.

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

    return available_models[0] if available_models else "llama3.2-1b-local"


def query_ollama(prompt, model_name):
    """Query Ollama API with generous 300-500s timeout."""
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": 0.35,
            "top_p": 0.85,
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
            print(f"✓ Generated in {elapsed:.1f}s!")
            return raw_text, elapsed
    except urllib.error.URLError as e:
        print(f"\n❌ Error contacting Ollama ({e}). Ensure Ollama is running at {OLLAMA_HOST}")
        return None, 0.0


def clean_generated_code(text):
    """Extract and format Python code from model response."""
    if not text:
        return ""

    # Strip markdown block if present
    match = re.search(r"```(?:python)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        code = match.group(1).strip()
    else:
        # Filter lines to code-like lines
        lines = []
        for line in text.splitlines():
            line_s = line.strip()
            # Skip comments or fluff lines
            if line_s.startswith("def ") or line_s.startswith("import ") or line_s.startswith("return ") or line_s.endswith("()"):
                continue
            if line_s.startswith("p(") or line_s.startswith("s(") or line_s.startswith("#") or line_s.startswith("hush()") or line_s.startswith(">>") or "=" in line_s:
                lines.append(line_s)
        code = "\n".join(lines).strip()

    code = code or text.strip()

    # Separate chained .p( into newlines: p(...).p(...) -> p(...)\np(...)
    code = re.sub(r"\)\s*\.?p\(", ")\np(", code)
    # Ensure separate pattern statements start on newlines
    code = re.sub(r"\)\s*(p\()", ")\n\\1", code)
    return code


def repair_code(code):
    """
    Auto-repair common LLM mini-notation & Python mistakes:
    1. Sample names starting with digits (e.g. 808bd -> bd, 808sd -> sd).
    2. Stray chaining dots (.p( -> p().
    3. Trailing or misplaced >> operators.
    4. Accidental function or import wrappers.
    """
    if not code:
        return ""

    # Remove markdown code fences
    cleaned = re.sub(r"```(?:python)?", "", code)
    cleaned = cleaned.replace("```", "").strip()

    # Fix chained .p(...) to newline p(...)
    cleaned = re.sub(r"\)\s*\.?p\(", ")\np(", cleaned)

    # Strip function wrappers def ...():, return ..., import ...
    lines = []
    for line in cleaned.splitlines():
        line_s = line.strip()
        if line_s.startswith("def ") or line_s.startswith("return ") or line_s.startswith("import ") or line_s.endswith("()"):
            continue
        lines.append(line_s)
    cleaned = "\n".join(lines).strip()

    # Fix sample names starting with numbers inside s("...")
    def fix_mini(match):
        pat = match.group(1)
        # 808bd -> bd, 909hh -> hh
        pat = re.sub(r"\b\d+([a-zA-Z_]+)\b", r"\1", pat)
        return f's("{pat}")'

    cleaned = re.sub(r's\(["\'](.*?)["\']\)', fix_mini, cleaned)

    # Clean up double >> or trailing >> or >> before closing paren
    cleaned = re.sub(r">>\s*>>+", ">>", cleaned)
    cleaned = re.sub(r">>\s*\)", ")", cleaned)
    cleaned = re.sub(r">>\s*$", "", cleaned, flags=re.MULTILINE)

    return cleaned


def validate_code(code):
    """
    Validate Python syntax and Vortex mini-notation grammar.
    Returns (is_valid: bool, error_type: str, error_msg: str).
    """
    if not code or not code.strip():
        return False, "EmptyCodeError", "Generated code was empty."

    # 1. Check Python syntax compilation
    try:
        compile(code, "<ai_beat>", "exec")
    except SyntaxError as se:
        return False, "PythonSyntaxError", f"Line {se.lineno}: {se.msg}"
    except Exception as e:
        return False, "PythonCompileError", str(e)

    # 2. Check Vortex mini-notation & DSL grammar via dry-run execution
    try:
        from vortex import vortex_dsl
        with vortex_dsl() as dsl:
            scope = dict(vars(dsl))
            # Mock p and hush so validation NEVER triggers audio output or leaks state
            scope["p"] = lambda key, pattern=None: pattern
            scope["hush"] = lambda: None
            exec(code, scope)
    except Exception as dsl_err:
        err_type = type(dsl_err).__name__
        return False, err_type, str(dsl_err)

    return True, "", ""


def log_model_error(model, prompt, attempt, error_type, error_msg, raw_code, auto_repaired, repaired_code=None):
    """Log an error occurrence to model_errors.json as requested by Jack."""
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "model": model,
        "prompt": prompt,
        "attempt": attempt,
        "error_type": error_type,
        "error_message": error_msg,
        "raw_code": raw_code,
        "auto_repair_succeeded": auto_repaired,
        "repaired_code": repaired_code if auto_repaired else None
    }
    try:
        entries = []
        if os.path.exists(ERROR_LOG_FILE):
            try:
                with open(ERROR_LOG_FILE, "r", encoding="utf-8") as f:
                    entries = json.load(f)
                    if not isinstance(entries, list):
                        entries = []
            except Exception:
                entries = []
        entries.append(entry)
        with open(ERROR_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
        print(f"📝 \033[1;30mLogged grammar error to {os.path.basename(ERROR_LOG_FILE)}\033[0m")
    except Exception as e:
        print(f"⚠️ Could not write to {ERROR_LOG_FILE}: {e}")


def log_model_run(model, prompt, status, attempts, elapsed, errors=None):
    """Log overall generation outcome to model_benchmark.json."""
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "model": model,
        "prompt": prompt,
        "status": status,
        "attempts": attempts,
        "elapsed_seconds": round(elapsed, 2),
        "errors": errors or []
    }
    try:
        entries = []
        if os.path.exists(BENCHMARK_LOG_FILE):
            try:
                with open(BENCHMARK_LOG_FILE, "r", encoding="utf-8") as f:
                    entries = json.load(f)
                    if not isinstance(entries, list):
                        entries = []
            except Exception:
                entries = []
        entries.append(entry)
        with open(BENCHMARK_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
    except Exception as e:
        print(f"⚠️ Could not write to {BENCHMARK_LOG_FILE}: {e}")


def display_model_scoreboard():
    """Display comparison scoreboard showing which model does the best job."""
    if not os.path.exists(BENCHMARK_LOG_FILE) and not os.path.exists(ERROR_LOG_FILE):
        print("\n📊 No benchmark data recorded yet. Generate some beats to populate the scoreboard!")
        return

    runs = []
    if os.path.exists(BENCHMARK_LOG_FILE):
        try:
            with open(BENCHMARK_LOG_FILE, "r", encoding="utf-8") as f:
                runs = json.load(f)
        except Exception:
            runs = []

    errors = []
    if os.path.exists(ERROR_LOG_FILE):
        try:
            with open(ERROR_LOG_FILE, "r", encoding="utf-8") as f:
                errors = json.load(f)
        except Exception:
            errors = []

    stats = {}
    for r in runs:
        m = r.get("model", "unknown")
        if m not in stats:
            stats[m] = {"runs": 0, "first_pass": 0, "retried": 0, "repaired": 0, "failed": 0, "errors": 0}
        stats[m]["runs"] += 1
        st = r.get("status")
        if st == "PASS_FIRST_TRY":
            stats[m]["first_pass"] += 1
        elif st == "PASS_AFTER_RETRY":
            stats[m]["retried"] += 1
        elif st == "AUTO_REPAIRED":
            stats[m]["repaired"] += 1
        elif st == "FAILED":
            stats[m]["failed"] += 1

    for e in errors:
        m = e.get("model", "unknown")
        if m not in stats:
            stats[m] = {"runs": 0, "first_pass": 0, "retried": 0, "repaired": 0, "failed": 0, "errors": 0}
        stats[m]["errors"] += 1

    print("\n" + "=" * 74)
    print("               📊 AI DJ MODEL BENCHMARK SCOREBOARD 🏆")
    print("=" * 74)
    header = f"{'Model Name':<28} {'Runs':<6} {'1st Pass':<10} {'Retried':<9} {'Errors':<8} {'Success%'}"
    print(header)
    print("-" * 74)

    for m, d in sorted(stats.items(), key=lambda x: (x[1]["first_pass"] / max(x[1]["runs"], 1)), reverse=True):
        total = d["runs"]
        success_pct = (d["first_pass"] / total * 100) if total > 0 else 0
        name = m[:27]
        print(f"{name:<28} {d['runs']:<6} {d['first_pass']:<10} {d['retried']:<9} {d['errors']:<8} {success_pct:>6.1f}%")

    print("=" * 74)
    print(f"📝 Raw error logs: {ERROR_LOG_FILE}")
    print(f"📈 Raw run logs:   {BENCHMARK_LOG_FILE}\n")


def generate_valid_beat(prompt, model_name, max_retries=3):
    """
    Generate a beat and validate its grammar before releasing it.
    If bad, records error to model_errors.json and retries with specific correction feedback.
    """
    current_prompt = prompt
    total_elapsed = 0.0
    logged_errors = []

    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            print(f"🔄 \033[1;33mRetrying generation (Attempt {attempt}/{max_retries}) with grammar feedback...\033[0m")

        raw_output, elapsed = query_ollama(current_prompt, model_name)
        total_elapsed += elapsed

        if raw_output is None:
            log_model_run(model_name, prompt, "FAILED", attempt, total_elapsed, logged_errors)
            return None

        code = clean_generated_code(raw_output)

        # Check grammar
        is_valid, err_type, err_msg = validate_code(code)

        if is_valid:
            if attempt == 1:
                print("✅ \033[1;32mGrammar check passed on first attempt!\033[0m\n")
                log_model_run(model_name, prompt, "PASS_FIRST_TRY", 1, total_elapsed, logged_errors)
            else:
                print(f"✅ \033[1;32mGrammar check passed after retry (Attempt {attempt})!\033[0m\n")
                log_model_run(model_name, prompt, "PASS_AFTER_RETRY", attempt, total_elapsed, logged_errors)
            return code

        # Grammar check failed
        print(f"⚠️ \033[1;31mGrammar check failed (Attempt {attempt}/{max_retries}):\033[0m [{err_type}] {err_msg}")
        logged_errors.append(f"{err_type}: {err_msg}")

        # Check if auto-repair can salvage it
        repaired = repair_code(code)
        rep_valid, rep_type, rep_msg = validate_code(repaired)

        # Log error to model_errors.json
        log_model_error(
            model=model_name,
            prompt=prompt,
            attempt=attempt,
            error_type=err_type,
            error_msg=err_msg,
            raw_code=code,
            auto_repaired=rep_valid,
            repaired_code=repaired if rep_valid else None
        )

        # If not last attempt, build targeted correction feedback for model
        if attempt < max_retries:
            current_prompt = (
                f"{prompt}\n\n"
                f"CORRECTION FEEDBACK: Your previous output failed grammar validation with error:\n"
                f"{err_msg}\n\n"
                f"RULES TO FIX:\n"
                f"1. Sample names must NEVER start with numbers (use 'bd' NOT '808bd', 'snare' NOT '808sd').\n"
                f"2. Return ONLY 1-3 lines of p(\"channel\", s(\"...\") >> room(0.3)).\n"
                f"3. NO imports, NO def functions, NO markdown code blocks."
            )
        else:
            # Last attempt exhausted: fallback to auto-repair if valid
            if rep_valid:
                print("🔧 \033[1;33mAuto-repaired pattern grammar successfully so beat is playable!\033[0m\n")
                log_model_run(model_name, prompt, "AUTO_REPAIRED", max_retries, total_elapsed, logged_errors)
                return repaired
            else:
                print("❌ All retry attempts failed strict grammar validation.\n")
                log_model_run(model_name, prompt, "FAILED", max_retries, total_elapsed, logged_errors)
                return code

    return None


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
        print("  [\033[1;36mB\033[0m] Benchmark / Scoreboard (see which model does best)")
        print("  [\033[1;31mH\033[0m] Hush sound")
        print("  [\033[1;37mN\033[0m] New beat prompt")
        print("  [\033[1;37mQ\033[0m] Quit")

        try:
            choice = input("Select [P/S/F/B/H/N/Q] > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = "q"

        if choice == "p":
            play_code_live(code)
        elif choice == "s":
            save_to_beat_notes(code, prompt_title)
        elif choice == "f":
            save_as_python_script(code, prompt_title)
        elif choice == "b":
            display_model_scoreboard()
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
    parser.add_argument("--retries", "-r", type=int, default=3, help="Max retry attempts on grammar failure (default: 3)")
    parser.add_argument("--scoreboard", "-s", action="store_true", help="Display model benchmark scoreboard and exit")
    args = parser.parse_args()

    # Scoreboard mode
    if args.scoreboard:
        display_model_scoreboard()
        sys.exit(0)

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
    print(f"⚙️ Timeout limit: {REQUEST_TIMEOUT}s (SSD/CPU safe)")
    print(f"🛡️ Self-Healing Grammar: Active (max retries={args.retries})")
    print("----------------------------------------------------------\n")

    # If single-shot prompt passed via CLI
    if args.prompt:
        prompt_str = " ".join(args.prompt)
        print(f"🎯 Beat Prompt: \"\033[1;35m{prompt_str}\033[0m\"")
        code = generate_valid_beat(prompt_str, active_model, max_retries=args.retries)
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
            print("  • 'fast 90s acid house with screaming bass'")
            print("  • 'celtic folk dance beat with flute and percussion'")
            user_prompt = input("\n🎵 AI DJ > ").strip()

            if not user_prompt:
                continue
            if user_prompt.lower() in ("exit", "quit", "q"):
                hush_live()
                print("👋 Bye Jack!")
                break
            if user_prompt.lower() in ("scoreboard", "benchmark", "stats"):
                display_model_scoreboard()
                continue

            code = generate_valid_beat(user_prompt, active_model, max_retries=args.retries)
            if code:
                display_code_banner(code)
                interactive_menu(code, user_prompt)

        except KeyboardInterrupt:
            hush_live()
            print("\n👋 Session ended.")
            break


if __name__ == "__main__":
    main()
