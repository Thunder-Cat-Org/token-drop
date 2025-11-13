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

    def test_blacklist_single_address(self):
        operator = "sys"
        user = "user_address"

        self.blacklist.blacklist_address(address=user, signer=operator)

        status = self.blacklist.check_blacklist_for_address(address=user)
        assert status == "Address is blacklisted!"

    def test_blacklist_multiple_addresses(self):
        operator = "sys"
        users = ["u1", "u2", "u3"]

        result = self.blacklist.blacklist_addresses(addresses=users, signer=operator)

        assert result["added"] == users

        for u in users:
            status = self.blacklist.check_blacklist_for_address(address=u)
            assert status == "Address is blacklisted!"

    def test_remove_from_blacklist(self):
        operator = "sys"
        user = "removed_user"

        self.blacklist.blacklist_address(address=user, signer=operator)
        self.blacklist.remove_from_blacklist(address=user, signer=operator)

        status = self.blacklist.check_blacklist_for_address(address=user)
        assert status == "Address is not blacklisted!"
