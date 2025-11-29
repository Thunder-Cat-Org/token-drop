I = importlib
metadata = Hash()
pool_owner = Hash()  # pool_owner[pool_id] = owner addr
pool_token = Hash()  # pool_token[pool_id] = token contract name
pool_mode = Hash()  # pool_mode[pool_id] = "whitelist" | "open"
claimed = Hash(default_value=0)
deposits = Hash(default_value=0)
allocated = Hash(default_value=0)
pool_balance = Hash(default_value=0)
open_pool_limit = Hash(default_value=0)
pool_index = Hash()  # pool_index[pool_id] = list of addresses

# blacklist stored as boolean per (pool_id, addr)
pool_blacklist = Hash(default_value=False)

POOL_CREATION_FEE = 10  # 10 XIAN
FEE_RECIPIENT = Variable()

CURRENCY = "currency"

CreatePoolEvent = LogEvent(
    event="CreatePool",
    params={
        "pool_id": {"type": str},
        "owner": {"type": str},
        "token": {"type": str},
        "fee_paid": {"type": (int, float, decimal)},
    },
)

DepositEvent = LogEvent(
    event="Deposit",
    params={
        "pool_id": {"type": str},
        "from": {"type": str},
        "amount": {"type": (int, float, decimal)},
    },
)

WithdrawEvent = LogEvent(
    event="Withdraw",
    params={
        "pool_id": {"type": str},
        "to": {"type": str},
        "amount": {"type": (int, float, decimal)},
    },
)

SetAllocationEvent = LogEvent(
    event="SetAllocation",
    params={"pool_id": {"type": str}, "by": {"type": str}},
)

ClaimEvent = LogEvent(
    event="Claim",
    params={
        "pool_id": {"type": str},
        "by": {"type": str},
        "to": {"type": str},
        "amount": {"type": (int, float, decimal)},
    },
)

BlacklistEvent = LogEvent(
    event="Blacklist",
    params={"pool_id": {"type": str}, "by": {"type": str}, "added": {"type": str}},
)

RemoveBlacklistEvent = LogEvent(
    event="RemoveBlacklist",
    params={"pool_id": {"type": str}, "by": {"type": str}, "removed": {"type": str}},
)

RevokeMutabilityEvent = LogEvent(event="RevokeMutability", params={"by": {"type": str}})

TransferOperator = LogEvent(
    event="TransferOperator", params={"new_operator": {"type": str}}
)


@construct
def seed():
    metadata["operator"] = ctx.caller
    FEE_RECIPIENT.set(ctx.caller)


@export
def set_fee_recipient(address: str):
    assert (
        ctx.caller == metadata["operator"]
    ), "Only fee recipient can change recipient!"
    FEE_RECIPIENT.set(address)
    return {"fee_recipient": address}


@export
def get_fee_recipient():
    return FEE_RECIPIENT.get()


@export
def create_pool(pool_name: str, token_contract: str, mode: str):
    assert mode == "whitelist" or mode == "open", "Invalid mode!"
    pool_id = pool_name

    # Ensure pool doesn't already exist
    assert pool_owner[pool_id] is None, "Pool already exists!"

    # Charge the pool creation fee
    fee_recipient = FEE_RECIPIENT.get()
    currency = I.import_module(CURRENCY)
    currency.transfer_from(
        amount=POOL_CREATION_FEE, to=fee_recipient, main_account=ctx.caller
    )

    pool_owner[pool_id] = ctx.caller
    pool_token[pool_id] = token_contract
    pool_mode[pool_id] = mode
    pool_balance[pool_id] = 0.0

    CreatePoolEvent(
        {
            "pool_id": pool_id,
            "owner": ctx.caller,
            "token": token_contract,
            "fee_paid": POOL_CREATION_FEE,
        }
    )

    return {"pool_id": pool_id, "mode": mode}


@export
def deposit_to_pool(pool_id: str, amount: float):
    owner = pool_owner[pool_id]
    assert owner is not None, f"Pool not found: {pool_id}"

    # Get token contract
    token_contract_name = pool_token[pool_id]
    assert token_contract_name is not None, "Pool token not set!"

    token_contract = I.import_module(token_contract_name)

    # Transfer tokens from caller to this contract
    token_contract.transfer_from(amount=amount, to=ctx.this, main_account=ctx.caller)

    # Update pool state
    pool_balance[pool_id] += amount
    deposits[ctx.caller, token_contract_name] += amount

    DepositEvent({"pool_id": pool_id, "from": ctx.caller, "amount": amount})

    return {"deposited": amount, "pool_balance": pool_balance[pool_id]}


@export
def set_allocation(pool_id: str, allocations: list):
    owner = pool_owner[pool_id]
    assert owner is not None, "Pool not found!"
    assert owner == ctx.caller, "Only pool owner!"

    count = 0
    addresses = []

    for allocation in allocations:
        amt = allocation["amount"]

        addr = allocation["address"]
        allocated[(pool_id, addr)] = amt
        addresses.append(addr)
        count = count + 1

    SetAllocationEvent({"pool_id": pool_id, "by": ctx.caller})
    return {"allocated": count, "addresses": addresses}


@export
def get_allocation(pool_id: str, address: str):
    return allocated[(pool_id, address)]


@export
def set_open_pool_limit(pool_id: str, limit: float):
    owner = pool_owner[pool_id]
    assert owner is not None, "Pool not found!"
    assert owner == ctx.caller, "Only pool owner!"

    assert limit > 0, "Limit must be > 0"

    open_pool_limit[pool_id] = limit
    return {"pool_id": pool_id, "limit": limit}


@export
def blacklist_addresses(pool_id: str, addresses: list):
    owner = pool_owner[pool_id]
    assert owner is not None, "Pool not found!"
    assert owner == ctx.caller, "Only pool owner!"

    added = []
    for entry in addresses:
        addr = entry["address"]

        if pool_blacklist[(pool_id, addr)] is False:
            pool_blacklist[(pool_id, addr)] = True
            added.append(addr)

    # build comma-joined string
    joined = ",".join(added)

    BlacklistEvent({"pool_id": pool_id, "by": ctx.caller, "added": joined})
    return {"added": added}


@export
def remove_from_blacklist(pool_id: str, addresses: list):
    owner = pool_owner[pool_id]
    assert owner is not None, "Pool not found!"
    assert owner == ctx.caller, "Only pool owner!"

    removed = []
    for entry in addresses:
        addr = entry["address"]

        if pool_blacklist[(pool_id, addr)] is True:
            pool_blacklist[(pool_id, addr)] = False
            removed.append(addr)

    joined = ",".join(removed)

    RemoveBlacklistEvent({"pool_id": pool_id, "by": ctx.caller, "removed": joined})

    return {"removed": removed}


@export
def is_address_blacklisted(pool_id: str, address: str):
    return pool_blacklist[(pool_id, address)]


@export
def get_claimed(pool_id: str, address: str):
    return claimed[(pool_id, address)]


@export
def get_pool_balance(pool_id: str):
    return pool_balance[pool_id]


@export
def claim(pool_id: str, amount: float, to: str):
    assert amount > 0.0, "Amount must be greater than 0!"

    owner = pool_owner[pool_id]
    assert owner is not None, "Pool not found!"

    assert not pool_blacklist[(pool_id, ctx.caller)], "Address is blacklisted!"

    mode = pool_mode[pool_id]
    assert mode is not None, "Pool mode not set!"

    remaining_pool = pool_balance[pool_id]
    assert remaining_pool >= amount, "Not enough tokens in pool!"

    already = claimed[(pool_id, ctx.caller)]

    if mode == "whitelist":
        alloc = allocated[(pool_id, ctx.caller)]
        assert alloc > 0.0, "Address not whitelisted!"
        assert already + amount <= alloc, "Claim amount exceeds allocation!"
    else:
        limit = open_pool_limit[pool_id]
        assert limit > 0.0, "Open pool limit not set!"
        assert already + amount <= limit, "Claim exceeds per-address limit!"

    token_contract = pool_token[pool_id]
    assert token_contract is not None, "Pool token not set!"

    token = I.import_module(token_contract)
    token.transfer(amount=amount, to=to)

    claimed[(pool_id, ctx.caller)] = already + amount
    pool_balance[pool_id] = remaining_pool - amount

    ClaimEvent({"pool_id": pool_id, "by": ctx.caller, "to": to, "amount": amount})

    return {
        "claimed": amount,
        "total_claimed": claimed[(pool_id, ctx.caller)],
        "pool_remaining": pool_balance[pool_id],
    }


@export
def withdraw_from_pool(pool_id: str, amount: float):
    assert decimal(amount) > 0.0, "Amount must be greater than 0!"

    owner = pool_owner[pool_id]
    assert owner is not None, "Pool not found!"
    assert owner == ctx.caller, "Only pool owner!"

    rem = pool_balance[pool_id]
    assert rem >= amount, "Insufficient pool balance!"

    token_contract = pool_token[pool_id]

    token = I.import_module(token_contract)
    token.transfer(amount=amount, to=ctx.caller)

    pool_balance[pool_id] = rem - amount
    deposits[(ctx.caller, token_contract)] = (
        deposits[(ctx.caller, token_contract)] - amount
    )

    WithdrawEvent({"pool_id": pool_id, "to": ctx.caller, "amount": amount})
    return {"withdrawn": amount, "pool_remaining": pool_balance[pool_id]}


@export
def get_allocation_stats(pool_id: str):
    owner = pool_owner[pool_id]
    assert owner is not None, "Pool not found!"

    total_alloc = 0.0

    addrs = pool_index[pool_id] or []

    for addr in addrs:
        total_alloc += allocated[(pool_id, addr)]

    balance = pool_balance[pool_id]

    status = (
        "underfunded"
        if balance < total_alloc
        else "fully_funded" if balance == total_alloc else "overfunded"
    )

    return {
        "pool_id": pool_id,
        "total_allocated": total_alloc,
        "pool_balance": balance,
        "status": status,
    }


@export
def get_effective_allocation(pool_id: str, address: str):
    mode = pool_mode[pool_id]
    assert mode is not None, "Pool not found!"

    if mode == "open":
        return open_pool_limit[pool_id]
    else:
        return allocated[(pool_id, address)]


@export
def transfer_operator(new_operator: str):
    assert ctx.caller == metadata["operator"], "Only current operator can transfer!"
    assert new_operator is not None and new_operator != "", "Invalid address!"
    metadata["operator"] = new_operator
    TransferOperator({"new_operator": new_operator})
    return {"operator": new_operator}
