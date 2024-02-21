import os
import sys
import re
import logging
from logging.handlers import RotatingFileHandler
import subprocess
import json
import platform


PLATFORM = platform.system()
FFMPEG = "ffmpeg.exe" if PLATFORM == "Windows" else "ffmpeg"
FFPROBE = "ffprobe.exe" if PLATFORM == "Windows" else "ffprobe"

def check_ffmpeg():
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=True)
        logging.info(f'FFmpeg version: {result.stdout.strip()}')
        return True
    except subprocess.CalledProcessError as e:
        print('Error: FFmpeg is not installed or not in the system PATH.')
        print(f'Command output (stderr): {e.stderr.strip()}')
        sys.exit(1)  # Exit with an error code


def setup_directories():
    """
    Check and create directories if not present.
    """
    directories = ["convert_media", "converted_media", "logging"]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")


def setup_logging(log_directory="logging"):
    """
    Set up logging to a file with a rotating file handler.

    :param log_directory: The directory where log files will be saved.
    :return: The path to the log file.
    """
    log_file_path = os.path.join(log_directory, "convertlog.log")

    # Create a rotating file handler that rotates the log file every 5 MB and keeps 1 backup
    rotating_handler = RotatingFileHandler(
        log_file_path, maxBytes=5 * 1024 * 1024, backupCount=1
    )

    # Set up the logging format and level
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    rotating_handler.setFormatter(formatter)
    rotating_handler.setLevel(logging.INFO)

    # Get the root logger and remove any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers = []

    # Add the rotating file handler to the root logger
    root_logger.addHandler(rotating_handler)

    # Set the global logging level
    root_logger.setLevel(logging.INFO)

    root_logger.info("Execution start")
    return log_file_path


def prepare_files():
    """
    Check and rename files in the 'convert_media' folder, replacing spaces with underscores
    and handling other non-alphanumeric characters.
    """
    logging.info("Checking filenames for non-standard characters")

    convert_folder = "convert_media"

    files_in_convert = [
        file
        for file in os.listdir(convert_folder)
        if os.path.isfile(os.path.join(convert_folder, file))
    ]

    for file in files_in_convert:
        # Remove non-alphanumeric characters
        new_file_name = re.sub(r"[^a-zA-Z0-9_. ]", "", file)

        # Replace spaces with underscores in the file name
        new_file_name = new_file_name.replace(" ", "_")

        file_path = os.path.join(convert_folder, file)
        new_file_path = os.path.join(convert_folder, new_file_name)

        # Rename the file if it contains spaces or other non-alphanumeric characters
        if file != new_file_name:
            os.rename(file_path, new_file_path)
            logging.info(f'Renamed file: "{file}" to "{new_file_name}"')

    logging.info("Filenames checked")


def validate_files():
    """
    Check for the presence of video files in the 'convert_media' folder.
    Log an error if no files are present or if a file does not contain video.
    Return a list of valid video files.
    """
    logging.info(
        "Validating video files. Files without video content will not be processed."
    )
    convert_folder = "convert_media"
    valid_video_files = []

    files_in_convert = [
        file
        for file in os.listdir(convert_folder)
        if os.path.isfile(os.path.join(convert_folder, file))
    ]

    if not files_in_convert:
        error_message = "No files found in the convert_media folder."
        logging.error(error_message)
        print(error_message)
        return valid_video_files

    for file in files_in_convert:
        file_path = os.path.join(convert_folder, file)

        # Use ffprobe to check if the file contains video
        ffprobe_command = f'{FFPROBE} -hide_banner -v error -select_streams v:0 -show_entries stream=codec_type -of csv=p=0 "{file_path}"'
        try:
            result = subprocess.check_output(
                ffprobe_command, shell=True, text=True, stderr=subprocess.STDOUT
            )
            codec_type = result.strip()
            if codec_type == "video":
                valid_video_files.append(file)
            else:
                error_message = f'File "{file}" does not contain video.'
                logging.error(error_message)
                logging.error(f"ffprobe output: {result}")
                # print(error_message)
        except subprocess.CalledProcessError as e:
            # ffprobe command failed
            error_message = f'Error in function `validate_files` running ffprobe for file "{file}".'
            logging.error(error_message)
            logging.info(f"Error from ffprobe: {e.output.strip()}")

    logging.info("Video files validated.")

    return valid_video_files


def inspect_files(valid_video_files):
    """
    Using ffprobe, inventory and log detailed information about valid video files to be converted.
    """
    convert_folder = "convert_media"

    if not valid_video_files:
        logging.info("No valid video files found in the convert_media folder.")
        return

    logging.info("Inspecting validated files:")

    for file in valid_video_files:
        file_path = os.path.join(convert_folder, file)

        # Use ffprobe to capture detailed information about the file
        ffprobe_command = f'{FFPROBE} -hide_banner -v error -show_entries format=duration,bit_rate,size -show_entries stream=codec_type,width,height,display_aspect_ratio,codec_name -of json "{file_path}"'
        try:
            result = subprocess.check_output(
                ffprobe_command, shell=True, text=True, stderr=subprocess.STDOUT
            )
            data = json.loads(result)

            # Format Duration as HH:MM:SS.ss
            duration_seconds = float(data["format"]["duration"])
            formatted_duration = "{:02}:{:02}:{:.2f}".format(
                int(duration_seconds // 3600),
                int((duration_seconds % 3600) // 60),
                duration_seconds % 60,
            )

            # Format Bitrate in kb/s
            formatted_bitrate = "{:.2f} kb/s".format(
                float(data["format"]["bit_rate"]) / 1000
            )

            # Format Size in MB
            formatted_size_mb = "{:.2f} MB".format(
                float(data["format"]["size"]) / (1024 * 1024)
            )

            logging.info(f"File: {file}")
            logging.info(f"Size: {formatted_size_mb}")
            logging.info(f"Duration: {formatted_duration}")
            logging.info(f"Bitrate: {formatted_bitrate}")

            for stream in data["streams"]:
                if stream["codec_type"] == "video":
                    if "codec_name" in stream:
                        logging.info(f'Video Codec: {stream["codec_name"]}')
                    logging.info(
                        f'Resolution: {stream["width"]}x{stream["height"]} [{stream["display_aspect_ratio"]}]'
                    )
                elif stream["codec_type"] == "audio":
                    logging.info("Audio: Present")

        except subprocess.CalledProcessError as e:
            # ffprobe command failed
            logging.error(
                f'Error in `inspect_file` function running ffprobe for file "{file}": {str(e)}'
            )

    logging.info("File inspection completed.")


def convert_video(file):
    """
    Convert a video file to .mp4 format.
    """
    logging.info(f"Start file conversion for file {file}")
    try:
        file_path = os.path.join("convert_media", file)
        output_file = get_output_file_path(file)

        # Construct ffmpeg command
        ffmpeg_command = [
            FFMPEG,
            "-hide_banner",
            "-i",
            file_path,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-vf",
            "scale=-2:720",
            "-c:a",
            "aac",
            "-q:a",
            "100",
            "-movflags",
            "faststart",
            output_file,
        ]

        # Execute ffmpeg command and capture output
        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)

        # Log only essential information
        if result.returncode == 0:
            logging.info(f"Conversion complete for file: {file}")
        else:
            error_message = f'Error converting file "{file}": {result.stderr.strip()}'
            logging.error(error_message)

    except subprocess.CalledProcessError as e:
        logging.error(f'Error converting file "{file}": {e}')


def get_output_file_path(file):
    """
    Get the output file path for the converted_media video, handling duplicate filenames.
    """
    convert_folder = "converted_media"
    file_prefix, file_extension = os.path.splitext(file)
    output_file_path = os.path.join(convert_folder, f"{file_prefix}_converted.mp4")

    counter = 1
    while os.path.exists(output_file_path):
        # If file with the same name exists, add a counter to the filename
        output_file_path = os.path.join(
            convert_folder, f"{file_prefix}_converted_{counter}.mp4"
        )
        counter += 1

    return output_file_path


def inspect_converted_files():
    """
    Inspect converted video files in the 'converted_media' folder.
    Log detailed information about the converted videos.
    """
    convert_folder = "converted_media"

    converted_files = [
        file
        for file in os.listdir(convert_folder)
        if os.path.isfile(os.path.join(convert_folder, file))
    ]

    if not converted_files:
        logging.info("No converted video files found in the converted_media folder.")
        return

    logging.info("Inspecting converted files:")

    for file in converted_files:
        file_path = os.path.join(convert_folder, file)

        # Use ffprobe to capture detailed information about the converted file
        ffprobe_command = f'{FFPROBE} -hide_banner -v error -show_entries format=duration,bit_rate,size -show_entries stream=codec_type,width,height,display_aspect_ratio,codec_name -of json "{file_path}"'
        try:
            result = subprocess.check_output(
                ffprobe_command, shell=True, text=True, stderr=subprocess.STDOUT
            )
            data = json.loads(result)

            # Format Duration as HH:MM:SS.ss
            duration_seconds = float(data["format"]["duration"])
            formatted_duration = "{:02}:{:02}:{:.2f}".format(
                int(duration_seconds // 3600),
                int((duration_seconds % 3600) // 60),
                duration_seconds % 60,
            )

            # Format Bitrate in kb/s
            formatted_bitrate = "{:.2f} kb/s".format(
                float(data["format"]["bit_rate"]) / 1000
            )

            # Format Size in MB
            formatted_size_mb = "{:.2f} MB".format(
                float(data["format"]["size"]) / (1024 * 1024)
            )

            logging.info(f"Converted File: {file}")
            logging.info(f"Size: {formatted_size_mb}")
            logging.info(f"Duration: {formatted_duration}")
            logging.info(f"Bitrate: {formatted_bitrate}")

            for stream in data["streams"]:
                if stream["codec_type"] == "video":
                    if "codec_name" in stream:
                        logging.info(f'Video Codec: {stream["codec_name"]}')
                    logging.info(
                        f'Resolution: {stream["width"]}x{stream["height"]} [{stream["display_aspect_ratio"]}]'
                    )
                elif stream["codec_type"] == "audio":
                    logging.info("Audio: Present")

        except subprocess.CalledProcessError as e:
            # ffprobe command failed
            logging.error(
                f'Error in `inspect_converted_files` function running ffprobe for file "{file}": {str(e)}'
            )

    logging.info("Converted file inspection completed.")


if __name__ == "__main__":
    ffmpeg_installed = check_ffmpeg()

    setup_directories()

    log_file_path = setup_logging()

    prepare_files()

    valid_video_files = validate_files()

    if valid_video_files:
        inspect_files(valid_video_files)

        for file in valid_video_files:
            convert_video(file)

        inspect_converted_files()

    logging.info("Execution end\n")
