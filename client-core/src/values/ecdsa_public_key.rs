use nillion_client_core::values::{Clear, NadaValue};
use pyo3::{exceptions::PyValueError, prelude::*, types::PyByteArray};

/// This is a :py:class:`EcdsaPublicKey` class used to
/// encode an ecdsa public key.
///
/// Arguments
/// ---------
/// value : bytearray
///     Value of the ecdsa public key as a `bytearray`.
///
/// Returns
/// -------
/// EcdsaPublicKey
///     Instance of the :py:class:`EcdsaPublicKey` class.
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
///     import py_nillion_client as nillion
///
///     gm_ecdsa_pk_ba = bytearray("gm, builder!", "utf-8")
///     gm_ecdsa_pk = nillion.EcdsaPublicKey(gm_ecdsa_pk_ba)
///     ready_ecdsa_pk_ba = bytearray("ready to build!", "utf-8")
///     ready_ecdsa_pk = nillion.EcdsaPublicKey(ready_ecdsa_pk_ba)
///
///     print("Are these ecdsa public keys the same?", gm_ecdsa_pk == ready_ecdsa_pk)
///
/// .. code-block:: text
///
///     >>> Are these ecdsa public keys the same?  False
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct EcdsaPublicKey {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for EcdsaPublicKey {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value
            .is_ecdsa_public_key()
            .then(|| EcdsaPublicKey { inner: value })
            .ok_or_else(|| PyValueError::new_err("expected ecdsa public key"))
    }
}

#[pymethods]
impl EcdsaPublicKey {
    /// Returns a new EcdsaPublicKey.
    #[new]
    fn new(value: &Bound<'_, PyByteArray>) -> PyResult<EcdsaPublicKey> {
        let ecdsa_public_key = to_33_byte_array(value)?;

        Ok(EcdsaPublicKey { inner: NadaValue::new_ecdsa_public_key(ecdsa_public_key) })
    }

    /// Getter and setter for the `value` inside a
    /// :py:class:`EcdsaPublicKey` instance.
    ///
    /// Returns
    /// -------
    /// int
    ///     The value of the ecdsa public key.
    ///
    /// Example
    /// -------
    ///
    /// .. code-block:: py3
    ///     
    ///     gm_ecdsa_pk_ba = bytearray("gm, builder!", "utf-8")
    ///     ecdsa_pk = nillion.EcdsaPublicKey(gm_ecdsa_pk_ba)
    ///     print("EcdsaPublicKey is: ", ecdsa_pk.value)
    ///     ready_ecdsa_pk_ba = bytearray("ready to build!", "utf-8")
    ///     ecdsa_pk.value = ready_ecdsa_pk_ba
    ///     print("EcdsaPublicKey is now: ", ecdsa_pk.value)
    ///
    /// .. code-block:: text
    ///
    ///     >>> EcdsaPublicKey is:  bytearray(b'gm, builder!')
    ///     >>> EcdsaPublicKey is now:  bytearray(b'ready to build!')
    #[getter]
    fn get_value(&self, py: Python<'_>) -> PyResult<Py<PyByteArray>> {
        Ok(PyByteArray::new_bound(
            py,
            &self.inner.as_ecdsa_public_key().ok_or_else(|| PyValueError::new_err("expected ecdsa public key"))?.0,
        )
        .into())
    }

    #[setter]
    fn set_value(&mut self, value: &Bound<'_, PyByteArray>) -> PyResult<()> {
        *self = Self::new(value)?;
        Ok(())
    }
}

fn to_33_byte_array(value: &Bound<'_, PyByteArray>) -> PyResult<[u8; 33]> {
    let array: [u8; 33] = value.to_vec().try_into().map_err(|_| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>("Ecdsa public key must be exactly 33 bytes long")
    })?;
    Ok(array)
}
