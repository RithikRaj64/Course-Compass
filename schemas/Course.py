from pydantic import BaseModel  # type: ignore


class Course(BaseModel):
    """
    Model for the courses list output
    """

    topic: str
    url: str
    description: str

    class Config:
        schema_extra: dict[str, dict[str, str | list[str]]] = {
            "example": {
                "topic": "Test",
                "url": "https://www.wikipedia.com/",
                "description": "This is a test",
            }
        }
