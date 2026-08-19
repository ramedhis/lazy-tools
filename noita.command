#!/bin/bash

# ============================================================
#              NOITA GIF UPSCALER & CONVERTER
#                       macOS Edition
# ============================================================
#
# For Universal Intel + Apple Silicon
#
# Required:
#   - gifsicle
#   - ffmpeg
#
# Homebrew is only used when a required dependency is missing.
#
# ============================================================


# ------------------------------------------------------------
# Header (reusable, so we can reprint it after clearing)
# ------------------------------------------------------------

print_header() {
    echo "================================================"
    echo "       NOITA GIF UPSCALER & CONVERTER (x4)"
    echo "                  macOS Edition"
    echo "================================================"
    echo
}

clear
print_header


# ------------------------------------------------------------
# Detect architecture
# ------------------------------------------------------------

ARCH="$(uname -m)"

case "$ARCH" in
    arm64)
        ARCH_NAME="Apple Silicon"
        ;;
    x86_64)
        ARCH_NAME="Intel"
        ;;
    *)
        ARCH_NAME="Unknown"
        ;;
esac

MACOS_VERSION="$(sw_vers -productVersion)"

echo "Checking required components..."
echo
echo "macOS:        $MACOS_VERSION"
echo "Architecture: $ARCH_NAME ($ARCH)"
echo


# ============================================================
# HELPER: LOAD HOMEBREW
# ============================================================

load_homebrew() {

    # Homebrew already available in PATH
    if command -v brew >/dev/null 2>&1; then
        eval "$(brew shellenv)"
        return 0
    fi

    # Apple Silicon default location
    if [ -x "/opt/homebrew/bin/brew" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
        return 0
    fi

    # Intel default location
    if [ -x "/usr/local/bin/brew" ]; then
        eval "$(/usr/local/bin/brew shellenv)"
        return 0
    fi

    return 1
}


# ============================================================
# CHECK DEPENDENCIES
# ============================================================

GIFSICLE_INSTALLED=false
FFMPEG_INSTALLED=false

if command -v gifsicle >/dev/null 2>&1; then
    GIFSICLE_INSTALLED=true
fi

if command -v ffmpeg >/dev/null 2>&1; then
    FFMPEG_INSTALLED=true
fi


# ------------------------------------------------------------
# Show dependency status
# ------------------------------------------------------------

if [ "$GIFSICLE_INSTALLED" = true ]; then
    echo "gifsicle    [v] Installed"
else
    echo "gifsicle    [x] Not installed"
fi

if [ "$FFMPEG_INSTALLED" = true ]; then
    echo "ffmpeg      [v] Installed"
else
    echo "ffmpeg      [x] Not installed"
fi

echo


# ============================================================
# DETERMINE WHAT IS MISSING
# ============================================================

MISSING_COUNT=0

if [ "$GIFSICLE_INSTALLED" = false ]; then
    MISSING_COUNT=$((MISSING_COUNT + 1))
fi

if [ "$FFMPEG_INSTALLED" = false ]; then
    MISSING_COUNT=$((MISSING_COUNT + 1))
fi


# ============================================================
# SOMETHING IS MISSING
# ============================================================

if [ "$MISSING_COUNT" -gt 0 ]; then

    print_missing_prompt() {

        clear
        print_header

        echo "================================================"
        echo "          MISSING COMPONENTS"
        echo "================================================"
        echo

        if [ "$MISSING_COUNT" -eq 2 ]; then

            echo "Two required components are missing:"
            echo
            echo "  [x] gifsicle > gifsicle is used to upscale the GIF."
            echo "  [x] ffmpeg   > ffmpeg is used to convert the GIF into MP4."
            echo

            echo "Install them automatically? [y/n]"
            echo

        else

            echo "One required component is missing:"
            echo

            if [ "$GIFSICLE_INSTALLED" = false ]; then
                echo "  [x] gifsicle"
                echo
                echo "gifsicle is used to upscale the GIF."
            fi

            if [ "$FFMPEG_INSTALLED" = false ]; then
                echo "  [x] ffmpeg"
                echo
                echo "ffmpeg is used to convert the GIF into MP4."
            fi

            echo
            echo "Install it automatically? [y/n]"
            echo

        fi

    }

    print_missing_prompt


    # ========================================================
    # ASK WHETHER TO INSTALL
    # ========================================================

    while true; do

        read -p "Choice: " INSTALL_CHOICE

        case "$INSTALL_CHOICE" in

            y|Y)
                break
                ;;

            n|N)

                echo
                echo "Installation cancelled."
                echo
                echo "This program cannot run without"
                echo "the required components."
                echo
                echo "Goodbye."
                echo

                read -p "Press Enter to close..."
                exit 0
                ;;

            *)

                print_missing_prompt
                ;;

        esac

    done


    # ========================================================
    # CHECK FOR HOMEBREW
    # ========================================================

    echo
    echo "Preparing installation..."
    echo

    if load_homebrew; then

        echo "Homebrew: [v] Found"
        echo "Location:  $(brew --prefix)"
        echo

    else

        print_brew_prompt() {

            clear
            print_header

            echo "Homebrew is not installed."
            echo
            echo "Homebrew is needed to install the missing"
            echo "components automatically."
            echo

            echo "Install Homebrew? [y/n]"
            echo

        }

        print_brew_prompt


        while true; do

            read -p "Choice: " BREW_CHOICE

            case "$BREW_CHOICE" in

                y|Y)

                    echo
                    echo "Starting the official Homebrew installer..."
                    echo
                    echo "The installer may ask for your Mac password."
                    echo

                    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

                    BREW_RESULT=$?


                    if [ $BREW_RESULT -ne 0 ]; then

                        echo
                        echo "================================================"
                        echo "           HOMEBREW INSTALL FAILED"
                        echo "================================================"
                        echo
                        echo "Homebrew could not be installed."
                        echo

                        read -p "Press Enter to close..."
                        exit 1

                    fi


                    # Try to load newly installed Homebrew
                    if ! load_homebrew; then

                        echo
                        echo "Homebrew was installed, but this program"
                        echo "could not find it yet."
                        echo
                        echo "Please restart the program."
                        echo

                        read -p "Press Enter to close..."
                        exit 1

                    fi


                    echo
                    echo "Homebrew installed successfully!"
                    echo
                    echo "Location:"
                    echo "  $(brew --prefix)"
                    echo

                    break
                    ;;


                n|N)

                    echo
                    echo "Homebrew installation cancelled."
                    echo
                    echo "The required components cannot be"
                    echo "installed automatically."
                    echo
                    echo "Program ending."
                    echo

                    read -p "Press Enter to close..."
                    exit 0
                    ;;


                *)

                    print_brew_prompt
                    ;;

            esac

        done

    fi


    # ========================================================
    # INSTALL GIFSICLE IF MISSING
    # ========================================================

    if [ "$GIFSICLE_INSTALLED" = false ]; then

        echo
        echo "================================================"
        echo "              INSTALLING GIFSICLE"
        echo "================================================"
        echo

        brew install gifsicle


        if [ $? -ne 0 ]; then

            echo
            echo "ERROR: Failed to install gifsicle."
            echo
            echo "You can try manually with:"
            echo
            echo "  brew install gifsicle"
            echo

            read -p "Press Enter to close..."
            exit 1

        fi


        eval "$(brew shellenv)"


        if ! command -v gifsicle >/dev/null 2>&1; then

            echo
            echo "ERROR: gifsicle was installed but could"
            echo "not be found."
            echo

            read -p "Press Enter to close..."
            exit 1

        fi


        echo
        echo "gifsicle installed successfully."
        echo

    fi


    # ========================================================
    # INSTALL FFMPEG IF MISSING
    # ========================================================

    if [ "$FFMPEG_INSTALLED" = false ]; then

        echo
        echo "================================================"
        echo "               INSTALLING FFMPEG"
        echo "================================================"
        echo

        brew install ffmpeg


        if [ $? -ne 0 ]; then

            echo
            echo "ERROR: Failed to install ffmpeg."
            echo
            echo "You can try manually with:"
            echo
            echo "  brew install ffmpeg"
            echo

            read -p "Press Enter to close..."
            exit 1

        fi


        eval "$(brew shellenv)"


        if ! command -v ffmpeg >/dev/null 2>&1; then

            echo
            echo "ERROR: ffmpeg was installed but could"
            echo "not be found."
            echo

            read -p "Press Enter to close..."
            exit 1

        fi


        echo
        echo "ffmpeg installed successfully."
        echo

    fi


    # ========================================================
    # FINAL DEPENDENCY CHECK
    # ========================================================

    echo
    echo "================================================"
    echo "          COMPONENTS ARE READY"
    echo "================================================"
    echo

    if command -v gifsicle >/dev/null 2>&1; then
        echo "gifsicle    [v] Ready"
    else
        echo "gifsicle    [x] Missing"
    fi

    if command -v ffmpeg >/dev/null 2>&1; then
        echo "ffmpeg      [v] Ready"
    else
        echo "ffmpeg      [x] Missing"
    fi

    echo

fi


# ============================================================
# EVERYTHING IS READY
# ============================================================

echo "Everything is ready."
echo
sleep 1


# ------------------------------------------------------------
# Clear clutter, reprint header, show a clean menu
# ------------------------------------------------------------

show_menu() {
    clear
    print_header
    echo
    echo "Select:"
    echo
    echo "  [O] Open GIF"
    echo "  [Q] Quit"
    echo
}


# ============================================================
# GIF CONVERSION FUNCTION
# ============================================================

convert_gif() {

    clear
    print_header
    echo "================================================"
    echo "              SELECT NOITA GIF"
    echo "================================================"
    echo

    echo "Opening Finder..."
    echo


    GIF_PATH=$(osascript <<'APPLESCRIPT'
try
    set selectedFile to choose file with prompt "Select a Noita animated screenshot:" of type {"com.compuserve.gif"}
    POSIX path of selectedFile
on error
    return ""
end try
APPLESCRIPT
)


    # --------------------------------------------------------
    # User cancelled
    # --------------------------------------------------------

    if [ -z "$GIF_PATH" ]; then

        echo
        echo "No file selected."
        echo

        return 1

    fi


    GIF_PATH="${GIF_PATH%$'\n'}"


    # --------------------------------------------------------
    # File information
    # --------------------------------------------------------

    GIF_DIR="$(dirname "$GIF_PATH")"

    ORIGINAL_FILENAME="$(basename "$GIF_PATH")"

    FILENAME="${ORIGINAL_FILENAME%.*}"


    # --------------------------------------------------------
    # Output folders
    # --------------------------------------------------------

    OUT_DIR="$GIF_DIR/Output"
    GIF_OUT_DIR="$OUT_DIR/GIF"
    MP4_OUT_DIR="$OUT_DIR/MP4"

    mkdir -p "$GIF_OUT_DIR"
    mkdir -p "$MP4_OUT_DIR"


    # --------------------------------------------------------
    # Find unused output filename
    #
    # Both files always receive the same suffix.
    #
    # Example:
    #
    # Screenshot-Upscaled.gif
    # Screenshot-Video.mp4
    #
    # Screenshot-Upscaled (1).gif
    # Screenshot-Video (1).mp4
    # --------------------------------------------------------

    SUFFIX=""

    COUNTER=1


    while true; do

        UPSCALED_GIF="$GIF_OUT_DIR/${FILENAME}-Upscaled${SUFFIX}.gif"

        OUTPUT_MP4="$MP4_OUT_DIR/${FILENAME}-Video${SUFFIX}.mp4"


        if [ ! -e "$UPSCALED_GIF" ] && [ ! -e "$OUTPUT_MP4" ]; then
            break
        fi


        SUFFIX=" ($COUNTER)"

        COUNTER=$((COUNTER + 1))

    done


    # --------------------------------------------------------
    # Tell user if duplicate was found
    # --------------------------------------------------------

    if [ -n "$SUFFIX" ]; then

        echo
        echo "An output with this name already exists."
        echo
        echo "Using the next available name:"
        echo
        echo "  ${FILENAME}-Upscaled${SUFFIX}.gif"
        echo "  ${FILENAME}-Video${SUFFIX}.mp4"
        echo

    fi


    # ========================================================
    # UPSCALE GIF
    # ========================================================

    clear
    print_header
    echo "================================================"
    echo "                UPSCALING GIF"
    echo "================================================"
    echo

    echo "Original:"
    echo "  $ORIGINAL_FILENAME"
    echo

    echo "Target resolution:"
    echo "  2560 x 1440"
    echo

    echo "Output:"
    echo "  $(basename "$UPSCALED_GIF")"
    echo

    echo "Processing..."
    echo


    gifsicle \
        --resize 2560x1440 \
        --resize-method sample \
        "$GIF_PATH" \
        -o "$UPSCALED_GIF"


    if [ $? -ne 0 ]; then

        echo
        echo "ERROR: Gifsicle failed."
        echo

        return 1

    fi


    echo
    echo "Upscaled GIF complete."
    echo
    echo "Saved to:"
    echo "  $UPSCALED_GIF"


    # ========================================================
    # CONVERT GIF -> MP4
    # ========================================================

    clear
    print_header
    echo "================================================"
    echo "                 CREATING MP4"
    echo "================================================"
    echo

    echo "Output:"
    echo "  $(basename "$OUTPUT_MP4")"
    echo

    echo "Processing..."
    echo


    ffmpeg \
        -f gif \
        -i "$UPSCALED_GIF" \
        -pix_fmt yuv420p \
        -c:v libx264 \
        "$OUTPUT_MP4"


    if [ $? -ne 0 ]; then

        echo
        echo "ERROR: FFmpeg failed."
        echo

        return 1

    fi


    # ========================================================
    # COMPLETE
    # ========================================================

    clear
    print_header
    echo "================================================"
    echo "                  COMPLETE!"
    echo "================================================"
    echo

    echo "Upscaled GIF:"
    echo "  $UPSCALED_GIF"
    echo

    echo "MP4:"
    echo "  $OUTPUT_MP4"
    echo


    # Open output folder
    open "$OUT_DIR"


    return 0
}


# ============================================================
# INITIAL MENU
# ============================================================

show_menu


while true; do

    read -p "Choice: " MAIN_CHOICE

    case "$MAIN_CHOICE" in

        o|O)

            convert_gif
            break
            ;;


        q|Q)

            clear
            print_header
            echo "================================================"
            echo "                   GOODBYE."
            echo "================================================"
            echo

            read -p "Press Enter to close..."
            exit 0
            ;;


        *)

            show_menu
            ;;

    esac

done


# ============================================================
# REPEAT CONVERSION LOOP
# ============================================================

while true; do

    clear
    print_header
    echo "Convert another GIF? [y/n]"
    echo


    while true; do

        read -p "Choice: " AGAIN_CHOICE

        case "$AGAIN_CHOICE" in

            y|Y)

                echo
                echo "Opening the file selector..."
                echo

                # Finder opens immediately
                convert_gif

                # After conversion, ask again
                break
                ;;


            n|N)

                clear
                print_header
                echo "================================================"
                echo "                   GOODBYE."
                echo "================================================"
                echo
                echo "Thanks for using Noita GIF Upscaler & Converter! :-)"
                echo

                read -p "Press Enter to close..."
                exit 0
                ;;


            *)

                clear
                print_header
                echo "Convert another GIF? [y/n]"
                echo

                ;;

        esac

    done

done
