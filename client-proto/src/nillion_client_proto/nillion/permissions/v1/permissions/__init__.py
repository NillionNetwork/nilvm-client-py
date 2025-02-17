# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: nillion/permissions/v1/permissions.proto
# plugin: python-betterproto
# This file has been @generated

from dataclasses import dataclass
from typing import List

import betterproto

from ....auth.v1 import user as ___auth_v1_user__


@dataclass(eq=False, repr=False)
class Permissions(betterproto.Message):
    """The permissions for a set of stored values."""

    owner: "___auth_v1_user__.UserId" = betterproto.message_field(1)
    """The user id for the owner of these values."""

    retrieve: List["___auth_v1_user__.UserId"] = betterproto.message_field(2)
    """The list of user ids that are allowed to retrieve the stored values."""

    update: List["___auth_v1_user__.UserId"] = betterproto.message_field(3)
    """The list of user ids that are allowed to update the stored values."""

    delete: List["___auth_v1_user__.UserId"] = betterproto.message_field(4)
    """The list of user ids that are allowed to delete the stored values."""

    compute: List["ComputePermissions"] = betterproto.message_field(5)
    """The list of compute permissions."""


@dataclass(eq=False, repr=False)
class ComputePermissions(betterproto.Message):
    """The permissions to execute a program."""

    user: "___auth_v1_user__.UserId" = betterproto.message_field(1)
    """The user id we're granting permissions to."""

    program_ids: List[str] = betterproto.string_field(2)
    """The program ids this user is allowed to use the stored values in."""
