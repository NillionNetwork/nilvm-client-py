use nillion_client_core::{
    generic_ec::{curves::Secp256k1, NonZero, Scalar},
    signature,
    values::{Clear, NadaValue},
};
use pyo3::{
    exceptions::PyValueError,
    prelude::*,
    types::{PyByteArray, PyTuple},
};

/// This is a :py:class:`EcdsaSignature` class used to
/// encode a secret bytearray as an ecdsa private key.
///
/// Arguments
/// ---------
/// value : bytearray
///     Value of the private ecdsa key as a `bytearray`.
///
/// Returns
/// -------
/// EcdsaSignature
///     Instance of the :py:class:`EcdsaSignature` class.
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
///     from nillion_client import EcdsaSignature
///     import os
///     
///     r = bytearray(os.urandom(32))
///     s = bytearray(os.urandom(32))
///     sig = EcdsaSignature((r, s))
#[pyclass(eq)]
#[derive(PartialEq, Clone)]
pub struct EcdsaSignature {
    pub(crate) inner: NadaValue<Clear>,
}

impl TryFrom<NadaValue<Clear>> for EcdsaSignature {
    type Error = PyErr;

    fn try_from(value: NadaValue<Clear>) -> Result<Self, Self::Error> {
        value
            .is_ecdsa_signature()
            .then(|| EcdsaSignature { inner: value })
            .ok_or_else(|| PyValueError::new_err("expected ecdsa private key"))
    }
}

#[pymethods]
impl EcdsaSignature {
    /// Returns a new EcdsaSignature. The byte arrays corresponding to r and s should be in big-endian format.
    #[new]
    fn new(value: &Bound<'_, PyTuple>) -> PyResult<EcdsaSignature> {
        // let (r, s) = value;
        if value.len() != 2 {
            return Err(PyValueError::new_err("Expected a tuple with exactly two elements."));
        }

        let r_mid = value.get_item(0)?;
        let r: &Bound<'_, PyByteArray> = r_mid.downcast::<PyByteArray>()?;
        let s_mid = value.get_item(1)?;
        let s: &Bound<'_, PyByteArray> = s_mid.downcast::<PyByteArray>()?;

        let r_scalar = parse_scalar(&r.to_vec(), "r")?;
        let s_scalar = parse_scalar(&s.to_vec(), "s")?;

        let ecdsa_signature = signature::EcdsaSignature { r: r_scalar, s: s_scalar };

        Ok(EcdsaSignature { inner: NadaValue::new_ecdsa_signature(ecdsa_signature) })
    }

    fn __repr__(&self) -> String {
        self.inner.to_string()
    }

    /// Getter for the `r` inside a
    /// :py:class:`EcdsaSignature` instance.
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
    ///     from nillion_client import EcdsaSignature
    ///     import os
    ///     
    ///     r = bytearray(os.urandom(32))
    ///     s = bytearray(os.urandom(32))
    ///     signature = EcdsaSignature((r, s))
    ///     print("Ecdsa signature is: ", signature.value)
    #[getter]
    fn get_value(&self, py: Python<'_>) -> PyResult<(Py<PyByteArray>, Py<PyByteArray>)> {
        let signature::EcdsaSignature { r, s } =
            self.inner.as_ecdsa_signature().ok_or_else(|| PyValueError::new_err("expected ecdsa signature"))?;
        let r_bytes = Scalar::to_be_bytes(r);
        let s_bytes = Scalar::to_be_bytes(s);

        let r_pybytes = PyByteArray::new_bound(py, &r_bytes).into();
        let s_pybytes = PyByteArray::new_bound(py, &s_bytes).into();

        Ok((r_pybytes, s_pybytes))
    }
}

/// parse a scalar from bytes in big-endian order
fn parse_scalar(bytes: &[u8], param: &str) -> PyResult<NonZero<Scalar<Secp256k1>>> {
    let scalar = Scalar::from_be_bytes(bytes).map_err(|_| {
        PyValueError::new_err(format!(
            "Ecdsa signature parameter {} format error as the encoded integer is larger than group order. Note that byte representation should be in big-endian format.",
            param
        ))
    })?;

    NonZero::from_scalar(scalar)
        .ok_or_else(|| PyValueError::new_err(format!("Ecdsa signature parameter {} cannot be 0.", param)))
}
