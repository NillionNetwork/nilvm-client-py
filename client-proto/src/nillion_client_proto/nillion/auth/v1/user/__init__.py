# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: nillion/auth/v1/user.proto
# plugin: python-betterproto
# This file has been @generated

from dataclasses import dataclass

import betterproto


@dataclass(eq=False, repr=False)
class UserId(betterproto.Message):
    """A user identifier."""

    contents: bytes = betterproto.bytes_field(1)
    """The contents of the user identifier."""
