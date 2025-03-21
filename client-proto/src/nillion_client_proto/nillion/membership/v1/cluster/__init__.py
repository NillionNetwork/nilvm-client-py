# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: nillion/membership/v1/cluster.proto
# plugin: python-betterproto
# This file has been @generated

from dataclasses import dataclass
from typing import List

import betterproto

from ....auth.v1 import public_key as ___auth_v1_public_key__


class Prime(betterproto.Enum):
    """A prime number."""

    SAFE_64_BITS = 0
    """
    A safe 64 bit prime number.
    
     This is prime number 18446744072637906947.
    """

    SAFE_128_BITS = 1
    """
    A safe 128 bit prime number.
    
     This is prime number 340282366920938463463374607429104828419.
    """

    SAFE_256_BITS = 2
    """
    A safe 256 bit prime number.
    
     This is prime number 115792089237316195423570985008687907853269984665640564039457584007911397392387.
    """


@dataclass(eq=False, repr=False)
class Cluster(betterproto.Message):
    """The definition of a cluster."""

    members: List["ClusterMember"] = betterproto.message_field(1)
    """The members of this cluster."""

    leader: "ClusterMember" = betterproto.message_field(2)
    """The leader of this cluster."""

    prime: "Prime" = betterproto.enum_field(3)
    """The prime number this cluster uses."""

    polynomial_degree: int = betterproto.uint32_field(4)
    """The polynomial degree used in this cluster."""

    kappa: int = betterproto.uint32_field(5)
    """The security parameter kappa used in this cluster."""


@dataclass(eq=False, repr=False)
class ClusterMember(betterproto.Message):
    """A cluster member."""

    identity: "NodeId" = betterproto.message_field(1)
    """
    The identity for this member.
    
     This is a unique identifier derived from the public key.
    """

    public_key: "___auth_v1_public_key__.PublicKey" = betterproto.message_field(2)
    """
    The public key for this member.
    
     **This field is deprecated**. `public_keys.authentication` should be used instead.
    """

    grpc_endpoint: str = betterproto.string_field(3)
    """The gRPC endpoint this member can be reached at."""

    public_keys: "PublicKeys" = betterproto.message_field(4)
    """The public keys for a cluster member."""


@dataclass(eq=False, repr=False)
class PublicKeys(betterproto.Message):
    """The public keys for a cluster member."""

    authentication: "___auth_v1_public_key__.PublicKey" = betterproto.message_field(1)
    """The authentication public key for this member."""


@dataclass(eq=False, repr=False)
class NodeId(betterproto.Message):
    """
    A node identifier.

     This is currently used from a client perspective when:

     * Creating an authentication token.
     * Creating secret shares.
    """

    contents: bytes = betterproto.bytes_field(1)
    """The contents of this node identifier."""
