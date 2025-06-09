# Trial_Run

## Project Overview
This repository contains the initial work for a Raspberry Pi–based voice chatbot. The goal is to embed a Pi 4 inside a plastic skull with a microphone and speaker so it can converse using OpenAI and sound like Bob the skull from *The Dresden Files*. Responses will be generated using the OpenAI API and read aloud via a text-to-speech engine.

## Getting Started
1. **Install Python 3** (if not already present)
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-pip
   ```
2. **Install required libraries**
   ```bash
   pip install speechrecognition pyttsx3 openai
   ```
   You can substitute another text-to-speech engine if preferred.
3. **Configure your OpenAI API key**
   ```bash
   export OPENAI_API_KEY=<your-api-key>
   ```
   Add this line to your shell profile (e.g., `.bashrc`) so the application can access the key at runtime.

