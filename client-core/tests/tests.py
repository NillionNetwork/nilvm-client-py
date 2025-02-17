from nillion_client_core import (
    Array,
    Boolean,
    Integer,
    PartyId,
    SecretBlob,
    SecretBoolean,
    SecretInteger,
    SecretMasker,
    SecretUnsignedInteger,
    UnsignedInteger,
    EcdsaPrivateKey,
    EcdsaDigestMessage,
    EcdsaSignature,
)


def test_asdf():
    values = {
        "integer": Integer(-1),
        "secretInteger": SecretInteger(-1),
        "unsignedInteger": UnsignedInteger(1),
        "secretUnsignedInteger": SecretUnsignedInteger(1),
        "boolean": Boolean(True),
        "secretBoolean": SecretBoolean(False),
        "secretBlob": SecretBlob(bytearray([1, 2, 3])),
        "EcdsaPrivateKey": EcdsaPrivateKey(bytearray([i for i in range(32)])),
        "EcdsaDigestMessage": EcdsaDigestMessage(bytearray([i for i in range(32)])),
        "EcdsaSignature": EcdsaSignature((bytearray([1, 2, 3]), bytearray([1, 2, 3]))),
        "array": Array([Integer(-1), Integer(-1), Integer(-1)]),
    }

    party1 = PartyId.from_bytes(bytes("1", "utf-8"))
    party2 = PartyId.from_bytes(bytes("2", "utf-8"))
    party3 = PartyId.from_bytes(bytes("3", "utf-8"))

    secret_masker = SecretMasker.new_64_bit_safe_prime(1, [party1, party2, party3])
    masked_values = secret_masker.mask(values)

    masked_values_party1 = masked_values[party1]
    masked_values_party2 = masked_values[party2]
    masked_values_party3 = masked_values[party3]

    party_jar = secret_masker.build_jar()
    party_jar.add_element(party1, masked_values_party1)
    party_jar.add_element(party2, masked_values_party2)
    party_jar.add_element(party3, masked_values_party3)

    unmasked = secret_masker.unmask(party_jar)

    assert unmasked["integer"].value == values["integer"].value
    assert unmasked["secretInteger"].value == values["secretInteger"].value
    assert unmasked["unsignedInteger"].value == values["unsignedInteger"].value
    assert (
        unmasked["secretUnsignedInteger"].value == values["secretUnsignedInteger"].value
    )
    assert unmasked["boolean"].value == values["boolean"].value
    assert unmasked["secretBoolean"].value == values["secretBoolean"].value
    assert unmasked["secretBlob"].value == values["secretBlob"].value
    assert unmasked["EcdsaPrivateKey"].value == values["EcdsaPrivateKey"].value
    assert unmasked["EcdsaDigestMessage"].value == values["EcdsaDigestMessage"].value
    assert unmasked["EcdsaSignature"].value == values["EcdsaSignature"].value
    assert unmasked["EcdsaSignature"].value == values["EcdsaSignature"].value
    assert unmasked["array"].value == values["array"].value

    assert repr(unmasked["integer"]) == "Integer(-1)"
    assert repr(unmasked["secretInteger"]) == "SecretInteger(-1)"
    assert repr(unmasked["unsignedInteger"]) == "UnsignedInteger(1)"
    assert repr(unmasked["secretUnsignedInteger"]) == "SecretUnsignedInteger(1)"
    assert repr(unmasked["boolean"]) == "Boolean(true)"
    assert repr(unmasked["secretBoolean"]) == "SecretBoolean(false)"
    assert repr(unmasked["secretBlob"]) == "Blob(1, 2, 3)"
    assert repr(unmasked["EcdsaPrivateKey"]) == "EcdsaPrivateKey(NonZero(SecretScalar))"
    assert repr(unmasked["array"]) == "Array(Integer(-1), Integer(-1), Integer(-1))"
