# mediaconv_v2

- Converts video files to .mp4 format, optimizing for compatibility and file size.
- This script assumes a basic understanding of Python and some exposure to FFmpeg commands.

## Description

- **Logging:** Events and errors are logged to a file (`logging/convertlog.log`) for debugging.
- **Filename Checks:** Non-alphanumeric characters and spaces in filenames are replaced and standardized.
- **Validation:** Video files are validated for presence and content before conversion.
- **Inspection:** Detailed pre-conversion and post-conversion information is logged using FFprobe.
- **Conversion:** Videos are converted to .mp4 with h.264 compression, 720p resolution, and AAC audio.


## Usage

1. **Install Dependencies:**

    - Python 3.x (developed and tested on 3.10)
    - FFMpeg (https://ffmpeg.org/)

2. **Setup:**
   - Folders are created if not present: `convert_media`, `converted_media`, and `logging`.
   - Place video files to be converted in the `convert_media` folder.

3. **Run the Script:**
   - Open a command prompt or terminal.
   - Navigate to the project directory.
   - Run the script:
     ```bash
     python main.py  # For Windows
     # OR
     python3 main.py  # For macOS/Linux
     ```

## Configuration

- Adjust constants in the script:
  - `CONVERT_MEDIA_FOLDER`, `CONVERTED_MEDIA_FOLDER`, `LOGGING_FOLDER`: Directories for input, output, and logs.
  - `PLATFORM`, `FFMPEG`, `FFPROBE`: Settings for Windows/*nix compatibility.

## Logging

- Logs are stored in `logging/convertlog.log`.
- Information, errors, and detailed file inspection results are logged.

### Create a Virtual Environment (Optional but recommended)

Isolates dependencies and avoids globally installing the required libraries.
If you don't have `virtualenv` installed, you can install it using:

```bash
pip install virtualenv
```

Create a virtual environment:

```bash
python -m venv venv  # For Windows
# OR
python3 -m venv venv  # For macOS/Linux
```

Activate the virtual environment:

```bash
venv\Scripts\activate.ps1 # For Windows (command line with Admin)
# OR
source venv/bin/activate # For macOS/Linux
```