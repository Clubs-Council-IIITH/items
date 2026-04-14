import strawberry
from typing import List, Optional
from models import Item
from otypes import Info, SimpleItemType, FullItemType
from db import itemsdb

@strawberry.field
async def getItems(
    info: Info, clubid: Optional[str] = None, limit: Optional[int] = None
) -> List[SimpleItemType]:
    """
    Query to retrieve items.
    Allows optional filtering by clubid and limiting the number of items returned.
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    query = {}
    if clubid:
        query["clubid"] = clubid

    results = await itemsdb.find(query).to_list(length=limit)
    return [SimpleItemType.from_pydantic(Item.model_validate(result)) for result in results]

@strawberry.field
async def getItem(info: Info, iid: str) -> FullItemType:
    """
    Query to retrieve full details of an item by iid.
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    result = await itemsdb.find_one({"iid": iid})
    if not result:
        raise Exception("Item not found")
    return FullItemType.from_pydantic(Item.model_validate(result))


@strawberry.field
async def checkAvailability(info: Info, iid: str, borrow_qty: int) -> bool:
    """
    Query to check if an item has enough available quantity for the requested borrow quantity.
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    result = await itemsdb.find_one({"iid": iid})
    if not result:
        raise Exception("Item not found")

    available_qty = result.get("available_qty", 0)
    return available_qty >= borrow_qty


queries = [getItems, getItem, checkAvailability]
