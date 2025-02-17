use nillion_client_core::values::{Clear, NadaValue};
use pyo3::{exceptions::PyValueError, prelude::*, types::PyByteArray};

/// This is a :py:class:`SecretBlob` class used to
/// encode a secret as a blob.
///
/// Arguments
/// ---------
/// value : bytearray
///     Value of the secret blob as a `bytearray`.
///
/// Returns
/// -------
/// SecretBlob
///     Instance of the :py:class:`SecretBlob` class.
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
///     from nillion_client import SecretBlob
///
///     gm_blob_ba = bytearray("gm, builder!", "utf-8")
///     gm_blob = SecretBlob(gm_blob_ba)
///     ready_blob_ba = bytearray("ready to build!", "utf-8")
///     ready_blob = SecretBlob(ready_blob_ba)
///
///     print("Are these blobs the same?", gm_blob == ready_blob)
///
/// .. code-block:: text
///
///     >>> Are these blobs the same?  False
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct SecretBlob {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for SecretBlob {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value
            .is_secret_blob()
            .then(|| SecretBlob { inner: value })
            .ok_or_else(|| PyValueError::new_err("expected secret blob"))
    }
}

#[pymethods]
impl SecretBlob {
    /// Returns a new SecretBlob.
    #[new]
    fn new(value: &Bound<'_, PyByteArray>) -> SecretBlob {
        SecretBlob { inner: NadaValue::new_secret_blob(value.to_vec()) }
    }

    /// Getter and setter for the `value` inside a
    /// :py:class:`SecretBlob` instance.
    ///
    /// Returns
    /// -------
    /// int
    ///     The value of the secret blob.
    ///
    /// Example
    /// -------
    ///
    /// .. code-block:: py3
    ///     
    ///     gm_blob_ba = bytearray("gm, builder!", "utf-8")
    ///     blob = SecretBlob(gm_blob_ba)
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
            self.inner.as_secret_blob().ok_or_else(|| PyValueError::new_err("expected secret blob"))?,
        )
        .into())
    }

    #[setter]
    fn set_value(&mut self, value: &Bound<'_, PyByteArray>) {
        self.inner = NadaValue::new_secret_blob(value.to_vec());
    }

    fn __repr__(&self) -> String {
        self.inner.to_string()
    }
}
