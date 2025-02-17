use nillion_client_core::values::{Clear, NadaValue};
use pyo3::{exceptions::PyValueError, prelude::*, types::PyByteArray};

/// This is a :py:class:`EcdsaDigestMessage` class used to
/// encode a secret as a message digest.
///
/// Arguments
/// ---------
/// value : bytearray
///     Value of the secret message digest as a `bytearray`.
///
/// Returns
/// -------
/// EcdsaDigestMessage
///     Instance of the :py:class:`EcdsaDigestMessage` class.
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
///     gm_blob_ba = bytearray("gm, builder!", "utf-8")
///     gm_blob = nillion.EcdsaDigestMessage(gm_blob_ba)
///     ready_blob_ba = bytearray("ready to build!", "utf-8")
///     ready_blob = nillion.EcdsaDigestMessage(ready_blob_ba)
///
///     print("Are these blobs the same?", gm_blob == ready_blob)
///
/// .. code-block:: text
///
///     >>> Are these blobs the same?  False
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct EcdsaDigestMessage {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for EcdsaDigestMessage {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value
            .is_ecdsa_digest_message()
            .then(|| EcdsaDigestMessage { inner: value })
            .ok_or_else(|| PyValueError::new_err("expected ecdsa digest message"))
    }
}

#[pymethods]
impl EcdsaDigestMessage {
    /// Returns a new EcdsaDigestMessage.
    #[new]
    fn new(value: &Bound<'_, PyByteArray>) -> PyResult<EcdsaDigestMessage> {
        let ecdsa_digest_message = to_32_byte_array(value)?;

        Ok(EcdsaDigestMessage { inner: NadaValue::new_ecdsa_digest_message(ecdsa_digest_message) })
    }

    /// Getter and setter for the `value` inside a
    /// :py:class:`EcdsaDigestMessage` instance.
    ///
    /// Returns
    /// -------
    /// int
    ///     The value of the secret message digest.
    ///
    /// Example
    /// -------
    ///
    /// .. code-block:: py3
    ///     
    ///     gm_blob_ba = bytearray("gm, builder!", "utf-8")
    ///     blob = nillion.EcdsaDigestMessage(gm_blob_ba)
    ///     print("Blob is: ", blob.value)
    ///     ready_blob_ba = bytearray("ready to build!", "utf-8")
    ///     blob.value = ready_blob_ba
    ///     print("Blob is now: ", blob.value)
    ///
    /// .. code-block:: text
    ///
    ///     >>> Blob is:  bytearray(b'gm, builder!')
    ///     >>> Blob is now:  bytearray(b'ready to build!')
    #[getter]
    fn get_value(&self, py: Python<'_>) -> PyResult<Py<PyByteArray>> {
        Ok(PyByteArray::new_bound(
            py,
            self.inner
                .as_ecdsa_digest_message()
                .ok_or_else(|| PyValueError::new_err("expected ecdsa digest message"))?,
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
    let array: [u8; 32] = value
        .to_vec()
        .try_into()
        .map_err(|_| PyErr::new::<pyo3::exceptions::PyValueError, _>("Message digest must be exactly 32 bytes long"))?;
    Ok(array)
}
