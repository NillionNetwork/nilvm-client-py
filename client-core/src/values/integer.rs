use nillion_client_core::values::{BigInt, Clear, NadaValue};
use pyo3::{exceptions::PyValueError, prelude::*};

/// This is a :py:class:`SecretInteger` class used to encode a secret as an integer.
///
/// Arguments
/// ---------
/// value : int
///     Value of the secret encoded element.
///
/// Returns
/// -------
/// SecretInteger
///     Instance of the :py:class:`SecretInteger` class.
///
///
/// Example
/// -------
///
/// .. code-block:: py3
///
///     from nillion_client import SecretInteger
///
///     sec_integer_1 = SecretInteger(1)
///     sec_integer_2 = SecretInteger(2)
///
///     print("Are the secret integers the same? ", sec_integer_1 == sec_integer_2)
///
/// .. code-block:: text
///
///     >>> Are the secret integers the same?  False
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct SecretInteger {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for SecretInteger {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> PyResult<Self> {
        value
            .is_secret_integer()
            .then(|| SecretInteger { inner: value })
            .ok_or_else(|| PyValueError::new_err("expected secret integer"))
    }
}

#[pymethods]
impl SecretInteger {
    /// Returns a new SecretInteger.
    #[new]
    pub(crate) fn new(value: BigInt) -> SecretInteger {
        SecretInteger { inner: NadaValue::new_secret_integer(value) }
    }

    #[getter]
    fn get_value(&self) -> PyResult<BigInt> {
        Ok(self
            .inner
            .as_secret_integer()
            .ok_or_else(|| PyValueError::new_err("expected secret integer"))?
            .clone()
            .into())
    }

    #[setter]
    fn set_value(&mut self, value: BigInt) {
        self.inner = NadaValue::new_secret_integer(value);
    }

    fn __repr__(&self) -> String {
        self.inner.to_string()
    }
}

/// This is a :py:class:`Integer` class used to
/// encode a public variable value as an integer.
///
/// Arguments
/// ---------
/// value : int
///     Value of the public encoded element.
///
/// Returns
/// -------
/// Integer
///     Instance of the :py:class:`Integer` class.
///
///
/// Example
/// -------
///
/// .. code-block:: py3
///
///     from nillion_client import Integer
///
///     pub_integer_1 = Integer(1)
///     pub_integer_2 = Integer(2)
///
///     print("Are the public integers the same? ", pub_integer_1 == pub_integer_2)
///
/// .. code-block:: text
///
///     >>> Are the public integers the same?  False
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct Integer {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for Integer {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> PyResult<Self> {
        value.is_integer().then(|| Integer { inner: value }).ok_or_else(|| PyValueError::new_err("expected integer"))
    }
}

#[pymethods]
impl Integer {
    /// Returns a new Integer.
    #[new]
    fn new(value: BigInt) -> Integer {
        Integer { inner: NadaValue::new_integer(value) }
    }

    #[getter]
    fn get_value(&self) -> PyResult<BigInt> {
        Ok(self.inner.as_integer().ok_or_else(|| PyValueError::new_err("expected integer"))?.clone().into())
    }

    #[setter]
    fn set_value(&mut self, value: BigInt) {
        self.inner = NadaValue::new_integer(value);
    }

    fn __repr__(&self) -> String {
        self.inner.to_string()
    }
}
