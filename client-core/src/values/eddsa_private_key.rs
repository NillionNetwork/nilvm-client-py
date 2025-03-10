use nillion_client_core::{
    privatekey,
    values::{Clear, NadaValue},
};
use pyo3::{exceptions::PyValueError, prelude::*, types::PyByteArray};

/// This is a :py:class:`EddsaPrivateKey` class used to
/// encode a secret bytearray as an eddsa private key.
///
/// Arguments
/// ---------
/// value : bytearray
///     Value of the private eddsa key as a `bytearray`.
///
/// Returns
/// -------
/// EddsaPrivateKey
///     Instance of the :py:class:`EddsaPrivateKey` class.
///
/// Raises
/// -------
/// VTypeError: argument 'value'
///     Raises an error when a non-bytearray object is provided.
///
/// Example
/// -------
///
/// .. code-block:: py3
///
///     from nillion_client import EddsaPrivateKey
///     import os
///     
///     pk1_bytes = bytearray(os.urandom(32))
///     pk1 = EddsaPrivateKey(pk1_bytes)
///     pk2_bytes = bytearray(os.urandom(32))
///     pk2 = EddsaPrivateKey(pk2_bytes)
///
///     print("Are these eddsa private keys the same?", pk1 == pk2)
///
/// .. code-block:: text
///
///     >>> Are these eddsa private keys the same?  False
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct EddsaPrivateKey {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for EddsaPrivateKey {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value
            .is_eddsa_private_key()
            .then(|| EddsaPrivateKey { inner: value })
            .ok_or_else(|| PyValueError::new_err("expected eddsa private key"))
    }
}

#[pymethods]
impl EddsaPrivateKey {
    /// Returns a new EddsaPrivateKey. The byte array should be in big-endian format.
    #[new]
    fn new(value: &Bound<'_, PyByteArray>) -> PyResult<EddsaPrivateKey> {
        let eddsa_private_key = privatekey::ThresholdPrivateKey::from_le_bytes(&value.to_vec()).map_err(|_| {
            PyValueError::new_err(
                "Private key format error. Check your eddsa secret key is exactly 32 bytes and different from 0.",
            )
        })?;
        Ok(EddsaPrivateKey { inner: NadaValue::new_eddsa_private_key(eddsa_private_key) })
    }

    /// Getter and setter for the `value` inside a
    /// :py:class:`EddsaPrivateKey` instance.
    ///
    /// Returns
    /// -------
    /// int
    ///     The value of the private eddsa key.
    ///
    /// Example
    /// -------
    ///
    /// .. code-block:: py3
    ///     
    ///     ecdas_pk_ba = bytearray(b'these are not random 32 bytes!!!')
    ///     eddsa_pk = EddsaPrivateKey(eddsa_pk_ba)
    ///     print("Eddsa private key is: ", eddsa_pk.value)
    ///     eddsa_pk_ba_prime = bytearray(b'these are good random 32 bytes!!')
    ///     eddsa_pk.value = eddsa_pk_ba_prime
    ///     print("Eddsa private key is now: ", eddsa_pk.value)
    ///
    /// .. code-block:: text
    ///
    ///     >>> Eddsa private key is:  bytearray(b'these are not random 32 bytes!!!')
    ///     >>> Eddsa private key is now:  bytearray(b'these are good random 32 bytes!!')
    #[getter]
    fn get_value(&self, py: Python<'_>) -> PyResult<Py<PyByteArray>> {
        let bytes = self
            .inner
            .as_eddsa_private_key()
            .ok_or_else(|| PyValueError::new_err("expected eddsa private key"))?
            .clone()
            .to_le_bytes();
        Ok(PyByteArray::new_bound(py, &bytes).into())
    }

    #[setter]
    fn set_value(&mut self, value: &Bound<'_, PyByteArray>) -> PyResult<()> {
        *self = Self::new(value)?;
        Ok(())
    }

    fn __repr__(&self) -> String {
        self.inner.to_string()
    }
}
