"""
Vortex Raven Glass Studio - Vulkan-Powered Retained Mode Music Studio.
Created by Esperanza for Jack.
"""

import datetime
import os
import signal
import subprocess
import sys
import threading
import time

import raven as r
from vortex import vortex_dsl

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

XML = """
<Window Title="⚡ Vortex Glass Studio (Vulkan Powered)" Width="840" Height="680" Theme="RavenGlassDark">
    <Border Padding="20" Material="Glass" CornerRadius="16" Background="#11111bee">
        <VBox Spacing="16">
            <!-- Header Title -->
            <VBox Spacing="4">
                <HBox Spacing="12">
                    <Label Text="🎵 VORTEX GLASS STUDIO" TextSize="24" Color.Text="#89b4fa"/>
                    <Label Text="⚡ VULKAN 60FPS" TextSize="12" Color.Text="#a6e3a1" Slot.VAlign="Center"/>
                </HBox>
                <Label Text="Next-Gen Algorithmic Live Coding DAW by Esperanza &amp; Jack" TextSize="13" Color.Text="#6c7086"/>
            </VBox>

            <!-- Quick Jam Presets Panel -->
            <Border Padding="12" Material="Glass" CornerRadius="10" Background="#1e1e2ebb" BorderColor="#313244">
                <VBox Spacing="8">
                    <Label Text="🎹 ONE-CLICK BEAT LAUNCHER" TextSize="13" Color.Text="#fab387"/>
                    <HBox Spacing="8">
                        <Button Text="🔥 Acid House" Style="Primary" OnClicked="play.acid" Slot.Fill="1"/>
                        <Button Text="⚡ Jungle Amen" Style="Primary" OnClicked="play.jungle" Slot.Fill="1"/>
                        <Button Text="💥 808 Trap" Style="Primary" OnClicked="play.trap" Slot.Fill="1"/>
                        <Button Text="🌌 Ambient Arp" Style="Primary" OnClicked="play.ambient" Slot.Fill="1"/>
                    </HBox>
                </VBox>
            </Border>

            <!-- Live Slider Controls -->
            <Border Padding="12" Material="Glass" CornerRadius="10" Background="#1e1e2ebb" BorderColor="#313244">
                <VBox Spacing="10">
                    <Label Text="🎛️ REAL-TIME TWEAKERS" TextSize="13" Color.Text="#89dceb"/>
                    <HBox Spacing="16">
                        <VBox Spacing="4" Slot.Fill="1">
                            <Label Name="speed_label" Text="⚡ Playback Speed / Pitch: 1.0x" TextSize="12" Color.Text="#cdd6f4"/>
                            <Slider Name="speed_slider" Min="50" Max="200" Value="100" OnChanged="slider.speed"/>
                        </VBox>
                        <VBox Spacing="4" Slot.Fill="1">
                            <Label Name="room_label" Text="🌊 Reverb Room: 35%" TextSize="12" Color.Text="#cdd6f4"/>
                            <Slider Name="room_slider" Min="0" Max="100" Value="35" OnChanged="slider.room"/>
                        </VBox>
                    </HBox>
                </VBox>
            </Border>

            <!-- Custom Mini-Notation Pattern Box -->
            <Border Padding="12" Material="Glass" CornerRadius="10" Background="#1e1e2ebb" BorderColor="#313244">
                <VBox Spacing="8">
                    <Label Text="✍️ LIVE MINI-NOTATION PATTERN" TextSize="13" Color.Text="#f9e2af"/>
                    <HBox Spacing="8">
                        <TextInput Name="pattern_input" Text="bd*4 [~ cp]*2 hh*8" Placeholder="Type mini-notation e.g. amencutup*8 or bd*4..." Slot.Fill="1"/>
                        <Button Text="▶ Run Custom" Style="Primary" OnClicked="play.custom"/>
                    </HBox>
                </VBox>
            </Border>

            <!-- Audio Recording & Playback Bar -->
            <Border Padding="12" Material="Glass" CornerRadius="10" Background="#1e1e2ebb" BorderColor="#313244">
                <HBox Spacing="10">
                    <Button Name="rec_btn" Text="⏺ Record MP3" Style="Danger" OnClicked="audio.record" Slot.Fill="1"/>
                    <Button Name="play_mp3_btn" Text="▶ Play Last MP3" Style="Primary" OnClicked="audio.play_mp3" Slot.Fill="1"/>
                    <Button Text="🛑 STOP ALL (Hush)" Style="Secondary" OnClicked="play.hush" Slot.Fill="1"/>
                </HBox>
            </Border>

            <!-- Status Bar -->
            <Border Padding="10" CornerRadius="8" Background="#11111b" BorderColor="#313244">
                <HBox Spacing="8">
                    <Label Text="Status:" TextSize="13" Color.Text="#89b4fa"/>
                    <Label Name="status" Text="Ready to Jam! Click a beat or hit Record MP3." TextSize="13" Color.Text="#a6e3a1" Slot.Fill="1"/>
                </HBox>
            </Border>
        </VBox>
    </Border>
</Window>
"""


def run_raven_studio():
    # Handle Ctrl+C cleanly
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    print("⚡ Initializing Raven Vulkan backend...")
    if not r.Rinit(r.R_BACKEND_VULKAN):
        print("❌ Could not initialize Vulkan backend.")
        return 1

    with vortex_dsl() as v:
        window = r.Rwindow_create_from_xml(XML)
        if not window:
            print("❌ Failed to parse Raven XML.")
            r.Rshutdown()
            return 1

        # Find UI Widgets
        status_lbl = r.Rwidget_find(window, "status")
        speed_slider = r.Rwidget_find(window, "speed_slider")
        speed_lbl = r.Rwidget_find(window, "speed_label")
        room_slider = r.Rwidget_find(window, "room_slider")
        room_lbl = r.Rwidget_find(window, "room_label")
        pattern_input = r.Rwidget_find(window, "pattern_input")
        rec_btn = r.Rwidget_find(window, "rec_btn")
        play_mp3_btn = r.Rwidget_find(window, "play_mp3_btn")

        # Studio state
        state = {
            "speed": 1.0,
            "room": 0.35,
            "current_pattern_code": None,
            "is_recording": False,
            "record_proc": None,
            "last_mp3": None,
            "play_proc": None,
        }

        def set_status(msg):
            r.Rlabel_set_text(status_lbl, msg)

        def play_pattern(pat_str, name="live"):
            try:
                state["current_pattern_code"] = pat_str
                spd = state["speed"]
                rm = state["room"]
                v.p(name, v.s(pat_str) >> v.speed(spd) >> v.room(rm))
                set_status(f"▶ Playing: {pat_str} (speed: {spd:.2f}x, room: {rm:.2f})")
            except Exception as e:
                set_status(f"⚠️ Error: {e}")

        # Bind Beat Launcher buttons
        def on_acid(sender, action, user_data):
            v.hush()
            spd = state["speed"]
            rm = state["room"]
            v.p("acid", v.s(v.stack("gabba*4", "cp*2").every(3, v.fast(2))) >> v.speed(spd) >> v.room(rm))
            set_status("🔥 Playing: Acid House & Claps!")

        def on_jungle(sender, action, user_data):
            v.hush()
            play_pattern("amencutup*8", "jungle")
            set_status("⚡ Playing: UK Jungle Amen Break!")

        def on_trap(sender, action, user_data):
            v.hush()
            spd = state["speed"]
            rm = state["room"]
            v.p("trap", v.s(v.stack("808bd*2", "[~ 808sd]", "[~ 808oh]*2", "808*4")) >> v.speed(spd) >> v.room(rm))
            set_status("💥 Playing: Deep 808 Trap & Bounce!")

        def on_ambient(sender, action, user_data):
            v.hush()
            spd = state["speed"]
            rm = state["room"]
            v.p("ambient", v.s("arpy*8") >> v.speed(spd) >> v.room(rm) >> v.size(0.9))
            set_status("🌌 Playing: Ambient Sci-Fi Arpeggios!")

        def on_hush(sender, action, user_data):
            v.hush()
            if state["play_proc"]:
                try:
                    state["play_proc"].terminate()
                except:
                    pass
                state["play_proc"] = None
            set_status("🛑 HUSH: All sound silenced.")

        def on_custom(sender, action, user_data):
            text = r.Rtext_input_get_text(pattern_input)
            if text:
                v.hush()
                play_pattern(text.strip(), "custom")

        # Bind Sliders
        def on_speed(sender, action, user_data):
            val = r.Rslider_get_value(speed_slider) / 100.0
            state["speed"] = val
            r.Rlabel_set_text(speed_lbl, f"⚡ Playback Speed / Pitch: {val:.2f}x")
            if state["current_pattern_code"]:
                play_pattern(state["current_pattern_code"])

        def on_room(sender, action, user_data):
            val = r.Rslider_get_value(room_slider) / 100.0
            state["room"] = val
            r.Rlabel_set_text(room_lbl, f"🌊 Reverb Room: {int(val * 100)}%")
            if state["current_pattern_code"]:
                play_pattern(state["current_pattern_code"])

        # Bind MP3 Recording
        def on_record(sender, action, user_data):
            if not state["is_recording"]:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                mp3_path = os.path.join(RECORDINGS_DIR, f"vortex_glass_{timestamp}.mp3")
                ffmpeg_bin = "/usr/local/bin/ffmpeg"
                if not os.path.exists(ffmpeg_bin):
                    ffmpeg_bin = "ffmpeg"
                cmd = [
                    ffmpeg_bin, "-y", "-f", "pulse", "-i", "default.monitor",
                    "-b:a", "192k", mp3_path
                ]
                try:
                    state["record_proc"] = subprocess.Popen(
                        cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    state["is_recording"] = True
                    state["last_mp3"] = mp3_path
                    r.Rbutton_set_text(rec_btn, "⏹ Stop REC")
                    set_status(f"🔴 RECORDING: Capturing live audio to MP3...")
                except Exception as e:
                    set_status(f"⚠️ Recording failed: {e}")
            else:
                state["is_recording"] = False
                r.Rbutton_set_text(rec_btn, "⏺ Record MP3")
                if state["record_proc"]:
                    try:
                        state["record_proc"].communicate(input=b"q", timeout=2)
                    except:
                        state["record_proc"].kill()
                    state["record_proc"] = None

                if state["last_mp3"] and os.path.exists(state["last_mp3"]):
                    size_kb = os.path.getsize(state["last_mp3"]) / 1024
                    base = os.path.basename(state["last_mp3"])
                    r.Rbutton_set_text(play_mp3_btn, f"▶ Play {base[:10]}...")
                    set_status(f"🎉 Saved MP3: {base} ({size_kb:.1f} KB)!")

        # Bind MP3 Playback
        def on_play_mp3(sender, action, user_data):
            if state["play_proc"]:
                try:
                    state["play_proc"].terminate()
                except:
                    pass
                state["play_proc"] = None
                r.Rbutton_set_text(play_mp3_btn, "▶ Play MP3")
                set_status("⏹ MP3 playback stopped.")
                return

            if state["last_mp3"] and os.path.exists(state["last_mp3"]):
                try:
                    state["play_proc"] = subprocess.Popen(
                        ["pw-play", state["last_mp3"]],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    r.Rbutton_set_text(play_mp3_btn, "⏹ Stop MP3")
                    set_status(f"🎵 Playing MP3: {os.path.basename(state['last_mp3'])}")
                except Exception as e:
                    set_status(f"⚠️ Playback error: {e}")
            else:
                set_status("⚠️ No recorded MP3 yet. Click [⏺ Record MP3] first!")

        # Register all Raven actions
        r.Raction_bind("play.acid", on_acid)
        r.Raction_bind("play.jungle", on_jungle)
        r.Raction_bind("play.trap", on_trap)
        r.Raction_bind("play.ambient", on_ambient)
        r.Raction_bind("play.hush", on_hush)
        r.Raction_bind("play.custom", on_custom)
        r.Raction_bind("slider.speed", on_speed)
        r.Raction_bind("slider.room", on_room)
        r.Raction_bind("audio.record", on_record)
        r.Raction_bind("audio.play_mp3", on_play_mp3)

        print("⚡ Vortex Raven Glass Studio running! Entering frame loop...")
        while r.Rwait_frame(-1.0):
            pass

        r.Rshutdown()
        print("⚡ Raven Studio closed cleanly.")
        return 0


if __name__ == "__main__":
    sys.exit(run_raven_studio())
