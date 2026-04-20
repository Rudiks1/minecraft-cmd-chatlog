# MC-Chat-Mirror
A Python-based tool designed to display your Minecraft chat in real-time directly from the command line.

## Usage
 1. File Path: Set the correct path to your Minecraft client's `latest.log` file within the code.
 2. Encoding Fix: If you play on servers with special characters (like Hungarian), add the following line to your Minecraft client's JVM launch arguments to ensure proper UTF-8 logging: `-Dfile.encoding=UTF-8`
 3. Filtering: Use the built-in Blacklist to hide specific messages or users. Use the Filter List if you want to scan for specific content or keywords.
 4. Launch: Run the script via terminal or simply click the "Start" button on the UI.
