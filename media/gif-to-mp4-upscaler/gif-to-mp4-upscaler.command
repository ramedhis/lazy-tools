#!/bin/bash

# ============================================================
#                 LAZY GIF TO MP4 UPSCALER
#                       macOS Edition
# ============================================================
#
# Universal Intel + Apple Silicon
#
# Required:
#   - gifsicle
#   - ffmpeg
#
# Homebrew is only used when a required dependency is missing.
#
# ============================================================


# ------------------------------------------------------------
# Header (shown on startup and the main menu)
# ------------------------------------------------------------

print_header() {
    echo "╭──────────────────────────────────────────────╮"
    echo "│           LAZY GIF TO MP4 UPSCALER           │"
    echo "╰──────────────────────────────────────────────╯"
    echo
}


# ------------------------------------------------------------
# Reusable boxed title, used by every screen in the program.
# Keeps box width/centering consistent in one place instead
# of hand-typing borders + padding on every screen.
# ------------------------------------------------------------

print_box() {

    local title="$1"
    local width=46

    local title_len=${#title}
    local pad_l=$(( (width - title_len) / 2 ))
    local pad_r=$(( width - title_len - pad_l ))

    printf "╭%s╮\n" "$(printf '%*s' "$width" '')"
    printf "│%*s%s%*s│\n" "$pad_l" "" "$title" "$pad_r" ""
    printf "╰%s╯\n" "$(printf '%*s' "$width" '')"

}


clear
print_header


# ------------------------------------------------------------
# Goodbye screen (used whenever the program exits normally)
# ------------------------------------------------------------

show_goodbye() {

    local message="$1"

    clear

    print_box "GOODBYE! :)"
    echo

    if [ -n "$message" ]; then
        echo "$message"
        echo
    fi

    read -p "Press Enter to close..."
    exit 0

}


# ------------------------------------------------------------
# Directory the .command file lives in (output goes here)
# ------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"


# ------------------------------------------------------------
# Upscale factor (how much to scale each GIF by, e.g. x4)
# ------------------------------------------------------------

UPSCALE_FACTOR=4


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
# HELPER: INSTALL A DEPENDENCY VIA HOMEBREW
# ============================================================

install_dependency() {

    local pkg_name="$1"     # e.g. "gifsicle"
    local title="$2"        # e.g. "INSTALLING GIFSICLE"

    echo
    print_box "$title"
    echo

    brew install "$pkg_name"

    if [ $? -ne 0 ]; then

        echo
        echo "ERROR: Failed to install $pkg_name."
        echo
        echo "You can try manually with:"
        echo
        echo "  brew install $pkg_name"
        echo

        read -p "Press Enter to close..."
        exit 1

    fi

    eval "$(brew shellenv)"

    if ! command -v "$pkg_name" >/dev/null 2>&1; then

        echo
        echo "ERROR: $pkg_name was installed but could"
        echo "not be found."
        echo

        read -p "Press Enter to close..."
        exit 1

    fi

    echo
    echo "$pkg_name installed successfully."
    echo

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
    echo "  gifsicle    [v] Installed"
else
    echo "  gifsicle    [x] Not installed"
fi

if [ "$FFMPEG_INSTALLED" = true ]; then
    echo "  ffmpeg      [v] Installed"
else
    echo "  ffmpeg      [x] Not installed"
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

        print_box "MISSING COMPONENTS!"
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

        read -n 1 INSTALL_CHOICE
        echo

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

            read -n 1 BREW_CHOICE
            echo

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
                        print_box "HOMEBREW INSTALL FAILED!"
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
        install_dependency "gifsicle" "INSTALLING GIFSICLE"
    fi


    # ========================================================
    # INSTALL FFMPEG IF MISSING
    # ========================================================

    if [ "$FFMPEG_INSTALLED" = false ]; then
        install_dependency "ffmpeg" "INSTALLING FFMPEG"
    fi


    # ========================================================
    # FINAL DEPENDENCY CHECK
    # ========================================================

    echo
    print_box "COMPONENTS ARE READY!"
    echo

    if command -v gifsicle >/dev/null 2>&1; then
        echo "  gifsicle    [v] Ready"
    else
        echo "  gifsicle    [x] Missing"
    fi

    if command -v ffmpeg >/dev/null 2>&1; then
        echo "  ffmpeg      [v] Ready"
    else
        echo "  ffmpeg      [x] Missing"
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
# Main menu (the only screen that shows the header)
# ------------------------------------------------------------

show_menu() {

    clear
    print_header

    echo "Current upscale factor: x${UPSCALE_FACTOR}"
    echo

    echo "Select:"
    echo
    echo "  [O] Open GIF(s)"
    echo "  [F] Set Upscale Factor"
    echo "  [I] Info"
    echo "  [Q] Quit"
    echo

}


# ------------------------------------------------------------
# Set upscale factor screen
# ------------------------------------------------------------

set_factor() {

    while true; do

        clear

        print_box "SET UPSCALE FACTOR"
        echo
        echo "Current factor: x${UPSCALE_FACTOR}"
        echo
        echo "This multiplies each GIF's original size."
        echo "Example: x4 turns a 320x180 GIF into 1280x720."
        echo
        echo "Enter a new factor (e.g. 2, 3, 4, 1.5):"
        echo "Or press [Enter] to keep the current factor (x${UPSCALE_FACTOR})."
        echo

        read -p "Factor: " FACTOR_INPUT

        # Blank input keeps the current factor.
        if [ -z "$FACTOR_INPUT" ]; then
            break
        fi

        if [[ "$FACTOR_INPUT" =~ ^[0-9]+([.][0-9]+)?$ ]] && awk "BEGIN {exit !($FACTOR_INPUT > 0)}"; then
            UPSCALE_FACTOR="$FACTOR_INPUT"
            break
        else
            echo
            echo "Invalid input. Please enter a positive number."
            echo
            sleep 1
        fi

    done

    show_menu

}


# ------------------------------------------------------------
# Info screen
# ------------------------------------------------------------

show_info() {

    clear

    print_box "INFO"
    echo

    echo "lazy-gif-to-mp4-upscaler upscales any GIF by"
    echo "a factor you set (default x4) and converts"
    echo "it into MP4, using gifsicle and ffmpeg."
    echo

    echo "Set the factor from the main menu with [F] --"
    echo "it applies to every file you process afterward."
    echo

    echo "You can select multiple GIFs at once -- they're"
    echo "processed one at a time automatically."
    echo

    echo "Read more on README.md"
    echo
    echo "[B] Back"
    echo

}


# ------------------------------------------------------------
# Animated "..." while a background job (gifsicle/ffmpeg) runs
# ------------------------------------------------------------

animate_step() {

    local pid="$1"
    local dots=("" "." ". ." ". . .")
    local i=0

    while kill -0 "$pid" 2>/dev/null; do
        printf "\r[%d/%d] %s %-7s" "$INDEX" "$TOTAL" "$ORIGINAL_FILENAME" "${dots[$((i % 4))]}"
        i=$((i + 1))
        sleep 0.35
    done

    wait "$pid"
    return $?

}


# ------------------------------------------------------------
# Select-GIF(s) screen header (used on open + on retry)
# ------------------------------------------------------------

print_select_screen() {

    clear

    print_box "SELECT GIF(S)"
    echo

}


# ------------------------------------------------------------
# "Convert more GIF(s)?" prompt (used after each batch)
#
# Returns 0 if the user wants to convert more (loop again),
# 1 if the user wants to return to the main menu.
# ------------------------------------------------------------

ask_convert_more() {

    while true; do

        clear

        print_box "CONVERSION COMPLETE"
        echo

        echo "Current upscale factor: x${UPSCALE_FACTOR}"
        echo

        echo "Convert more GIF(s) with the same factor? [y/n]"
        echo

        read -n 1 AGAIN_CHOICE
        echo

        case "$AGAIN_CHOICE" in

            y|Y)
                return 0
                ;;

            n|N)
                return 1
                ;;

            *)
                # Loop redraws the prompt automatically
                ;;

        esac

    done

}


# ============================================================
# GIF CONVERSION FUNCTION (supports multiple files)
# ============================================================

convert_gifs() {

    while true; do

        print_select_screen

        echo "Current upscale factor: x${UPSCALE_FACTOR}"
        echo
        echo "Select one or more GIF files."
        echo "Opening Finder..."
        echo


        GIF_PATHS=$(osascript <<'APPLESCRIPT'
try
    set selectedFiles to choose file with prompt "Select GIF file(s):" of type {"com.compuserve.gif"} with multiple selections allowed
    set posixPaths to {}
    repeat with aFile in selectedFiles
        set end of posixPaths to POSIX path of aFile
    end repeat
    set AppleScript's text item delimiters to linefeed
    set pathsText to posixPaths as text
    set AppleScript's text item delimiters to ""
    return pathsText
on error
    return ""
end try
APPLESCRIPT
)


        # ----------------------------------------------------
        # User cancelled / nothing selected
        # ----------------------------------------------------

        if [ -n "$GIF_PATHS" ]; then
            break
        fi


        # ----------------------------------------------------
        # Ask whether to try again -- redraws the whole
        # screen every time, including on invalid input, so
        # nothing stacks up on repeated wrong keypresses.
        # ----------------------------------------------------

        while true; do

            print_select_screen

            echo "No GIF was selected."
            echo
            echo "Continue picking files? [y/n]"
            echo

            read -n 1 CONTINUE_CHOICE
            echo

            case "$CONTINUE_CHOICE" in

                y|Y)

                    # Open Finder again
                    break
                    ;;


                n|N)

                    # Return to the main menu
                    return 1
                    ;;


                *)

                    # Loop redraws the prompt automatically
                    ;;

            esac

        done

    done


    # --------------------------------------------------------
    # Split the returned paths into an array (bash 3.2 safe)
    # --------------------------------------------------------

    GIF_ARRAY=()

    while IFS= read -r LINE; do
        [ -n "$LINE" ] && GIF_ARRAY+=("$LINE")
    done <<< "$GIF_PATHS"

    TOTAL=${#GIF_ARRAY[@]}


    # --------------------------------------------------------
    # Output folders (next to this .command file)
    # --------------------------------------------------------

    OUT_DIR="$SCRIPT_DIR/Output"
    GIF_OUT_DIR="$OUT_DIR/GIF"
    MP4_OUT_DIR="$OUT_DIR/MP4"

    mkdir -p "$GIF_OUT_DIR"
    mkdir -p "$MP4_OUT_DIR"


    # --------------------------------------------------------
    # Process each file, one status line per file
    # --------------------------------------------------------

    clear

    print_box "PROCESSING GIFS"
    echo

    echo "$TOTAL file(s) selected."
    echo "Upscale factor: x${UPSCALE_FACTOR}"
    echo

    SUCCESS_COUNT=0
    FAIL_COUNT=0
    INDEX=0


    for GIF_PATH in "${GIF_ARRAY[@]}"; do

        INDEX=$((INDEX + 1))

        ORIGINAL_FILENAME="$(basename "$GIF_PATH")"
        FILENAME="${ORIGINAL_FILENAME%.*}"


        # Find an unused output filename for this file
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


        gifsicle \
            --scale "$UPSCALE_FACTOR" \
            --resize-method sample \
            "$GIF_PATH" \
            -o "$UPSCALED_GIF" >/dev/null 2>&1 &

        animate_step $!

        if [ $? -ne 0 ]; then
            printf "\r[%d/%d] %s [FAILED (gifsicle)]          \n" "$INDEX" "$TOTAL" "$ORIGINAL_FILENAME"
            FAIL_COUNT=$((FAIL_COUNT + 1))
            continue
        fi


        ffmpeg \
            -f gif \
            -i "$UPSCALED_GIF" \
            -pix_fmt yuv420p \
            -c:v libx264 \
            "$OUTPUT_MP4" >/dev/null 2>&1 &

        animate_step $!

        if [ $? -ne 0 ]; then
            printf "\r[%d/%d] %s [FAILED (ffmpeg)]          \n" "$INDEX" "$TOTAL" "$ORIGINAL_FILENAME"
            FAIL_COUNT=$((FAIL_COUNT + 1))
            continue
        fi


        printf "\r[%d/%d] %s [done]          \n" "$INDEX" "$TOTAL" "$ORIGINAL_FILENAME"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))

    done


    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    echo
    print_box "COMPLETE!"
    echo

    echo "Processed: $SUCCESS_COUNT / $TOTAL succeeded"

    if [ "$FAIL_COUNT" -gt 0 ]; then
        echo "           $FAIL_COUNT failed"
    fi

    echo

    echo "Output folder:"
    echo "  $OUT_DIR"
    echo


    # Open output folder
    open "$OUT_DIR"


    return 0
}


# ============================================================
# MAIN MENU
# ============================================================

show_menu


while true; do

    read -n 1 MAIN_CHOICE
    echo

    case "$MAIN_CHOICE" in

        o|O)

            # Keep the user in the conversion flow until they
            # choose N, which returns them to the main menu.
            while true; do

                convert_gifs

                # If the user cancelled the Finder selection,
                # return to the main menu.
                if [ $? -ne 0 ]; then
                    show_menu
                    break
                fi

                if ask_convert_more; then
                    continue
                else
                    show_menu
                    break
                fi

            done
            ;;


        f|F)

            set_factor
            ;;


        i|I)

            show_info

            while true; do

                read -n 1 INFO_CHOICE
                echo

                case "$INFO_CHOICE" in

                    b|B)

                        show_menu
                        break
                        ;;


                    *)

                        show_info
                        ;;

                esac

            done
            ;;


        q|Q)

            show_goodbye
            ;;


        *)

            show_menu
            ;;

    esac

done
