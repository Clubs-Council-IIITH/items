from pydantic import StringConstraints
import strawberry
from enum import StrEnum, auto


class Storage_Full_Location:
    """
    String representation of the storage locations in Storage_Location
    """
    amphi = "Amphitheater Storage Room"
    vindhya = "Vindhya Storage Room"
    himalaya = "Himalaya Storage Room"
    music_room = "Music Room"
    astro_lab = "Astro Lab"
    other = "Other"


@strawberry.enum
class Storage_Location(StrEnum):
    """
    Enum for storage locations for the Item
    """
    amphi = auto()
    vindhya = auto()
    himalaya = auto()
    music_room = auto()
    astro_lab = auto()
    other = auto()
