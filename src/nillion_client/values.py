from typing import Mapping, List, no_type_check

from betterproto.lib.google.protobuf import Empty
from nillion_client_core import (
    EncryptedNadaType,
    EncryptedNadaValue,
)
from nillion_client_proto.nillion.values.v1.value import (
    Array,
    ArrayType,
    EcdsaMessageDigest,
    EcdsaPublicKey,
    EcdsaPrivateKeyShare,
    EcdsaSignatureShare,
    EddsaMessage,
    EddsaPrivateKeyShare,
    EddsaPublicKey,
    EddsaSignature,
    NamedValue,
    PublicInteger,
    ShamirShare,
    ShamirSharesBlob,
    StoreId,
    Tuple,
    TupleType,
    Value,
    ValueType,
)


def encrypted_nada_values_to_protobuf(
    values: Mapping[str, EncryptedNadaValue],
) -> List[NamedValue]:
    return [
        NamedValue(name=name, value=encrypted_nada_value_to_protobuf(value))
        for (name, value) in values.items()
    ]


def encrypted_nada_value_to_protobuf(value: EncryptedNadaValue) -> Value:
    match value:
        case EncryptedNadaValue.ShamirShareInteger():  # type: ignore
            return Value(shamir_share_integer=ShamirShare(value=bytes(value.value)))
        case EncryptedNadaValue.ShamirShareUnsignedInteger():  # type: ignore
            return Value(
                shamir_share_unsigned_integer=ShamirShare(value=bytes(value.value))
            )
        case EncryptedNadaValue.ShamirShareBoolean():  # type: ignore
            return Value(shamir_share_boolean=ShamirShare(value=bytes(value.value)))
        case EncryptedNadaValue.ShamirSharesBlob():  # type: ignore
            return Value(
                shamir_shares_blob=ShamirSharesBlob(
                    shares=[ShamirShare(value=bytes(value)) for value in value.values],
                    original_size=value.original_size,
                )
            )
        case EncryptedNadaValue.PublicInteger():  # type: ignore
            return Value(public_integer=PublicInteger(value=bytes(value.value)))
        case EncryptedNadaValue.PublicUnsignedInteger():  # type: ignore
            return Value(
                public_unsigned_integer=PublicInteger(value=bytes(value.value))
            )
        case EncryptedNadaValue.PublicBoolean():  # type: ignore
            return Value(public_boolean=PublicInteger(value=bytes(value.value)))
        case EncryptedNadaValue.Array():  # type: ignore
            return Value(
                array=Array(
                    values=[encrypted_nada_value_to_protobuf(v) for v in value.values],
                    inner_type=encrypted_nada_type_to_protobuf(value.inner_type),
                )
            )
        case EncryptedNadaValue.Tuple():  # type: ignore
            return Value(
                tuple=Tuple(
                    left=encrypted_nada_value_to_protobuf(value.left),
                    right=encrypted_nada_value_to_protobuf(value.right),
                )
            )
        case EncryptedNadaValue.EcdsaMessageDigest():  # type: ignore
            return Value(
                ecdsa_message_digest=EcdsaMessageDigest(digest=bytes(value.value))
            )
        case EncryptedNadaValue.EcdsaSignature():  # type: ignore
            return Value(
                ecdsa_signature_share=EcdsaSignatureShare(
                    r=bytes(value.r), sigma=bytes(value.sigma)
                )
            )
        case EncryptedNadaValue.EcdsaPrivateKey():  # type: ignore
            return Value(
                ecdsa_private_key_share=EcdsaPrivateKeyShare(
                    i=value.i,
                    x=bytes(value.x),
                    shared_public_key=bytes(value.shared_public_key),
                    public_shares=[bytes(s) for s in value.public_shares],
                )
            )
        case EncryptedNadaValue.EcdsaPublicKey():  # type: ignore
            return Value(
                ecdsa_public_key=EcdsaPublicKey(
                    public_key=bytes(value.value),
                )
            )
        case EncryptedNadaValue.StoreId():  # type: ignore
            return Value(
                store_id=StoreId(
                    store_id=bytes(value.value),
                )
            )
        case EncryptedNadaValue.EddsaMessage():  # type: ignore
            return Value(eddsa_message=EddsaMessage(message=bytes(value.value)))
        case EncryptedNadaValue.EddsaSignature():  # type: ignore
            return Value(eddsa_signature=EddsaSignature(signature=bytes(value.value)))
        case EncryptedNadaValue.EddsaPrivateKey():  # type: ignore
            return Value(
                eddsa_private_key_share=EddsaPrivateKeyShare(
                    i=value.i,
                    x=bytes(value.x),
                    shared_public_key=bytes(value.shared_public_key),
                    public_shares=[bytes(s) for s in value.public_shares],
                )
            )
        case EncryptedNadaValue.EddsaPublicKey():  # type: ignore
            return Value(
                eddsa_public_key=EddsaPublicKey(
                    public_key=bytes(value.value),
                )
            )
        case _:
            raise Exception(f"unsupported type: {value}")


@no_type_check
def encrypted_nada_value_from_protobuf(value: Value) -> EncryptedNadaValue:
    match value:
        case Value(shamir_share_integer=share):
            return EncryptedNadaValue.ShamirShareInteger(value=list(share.value))
        case Value(shamir_share_unsigned_integer=share):
            return EncryptedNadaValue.ShamirShareUnsignedInteger(
                value=list(share.value)
            )
        case Value(shamir_share_boolean=share):
            return EncryptedNadaValue.ShamirShareBoolean(value=list(share.value))
        case Value(shamir_shares_blob=value):
            return EncryptedNadaValue.ShamirSharesBlob(
                values=[list(v.value) for v in value.shares],
                original_size=value.original_size,
            )
        case Value(public_integer=value):
            return EncryptedNadaValue.PublicInteger(value=list(value.value))
        case Value(public_unsigned_integer=value):
            return EncryptedNadaValue.PublicUnsignedInteger(value=list(value.value))
        case Value(public_boolean=value):
            return EncryptedNadaValue.PublicBoolean(value=list(value.value))
        case Value(array=value):
            return EncryptedNadaValue.Array(
                values=[encrypted_nada_value_from_protobuf(v) for v in value.values],
                inner_type=encrypted_nada_type_from_protobuf(value.inner_type),
            )
        case Value(tuple=value):
            return EncryptedNadaValue.Tuple(
                left=encrypted_nada_value_from_protobuf(value.left),
                right=encrypted_nada_value_from_protobuf(value.right),
            )
        case Value(ecdsa_message_digest=value):
            return EncryptedNadaValue.EcdsaMessageDigest(value=bytes(value.digest))
        case Value(ecdsa_signature_share=value):
            return EncryptedNadaValue.EcdsaSignature(
                r=bytes(value.r),
                sigma=bytes(value.sigma),
            )
        case Value(ecdsa_private_key_share=value):
            return EncryptedNadaValue.EcdsaPrivateKey(
                i=value.i,
                x=list(value.x),
                shared_public_key=list(value.shared_public_key),
                public_shares=[list(s) for s in value.public_shares],
            )
        case Value(ecdsa_public_key=value):
            return EncryptedNadaValue.EcdsaPublicKey(
                value=bytes(value.public_key),
            )
        case Value(eddsa_message=value):
            return EncryptedNadaValue.EddsaMessage(value=bytes(value.message))
        case Value(eddsa_signature=value):
            return EncryptedNadaValue.EddsaSignature(
                value=bytes(value.signature),
            )
        case Value(eddsa_private_key_share=value):
            return EncryptedNadaValue.EddsaPrivateKey(
                i=value.i,
                x=list(value.x),
                shared_public_key=list(value.shared_public_key),
                public_shares=[list(s) for s in value.public_shares],
            )
        case Value(eddsa_public_key=value):
            return EncryptedNadaValue.EddsaPublicKey(
                value=bytes(value.public_key),
            )
        case Value(store_id=value):
            return EncryptedNadaValue.StoreId(
                value=bytes(value.store_id),
            )
        case _:
            raise Exception(f"unsupported encrypted value: {value}")


def encrypted_nada_type_to_protobuf(nada_type: EncryptedNadaType) -> ValueType:
    match nada_type:  # type: ignore
        case EncryptedNadaType.Integer():  # type: ignore
            return ValueType(public_integer=Empty())
        case EncryptedNadaType.UnsignedInteger():  # type: ignore
            return ValueType(public_unsigned_integer=Empty())
        case EncryptedNadaType.Boolean():  # type: ignore
            return ValueType(public_boolean=Empty())
        case EncryptedNadaType.ShamirShareInteger():  # type: ignore
            return ValueType(shamir_share_integer=Empty())
        case EncryptedNadaType.ShamirShareUnsignedInteger():  # type: ignore
            return ValueType(shamir_share_unsigned_integer=Empty())
        case EncryptedNadaType.ShamirShareBoolean():  # type: ignore
            return ValueType(shamir_share_boolean=Empty())
        case EncryptedNadaType.Array():  # type: ignore
            return ValueType(
                array=ArrayType(
                    inner_type=encrypted_nada_type_to_protobuf(nada_type.inner_type),
                    size=nada_type.size,
                )
            )
        case EncryptedNadaType.Tuple():  # type: ignore
            return ValueType(
                tuple=TupleType(
                    left=encrypted_nada_type_to_protobuf(nada_type.left),
                    right=encrypted_nada_type_to_protobuf(nada_type.right),
                )
            )
        case EncryptedNadaType.EcdsaMessageDigest():  # type: ignore
            return ValueType(ecdsa_message_digest=Empty())
        case EncryptedNadaType.EcdsaSignature():  # type: ignore
            return ValueType(ecdsa_signature_share=Empty())
        case EncryptedNadaType.EcdsaPrivateKey():  # type: ignore
            return ValueType(ecdsa_private_key_share=Empty())
        case EncryptedNadaType.EcdsaPublicKey():  # type: ignore
            return ValueType(ecdsa_public_key=Empty())
        case EncryptedNadaType.StoreId():  # type: ignore
            return ValueType(store_id=Empty())
        case EncryptedNadaType.EddsaMessage():  # type: ignore
            return ValueType(eddsa_message=Empty())
        case EncryptedNadaType.EddsaSignature():  # type: ignore
            return ValueType(eddsa_signature=Empty())
        case EncryptedNadaType.EddsaPrivateKey():  # type: ignore
            return ValueType(eddsa_private_key_share=Empty())
        case EncryptedNadaType.EddsaPublicKey():  # type: ignore
            return ValueType(eddsa_public_key=Empty())
        case _:
            raise Exception(f"unsupported encrypted type: {nada_type}")


def encrypted_nada_type_from_protobuf(nada_type: ValueType) -> EncryptedNadaType:
    match nada_type:
        case ValueType(public_integer=_):
            return EncryptedNadaType.Integer()  # type: ignore
        case ValueType(public_unsigned_integer=_):
            return EncryptedNadaType.UnsignedInteger()  # type: ignore
        case ValueType(public_boolean=_):
            return EncryptedNadaType.Boolean()  # type: ignore
        case ValueType(shamir_share_integer=_):
            return EncryptedNadaType.ShamirShareInteger()  # type: ignore
        case ValueType(shamir_share_unsigned_integer=_):
            return EncryptedNadaType.ShamirShareUnsignedInteger()  # type: ignore
        case ValueType(shamir_share_boolean=_):
            return EncryptedNadaType.ShamirShareBoolean()  # type: ignore
        case ValueType(array=value):
            return EncryptedNadaType.Array(
                inner_type=encrypted_nada_type_from_protobuf(value.inner_type),
                size=value.size,
            )  # type: ignore
        case ValueType(tuple=value):
            return EncryptedNadaType.Tuple(
                left=encrypted_nada_type_from_protobuf(value.left),
                right=encrypted_nada_type_from_protobuf(value.right),
            )  # type: ignore
        case ValueType(ecdsa_message_digest=_):
            return EncryptedNadaType.EcdsaMessageDigest()  # type: ignore
        case ValueType(ecdsa_signature_share=_):
            return EncryptedNadaType.EcdsaSignature()  # type: ignore
        case ValueType(ecdsa_private_key_share=_):
            return EncryptedNadaType.EcdsaPrivateKey()  # type: ignore
        case ValueType(ecdsa_public_key=_):
            return EncryptedNadaType.EcdsaPublicKey()  # type: ignore
        case ValueType(store_id=_):
            return EncryptedNadaType.StoreId()  # type: ignore
        case ValueType(eddsa_message=_):
            return EncryptedNadaType.EddsaMessage()  # type: ignore
        case ValueType(eddsa_signature=_):
            return EncryptedNadaType.EddsaSignature()  # type: ignore
        case ValueType(eddsa_private_key_share=_):
            return EncryptedNadaType.EddsaPrivateKey()  # type: ignore
        case ValueType(eddsa_public_key=_):
            return EncryptedNadaType.EddsaPublicKey()  # type: ignore
        case _:
            raise Exception(f"unsupported type: {nada_type}")
