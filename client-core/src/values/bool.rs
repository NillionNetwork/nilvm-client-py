use nillion_client_core::values::{Clear, NadaValue};
use pyo3::{exceptions::PyValueError, prelude::*};

/// This is a :py:class:`SecretBoolean` class used to
/// encode a secret as a boolean.
///
/// Arguments
/// ---------
/// value : bool
///     Value of the secret encoded element.
///
/// Returns
/// -------
/// SecretBoolean
///     Instance of the :py:class:`SecretBoolean` class.
///
///
/// Example
/// -------
///
/// .. code-block:: py3
///
///     from nillion_client import SecretBoolean
///
///     sec_bool_1 = SecretBoolean(True)
///     sec_bool_2 = SecretBoolean(False)
///
///     print("Are the secret booleans the same? ", sec_bool_1 == sec_bool_2)
///
/// .. code-block:: text
///
///     >>> Are the secret booleans the same?  False
///
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct SecretBoolean {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for SecretBoolean {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value
            .is_secret_boolean()
            .then(|| SecretBoolean { inner: value })
            .ok_or_else(|| PyValueError::new_err("expected secret boolean"))
    }
}

#[pymethods]
impl SecretBoolean {
    /// Returns a new SecretBoolean.
    #[new]
    fn new(value: bool) -> SecretBoolean {
        SecretBoolean { inner: NadaValue::new_secret_boolean(value) }
    }

    #[getter]
    fn get_value(&self) -> PyResult<bool> {
        self.inner.as_secret_boolean().cloned().ok_or_else(|| PyValueError::new_err("expected secret boolean"))
    }

    #[setter]
    fn set_value(&mut self, value: bool) {
        self.inner = NadaValue::new_secret_boolean(value);
    }

    fn __repr__(&self) -> String {
        self.inner.to_string()
    }
}

/// This is a :py:class:`Boolean` class used to encode a public variable value as an boolean.
///
/// Arguments
/// ---------
/// value : int
///     Value of the public encoded element.
///
/// Returns
/// -------
/// Boolean
///     Instance of the :py:class:`Boolean` class.
///
///
/// Example
/// -------
///
/// .. code-block:: py3
///
///     from nillion_client import Boolean
///
///     pub_boolean_1 = Boolean(True)
///     pub_boolean_2 = Boolean(False)
///
///     print("Are the public booleans the same? ", pub_boolean_1 == pub_boolean_2)
///
/// .. code-block:: text
///
///     >>> Are the public booleans the same?  False
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct Boolean {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for Boolean {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value.is_boolean().then(|| Boolean { inner: value }).ok_or_else(|| PyValueError::new_err("expected boolean"))
    }
}

#[pymethods]
impl Boolean {
    /// Returns a new Boolean.
    #[new]
    fn new(value: bool) -> Boolean {
        Boolean { inner: NadaValue::new_boolean(value) }
    }

    #[getter]
    fn get_value(&self) -> PyResult<bool> {
        self.inner.as_boolean().cloned().ok_or_else(|| PyValueError::new_err("expected boolean"))
    }

    #[setter]
    fn set_value(&mut self, value: bool) {
        self.inner = NadaValue::new_boolean(value);
    }

    fn __repr__(&self) -> String {
        self.inner.to_string()
    }
}
