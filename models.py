from datetime import datetime
from enum import Enum
from typing import Annotated, Any, List
from zoneinfo import ZoneInfo

import strawberry
from bson import ObjectId
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    TypeAdapter,
    field_validator,
)
from pydantic_core import core_schema
from mtypes import Storage_Location

# for handling mongo ObjectIds
class PyObjectId(ObjectId):
    """
    Class for handling MongoDB document ObjectIds for 'id' fields in Models.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        return core_schema.union_schema(
            [
                # check if it's an instance first before doing any further work
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(cls.validate),
            ],
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class Item(BaseModel):
    """
    Model for storing Item details.

    Attributes:
        id (PyObjectId): Unique ObjectId of the document of the item.
        iid (str): The Item ID.
        name (str): The name of the Item
        brand (str | None): Optional brand name for the Item if applicable
        photo (str | None): photo of the Item. Defaults to None.
        clubid (str | None): The primary club the Item belongs to. Defaults 
                             to None which means it is owned by SLO.
        net_qty (int): Net qty. of the Item available for club to borrow
                       at a given time.
        available_qty (int): Max qty. of the Item available for borrow. 
        total_qty (int): Total qty. available in the inventory including 
                         for non-student events.
        warranty_details (str | None): Optional attribute for warranty details
                                       like warranty id, or other info.
        other_details (str | None): Other details to the Item
        current_location (List[mtypes.Storage_Location]): Current location of 
                                       the item.
        requires_approval (bool): Whether the item requires approval for a borrow
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    iid: str = Field(..., description="Item ID")
    name: str = Field(..., min_length=1, max_length=100)
    brand: str = Field(..., min_length=1, max_length=50)
    photo: str | None = Field(None, description="Item Photo for Identifictation")
    clubid: str | None 
    net_qty: int = Field(..., ge=0)
    available_qty: int = Field(..., ge=0)
    total_qty: int = Field(..., ge=0)
    warranty_details: str | None = Field(..., max_length=100)
    other_details: str | None = Field(..., description="Other Item details")
    current_location: List[Storage_Location]
    requires_approval: bool

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        # extra="forbid",
        str_strip_whitespace=True,
    )


