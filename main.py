import re
import os
import pinyin
import jieba
import pykakasi
import MeCab
import ipadic
import webvtt
from webvtt import WebVTT
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
from pyvi import ViTokenizer
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class Item(BaseModel):
    sub: str
    lang: str | None = "ja"
    sub_type: str


app = FastAPI()


@app.post('/netflix')
def get_result_data(item: Item):

    sub = item.sub
    lang = item.lang
    sub_type = item.sub_type
    main_type = sub_type

    vtt_file_path = get_subtitle_data_file_name(input_string=sub)
    vtt_subtitle = extract_subtitle(file_path=vtt_file_path)
    sub_respone = list()

    try:
        sub_type = sub_type.split("+")[1]
    except IndexError as e:
        sub_type = ""

    for sub in vtt_subtitle:
        sentence = re.sub(r"&.\w*.;", "", sub.text)
        tStartMs = sub.start
        dDurationMs = sub.end

        tStartMs = get_total_ms(timestamp_str=sub.start)
        dDurationMs = get_total_ms(timestamp_str=sub.end)

        segments = get_segmented_subtitle(sentence=sentence, language=lang)

        sub_data = create_sub_json(
            segments, tStartMs, dDurationMs, lang, sub_type, main_type, sub)
        sub_respone.append(sub_data)

    #     json = {
    #         "lang": lang,
    #         "type": json['type'],
    #         "sub": "WEBVTT"
    #     }

    #     for item in sub_respone:
    #         # print(item)
    #         json["sub"] += item

    return {"message": vtt_subtitle}


# seg = pkuseg.pkuseg()
kks = pykakasi.kakasi()
kor_transliter = Transliter(academic)

tagger = MeCab.Tagger(ipadic.MECAB_ARGS + " " + "-Owakati")

languages_need_phonetics = ["zh", "zh-CHS", "zh-Hans", "zh-CN",
                            "zh-SG", "zh-CHT", "zh-Hant", "zh-HK", "zh-MO", "zh-TW", "ja", "ko"]

chinese_need_phonetics = ["zh", "zh-CHS", "zh-Hans", "zh-CN",
                          "zh-SG", "zh-CHT", "zh-Hant", "zh-HK", "zh-MO", "zh-TW"]


times_list = []


def extract_subtitle(file_path: str) -> WebVTT:
    """
        convert subtitle file path from str to vtt object
    """
    try:
        # clear_duplicate_times(file_path=file_path)
        vtt = webvtt.read(file_path)
        safe_remove(file_path)
        return vtt
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        safe_remove(file_path)
        return None
    except webvtt.errors.MalformedFileError:
        print(f"Error: Malformed WebVTT file at '{file_path}'.")
        safe_remove(file_path)
        return None


def convert_all_words_in_japanese_sentence(word, type):
    str = ""
    turning = kks.convert(word)
    for x in turning:
        print(f"ORIGINAL:{x['orig']}")
        if x['orig'] != "+" and x['orig'] != "\n":
            str += f"<span class='lly-translatable-word'><span class='lly-translatable-word-transliteration'>{x[type]}</span>{x['orig']}</span> "
    return str


def add_phonetics(word: list, language: str, sub_type: str):
    """
    Get the phonetics of words

    parameter : word : subtitle word
    parameter : language : subtitle language
    paramter : sub_type : subtitle type

    return : phonetic words as list
    """

    if language in ["zh-Hant", "zh-Hans", "zh"]:
        final_txt = ""
        list_ = list
        for i in word:
            # if len(i) > 1:
            if i == "+":
                i = ""
            if i is not None:
                ph = pinyin.get(i)
                if ph == i:
                    ph = ""
                if ph != "" or i != "":
                    if i != "\n" and ph != "\n":
                        final_txt += f"<span class='lly-translatable-word'><span class='lly-translatable-word-transliteration'>{ph}</span>{i}</span>"
        return final_txt

        # return pinyin.get(word)

    elif language == "ja":

        if sub_type is not None and sub_type.lower() == "hiragana":
            converted = convert_all_words_in_japanese_sentence(word, 'hira')
        else:
            converted = convert_all_words_in_japanese_sentence(word, 'hepburn')

        final_txt = f"{converted}"
        return final_txt

    elif language == "ko":
        # print(word)
        txt = ""
        turened = kor_transliter.translit(word)
        turened = turened.split("-")
        for i in turened:
            # for i in turened.split(" "):
            txt += f"<span class='lly-translatable-word'><span class='lly-translatable-word-transliteration'>{i}</span>{word}</span>"
        return txt

    else:
        return "Sorry, phonetic is not available for this language."


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


def convert_to_time(timestamp_str):
    h, m, s, ms = map(int, timestamp_str.replace('.', ':').split(':'))
    return h, m, s, ms


def get_total_ms(timestamp_str) -> float:
    h, m, s, ms = convert_to_time(timestamp_str)
    total_milliseconds = h * 3600000 + m * 60000 + s * 1000 + ms
    # Convert the result to a float
    total_milliseconds_float = float(total_milliseconds) / 1000.0
    return total_milliseconds_float


def create_sub_json(segments: list, tStartMs: int, dDurationMs: int, lang: str, sub_type: str, main_type, file):

    if lang not in languages_need_phonetics:
        sub_data = {
            "tStartMs": tStartMs,
            "dDurationMs": dDurationMs,
            "sentence": segments
        }
        return sub_data

    else:
        i = file
        phonetics = list()
        txt = ""
        # for i in vtt:
        if lang in ["zh-Hant", "zh-Hans", "zh"]:
            cuted = list(jieba.cut(i.text))
            phonetics.append(add_phonetics(cuted, lang, sub_type))
            soup = BeautifulSoup(i.raw_text)
            my = soup("span", {"class": "save-sentence"})
            txt += f"\n\n{i.identifier}\n{i.start} --> {i.end} \n {phonetics[0]}{my[0]}"
            return txt

        elif lang == "ja":
            phonetics.append(add_phonetics(i.text, lang, sub_type))
            soup = BeautifulSoup(i.raw_text)
            my = soup("span", {"class": "save-sentence"})
            txt += f"\n\n{i.identifier}\n{i.start} --> {i.end} \n {phonetics[0]}{my[0]}"
            return txt

        elif lang == "ko":
            # i.text = " ".join(i.text.split())
            # print(i.text)
            soup = BeautifulSoup(i.raw_text)
            my = soup("span", {"class": "save-sentence"})
            phonetics.append(add_phonetics(i.lines, lang, sub_type))
            txt += f"\n\n{i.identifier}\n{i.start} --> {i.end} \n {phonetics}{my}"
            return txt
        # print(cuted)
        # print(i.lines)
        # T = f"<span class='lly-translatable-word'>{phonetics[0]} {i.raw_text}</span>"
        # T = f"<span class='lly-translatable-word'>{phonetics[0]}</span>{i.text}</span>"
            # print(i.raw_text)
        # del i.text
        # i.text = phonetics[0]

        # json = {
        #     "sub" : ""
        # }
        # json["sub"] += txt


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


def clear_duplicate_times(file_path: str) -> bool:
    try:
        vtt = webvtt.read(file_path)

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


def safe_remove(file_path: str) -> None:
    try:
        os.remove(file_path)
        print(f"File '{file_path}' successfully removed.")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(
            f"Error: An unexpected error occurred while removing the file - {e}")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
