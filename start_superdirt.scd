// SuperDirt Startup Script for Vortex / TidalCycles
(
s.options.numBuffers = 1024 * 256;
s.options.memSize = 8192 * 32;
s.options.maxNodes = 1024 * 32;
s.options.numWireBufs = 64;
s.options.numOutputBusChannels = 2;
s.options.numInputBusChannels = 2;

s.waitForBoot {
    ~dirt = SuperDirt(2, s);
    ~dirt.loadSoundFiles("~/.local/share/SuperCollider/downloaded-quarks/Dirt-Samples/*".standardizePath);
    s.sync;
    ~dirt.start(57120, [0, 0]);
    "".postln;
    "============================================================".postln;
    "  * SUPERDIRT IS READY & LISTENING ON PORT 57120 *          ".postln;
    "  You can now start Vortex and make music!                  ".postln;
    "  (Keep this terminal open while live coding)               ".postln;
    "============================================================".postln;
    "".postln;
};
);
