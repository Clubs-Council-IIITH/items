import strawberry
from graphql import GraphQLError

from db import itemsdb
from models import Item
from otypes import FullItemType, Info, SimpleItemType


@strawberry.field
async def getItems(
    info: Info, clubid: str | None = None, limit: int | None = None
) -> list[SimpleItemType]:
    """
    Query to retrieve items.
    Allows optional filtering by clubid and limiting the number of items
    returned.
    Only accessible to 'club', 'cc', and 'slo' roles.
    """
    user = info.context.user
    if user is None:
        raise GraphQLError("Not Authenticated")

    role = user.get("role")
    if role not in ["club", "cc", "slo"]:
        raise GraphQLError("Not Authorized")

    query = {}
    if clubid:
        query["clubid"] = clubid

    results = await itemsdb.find(query).to_list(length=limit)
    return [
        SimpleItemType.from_pydantic(Item.model_validate(result))
        for result in results
    ]


@strawberry.field
async def getItem(info: Info, iid: str) -> FullItemType:
    """
    Query to retrieve full details of an item by iid.
    Only accessible to 'club', 'cc', and 'slo' roles.
    """
    user = info.context.user
    if user is None:
        raise GraphQLError("Not Authenticated")

    role = user.get("role")
    if role not in ["club", "cc", "slo"]:
        raise GraphQLError("Not Authorized")

    result = await itemsdb.find_one({"iid": iid})
    if not result:
        raise GraphQLError("Item not found")
    return FullItemType.from_pydantic(Item.model_validate(result))


@strawberry.field
async def checkAvailability(info: Info, iid: str, borrow_qty: int) -> bool:
    """
    Query to check if an item has enough available quantity for the requested
    borrow quantity.
    Only accessible to 'club', 'cc', and 'slo' roles.
    """
    user = info.context.user
    if user is None:
        raise GraphQLError("Not Authenticated")

    role = user.get("role")
    if role not in ["club", "cc", "slo"]:
        raise GraphQLError("Not Authorized")

    result = await itemsdb.find_one({"iid": iid})
    if not result:
        raise GraphQLError("Item not found")

    available_qty = result.get("available_qty", 0)
    return available_qty >= borrow_qty


queries = [getItems, getItem, checkAvailability]
