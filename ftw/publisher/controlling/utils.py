from persistent.dict import PersistentDict
from persistent.list import PersistentList

def persistent_aware(item):
    """
    This function assures the persistency of the dictionaries.
    It gets an item and checkes recursive the content, if the item is a dictionary
    or a list/tuple it converts it to a PersistentDict or a PersistentList.
    @param item:    a dictionary, list, tuple or any other item
    @return:        PersistentDict, PersistentList or any other item
    """
    if isinstance(item, dict) or isinstance(item, PersistentDict):
        newitem = PersistentDict()
        for key, value in item.items():
            newitem[key] = persistent_aware(value)
        return newitem
    elif isinstance(item, list) or isinstance(item, tuple) or isinstance(item, PersistentList):
        newitem = PersistentList()
        for value in item:
            newitem.append(persistent_aware(value))
        return newitem
    return item
