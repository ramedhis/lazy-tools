# noita-gif-upscaler
 
A simple terminal tool for upscaling Noita exported GIFs and converting them to MP4.
Supports both Intel and Apple Silicon Macs.
 
## Requirements
 
The script relies on these tools and will offer to install them automatically if missing:
- [gifsicle](https://www.lcdf.org/gifsicle/)
- [ffmpeg](https://ffmpeg.org)
- [Homebrew](https://brew.sh)
## Features
 
- Upscales GIFs to 2560x1440 using `gifsicle`
- Converts the upscaled GIF into an MP4 using `ffmpeg`
- Automatically checks for and installs missing dependencies (via Homebrew)
- Simple terminal menu — no need to touch config files or flags
- Keeps upscaled GIFs and MP4s organized into separate output folders
- Avoids overwriting existing files by auto-numbering duplicates
## Usage
 
1. Double-click `noita-gif-upscaler.command`, or run it from Terminal:
```
   ./noita-gif-upscaler.command
```
2. The script checks for `gifsicle` and `ffmpeg`. If either is missing, it offers to install them for you via Homebrew.
3. From the main menu, press `O` to open a GIF, or `Q` to quit.
4. A Finder dialog opens — select the Noita GIF you want to process.
5. The script upscales the GIF, then converts it to MP4.
6. The output folder opens automatically once processing is complete.
## Output
 
After selecting the GIF, the script creates:
 
```
path/to/Output/
├── GIF/
│   └── MyClip-Upscaled.gif
└── MP4/
    └── MyClip-Video.mp4
```
 
