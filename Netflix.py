import re
import pinyin
import jieba
import pykakasi
import MeCab
import ipadic
import webvtt
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

    item_dict = item.dict()
    sub = item_dict.sub
    lang = item_dict.lang
    sub_type = item_dict.sub_type

    sub = get_subtitle_data_file_name(sub)
    sub_respone = list()
    subtitle = extract_subtitle(sub)

    try:
        sub_type = sub_type.split("+")[1]
    except IndexError as e:
        print()
        sub_type = ""

    for sub in subtitle:
        sentence = sub.text
        sentence = re.sub(r"&.\w*.;", "", sentence)
        tStartMs = sub.start
        dDurationMs = sub.end
        tStartMs, dDurationMs = time_to_second(tStartMs, dDurationMs)
        segs = get_segs_subtitle(sentence, lang)

        sub_data = create_sub_json(
            segs, tStartMs, dDurationMs, lang, sub_type, main_type, sub)
        sub_respone.append(sub_data)

        json = {
            "lang": lang,
            "type": json['type'],
            "sub": "WEBVTT"
        }

        for item in sub_respone:
            # print(item)
            json["sub"] += item

    return json


# seg = pkuseg.pkuseg()
kks = pykakasi.kakasi()
kor_transliter = Transliter(academic)

tagger = MeCab.Tagger(ipadic.MECAB_ARGS + " " + "-Owakati")

languages_need_phonetics = ["zh", "zh-CHS", "zh-Hans", "zh-CN",
                            "zh-SG", "zh-CHT", "zh-Hant", "zh-HK", "zh-MO", "zh-TW", "ja", "ko"]

chinese_need_phonetics = ["zh", "zh-CHS", "zh-Hans", "zh-CN",
                          "zh-SG", "zh-CHT", "zh-Hant", "zh-HK", "zh-MO", "zh-TW"]


times_list = []


def extract_subtitle(subtilte):
    """
    convert subtitle file from str to vtt object

    parameter : subtitle : subtitle file

    return : subtitle as vtt format
    """

    vtt = webvtt.read(f'{subtilte}')
    for i in vtt:
        print(i.text)
    remove_subtitle_file(subtilte)
    clear_duplicate_times_from_subtitles(vtt)
    print(vtt)
    return vtt


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


def get_segs_subtitle(sentence: str, language: str) -> list:
    """
    words separator and get the phonetics of words

    parameter : sentence : subtitle sentence
    parameter : language : subtitle language

    return : segmented subtitles
    """

    if language == "zh-Hans":
        # return seg.cut(sentence)
        return sentence.split(" ")

    elif language == "zh-Hant":
        return list(jieba.cut(sentence))

    # elif language == "ja":
    #     sentence = tagger.parse(sentence)
    #     sentence = sentence.split()
    #     print(sentence)

    elif language == "vi":
        return ViTokenizer.tokenize(sentence).split(" ")

    else:
        return sentence.split(" ")

    return sentence


def time_to_second(tStartMs, dDurationMs):
    """
    Calculate the start and end time of the subtitle

    parameter : tStartMs : subtitle start time
    parameter : dDurationMs : subtitle end time

    return : start and end time in milliseconds
    """

    start_time = tStartMs
    end_time = dDurationMs
    return end_time, dDurationMs
    # start_time_ms = sum(
    #     [
    #         float(v) * 60 ** (len(start_time.split(":")) - i - 1)
    #         for i, v in enumerate(start_time.split(":"))
    #     ]
    # )
    # end_time_ms = sum(
    #     [
    #         float(v) * 60 ** (len(end_time.split(":")) - i - 1)
    #         for i, v in enumerate(end_time.split(":"))
    #     ]
    # )
    # return start_time_ms, (end_time_ms - start_time_ms)


def create_sub_json(segs: list, tStartMs: int, dDurationMs: int, lang: str, sub_type: str, main_type, file):
    # print("++++++++++++++++")
    # print(file.text)
    # print("++++++++++++++++")
    # print(segs)
    """
    Create a json output

    parameter : segs : subtitle segments
    parameter : tStartMs : subtitle start time
    parameter : dDurationMs : subtitle end time
    paramter : lang : subtitle language
    paramter : sub_type : subtitle type


    return : dict output
    """
    # print(type(file))
    if lang not in languages_need_phonetics:
        sub_data = {
            "tStartMs": tStartMs,
            "dDurationMs": dDurationMs,
            "sentence": segs
        }
        return sub_data

    else:
        i = file
        # print(i.text)
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


def get_subtitle_data_file_name(subtilte: str) -> str:
    """
    create subtitle from str format to vtt file and return vtt file name

    paramter : subtitle : subtitle string
    """
    file_name = "test"
    # file2 = list(subtilte.strip())
    file2_to_breaked_str = ''
    print(f"S : {subtilte.strip()}")
    print("----------------")
    print(f"S : {subtilte}")
    # for i in file2:
    #     print(i)
    #     file2_to_breaked_str+= i.strip() + '\n'
    one = open(f'files/{file_name}', "w")
    one.write(subtilte.strip())
    one.close()
    # file_name = "test"
    # buffer = subtilte.encode().decode('utf-8')
    # f = open(f"files/{file_name}.vtt", "w+b")
    # f.write(buffer.encode())
    # f.close()

    return f"files/{file_name}.vtt"


def clear_duplicate_times_from_subtitles(vtt_sub) -> bool:
    """
    clear duplicate times from subtitles

    param: vtt_sub: subtitles
    return: True if clear duplicate times
    """
    for time in range(0, 3):
        counter = 0
        for sub in vtt_sub:
            if sub.start in times_list:
                text = sub.text
                vtt_sub[counter-1].text += " "+text
                del vtt_sub.captions[counter]
                times_list.append(sub.start)

            counter += 1
            times_list.append(sub.start)

        times_list.clear()


def remove_subtitle_file(file_name: str):
    """
    Remove subtitle file

    paramter : file_name : subtitle file name
    """
    pass
    # try:
    #     os.remove(file_name)
    # except OSError as e:
    #     print("Error: %s - %s." % (e.filename, e.strerror))


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
