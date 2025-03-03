use nillion_client_core::{
    generic_ec::Scalar,
    signature,
    values::{Clear, NadaValue},
};
use pyo3::{
    exceptions::PyValueError,
    prelude::*,
    types::{PyByteArray, PyTuple},
};

/// This is a :py:class:`EddsaSignature` class used to
/// encode a secret bytearray as an eddsa private key.
///
/// Arguments
/// ---------
/// value : bytearray
///     Value of the private eddsa key as a `bytearray`.
///
/// Returns
/// -------
/// EddsaSignature
///     Instance of the :py:class:`EddsaSignature` class.
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
///     from nillion_client import EddsaSignature
///     import os
///     
///     r = bytearray(os.urandom(32))
///     z = bytearray(os.urandom(32))
///     sig = EddsaSignature((r, z))
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct EddsaSignature {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for EddsaSignature {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value
            .is_eddsa_signature()
            .then(|| EddsaSignature { inner: value })
            .ok_or_else(|| PyValueError::new_err("expected eddsa signature"))
    }
}

#[pymethods]
impl EddsaSignature {
    /// Returns a new EddsaSignature. The byte arrays corresponding to r and z should be in big-endian format.
    #[new]
    fn new(value: &Bound<'_, PyTuple>) -> PyResult<EddsaSignature> {
        // let (r, z) = value;
        if value.len() != 2 {
            return Err(PyValueError::new_err("Expected a tuple with exactly two elements."));
        }

        let r_mid = value.get_item(0)?;
        let r: &Bound<'_, PyByteArray> = r_mid.downcast::<PyByteArray>()?;
        let s_mid = value.get_item(1)?;
        let s: &Bound<'_, PyByteArray> = s_mid.downcast::<PyByteArray>()?;

        let signature = signature::EddsaSignature::from_components_bytes(&r.to_vec(), &s.to_vec())
            .map_err(|e| PyValueError::new_err(e.to_string()))?;

        Ok(EddsaSignature { inner: NadaValue::new_eddsa_signature(signature) })
    }

    fn __repr__(&self) -> String {
        self.inner.to_string()
    }

    /// Getter for the tuple `(r, z)` inside a
    /// :py:class:`EddsaSignature` instance.
    ///
    /// Returns
    /// -------
    /// tuple
    ///     The value of the private eddsa key.
    ///
    /// Example
    /// -------
    ///
    /// .. code-block:: py3
    ///
    ///     from nillion_client import EddsaSignature
    ///     import os
    ///     
    ///     r = bytearray(os.urandom(32))
    ///     z = bytearray(os.urandom(32))
    ///     signature = EddsaSignature((r, z))
    ///     print("Eddsa signature is: ", signature.value)
    #[getter]
    fn get_value(&self, py: Python<'_>) -> PyResult<(Py<PyByteArray>, Py<PyByteArray>)> {
        let signature::EddsaSignature { signature } =
            self.inner.as_eddsa_signature().ok_or_else(|| PyValueError::new_err("expected eddsa signature"))?;

        let r_bytes = signature.r.to_bytes().to_vec();
        let z_bytes = Scalar::to_le_bytes(&signature.z);

        let r_pybytes = PyByteArray::new_bound(py, &r_bytes).into();
        let z_pybytes = PyByteArray::new_bound(py, &z_bytes).into();

        Ok((r_pybytes, z_pybytes))
    }
}
