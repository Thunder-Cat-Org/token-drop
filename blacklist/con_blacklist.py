# Purpose of this file is to blacklist a provided user from interacting with your contract.
metadata = Hash()
not_allowed = Variable()

BlacklistEvent = LogEvent(
    event="Blacklist",
    params={
        "from": {"type": str, "indx": True},
        "to": {"type": str, "indx": True},
    },
)

RemoveBlacklistEvent = LogEvent(
    event="RemoveBlackList",
    params={
        "from": {"type": str, "indx": True},
        "to": {"type": str, "indx": True},
    },
)


@construct
def seed():
    metadata["operator"] = ctx.caller
    not_allowed.set([])


@export
def blacklist_address(address: str):
    assert ctx.caller == metadata["operator"], "Only operator can perform this action!"

    current_list = not_allowed.get()
    assert address not in current_list, "Address is already blacklisted!"

    current_list.append(address)
    not_allowed.set(current_list)

    BlacklistEvent({"from": ctx.caller, "to": address})


@export
def blacklist_addresses(addresses: list):
    assert ctx.caller == metadata["operator"], "Only operator can perform this action!"

    current_list = not_allowed.get()
    added = []

    for address in addresses:
        if address not in current_list:
            current_list.append(address)
            added.append(address)

    not_allowed.set(current_list)
    BlacklistEvent({"from": ctx.caller, "to": str(added)})
    return {"added": added}


@export
def check_blacklist_for_address(address: str):
    current_list = not_allowed.get()
    if address in current_list:
        return "Address is blacklisted!"
    return "Address is not blacklisted!"


@export
def remove_from_blacklist(address: str):
    assert ctx.caller == metadata["operator"], "Only operator can perform this action!"

    current_list = not_allowed.get()
    assert address in current_list, "Address is not currently blacklisted!"

    current_list.remove(address)
    not_allowed.set(current_list)

    RemoveBlacklistEvent({"from": ctx.caller, "to": address})


@export
def change_metadata(key: str, value: str):
    assert ctx.caller == metadata["operator"], "Only operator can set metadata!"
    metadata[key] = value
