from pydantic import BaseModel


class Caption(BaseModel):
    lang: str | None = "ja"
    type: str
    sub: str