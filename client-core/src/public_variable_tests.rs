use pyo3::Python;

#[test]
fn test_public_integer() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            "from nillion_client_core import *; integer = Integer(22); assert integer.value == 22",
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
            "from nillion_client_core import *; integer = UnsignedInteger(22); assert integer.value == 22",
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_public_boolean() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            "from nillion_client_core import *; boolean = Boolean(True); assert boolean.value",
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_public_array_of_integers() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            "from nillion_client_core import *; array = Array([Integer(22),Integer(44)]); assert len(array) == 2",
            None,
            None,
        )
        .unwrap();
    })
}

#[test]
fn test_public_array_int_value_eq() {
    Python::with_gil(|py| {
        Python::run_bound(
            py,
            "from nillion_client_core import *; array = Array([Integer(22),Integer(44)]); int_1 = Integer(22); int_2 = Integer(44); assert array.value == [int_1, int_2] ",
            None,
            None,
        )
        .unwrap();
    })
}
