use nillion_client_core::{
    privatekey,
    values::{Clear, NadaValue},
};
use pyo3::{exceptions::PyValueError, prelude::*, types::PyByteArray};

/// This is a :py:class:`EcdsaPrivateKey` class used to
/// encode a secret bytearray as an ecdsa private key.
///
/// Arguments
/// ---------
/// value : bytearray
///     Value of the private ecdsa key as a `bytearray`.
///
/// Returns
/// -------
/// EcdsaPrivateKey
///     Instance of the :py:class:`EcdsaPrivateKey` class.
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
///     from nillion_client import EcdsaPrivateKey
///     import os
///     
///     pk1_bytes = bytearray(os.urandom(32))
///     pk1 = EcdsaPrivateKey(pk1_bytes)
///     pk2_bytes = bytearray(os.urandom(32))
///     pk2 = EcdsaPrivateKey(pk2_bytes)
///
///     print("Are these ecdsa private keys the same?", pk1 == pk2)
///
/// .. code-block:: text
///
///     >>> Are these ecdsa private keys the same?  False
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct EcdsaPrivateKey {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for EcdsaPrivateKey {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value
            .is_ecdsa_private_key()
            .then(|| EcdsaPrivateKey { inner: value })
            .ok_or_else(|| PyValueError::new_err("expected ecdsa private key"))
    }
}

#[pymethods]
impl EcdsaPrivateKey {
    /// Returns a new EcdsaPrivateKey. The byte array should be in big-endian format.
    #[new]
    fn new(value: &Bound<'_, PyByteArray>) -> PyResult<EcdsaPrivateKey> {
        let ecdsa_private_key = privatekey::EcdsaPrivateKey::from_bytes(&value.to_vec()).map_err(|_| {
            PyValueError::new_err(
                "Private key format error. Check your ecdsa secret key is exactly 32 bytes and different from 0.",
            )
        })?;
        Ok(EcdsaPrivateKey { inner: NadaValue::new_ecdsa_private_key(ecdsa_private_key) })
    }

    /// Getter and setter for the `value` inside a
    /// :py:class:`EcdsaPrivateKey` instance.
    ///
    /// Returns
    /// -------
    /// int
    ///     The value of the private ecdsa key.
    ///
    /// Example
    /// -------
    ///
    /// .. code-block:: py3
    ///     
    ///     ecdas_pk_ba = bytearray(b'these are not random 32 bytes!!!')
    ///     ecdsa_pk = EcdsaPrivateKey(ecdas_pk_ba)
    ///     print("Ecdsa private key is: ", ecdsa_pk.value)
    ///     ecdsa_pk_ba_prime = bytearray(b'these are good random 32 bytes!!')
    ///     ecdsa_pk.value = ecdsa_pk_ba_prime
    ///     print("Ecdsa private key is now: ", ecdsa_pk.value)
    ///
    /// .. code-block:: text
    ///
    ///     >>> Ecdsa private key is:  bytearray(b'these are not random 32 bytes!!!')
    ///     >>> Ecdsa private key is now:  bytearray(b'these are good random 32 bytes!!')
    #[getter]
    fn get_value(&self, py: Python<'_>) -> PyResult<Py<PyByteArray>> {
        let bytes = self
            .inner
            .as_ecdsa_private_key()
            .ok_or_else(|| PyValueError::new_err("expected ecdsa private key"))?
            .clone()
            .to_bytes();
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
