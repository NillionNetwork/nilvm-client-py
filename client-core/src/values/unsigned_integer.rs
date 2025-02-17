use nillion_client_core::values::{BigUint, Clear, NadaValue};
use pyo3::{exceptions::PyValueError, prelude::*};

/// This is a :py:class:`SecretUnsignedInteger` class used to
/// encode a secret as an unsigned integer.
///
/// Arguments
/// ---------
/// value : int
///     Value of the secret encoded element.
///
/// Returns
/// -------
/// SecretUnsignedInteger
///     Instance of the :py:class:`SecretUnsignedInteger` class.
///
/// Raises
/// -------
/// OverflowError: can't convert negative int to unsigned
///     Raises an error when a negative integer value is used.
///
/// Example
/// -------
///
/// .. code-block:: py3
///
///     from nillion_client import SecretUnsignedInteger
///
///     sec_uinteger_1 = SecretUnsignedInteger(1)
///     sec_uinteger_2 = SecretUnsignedInteger(2)
///
///     print("Are the secret unsigned integers the same? ", sec_uinteger_1 == sec_uinteger_2)
///
/// .. code-block:: text
///
///     >>> Are the secret unsigned integers the same?  False
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct SecretUnsignedInteger {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for SecretUnsignedInteger {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value
            .is_secret_unsigned_integer()
            .then(|| SecretUnsignedInteger { inner: value })
            .ok_or_else(|| PyValueError::new_err("expected secret unsigned integer"))
    }
}

#[pymethods]
impl SecretUnsignedInteger {
    /// Returns a new SecretUnsignedInteger.
    #[new]
    fn new(value: BigUint) -> SecretUnsignedInteger {
        SecretUnsignedInteger { inner: NadaValue::new_secret_unsigned_integer(value) }
    }

    #[getter]
    fn get_value(&self) -> PyResult<BigUint> {
        Ok(self
            .inner
            .as_secret_unsigned_integer()
            .ok_or_else(|| PyValueError::new_err("expected secret unsigned integer"))?
            .clone()
            .into())
    }

    #[setter]
    fn set_value(&mut self, value: BigUint) {
        self.inner = NadaValue::new_secret_unsigned_integer(value);
    }

    fn __repr__(&self) -> String {
        self.inner.to_string()
    }
}

/// This is a :py:class:`UnsignedInteger` class used to
/// encode a public variable value as an unsigned integer.
///
/// Arguments
/// ---------
/// value : int
///     Value of the public encoded element.
///
/// Returns
/// -------
/// UnsignedInteger
///     Instance of the :py:class:`UnsignedInteger` class.
///
/// Raises
/// -------
/// OverflowError: can't convert negative int to unsigned
///     Raises an error when a negative integer value is used.
///
/// Example
/// -------
///
/// .. code-block:: py3
///
///     from nillion_client import UnsignedInteger
///
///     pub_uinteger_1 = UnsignedInteger(1)
///     pub_uinteger_2 = UnsignedInteger(2)
///
///     print("Are the public unsigned integers the same? ", pub_uinteger_1 == pub_uinteger_2)
///
/// .. code-block:: text
///
///     >>> Are the public unsigned integers the same?  False
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct UnsignedInteger {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for UnsignedInteger {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value
            .is_unsigned_integer()
            .then(|| UnsignedInteger { inner: value })
            .ok_or_else(|| PyValueError::new_err("expected unsigned integer"))
    }
}

#[pymethods]
impl UnsignedInteger {
    /// Returns a new UnsignedInteger.
    #[new]
    fn new(value: BigUint) -> UnsignedInteger {
        UnsignedInteger { inner: NadaValue::new_unsigned_integer(value) }
    }

    #[getter]
    fn get_value(&self) -> PyResult<BigUint> {
        Ok(self
            .inner
            .as_unsigned_integer()
            .ok_or_else(|| PyValueError::new_err("expected unsigned integer"))?
            .clone()
            .into())
    }

    #[setter]
    fn set_value(&mut self, value: BigUint) {
        self.inner = NadaValue::new_unsigned_integer(value);
    }

    fn __repr__(&self) -> String {
        self.inner.to_string()
    }
}
