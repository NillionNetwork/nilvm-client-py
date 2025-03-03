use nillion_client_core::values::{Clear, NadaValue};
use pyo3::{exceptions::PyValueError, prelude::*, types::PyByteArray};

/// This is a :py:class:`EddsaPublicKey` class used to
/// encode an eddsa public key.
///
/// Arguments
/// ---------
/// value : bytearray
///     Value of the eddsa public key as a `bytearray`.
///
/// Returns
/// -------
/// EddsaPublicKey
///     Instance of the :py:class:`EddsaPublicKey` class.
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
///     gm_eddsa_pk_ba = bytearray("gm, builder!", "utf-8")
///     gm_eddsa_pk = nillion.EddsaPublicKey(gm_eddsa_pk_ba)
///     ready_eddsa_pk_ba = bytearray("ready to build!", "utf-8")
///     ready_eddsa_pk = nillion.EddsaPublicKey(ready_eddsa_pk_ba)
///
///     print("Are these eddsa public keys the same?", gm_eddsa_pk == ready_eddsa_pk)
///
/// .. code-block:: text
///
///     >>> Are these eddsa public keys the same?  False
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct EddsaPublicKey {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for EddsaPublicKey {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value
            .is_eddsa_public_key()
            .then(|| EddsaPublicKey { inner: value })
            .ok_or_else(|| PyValueError::new_err("expected eddsa public key"))
    }
}

#[pymethods]
impl EddsaPublicKey {
    /// Returns a new EddsaPublicKey.
    #[new]
    fn new(value: &Bound<'_, PyByteArray>) -> PyResult<EddsaPublicKey> {
        let eddsa_public_key = to_32_byte_array(value)?;

        Ok(EddsaPublicKey { inner: NadaValue::new_eddsa_public_key(eddsa_public_key) })
    }

    /// Getter and setter for the `value` inside a
    /// :py:class:`EddsaPublicKey` instance.
    ///
    /// Returns
    /// -------
    /// int
    ///     The value of the eddsa public key.
    ///
    /// Example
    /// -------
    ///
    /// .. code-block:: py3
    ///     
    ///     gm_eddsa_pk_ba = bytearray("gm, builder!", "utf-8")
    ///     eddsa_pk = nillion.EddsaPublicKey(gm_eddsa_pk_ba)
    ///     print("EddsaPublicKey is: ", eddsa_pk.value)
    ///     ready_eddsa_pk_ba = bytearray("ready to build!", "utf-8")
    ///     eddsa_pk.value = ready_eddsa_pk_ba
    ///     print("EddsaPublicKey is now: ", eddsa_pk.value)
    ///
    /// .. code-block:: text
    ///
    ///     >>> EddsaPublicKey is:  bytearray(b'gm, builder!')
    ///     >>> EddsaPublicKey is now:  bytearray(b'ready to build!')
    #[getter]
    fn get_value(&self, py: Python<'_>) -> PyResult<Py<PyByteArray>> {
        Ok(PyByteArray::new_bound(
            py,
            self.inner.as_eddsa_public_key().ok_or_else(|| PyValueError::new_err("expected eddsa public key"))?,
        )
        .into())
    }

    #[setter]
    fn set_value(&mut self, value: &Bound<'_, PyByteArray>) -> PyResult<()> {
        *self = Self::new(value)?;
        Ok(())
    }
}

fn to_32_byte_array(value: &Bound<'_, PyByteArray>) -> PyResult<[u8; 32]> {
    let array: [u8; 32] = value.to_vec().try_into().map_err(|_| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>("Eddsa public key must be exactly 32 bytes long")
    })?;
    Ok(array)
}
