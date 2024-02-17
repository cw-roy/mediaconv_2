import os
import logging
import subprocess
import json

# from datetime import datetime

def setup_directories():
    """
    Check and create directories if not present.
    """
    directories = ['convert', 'converted', 'logging']

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def setup_logging():
    """
    Set up logging to a file.
    """
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logging', 'convertlog.log')
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info('Execution start')

def check_for_files():
    """
    Check for the presence of video files in the 'convert' folder.
    Log an error if no files are present or if a file does not contain video.
    """
    convert_folder = 'convert'

    files_in_convert = [file for file in os.listdir(convert_folder) if os.path.isfile(os.path.join(convert_folder, file))]

    if not files_in_convert:
        error_message = 'No files found in the convert folder.'
        logging.error(error_message)
        print(error_message)
        return

    for file in files_in_convert:
        file_path = os.path.join(convert_folder, file)

        # Use ffprobe to check if the file contains video
        ffprobe_command = f'ffprobe -v error -select_streams v:0 -show_entries stream=codec_type -of csv=p=0 "{file_path}"'
        try:
            result = subprocess.check_output(ffprobe_command, shell=True, text=True, stderr=subprocess.STDOUT)
            codec_type = result.strip()
            if codec_type != 'video':
                error_message = f'File "{file}" does not contain video. Skipping.'
                logging.error(error_message)
                logging.error(f'ffprobe output: {result}')
                print(error_message)
                return
        except subprocess.CalledProcessError as e:
            # ffprobe command failed
            error_message = f'Error running ffprobe for file "{file}": {e.output.strip()}. Skipping.'
            logging.error(error_message)
            print(error_message)
            return
        
def inspect_files():
    """
    Inventory and log detailed information about files to be converted using ffprobe.
    """
    convert_folder = 'convert'

    files_in_convert = [file for file in os.listdir(convert_folder) if os.path.isfile(os.path.join(convert_folder, file))]

    if not files_in_convert:
        logging.info('No files found in the convert folder.')
        return

    logging.info('Files to be converted:')
    
    for file in files_in_convert:
        file_path = os.path.join(convert_folder, file)

        # Use ffprobe to capture detailed information about the file
        ffprobe_command = f'ffprobe -hide_banner -v error -show_entries format=duration,bit_rate -show_entries stream=codec_type,width,height,display_aspect_ratio,codec_name -of json "{file_path}"'
        try:
            result = subprocess.check_output(ffprobe_command, shell=True, text=True)
            data = json.loads(result)

            logging.info(f'File: {file}')
            logging.info(f'Duration: {data["format"]["duration"]}')
            logging.info(f'Bitrate: {data["format"]["bit_rate"]} bps')

            for stream in data["streams"]:
                if stream["codec_type"] == "video":
                    # logging.info('Video:')
                    if 'codec_name' in stream:
                        logging.info(f'Codec: {stream["codec_name"]}')
                    logging.info(f'Resolution: {stream["width"]}x{stream["height"]} [{stream["display_aspect_ratio"]}]')
                elif stream["codec_type"] == "audio":
                    logging.info('Audio: Present')

        except subprocess.CalledProcessError as e:
            # ffprobe command failed
            logging.error(f'Error running ffprobe for file "{file}": {e.output.strip()}')

if __name__ == "__main__":
    setup_directories()

    setup_logging()

    check_for_files()

    inspect_files()

    logging.info('Execution end\n')
