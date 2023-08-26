from pydantic import BaseModel  # type: ignore

from schemas.Course import Course


class Discover(BaseModel):
    """
    Model for the discover page output
    """

    topic: str
    url: str
    description: str
    courses: list[Course]

    class Config:
        schema_extra: dict[str, dict[str, str | list[str]]] = {
            "example": {
                "topic": "Test",
                "content": "This is a test",
                "url": "https://www.wikipedia.com/",
                "links": ["https://www.wikipedia.com/"],
            }
        }
