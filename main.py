import pinyin
import jieba
import pykakasi
import MeCab
import ipadic
from webvtt import WebVTT
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from utils import get_subtitle_data_file_name as gsdf 
from utils import extract_subtitle as es
# from utils import get_segmented_subtitle as gss
# from utils import get_total_ms as gts

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

    vtt_file_path = gsdf(input_string=sub)
    vtt_subtitle = es(file_path=vtt_file_path)

    try:
        sub_type = sub_type.split("+")[1]
    except IndexError as e:
        print(e)
        sub_type = ""

    for caption in vtt_subtitle:
        caption.text = create_sub_json(caption=caption, lang=lang, sub_type=sub_type)

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



def convert_all_words_in_japanese_sentence(word, type):
    str = ""
    turning = kks.convert(word)
    for x in turning:
        print(f"ORIGINAL:{x['orig']}")
        if x['orig'] != "+" and x['orig'] != "\n":
            str += f"<span class='lly-translatable-word'><span class='lly-translatable-word-transliteration'>{x[type]}</span>{x['orig']}</span> "
    return str


def create_sub_json(caption: WebVTT, lang: str, sub_type: str):

    # sentence = re.sub(r"&.\w*.;", "", caption.text)
    # tStartMs = gts(timestamp_str=caption.start)
    # dDurationMs = gts(timestamp_str=caption.end)
    # segments = gss(sentence=sentence, language=lang)

    
    # dnot need any phonetics
    if lang not in languages_need_phonetics:
        return caption
    
    # need phonetics
    else:
        phonetics = list()
        cap = ""
        if lang in ["zh-Hant", "zh-Hans", "zh"]:
            cuted = list(jieba.cut(caption.text))
            phonetics.append(add_phonetics(cuted, lang, sub_type))
            soup = BeautifulSoup(caption.text)
            my = soup("span", {"class": "save-sentence"})
            cap += f"\n\n{caption.identifier}\n{caption.start} --> {caption.end} \n {phonetics[0]}{my[0]}"
            return cap

        elif lang == "ja":
            phonetics.append(add_phonetics(caption.text, lang, sub_type))
            soup = BeautifulSoup(caption.text)
            my = soup("span", {"class": "save-sentence"})
            cap += f"\n\n{caption.identifier}\n{caption.start} --> {caption.end} \n {phonetics[0]}{my[0]}"
            return cap

        elif lang == "ko":
            soup = BeautifulSoup(caption.raw_text)
            my = soup("span", {"class": "save-sentence"})
            phonetics.append(add_phonetics(caption.lines, lang, sub_type))
            cap += f"\n\n{caption.identifier}\n{caption.start} --> {caption.end} \n {phonetics}{my}"
            return cap


def add_phonetics(word: str, language: str, sub_type: str):
    """
    Get the phonetics of words

    parameter : word : subtitle word
    parameter : language : subtitle language
    paramter : sub_type : subtitle type

    return : phonetic words as list
    """

    if language in ["zh-Hant", "zh-Hans", "zh"]:
        final_txt = ""
        for i in word:
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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
