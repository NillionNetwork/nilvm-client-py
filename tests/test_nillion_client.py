import os

import pytest
import nillion_client

import secp256k1
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives import hashes
import uuid
from cryptography.hazmat.primitives.asymmetric.ec import (
    SECP256K1,
    EllipticCurvePublicKey,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from nillion_client.errors import PartyError
from nillion_client.ids import UserId
from nillion_client.network import Network
from nillion_client.permissions import (
    PermissionCommand,
    Permissions,
    PermissionsDelta,
)
from grpclib import GRPCError


def relative_to_current_file(relative_path):
    """
    Convert a relative path to one relative to the current file's directory.
    """
    base_path = os.path.dirname(__file__)
    return os.path.normpath(os.path.join(base_path, relative_path))


@pytest.fixture(scope="session", autouse=True)
def devnet_setup():
    try:
        homedir = os.getenv("HOME")
        config_file_path = f"{homedir}/.config/nillion/nillion-devnet.env"
        grpc_endpoint, nilchain_private_key, nilchain_grpc_endpoint = None, None, None
        with open(config_file_path, "r") as config_file:
            for line in config_file:
                if "NILLION_GRPC_ENDPOINT" in line:
                    grpc_endpoint = line.split("=")[1].strip()
                if "NILLION_NILCHAIN_PRIVATE_KEY_0" in line:
                    nilchain_private_key = line.split("=")[1].strip()
                if "NILLION_NILCHAIN_GRPC" in line:
                    nilchain_grpc_endpoint = line.split("=")[1].strip()

        if not grpc_endpoint or not nilchain_private_key or not nilchain_grpc_endpoint:
            raise RuntimeError("Failed to read Nillion devnet config file")

        yield (
            nilchain_grpc_endpoint,
            grpc_endpoint,
            nilchain_private_key,
        )

    except Exception as e:
        print(f"Failed to start Nillion devnet: {e}")
        raise


async def new_client(devnet_setup) -> nillion_client.VmClient:
    (
        nilchain_grpc_endpoint,
        grpc_endpoint,
        nilchain_private_key,
    ) = devnet_setup

    signing_key = secp256k1.PrivateKey()

    network = nillion_client.Network.devnet(
        nilvm_grpc_endpoint=grpc_endpoint,
        chain_grpc_endpoint=nilchain_grpc_endpoint,
    )

    chain_client = nillion_client.NilChainPayer(
        network,
        wallet_private_key=nillion_client.NilChainPrivateKey(
            bytes.fromhex(nilchain_private_key)
        ),
        gas_limit=10000000,
    )
    vm_client = await nillion_client.VmClient.create(signing_key, network, chain_client)

    return vm_client


@pytest.mark.asyncio
async def test_pool_status(devnet_setup):
    """Test that we can fetch the pool status"""

    client = await new_client(devnet_setup)

    results = await client.pool_status().invoke()

    assert any(
        result.element == nillion_client.PreprocessingElement.COMPARE
        for result in results
    ), "No compare element found in pool"

    client.close()


@pytest.mark.asyncio
async def test_store_retrieve_all_value_types(devnet_setup):
    """Test that we can store and retrieve values"""

    client = await new_client(devnet_setup)

    nesteable_values = {
        "int": nillion_client.Integer(42),
        "sint": nillion_client.SecretInteger(43),
        "uint": nillion_client.UnsignedInteger(43),
        "suint": nillion_client.SecretUnsignedInteger(43),
        "bool": nillion_client.Boolean(True),
        "sbool": nillion_client.SecretBoolean(False),
        "array": nillion_client.Array(
            [nillion_client.Integer(1), nillion_client.Integer(2)]
        ),
        "ecdsa_key": nillion_client.EcdsaPrivateKey(bytearray(os.urandom(32))),
        "ecdsa_message": nillion_client.EcdsaDigestMessage(bytearray(os.urandom(32))),
        "ecdsa_signature": nillion_client.EcdsaSignature(
            (bytearray([1, 2, 3]), bytearray([1, 2, 3]))
        ),
        "ecdsa_public_key": nillion_client.EcdsaPublicKey(bytearray(os.urandom(33))),
        "eddsa_key": nillion_client.EddsaPrivateKey(bytearray([1] * 32)),
        "eddsa_message": nillion_client.EddsaMessage(bytearray(os.urandom(32))),
        "eddsa_signature": nillion_client.EddsaSignature(
            (
                bytearray(
                    [
                        228,
                        118,
                        63,
                        53,
                        138,
                        161,
                        20,
                        164,
                        93,
                        86,
                        233,
                        11,
                        211,
                        204,
                        186,
                        63,
                        255,
                        174,
                        220,
                        173,
                        222,
                        58,
                        64,
                        79,
                        108,
                        173,
                        130,
                        1,
                        134,
                        44,
                        244,
                        104,
                    ]
                ),
                bytearray(
                    [
                        137,
                        73,
                        233,
                        168,
                        34,
                        64,
                        148,
                        185,
                        177,
                        91,
                        184,
                        21,
                        246,
                        82,
                        65,
                        207,
                        83,
                        158,
                        44,
                        181,
                        199,
                        94,
                        83,
                        178,
                        88,
                        238,
                        210,
                        220,
                        10,
                        49,
                        154,
                        1,
                    ]
                ),
            )
        ),
        "eddsa_public_key": nillion_client.EddsaPublicKey(
            bytearray(
                [
                    186,
                    236,
                    247,
                    198,
                    7,
                    225,
                    204,
                    147,
                    116,
                    47,
                    207,
                    45,
                    149,
                    49,
                    212,
                    168,
                    136,
                    145,
                    98,
                    150,
                    152,
                    122,
                    50,
                    91,
                    141,
                    227,
                    182,
                    233,
                    8,
                    245,
                    72,
                    38,
                ]
            )
        ),
        "store_id": nillion_client.StoreId(bytearray(os.urandom(16))),
    }
    # nest all the types above under an array
    values = {
        f"array_{name}": nillion_client.Array([value])
        for (name, value) in nesteable_values.items()
    }
    # combine them all and include a secret blob (which can't be nested in an array)
    values.update(nesteable_values)
    values["sblob"] = nillion_client.SecretBlob(bytearray("1234", "utf-8"))  # type: ignore

    values_id = await client.store_values(values, 1).invoke()
    returned_values = await client.retrieve_values(values_id).invoke()

    assert returned_values == values

    client.close()


@pytest.mark.asyncio
async def test_update_values(devnet_setup):
    """Test that we can store and retrieve values"""

    client = await new_client(devnet_setup)

    values = {
        "foo": nillion_client.Integer(42),
    }

    values_id = await client.store_values(values, 1).invoke()
    updated_values = {
        "bar": nillion_client.SecretBoolean(True),
    }

    identifier = await client.store_values(
        updated_values, ttl_days=1, update_identifier=values_id
    ).invoke()
    assert identifier == values_id

    returned_values = await client.retrieve_values(values_id).invoke()

    assert returned_values == updated_values

    client.close()


@pytest.mark.asyncio
async def test_delete_values(devnet_setup):
    """Test that we can store and delete values"""

    client = await new_client(devnet_setup)

    # Store a value, then delete it
    values = {
        "value1": nillion_client.Integer(42),
        "value2": nillion_client.SecretInteger(43),
    }

    values_id = await client.store_values(values, 1).invoke()

    await client.delete_values(values_id).invoke()

    # Check that retrieving the value fails
    with pytest.raises(PartyError) as e:
        await client.retrieve_values(values_id).invoke()
    assert "not found" in str(e.value)

    # Check that deleting the value again fails
    with pytest.raises(PartyError) as e:
        await client.delete_values(values_id).invoke()
    assert "not found" in str(e.value)

    client.close()


@pytest.mark.asyncio
async def test_store_values_retrieve_overwrite_permissions(devnet_setup):
    """Test that we can store values and retrieve their permissions"""

    client = await new_client(devnet_setup)

    signing_key = secp256k1.PrivateKey()
    other_user_id = UserId.from_public_key(signing_key.pubkey)  # type: ignore

    permissions = nillion_client.Permissions.defaults_for_user(client.user_id)
    permissions.allow_retrieve(other_user_id)

    # Check that we can retrieve permissions after storing values
    values = {
        "value1": nillion_client.Integer(42),
        "value2": nillion_client.SecretInteger(43),
    }

    values_id = await client.store_values(values, 1, permissions=permissions).invoke()

    returned_permissions = await client.retrieve_permissions(values_id).invoke()

    assert returned_permissions == permissions

    # Check we can update permissions
    permissions.allow_compute(other_user_id, nillion_client.ProgramId("dummyProgramId"))

    await client.overwrite_permissions(values_id, permissions).invoke()

    returned_permissions = await client.retrieve_permissions(values_id).invoke()

    assert returned_permissions == permissions

    client.close()


@pytest.mark.asyncio
async def test_update_permissions(devnet_setup):
    """Test that we can store values and retrieve their permissions"""

    client = await new_client(devnet_setup)
    signing_key = secp256k1.PrivateKey()
    other_user_id = UserId.from_public_key(signing_key.pubkey)  # type: ignore

    values = {
        "value1": nillion_client.Integer(42),
        "value2": nillion_client.SecretInteger(43),
    }
    values_id = await client.store_values(values, ttl_days=1).invoke()

    delta = PermissionsDelta(retrieve=PermissionCommand(grant=set([other_user_id])))
    await client.update_permissions(values_id, delta).invoke()

    permissions = await client.retrieve_permissions(values_id).invoke()
    assert other_user_id in permissions.retrieve

    client.close()


@pytest.mark.asyncio
async def test_basic_compute(devnet_setup):
    """Test that we can store and compute a program"""

    client = await new_client(devnet_setup)

    test_program = relative_to_current_file("resources/programs/main.nada.bin")
    program = open(test_program, "rb").read()

    program_id = await client.store_program("main", program).invoke()

    values = {
        "my_int1": nillion_client.SecretInteger(40),
        "my_int2": nillion_client.SecretInteger(2),
    }

    compute_id = await client.compute(
        program_id,
        input_bindings=[
            nillion_client.InputPartyBinding(party_name="Party1", user=client.user_id)
        ],
        output_bindings=[
            nillion_client.OutputPartyBinding(
                party_name="Party1", users=[client.user_id]
            )
        ],
        values=values,
    ).invoke()

    results = await client.retrieve_compute_results(compute_id).invoke()

    assert results == {"sum": nillion_client.SecretInteger(42)}

    client.close()


@pytest.mark.asyncio
async def test_ecdsa_compute(devnet_setup):
    """Test that we can generate an ecdsa private key, store it, and use it to sign a message"""

    client = await new_client(devnet_setup)

    ###########################################
    #                                         #
    #          ECDSA CONFIG NAMES             #
    #                                         #
    ###########################################

    # program id
    tecdsa_sign_program_id = "builtin/tecdsa_sign"
    tecdsa_dks_program_id = "builtin/tecdsa_dkg"
    # input store name
    tecdsa_digest_name = "tecdsa_digest_message"
    # output store name
    tecdsa_signature_name = "tecdsa_signature"
    tecdsa_public_key_name = "tecdsa_public_key"
    tecdsa_store_id_name = "tecdsa_store_id"
    # party names
    tecdsa_key_party = "tecdsa_key_party"
    tecdsa_digest_party = "tecdsa_digest_message_party"
    tecdsa_output_party = "tecdsa_output_party"
    tecdsa_private_key_store_id_party = "tecdsa_private_key_store_id_party"
    tecdsa_public_key_party = "tecdsa_public_key_party"

    ###########################################
    #                                         #
    #              ECDSA DIGEST               #
    #                                         #
    ###########################################

    ##### GENERATE MESSAGE AND DIGEST

    # The message to sign
    message = b"A deep message with a deep number: 42."
    # Hashing the message
    digest = hashes.Hash(hashes.SHA256())
    digest.update(message)
    hashed_message = digest.finalize()

    tecdsa_digest_value = bytearray(hashed_message)
    # ecdsa digest to be used for signing
    my_ecdsa_digest = {
        tecdsa_digest_name: nillion_client.EcdsaDigestMessage(tecdsa_digest_value),
    }

    ###########################################
    #                                         #
    #             ECDSA DKG                   #
    #                                         #
    ###########################################

    ##### ECDSA DKG
    print("-----ECDSA DKG")

    # Bind the parties in the computation to the client to set input and output parties
    input_bindings = []
    output_bindings = [
        nillion_client.OutputPartyBinding(
            tecdsa_private_key_store_id_party, [client.user_id]
        ),
        nillion_client.OutputPartyBinding(tecdsa_public_key_party, [client.user_id]),
    ]

    # Create a computation time secret to use
    compute_time_values = {}

    # Compute, passing in the compute time values as well as the previously uploaded value.
    print(f"Invoking DKG using program {tecdsa_dks_program_id}")
    compute_id = await client.compute(
        tecdsa_dks_program_id,
        input_bindings,
        output_bindings,
        values=compute_time_values,
        value_ids=[],
    ).invoke()

    # 6. Return the computation result
    result = await client.retrieve_compute_results(compute_id).invoke()
    # Get the store ID and public key from results
    private_key_store_id = result[tecdsa_store_id_name].value
    tecdsa_public_key_value = result[tecdsa_public_key_name].value
    # Ensure private_key_store_id is a bytearray and convert to bytes
    if isinstance(private_key_store_id, bytearray):  # this is required to pass pyright
        private_key_store_id_bytes = bytes(private_key_store_id)
    else:
        raise TypeError("private_key_store_id must be a bytearray")
    ecdsa_private_key_store_id = uuid.UUID(bytes=private_key_store_id_bytes)
    # Ensure tecdsa_public_key_value is a bytearray and convert to bytes
    if isinstance(
        tecdsa_public_key_value, bytearray
    ):  # this is required to pass pyright
        tecdsa_public_key = bytes(tecdsa_public_key_value)
    else:
        raise TypeError("tecdsa_public_key must be a bytearray")

    ###########################################
    #                                         #
    #             ECDSA SIGNING               #
    #                                         #
    ###########################################

    ##### ECDSA SIGNING
    print("-----ECDSA SIGNING")

    # Bind the parties in the computation to the client to set input and output parties
    input_bindings = [
        nillion_client.InputPartyBinding(tecdsa_key_party, client.user_id),
        nillion_client.InputPartyBinding(tecdsa_digest_party, client.user_id),
    ]
    output_bindings = [
        nillion_client.OutputPartyBinding(tecdsa_output_party, [client.user_id])
    ]

    # Create a computation time secret to use
    compute_time_values = my_ecdsa_digest

    # Compute, passing in the compute time values as well as the previously uploaded value.
    compute_id = await client.compute(
        tecdsa_sign_program_id,
        input_bindings,
        output_bindings,
        values=my_ecdsa_digest,
        value_ids=[ecdsa_private_key_store_id],
    ).invoke()

    # 6. Return the computation result
    result = await client.retrieve_compute_results(compute_id).invoke()
    signature_value = result[tecdsa_signature_name]

    # Ensure the signature is of the correct type
    if isinstance(signature_value, nillion_client.EcdsaSignature):
        signature = signature_value
    else:
        raise TypeError("Cannot convert to EcdsaSignature.")

    ###########################################
    #                                         #
    #           ECDSA VERIFICATION            #
    #                                         #
    ###########################################

    ##### ECDSA VERIFICATION
    print("-----ECDSA VERIFICATION")

    # Transform the result signature to bytes for verification
    (r, s) = signature.value
    r_int = int.from_bytes(bytes(r), byteorder="big")
    s_int = int.from_bytes(bytes(s), byteorder="big")
    signature_bytes = utils.encode_dss_signature(r_int, s_int)

    # For SECP256K1, the first byte indicates if it's compressed (0x02 or 0x03)
    # The remaining 32 bytes are the x-coordinate
    if tecdsa_public_key[0] not in (0x02, 0x03):
        raise ValueError("Invalid public key format")

    # Create the public key object from the raw bytes
    ecdsa_public_key = EllipticCurvePublicKey.from_encoded_point(
        SECP256K1(), tecdsa_public_key
    )

    # Verify the signature
    try:
        ecdsa_public_key.verify(signature_bytes, message, ec.ECDSA(hashes.SHA256()))
    except Exception as e:
        raise ValueError(f"Signature is invalid: {str(e)}")

    client.close()


@pytest.mark.asyncio
async def test_eddsa_compute(devnet_setup):
    """Test that we can generate an eddsa private key, store it, and use it to sign a message"""

    client = await new_client(devnet_setup)

    ###########################################
    #                                         #
    #          EDDSA CONFIG NAMES             #
    #                                         #
    ###########################################

    # program id
    teddsa_sign_program_id = "builtin/teddsa_sign"
    teddsa_dks_program_id = "builtin/teddsa_dkg"
    # input store name
    teddsa_message_name = "teddsa_message"
    # output store name
    teddsa_signature_name = "teddsa_signature"
    teddsa_public_key_name = "teddsa_public_key"
    teddsa_store_id_name = "teddsa_store_id"
    # party names
    teddsa_key_party = "teddsa_key_party"
    teddsa_message_party = "teddsa_message_party"
    teddsa_output_party = "teddsa_output_party"
    teddsa_private_key_store_id_party = "teddsa_private_key_store_id_party"
    teddsa_public_key_party = "teddsa_public_key_party"

    ###########################################
    #                                         #
    #              EDDSA MESSAGE              #
    #                                         #
    ###########################################

    ##### GENERATE MESSAGE

    # The message to sign
    message = b"A deep message with a deep number: 42."

    teddsa_value = bytearray(message)
    # eddsa message to be used for signing
    my_eddsa_message = {
        teddsa_message_name: nillion_client.EddsaMessage(teddsa_value),
    }

    ###########################################
    #                                         #
    #             EDDSA DKG                   #
    #                                         #
    ###########################################

    ##### EDDSA DKG
    print("\n-----EDDSA DKG")

    # Bind the parties in the computation to the client to set input and output parties
    input_bindings = []
    output_bindings = [
        nillion_client.OutputPartyBinding(
            teddsa_private_key_store_id_party, [client.user_id]
        ),
        nillion_client.OutputPartyBinding(teddsa_public_key_party, [client.user_id]),
    ]

    # Create a computation time secret to use
    compute_time_values = {}

    # Compute, passing in the compute time values as well as the previously uploaded value.
    print(f"Invoking DKG using program {teddsa_dks_program_id}")
    compute_id = await client.compute(
        teddsa_dks_program_id,
        input_bindings,
        output_bindings,
        values=compute_time_values,
        value_ids=[],
    ).invoke()

    # 6. Return the computation result
    result = await client.retrieve_compute_results(compute_id).invoke()
    # Get the store ID and public key from results
    private_key_store_id = result[teddsa_store_id_name].value
    teddsa_public_key_value = result[teddsa_public_key_name].value
    # Ensure private_key_store_id is a bytearray and convert to bytes
    if isinstance(private_key_store_id, bytearray):  # this is required to pass pyright
        private_key_store_id_bytes = bytes(private_key_store_id)
    else:
        raise TypeError("private_key_store_id must be a bytearray")
    ecdsa_private_key_store_id = uuid.UUID(bytes=private_key_store_id_bytes)
    # Ensure tecdsa_public_key_value is a bytearray and convert to bytes
    if isinstance(
        teddsa_public_key_value, bytearray
    ):  # this is required to pass pyright
        teddsa_public_key = bytes(teddsa_public_key_value)
    else:
        raise TypeError("teddsa_public_key must be a bytearray")

    ###########################################
    #                                         #
    #             ECDSA SIGNING               #
    #                                         #
    ###########################################

    ##### EDDSA SIGNING
    print("-----EDDSA SIGNING")

    # Bind the parties in the computation to the client to set input and output parties
    input_bindings = [
        nillion_client.InputPartyBinding(teddsa_key_party, client.user_id),
        nillion_client.InputPartyBinding(teddsa_message_party, client.user_id),
    ]
    output_bindings = [
        nillion_client.OutputPartyBinding(teddsa_output_party, [client.user_id])
    ]

    # Create a computation time secret to use
    compute_time_values = my_eddsa_message

    # Compute, passing in the compute time values as well as the previously uploaded value.
    compute_id = await client.compute(
        teddsa_sign_program_id,
        input_bindings,
        output_bindings,
        values=my_eddsa_message,
        value_ids=[ecdsa_private_key_store_id],
    ).invoke()
    # 6. Return the computation result
    result = await client.retrieve_compute_results(compute_id).invoke()
    signature_value = result[teddsa_signature_name]
    public_key_value = result[teddsa_public_key_name]
    message_value = result[teddsa_message_name]

    # Ensure the signature is of the correct type
    if isinstance(signature_value, nillion_client.EddsaSignature):
        signature_output = signature_value
    else:
        raise TypeError("Cannot convert to EddsaSignature.")

    # Ensure the public key is of the correct type
    if isinstance(public_key_value, nillion_client.EddsaPublicKey):
        public_key_output = public_key_value
    else:
        raise TypeError("Cannot convert to EddsaPublicKey.")

    # Ensure the message is of the correct type
    if isinstance(message_value, nillion_client.EddsaMessage):
        message_output = message_value
    else:
        raise TypeError("Cannot convert to EddsaMessage.")

    ###########################################
    #                                         #
    #           ECDSA VERIFICATION            #
    #                                         #
    ###########################################

    ##### OUTPUT VERIFICATION
    # Verify the public key output from dkg is the same as the one given by signing
    assert teddsa_public_key == public_key_output.value

    # Verify the message output from signing is the same as input for signing
    assert message_output.value == message

    ##### EDDSA VERIFICATION
    print("-----EDDSA VERIFICATION")

    # Transform the result signature to bytes for verification
    (r, z) = signature_output.value
    # Convert r and z to bytes - note that EdDSA uses concatenated format (R || Z)
    r_bytes = bytes(r)
    z_bytes = bytes(z)
    # Ed25519 signatures are simply the concatenation of R and Z components
    signature_bytes = r_bytes + z_bytes

    # Create the public key object from the raw bytes
    try:
        ed25519_public_key = Ed25519PublicKey.from_public_bytes(teddsa_public_key)
    except Exception as e:
        raise ValueError(f"Invalid Ed25519 public key format: {str(e)}")

    # Verify the signature
    try:
        ed25519_public_key.verify(signature_bytes, message)
    except Exception as e:
        raise ValueError(f"Signature is invalid: {str(e)}")

    client.close()


@pytest.mark.asyncio
async def test_complex_compute(devnet_setup):
    client_party1 = await new_client(devnet_setup)
    client_party2 = await new_client(devnet_setup)
    client_output = await new_client(devnet_setup)

    test_program = relative_to_current_file("resources/programs/main_complex.nada.bin")
    program = open(test_program, "rb").read()

    program_id = await client_party1.store_program("main", program).invoke()

    values_p2 = {
        "my_int2": nillion_client.SecretInteger(2),
    }
    permissions = Permissions(client_party2.user_id)
    permissions.allow_compute(client_party1.user_id, program_id)
    values_p2_id = await client_party2.store_values(
        values_p2, ttl_days=1, permissions=permissions
    ).invoke()

    values_p1 = {
        "my_int1": nillion_client.SecretInteger(40),
    }

    compute_id = await client_party1.compute(
        program_id,
        input_bindings=[
            nillion_client.InputPartyBinding(
                party_name="Party1", user=client_party1.user_id
            ),
            nillion_client.InputPartyBinding(
                party_name="Party2", user=client_party2.user_id
            ),
        ],
        output_bindings=[
            nillion_client.OutputPartyBinding(
                party_name="Party3", users=[client_output.user_id]
            )
        ],
        values=values_p1,
        value_ids=[values_p2_id],
    ).invoke()

    results = await client_output.retrieve_compute_results(compute_id).invoke()

    assert results == {"sum": nillion_client.SecretInteger(42)}

    client_party1.close()
    client_party2.close()
    client_output.close()


def test_network_config():
    # simply load it to ensure it doesn't throw
    Network.from_config("devnet")


@pytest.mark.asyncio
async def test_store_program(devnet_setup):
    """Test that we can store and compute a program"""

    client = await new_client(devnet_setup)

    test_program = relative_to_current_file("resources/programs/main.nada.bin")
    program = open(test_program, "rb").read()

    await client.store_program(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890+.:_-",
        program,
    ).invoke()
    client.close()


@pytest.mark.asyncio
async def test_invalid_program_name(devnet_setup):
    client = await new_client(devnet_setup)
    test_program = relative_to_current_file("resources/programs/main.nada.bin")
    program = open(test_program, "rb").read()
    with pytest.raises(Exception):
        await client.store_program("main/nope", program).invoke()
    client.close()


@pytest.mark.asyncio
async def test_use_balance(devnet_setup):
    client = await new_client(devnet_setup)
    balance = await client.balance()
    assert balance.balance == 0

    # add some funds
    amount = 1000000
    await client.add_funds(amount)

    # ensure our balance went up
    balance = await client.balance()
    assert balance.balance == amount / 10000

    # run an operation and ensure it went down
    await client.pool_status().invoke()
    balance = await client.balance()
    assert balance.balance < amount / 10000

    client.close()
