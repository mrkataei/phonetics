from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from schema import Caption

from utils import get_subtitle_data_file_name as gsdf 
from utils import extract_subtitle as es
from utils import create_sub_json as csj
# from utils import get_segmented_subtitle as gss
# from utils import get_total_ms as gts



app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post('/netflix')
def get_result_data(item: Caption) -> Caption:

    sub_type = item.type
    vtt_file_path = gsdf(input_string=item.sub)
    vtt_subtitle = es(file_path=vtt_file_path)

    try:
        sub_type = sub_type.split("+")[1]
    except IndexError as e:
        print(e)
        sub_type = ""

    for caption in vtt_subtitle:
        caption.text = csj(caption=caption, lang=item.lang, sub_type=sub_type)

    return {"subtitle": caption}

