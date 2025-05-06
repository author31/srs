from datetime import datetime
from typing import Any, Literal, Union

from pydantic import BaseModel, HttpUrl


class UserRef(BaseModel):
    object: Literal['user']
    id: str

class Parent(BaseModel):
    type: Literal['database_id']
    database_id: str

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

class ListResponse(BaseModel):
    object: Literal['list']
    results: list[Page]
    next_cursor: Any | None
    has_more: bool
    type: Literal['page_or_database']
    page_or_database: dict[Any, Any]

class ErrorResponse(BaseModel):
    object: Literal['error']
    status: int
    code: str
    message: str

NotionResponse = Union[ListResponse, ErrorResponse]

