from webvtt import WebVTT ,read, errors
from pyvi import ViTokenizer
import os
import jieba



def get_subtitle_data_file_name(input_string: str, file_name: str = 'sub') -> str:
    """
        create subtitle from str format to vtt file and return vtt file name
    """
    lines = input_string.strip().split("\n\n")
    vtt_content = "WEBVTT\n\n"

    for line in lines:
        parts = line.split("\n")
        if len(parts) >= 4 and parts[0].isdigit():
            vtt_content += f"{parts[1]} --> {parts[2]}\n{parts[3]}\n\n"
        else:
            print(f"Invalid entry: {line}")

    with open(f"files/{file_name}.vtt", "w", encoding="utf-8") as output_file:
        output_file.write(vtt_content)

    return f"files/{file_name}.vtt"


def extract_subtitle(file_path: str) -> WebVTT:
    """
        convert subtitle file path from str to vtt object
    """
    try:
        # clear_duplicate_times(file_path=file_path)
        vtt = read(file_path)
        safe_remove(file_path)
        return vtt
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        safe_remove(file_path)
        return None
    except errors.MalformedFileError:
        print(f"Error: Malformed WebVTT file at '{file_path}'.")
        safe_remove(file_path)
        return None
    
def safe_remove(file_path: str) -> None:
    try:
        os.remove(file_path)
        print(f"File '{file_path}' successfully removed.")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(
            f"Error: An unexpected error occurred while removing the file - {e}")


def convert_to_time(timestamp_str):
    h, m, s, ms = map(int, timestamp_str.replace('.', ':').split(':'))
    return h, m, s, ms


def get_total_ms(timestamp_str) -> float:
    h, m, s, ms = convert_to_time(timestamp_str)
    total_milliseconds = h * 3600000 + m * 60000 + s * 1000 + ms
    # Convert the result to a float
    total_milliseconds_float = float(total_milliseconds) / 1000.0
    return total_milliseconds_float



def clear_duplicate_times(file_path: str) -> bool:
    try:
        vtt = read(file_path)

        # Create a dictionary to store unique timestamps and captions
        unique_times = {}

        # Iterate through the captions and store only unique times in the dictionary
        for caption in vtt:
            start_time = caption.start
            end_time = caption.end
            if (start_time, end_time) not in unique_times:
                unique_times[(start_time, end_time)] = caption.text
            else:
                print(f"Removing duplicate caption: {caption.text}")
                vtt.captions.remove(caption)

        # Write the updated captions back to the file
        with open(file_path, "w", encoding="utf-8") as output_file:
            output_file.write(str(vtt))

        return True
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return False
    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}")
        return False


def get_segmented_subtitle(sentence: str, language: str) -> list:
    """
        words separator and get the phonetics of words
    """
    if language == "zh-Hant" or language == "ja":
        return list(jieba.cut(sentence))

    elif language == "vi":
        return ViTokenizer.tokenize(sentence).split(" ")

    else:
        return sentence.split(" ")