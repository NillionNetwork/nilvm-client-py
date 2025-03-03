use nillion_client_core::values::{Clear, NadaValue};
use pyo3::{exceptions::PyValueError, prelude::*, types::PyByteArray};

/// This is a :py:class:`EddsaMessage` class used to
/// encode a secret as a message digest.
///
/// Arguments
/// ---------
/// value : bytearray
///     Value of the secret message digest as a `bytearray`.
///
/// Returns
/// -------
/// EddsaMessage
///     Instance of the :py:class:`EddsaMessage` class.
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
pub struct EddsaMessage {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for EddsaMessage {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value
            .is_eddsa_message()
            .then(|| EddsaMessage { inner: value })
            .ok_or_else(|| PyValueError::new_err("expected eddsa message"))
    }
}

#[pymethods]
impl EddsaMessage {
    /// Returns a new EddsaMessage.
    #[new]
    fn new(value: &Bound<'_, PyByteArray>) -> PyResult<EddsaMessage> {
        let eddsa_message = value.to_vec();

        Ok(EddsaMessage { inner: NadaValue::new_eddsa_message(eddsa_message) })
    }

    /// Getter and setter for the `value` inside a
    /// :py:class:`EddsaMessage` instance.
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
    ///     blob = nillion.EddsaMessage(gm_blob_ba)
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
            self.inner.as_eddsa_message().ok_or_else(|| PyValueError::new_err("expected eddsa message"))?,
        )
        .into())
    }

    #[setter]
    fn set_value(&mut self, value: &Bound<'_, PyByteArray>) -> PyResult<()> {
        *self = Self::new(value)?;
        Ok(())
    }
}
