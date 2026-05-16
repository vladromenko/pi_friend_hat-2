# pi_friend

Clean Raspberry Pi voice assistant project.

Default Stage 1:
- press Enter in terminal
- record 4 seconds from microphone
- transcribe with local whisper.cpp
- ask local hailo-ollama
- speak with local Piper
- play through USB speaker

## Install

```bash
cd /home/vlados/pi_friend
./install.sh
