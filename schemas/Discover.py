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

    def asDict(self) -> dict[str, str | list[Course]]:
        return {
            "topic": self.topic,
            "url": self.url,
            "description": self.description,
            "courses": self.courses,
        }

    class Config:
        schema_extra: dict[str, dict[str, str | list[str]]] = {
            "example": {
                "topic": "Test",
                "content": "This is a test",
                "url": "https://www.wikipedia.com/",
                "links": ["https://www.wikipedia.com/"],
            }
        }
