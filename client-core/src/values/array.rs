//! Python bindings for array and utilities.

use crate::values::{nada_value_clear_to_pyobject, pyany_to_nada_value_clear};
use nillion_client_core::values::{Clear, NadaValue};
use pyo3::{exceptions::PyValueError, pyclass, pymethods, PyErr, PyObject, PyResult, Python};

/// This is a :py:class:`Array` class used to
/// encode a secret array of elements.
///
/// Note: `__len__` method is implemented to allow
/// getting the length of the array.
///
/// Arguments
/// ---------
/// value : list
///     List of secret encoded elements.
///
/// Returns
/// -------
/// Array
///     Instance of the :py:class:`Array` class.
///
/// Raises
/// -------
/// ValueError: invalid secret type
///     Raises an error when a public encoded element is included inside a
///     secret array.
///
/// Example
/// -------
///
/// .. code-block:: py3
///
///     from nillion_client import Array, SecretInteger
///
///     secret_array = Array([ SecretInteger(1), SecretInteger(2) ])
///
///     print("The length of the array is: ", len(secret_array))
///
/// .. code-block:: text
///
///     >>> The length of the array is: 2
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct Array {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for Array {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value.is_array().then(|| Array { inner: value }).ok_or_else(|| PyValueError::new_err("expected array"))
    }
}

#[pymethods]
impl Array {
    /// Returns a new [`Array`].
    #[new]
    fn new(value: Vec<PyObject>, py: Python) -> PyResult<Self> {
        let values = value
            .into_iter()
            .map(|e| {
                let e_any = e.into_any();
                let e = pyany_to_nada_value_clear(e_any.into_bound(py))?;
                Ok(e)
            })
            .collect::<Result<Vec<_>, PyErr>>()?;
        let nada_type =
            values.first().ok_or_else(|| PyValueError::new_err("Array must have at least one element"))?.to_type();
        Ok(Array { inner: NadaValue::new_array(nada_type, values).map_err(|e| PyValueError::new_err(e.to_string()))? })
    }

    fn __len__(&self) -> PyResult<usize> {
        Ok(self.inner.as_array().unwrap().1.len())
    }

    /// Getter method for the `value` inside a
    /// :py:class:`Array` instance.
    ///
    /// Returns
    /// -------
    /// list
    ///     List of secret encoded elements.
    ///
    /// Example
    /// -------
    ///
    /// .. code-block:: py3
    ///
    ///     print("My secret array: \n", secret_array.value)
    ///
    /// .. code-block:: text
    ///
    ///     >>> My secret array:
    ///     >>>  [SecretInteger(1), SecretInteger(2)]
    #[getter]
    fn get_value(&self, py: Python<'_>) -> PyResult<Vec<PyObject>> {
        self.inner
            .as_array()
            .unwrap()
            .1
            .iter()
            .cloned()
            .map(|v| nada_value_clear_to_pyobject(py, v))
            .collect::<Result<Vec<_>, _>>()
    }

    fn __str__(&self) -> String {
        let str_values =
            self.inner.as_array().unwrap().1.iter().cloned().map(|v| v.to_string()).collect::<Vec<_>>().join(", ");
        format!("[{str_values}]")
    }

    fn __repr__(&self) -> String {
        self.inner.to_string()
    }
}
