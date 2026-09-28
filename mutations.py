from datetime import datetime, timezone

import strawberry
from fastapi.encoders import jsonable_encoder
from graphql import GraphQLError

from db import itemsdb, transactionsdb
from models import Item
from otypes import (
    FullItemInput,
    FullItemType,
    Info,
    ItemQtyInput,
    SimpleItemType,
)

ACTIVE_TRANSACTION_STATES = [
    "incomplete",
    "pending",
    "pending_club",
    "pending_slo",
    "approved_slo",
    "borrowed",
]

@strawberry.mutation
async def addItem(itemInput: FullItemInput, info: Info) -> FullItemType:
    """
    Add a new item. Only accessible to 'cc' and 'slo' roles.
    """
    user = info.context.user
    if user is None:
        raise GraphQLError("Not Authenticated")

    role = user.get("role")
    if role not in ["cc", "slo"]:
        raise GraphQLError("Not Authorized")

    item_input = jsonable_encoder(itemInput.to_pydantic())
    if not item_input.get("clubid"):
        item_input["clubid"] = "slo"

    if (
        item_input.get("total_qty") == 1
        and len(item_input.get("current_location", [])) != 1
    ):
        raise GraphQLError(
            "If total_qty is 1, current_location must have exactly 1 item"
        )

    existing = await itemsdb.find_one(
        {"$or": [{"iid": item_input["iid"]}, {"name": item_input.get("name")}]}
    )
    if existing:
        raise GraphQLError("Item with this iid or name already exists")

    created_record = await itemsdb.insert_one(item_input)
    created_sample = Item.model_validate(
        await itemsdb.find_one({"_id": created_record.inserted_id})
    )
    return FullItemType.from_pydantic(created_sample)


@strawberry.mutation
async def editItem(itemInput: FullItemInput, info: Info) -> FullItemType:
    """
    Edit an existing item. Only accessible to 'cc' and 'slo' roles.
    """
    user = info.context.user
    if user is None:
        raise GraphQLError("Not Authenticated")

    role = user.get("role")
    if role not in ["cc", "slo"]:
        raise GraphQLError("Not Authorized")

    item_input = jsonable_encoder(itemInput.to_pydantic())

    existing = await itemsdb.find_one({"iid": item_input["iid"]})
    if not existing:
        raise GraphQLError("Item doesn't exist")

    if (
        item_input.get("total_qty") == 1
        and len(item_input.get("current_location", [])) != 1
    ):
        raise GraphQLError(
            "If total_qty is 1, current_location must have exactly 1 item"
        )

    item_input["_id"] = existing["_id"]
    await itemsdb.replace_one({"iid": item_input["iid"]}, item_input)

    updated_sample = Item.model_validate(
        await itemsdb.find_one({"iid": item_input["iid"]})
    )
    return FullItemType.from_pydantic(updated_sample)


@strawberry.mutation
async def editItemQty(
    itemQtyInputs: list[ItemQtyInput], info: Info
) -> list[SimpleItemType]:
    """
    Directly change item quantities. Accessible to 'cc' and 'slo'.
    Accepts a list of ItemQtyInput and returns a list of updated items.
    """
    user = info.context.user
    if user is None:
        raise GraphQLError("Not Authenticated")

    role = user.get("role")
    if role not in ["cc", "slo"]:
        raise GraphQLError("Not Authorized")

    updated_items = []

    for input_data in itemQtyInputs:
        existing = await itemsdb.find_one({"iid": input_data.iid})
        if not existing:
            raise GraphQLError(f"Item {input_data.iid} doesn't exist")

        set_fields = {
            "net_qty": input_data.net_qty,
            "available_qty": input_data.available_qty,
        }
        if input_data.total_qty is not None:
            set_fields["total_qty"] = input_data.total_qty

        await itemsdb.update_one({"iid": input_data.iid}, {"$set": set_fields})

        updated_sample = Item.model_validate(
            await itemsdb.find_one({"iid": input_data.iid})
        )
        updated_items.append(SimpleItemType.from_pydantic(updated_sample))

    return updated_items


@strawberry.mutation
async def adjustAvailableQty(
    iid: str, delta: int, info: Info
) -> SimpleItemType:
    """
    Atomically increment or decrement available_qty for a single item.
    Pass delta=+1 or delta=-1. Result is clamped to [0, net_qty].
    Accessible to 'cc' and 'slo' roles only.
    """
    user = info.context.user
    if user is None:
        raise GraphQLError("Not Authenticated")

    role = user.get("role")
    if role not in ["cc", "slo"]:
        raise GraphQLError("Not Authorized")

    if delta == 0:
        raise GraphQLError("delta must be non-zero")

    existing = await itemsdb.find_one({"iid": iid})
    if not existing:
        raise GraphQLError(f"Item {iid} doesn't exist")

    current_avail = existing.get("available_qty", 0)
    net = existing.get("net_qty", 0)

    new_avail = max(0, min(net, current_avail + delta))

    await itemsdb.update_one(
        {"iid": iid},
        {"$set": {"available_qty": new_avail}},
    )

    updated = Item.model_validate(await itemsdb.find_one({"iid": iid}))
    return SimpleItemType.from_pydantic(updated)


@strawberry.mutation
async def deleteItem(iid: str, info: Info) -> FullItemType:
    """
    Soft-delete an item (sets is_deleted to True).
    Cascades: any of its transactions that are still in an active
    (non-terminal) state are force-moved to 'deleted' too.
    Only accessible to the 'slo' role.
    """
    user = info.context.user
    if user is None:
        raise GraphQLError("Not Authenticated")

    role = user.get("role")
    uid = user.get("uid", "")
    if role != "slo":
        raise GraphQLError("Not Authorized")

    existing = await itemsdb.find_one({"iid": iid})
    if not existing:
        raise GraphQLError(f"Item {iid} doesn't exist")
    if existing.get("is_deleted"):
        raise GraphQLError(f"Item {iid} is already deleted")

    await itemsdb.update_one({"iid": iid}, {"$set": {"is_deleted": True}})

    await transactionsdb.update_many(
        {"itemid": iid, "status.state": {"$in": ACTIVE_TRANSACTION_STATES}},
        {
            "$set": {
                "status.state": "deleted",
                "status.lastUpdatedTime": datetime.now(timezone.utc),
                "status.lastUpdatedBy": uid,
            }
        },
    )

    updated = Item.model_validate(await itemsdb.find_one({"iid": iid}))
    return FullItemType.from_pydantic(updated)


mutations = [addItem, editItem, editItemQty, adjustAvailableQty, deleteItem]
