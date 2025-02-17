use nillion_client_core::values::{Clear, NadaValue};
use pyo3::{exceptions::PyValueError, prelude::*, types::PyByteArray};

/// This is a :py:class:`StoreId` class used to
/// encode a store id.
///
/// Arguments
/// ---------
/// value : bytearray
///     Value of the store id as a `bytearray`.
///
/// Returns
/// -------
/// StoreId
///     Instance of the :py:class:`StoreId` class.
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
///     gm_store_id_ba = bytearray("gm, builder!", "utf-8")
///     gm_store_id = nillion.StoreId(gm_store_id_ba)
///     ready_store_id_ba = bytearray("ready to build!", "utf-8")
///     ready_store_id = nillion.StoreId(ready_store_id_ba)
///
///     print("Are these store ids the same?", gm_store_id == ready_store_id)
///
/// .. code-block:: text
///
///     >>> Are these store ids the same?  False
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct StoreId {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for StoreId {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value.is_store_id().then(|| StoreId { inner: value }).ok_or_else(|| PyValueError::new_err("expected store id"))
    }
}

#[pymethods]
impl StoreId {
    /// Returns a new StoreId.
    #[new]
    fn new(value: &Bound<'_, PyByteArray>) -> PyResult<StoreId> {
        let store_id = to_16_byte_array(value)?;

        Ok(StoreId { inner: NadaValue::new_store_id(store_id) })
    }

    /// Getter and setter for the `value` inside a
    /// :py:class:`StoreId` instance.
    ///
    /// Returns
    /// -------
    /// int
    ///     The value of the store id.
    ///
    /// Example
    /// -------
    ///
    /// .. code-block:: py3
    ///     
    ///     gm_store_id_ba = bytearray("gm, builder!", "utf-8")
    ///     store_id = nillion.StoreId(gm_store_id_ba)
    ///     print("StoreId is: ", store_id.value)
    ///     ready_store_id_ba = bytearray("ready to build!", "utf-8")
    ///     store_id.value = ready_store_id_ba
    ///     print("StoreId is now: ", store_id.value)
    ///
    /// .. code-block:: text
    ///
    ///     >>> StoreId is:  bytearray(b'gm, builder!')
    ///     >>> StoreId is now:  bytearray(b'ready to build!')
    #[getter]
    fn get_value(&self, py: Python<'_>) -> PyResult<Py<PyByteArray>> {
        Ok(PyByteArray::new_bound(
            py,
            self.inner.as_store_id().ok_or_else(|| PyValueError::new_err("expected store id"))?,
        )
        .into())
    }

    #[setter]
    fn set_value(&mut self, value: &Bound<'_, PyByteArray>) -> PyResult<()> {
        *self = Self::new(value)?;
        Ok(())
    }
}

fn to_16_byte_array(value: &Bound<'_, PyByteArray>) -> PyResult<[u8; 16]> {
    let array: [u8; 16] = value
        .to_vec()
        .try_into()
        .map_err(|_| PyErr::new::<pyo3::exceptions::PyValueError, _>("Store id must be exactly 16 bytes long"))?;
    Ok(array)
}
