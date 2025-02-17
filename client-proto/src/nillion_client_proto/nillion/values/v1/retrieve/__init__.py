# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: nillion/values/v1/retrieve.proto
# plugin: python-betterproto
# This file has been @generated

from dataclasses import dataclass
from typing import List

import betterproto

from ....payments.v1 import receipt as ___payments_v1_receipt__
from .. import value as _value__


@dataclass(eq=False, repr=False)
class RetrieveValuesRequest(betterproto.Message):
    """A request to retrieve a set of stored values."""

    signed_receipt: "___payments_v1_receipt__.SignedReceipt" = (
        betterproto.message_field(1)
    )
    """
    The receipt that proves this operation was paid for.
    
     The receipt must be for a `RetrieveValues` operation.
    """


@dataclass(eq=False, repr=False)
class RetrieveValuesResponse(betterproto.Message):
    """A response to a request to retrieve values stored in the network."""

    values: List["_value__.NamedValue"] = betterproto.message_field(2)
    """The values."""
