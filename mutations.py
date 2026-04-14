import strawberry
from fastapi.encoders import jsonable_encoder
from typing import List
from models import Item
from otypes import Info, FullItemInput, ItemQtyInput, FullItemType, SimpleItemType
from db import itemsdb

@strawberry.mutation
async def addItem(itemInput: FullItemInput, info: Info) -> FullItemType:
    """
    Add a new item. Only accessible to 'cc' and 'club' roles.
    Clubs can only add items for their own club.
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user.get("role")
    item_input = jsonable_encoder(itemInput.to_pydantic())

    if role not in ["cc", "slo"]:
        raise Exception("Not Authorized")

    if item_input.get("total_qty") == 1 and len(item_input.get("current_location", [])) != 1:
        raise Exception("If total_qty is 1, current_location must have exactly 1 item")

    existing = await itemsdb.find_one({
        "$or": [
            {"iid": item_input["iid"]},
            {"name": item_input.get("name")}
        ]
    })
    if existing:
        raise Exception("Item with this iid or name already exists")

    created_record = await itemsdb.insert_one(item_input)
    created_sample = Item.model_validate(
        await itemsdb.find_one({"_id": created_record.inserted_id})
    )
    return FullItemType.from_pydantic(created_sample)


@strawberry.mutation
async def editItem(itemInput: FullItemInput, info: Info) -> FullItemType:
    """
    Edit an existing item. Only accessible to 'cc' and 'club' roles.
    Clubs can only edit their own items.
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user.get("role")
    item_input = jsonable_encoder(itemInput.to_pydantic())

    existing = await itemsdb.find_one({"iid": item_input["iid"]})
    if not existing:
        raise Exception("Item doesn't exist")

    if role not in ["cc", "slo"]:
        raise Exception("Not Authorized")

    if item_input.get("total_qty") == 1 and len(item_input.get("current_location", [])) != 1:
        raise Exception("If total_qty is 1, current_location must have exactly 1 item")

    item_input["_id"] = existing["_id"]
    await itemsdb.replace_one({"iid": item_input["iid"]}, item_input)

    updated_sample = Item.model_validate(
        await itemsdb.find_one({"iid": item_input["iid"]})
    )
    return FullItemType.from_pydantic(updated_sample)


@strawberry.mutation
async def editItemQty(itemQtyInputs: List[ItemQtyInput], info: Info) -> List[SimpleItemType]:
    """
    Directly change item quantities. Only accessible to 'slo'.
    Accepts a list of ItemQtyInput and returns a list of updated items.
    """
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user.get("role")

    if role not in ["slo"]:
        raise Exception("Not Authorized: only slo can change quantity directly")

    updated_items = []

    for input_data in itemQtyInputs:
        existing = await itemsdb.find_one({"iid": input_data.iid})
        if not existing:
            raise Exception(f"Item {input_data.iid} doesn't exist")

        await itemsdb.update_one(
            {"iid": input_data.iid},
            {"$set": {
                "net_qty": input_data.net_qty,
                "available_qty": input_data.available_qty
            }}
        )

        updated_sample = Item.model_validate(
            await itemsdb.find_one({"iid": input_data.iid})
        )
        updated_items.append(SimpleItemType.from_pydantic(updated_sample))

    return updated_items


mutations = [addItem, editItem, editItemQty]
