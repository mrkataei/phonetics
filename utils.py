from webvtt import WebVTT ,read, errors
# from pyvi import ViTokenizer
import os
import jieba
import pykakasi
import pinyin
from hangul_romanize import Transliter
from hangul_romanize.rule import academic



languages_need_phonetics = ["zh", "zh-CHS", "zh-Hans", "zh-CN",
                            "zh-SG", "zh-CHT", "zh-Hant", "zh-HK", "zh-MO", "zh-TW", "ja", "ko"]


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
        # return ViTokenizer.tokenize(sentence).split(" ")
        return None

    else:
        return sentence.split(" ")
    


def convert_all_words_in_japanese_sentence(text: str, type: str) -> str:
    result = ""
    kks = pykakasi.kakasi()
    turning = kks.convert(text)
    for x in turning:
        print(f"ORIGINAL:{x['orig']}")
        if x['orig'] != "+" and x['orig'] != "\n":
            result += f"<span class='lly-translatable-word'><span class='lly-translatable-word-transliteration'>{x[type]}</span>{x['orig']}</span> "
    return result


def add_phonetics(text: str, language: str, sub_type: str) -> str:
    """
        Get the phonetics of words
    """
    result = ""
    if language in ["zh-Hant", "zh-Hans", "zh"]:
        for word in text:
            if word == "+" and word == "\n":
                continue
            ph = pinyin.get(word)
            if ph == word:
                continue
            result += f"<span class='lly-translatable-word'><span class='lly-translatable-word-transliteration'>{ph}</span>{word}</span>"

    elif language == "ja":
        if sub_type is not None and sub_type.lower() == "hiragana":
            converted = convert_all_words_in_japanese_sentence(text, 'hira')
        else:
            converted = convert_all_words_in_japanese_sentence(text, 'hepburn')
        result = converted

    elif language == "ko":
        kor_transliter = Transliter(academic)
        turened = kor_transliter.translit(text)
        turened = turened.split("-")
        for i in turened:
            # for i in turened.split(" "):
            result += f"<span class='lly-translatable-word'><span class='lly-translatable-word-transliteration'>{i}</span>{text}</span>"
        return result

    return result
    


def create_sub_json(caption: WebVTT, lang: str, sub_type: str) -> str:

    # sentence = re.sub(r"&.\w*.;", "", caption.text)
    # tStartMs = gts(timestamp_str=caption.start)
    # dDurationMs = gts(timestamp_str=caption.end)
    # segments = gss(sentence=sentence, language=lang)

    
    # dnot need any phonetics
    if lang not in languages_need_phonetics:
        return caption
    
    # need phonetics
    else:
        phonetics = ""
        cap_text = ""

        if lang in ["zh-Hant", "zh-Hans", "zh"]:
            caption.text = list(jieba.cut(caption.text))

        elif lang == "ja" or lang == "ko":
            cap_text = caption.text

        phonetics = add_phonetics(cap_text, lang, sub_type)

        return phonetics

