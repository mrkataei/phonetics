from pydantic import BaseModel


class Caption(BaseModel):
    sub: str
    lang: str | None = "ja"
    type: str