# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: nillion/payments/v1/config.proto
# plugin: python-betterproto
# This file has been @generated

from dataclasses import dataclass

import betterproto


@dataclass(eq=False, repr=False)
class PaymentsConfigResponse(betterproto.Message):
    """A response to a payments configuration request."""

    minimum_add_funds_payment: int = betterproto.uint64_field(1)
    """
    The minimum amount of unil that can be added in a `Payments.add_funds` request.
    """

    credits_per_nil: int = betterproto.uint64_field(2)
    """The number of credits one gets for every nil funded to an account."""
