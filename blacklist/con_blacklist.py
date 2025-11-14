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


# Remove a list of addresses from the blacklist
@export
def remove_from_blacklist(address: list):
    assert ctx.caller == metadata["operator"], "Only operator can perform this action!"

    current_list = not_allowed.get()
    removed = []

    for addr in address:
        if addr in current_list:
            current_list.remove(addr)
            removed.append(addr)
    not_allowed.set(current_list)
    RemoveBlacklistEvent({"from": ctx.caller, "to": str(removed)})
    return {"removed": removed}


@export
def is_address_blacklisted(address: str):
    current_list = not_allowed.get()
    if address in current_list:
        return True
    return False
