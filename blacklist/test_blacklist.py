import os
from pathlib import Path
import pytest
from contracting.client import ContractingClient

HERE = Path(__file__).resolve().parent
FILE_PATH = HERE / "./con_blacklist.py"

# operator = "sys"; Default operator when no owner specified


class TestBlacklistContract:
    def setup_method(self):
        self.c = ContractingClient()
        self.c.flush()

        with open(FILE_PATH) as f:
            code = f.read()

        # Submit contract without specifying owner - uses "sys" as default
        # This sets metadata["operator"] = "sys" in the @construct function
        self.c.submit(code, name="con_blacklist")
        self.blacklist = self.c.get_contract("con_blacklist")

    def test_blacklist_multiple_addresses(self):
        operator = "sys"
        users = ["u1", "u2", "u3"]

        result = self.blacklist.blacklist_addresses(addresses=users, signer=operator)

        assert result["added"] == users

        for u in users:
            status = self.blacklist.is_address_blacklisted(address=u)
            assert status == True

    def test_remove_from_blacklist(self):
        operator = "sys"
        user = ["u1", "u2", "u3"]

        result = self.blacklist.blacklist_addresses(addresses=user, signer=operator)
        assert result["added"] == user
        for u in user:
            status = self.blacklist.is_address_blacklisted(address=u)
            assert status == True

        remove = self.blacklist.remove_from_blacklist(address=user, signer=operator)
        assert remove["removed"] == user
        for u in user:
            status = self.blacklist.is_address_blacklisted(address=u)
            assert status == False
