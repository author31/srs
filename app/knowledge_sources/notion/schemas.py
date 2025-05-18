from datetime import datetime
from typing import Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Flashcard(BaseModel):
    answer: dict = Field(alias="Answer")
    created_date: dict = Field(alias="Created Date")
    question: dict = Field(alias="Question")

    def model_post_init(self, __context):
        self.answer = self._santitize_answer(self.answer)
        self.question = self._santitize_question(self.question)

    def _santitize_answer(self, raw_answer: dict):
        return raw_answer['rich_text'][0]['text']['content']

    def _santitize_question(self, raw_question: dict):
        return raw_question['title'][0]['text']['content']

class UserRef(BaseModel):
    object: Literal['user']
    id: str

class Parent(BaseModel):
    type: Literal['database_id'] | Literal["page_id"]
    database_id: str | None = None
    page_id: str | None = None

class Page(BaseModel):
    object: Literal['page']
    id: str
    created_time: datetime
    last_edited_time: datetime
    created_by: UserRef
    last_edited_by: UserRef
    cover: None | str
    icon: None | str
    parent: Parent
    archived: bool
    properties: dict
    url: HttpUrl

class PageContent(BaseModel):
    object: Literal['block']
    id: str
    parent: Parent
    created_time: datetime
    last_edited_time: datetime
    created_by: UserRef
    last_edited_by: UserRef
    has_children: bool
    archived: bool
    in_trash: bool

    model_config = ConfigDict(extra="allow")


class NotionDatabaseQueryData(BaseModel):
    object: Literal['list']
    items: list[Page] = Field(alias="results")
    next_cursor: Any | None
    has_more: bool
    type: Literal['page_or_database'] | Literal['block']
    page_or_database: dict | None = None
    block: dict | None = None


class NotionBlockChildrenData(BaseModel):
    object: Literal['list']
    items: list[PageContent] = Field(alias="results")
    next_cursor: Any | None
    has_more: bool
    type: Literal['page_or_database'] | Literal['block']
    page_or_database: dict | None = None
    block: dict | None = None
