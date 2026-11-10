# lazy-gif-to-mp4-upscaler

A simple, lazy script for upscaling any GIF and converting it to MP4 -- no need to touch config files or flags.
Supports both Intel and Apple Silicon Macs.

Originally was meant for upscaling GIFs exported from Noita game, then decided to make it universal purpose.

The script relies on these tools and will offer to install them automatically if missing:
- [gifsicle](https://www.lcdf.org/gifsicle/)
- [ffmpeg](https://ffmpeg.org)
- [Homebrew](https://brew.sh)

## Usage

1. Double-click `lazy-gif-to-mp4-upscaler.command`, or run it from Terminal:
   ```
   ./lazy-gif-to-mp4-upscaler.command
   ```
2. The script checks for `gifsicle` and `ffmpeg`. If either is missing, it offers to install them for you via Homebrew.
3. From the main menu, press `O` to open GIF(s), `F` to set the upscale factor, `I` for info, or `Q` to quit.
4. A Finder dialog opens -- select one or more GIF files to process.
5. Each file is upscaled by a configurable factor (default x4) using `gifsicle`, then converted to MP4 using `ffmpeg`, one at a time.
6. The output folder opens automatically once processing is complete.

## Output

After selecting your GIF(s), the script creates:

```
path/to/Output/
├── GIF/
│   └── MyClip-Upscaled.gif
└── MP4/
    └── MyClip-Video.mp4
```

