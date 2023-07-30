from pydantic import BaseModel


class Item(BaseModel):
    sub: str
    lang: str | None = "ja"
    sub_type: str