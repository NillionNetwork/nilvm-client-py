# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: nillion/values/v1/value.proto
# plugin: python-betterproto
# This file has been @generated

from dataclasses import dataclass
from typing import List

import betterproto
import betterproto.lib.google.protobuf as betterproto_lib_google_protobuf


@dataclass(eq=False, repr=False)
class NamedValue(betterproto.Message):
    """A named value."""

    name: str = betterproto.string_field(1)
    """The name of this value."""

    value: "Value" = betterproto.message_field(2)
    """The value itself."""


@dataclass(eq=False, repr=False)
class Value(betterproto.Message):
    """A value."""

    public_boolean: "PublicInteger" = betterproto.message_field(1, group="value")
    """A public boolean."""

    public_integer: "PublicInteger" = betterproto.message_field(2, group="value")
    """A public integer."""

    public_unsigned_integer: "PublicInteger" = betterproto.message_field(
        3, group="value"
    )
    """A public unsigned integer."""

    shamir_share_boolean: "ShamirShare" = betterproto.message_field(4, group="value")
    """A shamir share of a secret boolean value."""

    shamir_share_integer: "ShamirShare" = betterproto.message_field(5, group="value")
    """A shamir share of a secret integer value."""

    shamir_share_unsigned_integer: "ShamirShare" = betterproto.message_field(
        6, group="value"
    )
    """A shamir share of a secret unsigned integer value."""

    array: "Array" = betterproto.message_field(7, group="value")
    """An array."""

    tuple: "Tuple" = betterproto.message_field(8, group="value")
    """A tuple."""

    shamir_shares_blob: "ShamirSharesBlob" = betterproto.message_field(9, group="value")
    """A secret shared blob."""

    ecdsa_private_key_share: "EcdsaPrivateKeyShare" = betterproto.message_field(
        10, group="value"
    )
    """An ECDSA private key share."""

    ecdsa_signature_share: "EcdsaSignatureShare" = betterproto.message_field(
        11, group="value"
    )
    """An ECDSA signature share."""

    ecdsa_message_digest: "EcdsaMessageDigest" = betterproto.message_field(
        12, group="value"
    )
    """The digest of a message."""

    ecdsa_public_key: "EcdsaPublicKey" = betterproto.message_field(13, group="value")
    """An ECDSA public key."""

    store_id: "StoreId" = betterproto.message_field(14, group="value")
    """A store id."""

    eddsa_private_key_share: "EddsaPrivateKeyShare" = betterproto.message_field(
        15, group="value"
    )
    """An Eddsa private key share."""

    eddsa_signature: "EddsaSignature" = betterproto.message_field(16, group="value")
    """An Eddsa signature."""

    eddsa_message: "EddsaMessage" = betterproto.message_field(17, group="value")
    """An Eddsa message."""

    eddsa_public_key: "EddsaPublicKey" = betterproto.message_field(18, group="value")
    """An Eddsa public key."""


@dataclass(eq=False, repr=False)
class PublicInteger(betterproto.Message):
    """A public integer."""

    value: bytes = betterproto.bytes_field(1)
    """The integer value, encoded in little endian."""


@dataclass(eq=False, repr=False)
class ShamirShare(betterproto.Message):
    """A shamir share."""

    value: bytes = betterproto.bytes_field(1)
    """The value, encoded in little endian."""


@dataclass(eq=False, repr=False)
class Array(betterproto.Message):
    """An array."""

    values: List["Value"] = betterproto.message_field(1)
    """
    The array values.
    
     All the values must be of the same type.
    """

    inner_type: "ValueType" = betterproto.message_field(2)
    """The type of all elements in this array."""


@dataclass(eq=False, repr=False)
class Tuple(betterproto.Message):
    """A tuple."""

    left: "Value" = betterproto.message_field(1)
    """The left value."""

    right: "Value" = betterproto.message_field(2)
    """The right value."""


@dataclass(eq=False, repr=False)
class EcdsaPrivateKeyShare(betterproto.Message):
    """An ECDSA private key share."""

    i: int = betterproto.uint32_field(1)
    """Index of local party in key generation protocol."""

    x: bytes = betterproto.bytes_field(2)
    """The secret share x."""

    shared_public_key: bytes = betterproto.bytes_field(3)
    """Public key corresponding to shared secret key, in compressed form."""

    public_shares: List[bytes] = betterproto.bytes_field(4)
    """Public shares of all signers sharing the key, in compressed form."""


@dataclass(eq=False, repr=False)
class EcdsaSignatureShare(betterproto.Message):
    """An ECDSA signature share."""

    r: bytes = betterproto.bytes_field(1)
    """r component of signature share"""

    sigma: bytes = betterproto.bytes_field(2)
    """sigma component of partial signature share."""


@dataclass(eq=False, repr=False)
class EcdsaMessageDigest(betterproto.Message):
    """The digest of a message."""

    digest: bytes = betterproto.bytes_field(1)
    """The digest."""


@dataclass(eq=False, repr=False)
class EcdsaPublicKey(betterproto.Message):
    """An ECDSA public key."""

    public_key: bytes = betterproto.bytes_field(1)
    """The public key."""


@dataclass(eq=False, repr=False)
class StoreId(betterproto.Message):
    """A store id."""

    store_id: bytes = betterproto.bytes_field(1)
    """The store id."""


@dataclass(eq=False, repr=False)
class EddsaPrivateKeyShare(betterproto.Message):
    """An Eddsa private key share."""

    i: int = betterproto.uint32_field(1)
    """Index of local party in key generation protocol."""

    x: bytes = betterproto.bytes_field(2)
    """The secret share x."""

    shared_public_key: bytes = betterproto.bytes_field(3)
    """Public key corresponding to shared secret key, in compressed form."""

    public_shares: List[bytes] = betterproto.bytes_field(4)
    """Public shares of all signers sharing the key, in compressed form."""


@dataclass(eq=False, repr=False)
class EddsaSignature(betterproto.Message):
    """An Eddsa signature."""

    signature: bytes = betterproto.bytes_field(1)
    """The signature."""


@dataclass(eq=False, repr=False)
class EddsaMessage(betterproto.Message):
    """An Eddsa message."""

    message: bytes = betterproto.bytes_field(1)
    """The message."""


@dataclass(eq=False, repr=False)
class EddsaPublicKey(betterproto.Message):
    """An Eddsa public key."""

    public_key: bytes = betterproto.bytes_field(1)
    """The public key."""


@dataclass(eq=False, repr=False)
class ShamirSharesBlob(betterproto.Message):
    """Shamir shares of a blob."""

    shares: List["ShamirShare"] = betterproto.message_field(1)
    """The shares."""

    original_size: int = betterproto.uint64_field(2)
    """The original size of the blob before secret sharing."""


@dataclass(eq=False, repr=False)
class ValueType(betterproto.Message):
    """A type of a value."""

    public_integer: "betterproto_lib_google_protobuf.Empty" = betterproto.message_field(
        1, group="value_type"
    )
    """A public integer."""

    public_unsigned_integer: "betterproto_lib_google_protobuf.Empty" = (
        betterproto.message_field(2, group="value_type")
    )
    """A public unsigned integer."""

    public_boolean: "betterproto_lib_google_protobuf.Empty" = betterproto.message_field(
        3, group="value_type"
    )
    """A public boolean."""

    shamir_share_integer: "betterproto_lib_google_protobuf.Empty" = (
        betterproto.message_field(4, group="value_type")
    )
    """A shamir share of an integer."""

    shamir_share_unsigned_integer: "betterproto_lib_google_protobuf.Empty" = (
        betterproto.message_field(5, group="value_type")
    )
    """A shamir share of an unsigned integer."""

    shamir_share_boolean: "betterproto_lib_google_protobuf.Empty" = (
        betterproto.message_field(6, group="value_type")
    )
    """A shamir share of a boolean."""

    array: "ArrayType" = betterproto.message_field(7, group="value_type")
    """An array."""

    tuple: "TupleType" = betterproto.message_field(8, group="value_type")
    """A tuple."""

    ecdsa_private_key_share: "betterproto_lib_google_protobuf.Empty" = (
        betterproto.message_field(9, group="value_type")
    )
    """An ECDSA private key share."""

    ecdsa_message_digest: "betterproto_lib_google_protobuf.Empty" = (
        betterproto.message_field(10, group="value_type")
    )
    """An ECDSA message digest."""

    ecdsa_signature_share: "betterproto_lib_google_protobuf.Empty" = (
        betterproto.message_field(11, group="value_type")
    )
    """An ECDSA signature share."""

    ecdsa_public_key: "betterproto_lib_google_protobuf.Empty" = (
        betterproto.message_field(12, group="value_type")
    )
    """An ECDSA public key."""

    store_id: "betterproto_lib_google_protobuf.Empty" = betterproto.message_field(
        13, group="value_type"
    )
    """A store id."""

    eddsa_private_key_share: "betterproto_lib_google_protobuf.Empty" = (
        betterproto.message_field(14, group="value_type")
    )
    """An Eddsa private key share."""

    eddsa_signature: "betterproto_lib_google_protobuf.Empty" = (
        betterproto.message_field(15, group="value_type")
    )
    """An Eddsa signature."""

    eddsa_message: "betterproto_lib_google_protobuf.Empty" = betterproto.message_field(
        16, group="value_type"
    )
    """An Eddsa message."""

    eddsa_public_key: "betterproto_lib_google_protobuf.Empty" = (
        betterproto.message_field(17, group="value_type")
    )
    """An Eddsa public key."""


@dataclass(eq=False, repr=False)
class ArrayType(betterproto.Message):
    """An array."""

    inner_type: "ValueType" = betterproto.message_field(1)
    """The type of each element in the array."""

    size: int = betterproto.uint64_field(2)
    """The array size."""


@dataclass(eq=False, repr=False)
class TupleType(betterproto.Message):
    """A tuple."""

    left: "ValueType" = betterproto.message_field(1)
    """The type of the left element in the tuple."""

    right: "ValueType" = betterproto.message_field(2)
    """The type of the right element in the tuple."""
