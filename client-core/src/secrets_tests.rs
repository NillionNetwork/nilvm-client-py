use pyo3::Python;

#[test]
fn test_secret_integer() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            "from nillion_client_core import *; integer = SecretInteger(22); assert integer.value == 22",
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_secret_unsigned_integer() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            "from nillion_client_core import *; integer = SecretUnsignedInteger(22); assert integer.value == 22",
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_secret_boolean() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            "from nillion_client_core import *; boolean = SecretBoolean(True); assert boolean.value",
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_secret_array_of_integers() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            "from nillion_client_core import *; array = Array([SecretInteger(22),SecretInteger(44)]); assert len(array) == 2",
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_secret_array_int_value_eq() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            "from nillion_client_core import *; array = Array([SecretInteger(22),SecretInteger(44)]); int_1 = SecretInteger(22); int_2 = SecretInteger(44); assert array.value == [int_1, int_2] ",
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_secret_blob() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            "from nillion_client_core import *; blob = SecretBlob(bytearray([1, 2, 3])); assert blob.value == bytearray([1, 2, 3])",
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_ecdsa_private_key() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            "from nillion_client_core import *; import os; ecdsa_pk_ba = bytearray(os.urandom(32)); ecdsa_pk = EcdsaPrivateKey(ecdsa_pk_ba); assert ecdsa_pk.value == ecdsa_pk_ba",
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_bad_ecdsa_private_key() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            r#"
from nillion_client_core import *
import os

# Check ecdsa private key creation fails with bytearray size different from 32
try:
    ecdsa_pk_ba = bytearray(os.urandom(33))
    ecdsa_pk = EcdsaPrivateKey(ecdsa_pk_ba)
    raise AssertionError("Expected ValueError not raised for invalid key size")
except ValueError as e:
    assert "Private key format error" in str(e), "Unexpected error message"

# Check ecdsa private key creation fails with 0 key
try:
    zero_key_ba = bytearray([0] * 32)
    ecdsa_pk = EcdsaPrivateKey(zero_key_ba)
    raise AssertionError("Expected ValueError not raised for zero key")
except ValueError as e:
    assert "Private key format error" in str(e), "Unexpected error message"
"#,
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_ecdsa_digest_message() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            r#"
from nillion_client_core import *
import os

ecdsa_digest_msg_ba = bytearray(os.urandom(32))
ecdsa_digest_msg = EcdsaDigestMessage(ecdsa_digest_msg_ba)
"#,
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_bad_ecdsa_digest_message() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            r#"
from nillion_client_core import *
import os

# Check ecdsa private key creation fails with bytearray size different from 32
try:
    ecdsa_pk_ba = bytearray(os.urandom(33))
    ecdsa_pk = EcdsaDigestMessage(ecdsa_pk_ba)
    raise AssertionError("Expected ValueError not raised for invalid message digest size")
except ValueError as e:
    assert "Message digest must be exactly 32 bytes long" in str(e), "Unexpected error message"
"#,
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_ecdsa_signature() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            r#"
from nillion_client_core import *
import os

r = bytearray(os.urandom(10))
s = bytearray(os.urandom(10))
ecdsa_digest_msg = EcdsaSignature((r, s))
print("Ecdsa signature is: ", ecdsa_digest_msg.value)
"#,
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_bad_ecdsa_signature() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            r#"
from nillion_client_core import *
import os

r = bytearray(os.urandom(1234))
s = bytearray(os.urandom(32))

# Check ecdsa signature creation fails with bytearray size very big
try:
    ecdsa_digest_msg = EcdsaSignature((r, s))
    raise AssertionError("Expected ValueError not raised for invalid signature")
except ValueError as e:
    assert "Ecdsa signature parameter r format error as the encoded integer is larger than group order." in str(e), "Unexpected error message"

"#,
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_ecdsa_public_key() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            r#"
from nillion_client_core import *
import os

key_bytes = bytearray(os.urandom(33))
ecdsa_pk = EcdsaPublicKey(key_bytes)
assert ecdsa_pk.value == key_bytes  # Compare against the same bytes
"#,
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_store_id() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            r#"
from nillion_client_core import *
import os

store_id_bytes = bytearray(os.urandom(16))
store_id = StoreId(store_id_bytes)
assert store_id.value == store_id_bytes  # Compare against the same bytes
"#,
            None,
            None,
        )
        .unwrap();
    })
}
