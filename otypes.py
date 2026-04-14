"""
Types and Inputs for items subgraph
"""

import json
from functools import cached_property
from typing import Dict, Union

import strawberry
from strawberry.fastapi import BaseContext
from strawberry.types import Info as _Info
from strawberry.types.info import RootValueType

from models import PyObjectId, Item


# custom context class
class Context(BaseContext):
    """
    Class provides user metadata and cookies from request headers, has
    methods for doing this.
    """

    @cached_property
    def user(self) -> Union[Dict, None]:
        if not self.request:
            return None

        user = json.loads(self.request.headers.get("user", "{}"))
        return user

    @cached_property
    def cookies(self) -> Union[Dict, None]:
        if not self.request:
            return None

        cookies = json.loads(self.request.headers.get("cookies", "{}"))
        return cookies


Info = _Info[Context, RootValueType]
"""custom info Type for user metadata"""

PyObjectIdType = strawberry.scalar(
    PyObjectId, serialize=str, parse_value=lambda v: PyObjectId(v)
)
"""A scalar Type for serializing PyObjectId, used for id field"""


@strawberry.experimental.pydantic.type(model=Item)
class SimpleItemType:
    id: strawberry.auto
    iid: strawberry.auto
    name: strawberry.auto
    clubid: strawberry.auto
    net_qty: strawberry.auto
    available_qty: strawberry.auto
    total_qty: strawberry.auto
    current_location: strawberry.auto


@strawberry.experimental.pydantic.type(model=Item)
class FullItemType:
    id: strawberry.auto
    iid: strawberry.auto
    name: strawberry.auto
    brand: strawberry.auto
    photo: strawberry.auto
    clubid: strawberry.auto
    net_qty: strawberry.auto
    available_qty: strawberry.auto
    total_qty: strawberry.auto
    warranty_details: strawberry.auto
    other_details: strawberry.auto
    current_location: strawberry.auto
    requires_approval: strawberry.auto


@strawberry.experimental.pydantic.input(model=Item)
class FullItemInput:
    iid: strawberry.auto
    name: strawberry.auto
    brand: strawberry.auto
    photo: strawberry.auto
    clubid: strawberry.auto
    net_qty: strawberry.auto
    available_qty: strawberry.auto
    total_qty: strawberry.auto
    warranty_details: strawberry.auto
    other_details: strawberry.auto
    current_location: strawberry.auto
    requires_approval: bool = True


@strawberry.input
class ItemQtyInput:
    iid: str
    net_qty: int
    available_qty: int
