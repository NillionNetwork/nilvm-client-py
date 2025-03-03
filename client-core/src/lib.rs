use crate::values::{nada_values_clear_to_pydict, pydict_to_nada_values_clear};
use ::nillion_client_core::values::{EncodedModulo, ShamirError};
use encrypted_value::EncryptedNadaValue;
use pyo3::{
    exceptions::PyValueError,
    prelude::*,
    types::{PyBytes, PyDict},
};
use std::collections::HashMap;

pub(crate) mod encrypted_value;
pub(crate) mod programs;
pub(crate) mod values;

#[cfg(test)]
#[ctor::ctor]
fn init() {
    pyo3::append_to_inittab!(nillion_client_core);
    // This is required in order to call Python APIs programmatically
    pyo3::prepare_freethreaded_python();
}

#[cfg(test)]
mod secrets_tests;

#[cfg(test)]
mod public_variable_tests;

#[pymodule]
fn nillion_client_core(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    values::add_module(py, m)?;
    encrypted_value::add_module(py, m)?;
    programs::add_module(py, m)?;
    m.add_class::<PartyId>()?;
    m.add_class::<PartyJar>()?;
    m.add_class::<NadaValuesClassification>()?;
    m.add_class::<SecretMasker>()?;

    Ok(())
}

/// Represents a party identifier.
#[pyclass(frozen, eq, hash)]
#[derive(Clone, PartialEq, Eq, Hash)]
struct PartyId {
    inner: ::nillion_client_core::values::PartyId,
}

#[pymethods]
impl PartyId {
    #[staticmethod]
    pub fn from_bytes(bytes: &Bound<'_, PyBytes>) -> PyResult<Self> {
        Ok(Self { inner: ::nillion_client_core::values::PartyId::from(bytes.as_bytes().to_vec()) })
    }

    fn __repr__(&self) -> String {
        format!("PartyId('{}')", self.inner)
    }
}

impl From<PartyId> for ::nillion_client_core::values::PartyId {
    fn from(value: PartyId) -> Self {
        value.inner
    }
}

/// A jar where every party puts an element.
#[pyclass]
#[derive(Clone)]
struct PartyJar {
    inner: ::nillion_client_core::values::PartyJar<::nillion_client_core::values::EncryptedValues>,
    modulo: EncodedModulo,
}

impl PartyJar {
    fn new(party_count: usize, modulo: EncodedModulo) -> Self {
        Self { inner: ::nillion_client_core::values::PartyJar::new(party_count), modulo }
    }
}

#[pymethods]
impl PartyJar {
    pub fn add_element(
        &mut self,
        py: Python<'_>,
        party: PartyId,
        values: HashMap<String, EncryptedNadaValue>,
    ) -> PyResult<()> {
        let values = values
            .into_iter()
            .map(|(k, v)| v.into_nada_value(py, self.modulo).map(|v| (k, v)))
            .collect::<Result<_, _>>()?;
        self.inner
            .add_element(party.into(), values)
            .map_err(|err| PyValueError::new_err(format!("adding element into party jar failed: {}", err)))?;
        Ok(())
    }
}

impl TryFrom<PartyJar> for ::nillion_client_core::values::PartyJar<::nillion_client_core::values::EncryptedValues> {
    type Error = PyErr;

    fn try_from(value: PartyJar) -> Result<Self, Self::Error> {
        Self::new_with_elements(value.inner.into_elements().collect::<Vec<_>>())
            .map_err(|err| PyValueError::new_err(format!("converting party jar failed: {}", err)))
    }
}

/// A classification of Nada values.
#[pyclass(get_all)]
#[derive(Clone)]
struct NadaValuesClassification {
    /// The number of shares
    shares: u64,

    /// The number of public values
    public: u64,

    /// The number of ecdsa key shares
    ecdsa_private_key_shares: u64,

    /// The number of ecdsa signatures shares
    ecdsa_signature_shares: u64,
}

#[pymethods]
impl NadaValuesClassification {
    fn __repr__(&self) -> String {
        format!(
            "NadaValuesClassification(shares='{}', public='{}', ecdsa_private_key_shares='{}')",
            self.shares, self.public, self.ecdsa_private_key_shares
        )
    }
}

impl From<::nillion_client_core::values::NadaValuesClassification> for NadaValuesClassification {
    fn from(value: ::nillion_client_core::values::NadaValuesClassification) -> Self {
        Self {
            shares: value.shares,
            public: value.public,
            ecdsa_private_key_shares: value.ecdsa_private_key_shares,
            ecdsa_signature_shares: value.ecdsa_signature_shares,
        }
    }
}

/// A secret masker.
///
/// This allows masking and unmasking secrets.
#[pyclass]
struct SecretMasker {
    inner: ::nillion_client_core::values::SecretMasker,
    party_count: usize,
    modulo: EncodedModulo,
}

impl SecretMasker {
    fn new<B>(polynomial_degree: u64, parties: Vec<Py<PartyId>>, modulo: EncodedModulo, builder: B) -> PyResult<Self>
    where
        B: Fn(
            u64,
            Vec<::nillion_client_core::values::PartyId>,
        ) -> Result<::nillion_client_core::values::SecretMasker, ShamirError>,
    {
        let party_count = parties.len();
        let inner = builder(
            polynomial_degree,
            parties.into_iter().map(|party| Python::with_gil(|py| party.borrow(py).clone()).inner).collect(),
        )
        .map_err(|err| PyValueError::new_err(format!("creating new secret masker failed: {}", err)))?;
        Ok(Self { inner, party_count, modulo })
    }
}

#[pymethods]
impl SecretMasker {
    /// Construct a new masker that uses a 64 bit safe prime under the hood.
    #[staticmethod]
    pub fn new_64_bit_safe_prime(polynomial_degree: u64, parties: Vec<Py<PartyId>>) -> PyResult<Self> {
        Self::new(
            polynomial_degree,
            parties,
            EncodedModulo::U64SafePrime,
            ::nillion_client_core::values::SecretMasker::new_64_bit_safe_prime,
        )
    }

    /// Construct a new masker that uses a 128 bit safe prime under the hood.
    #[staticmethod]
    pub fn new_128_bit_safe_prime(polynomial_degree: u64, parties: Vec<Py<PartyId>>) -> PyResult<Self> {
        Self::new(
            polynomial_degree,
            parties,
            EncodedModulo::U128SafePrime,
            ::nillion_client_core::values::SecretMasker::new_128_bit_safe_prime,
        )
    }

    /// Construct a new masker that uses a 256 bit safe prime under the hood.
    #[staticmethod]
    pub fn new_256_bit_safe_prime(polynomial_degree: u64, parties: Vec<Py<PartyId>>) -> PyResult<Self> {
        Self::new(
            polynomial_degree,
            parties,
            EncodedModulo::U256SafePrime,
            ::nillion_client_core::values::SecretMasker::new_256_bit_safe_prime,
        )
    }

    /// Mask a set of values.
    pub fn mask<'a>(
        &self,
        py: Python<'a>,
        values: &Bound<'a, PyDict>,
    ) -> PyResult<HashMap<PartyId, HashMap<String, EncryptedNadaValue>>> {
        let nada_values = pydict_to_nada_values_clear(values)?;
        let encrypted_values =
            self.inner.mask(nada_values).map_err(|err| PyValueError::new_err(format!("masking failed: {}", err)))?;
        let mut party_values = HashMap::new();
        for (party, values) in encrypted_values {
            let mut named_values = HashMap::new();
            for (name, value) in values {
                named_values.insert(name, EncryptedNadaValue::new(py, value)?);
            }
            party_values.insert(PartyId { inner: party }, named_values);
        }
        Ok(party_values)
    }

    /// Unmask a set of values.
    pub fn unmask<'a>(&self, py: Python<'a>, jar: PartyJar) -> PyResult<Bound<'a, PyDict>> {
        let result = self
            .inner
            .unmask(jar.try_into()?)
            .map_err(|err| PyValueError::new_err(format!("unmasking failed: {}", err)))?;
        nada_values_clear_to_pydict(py, result)
    }

    /// Classify the given cleartext values.
    ///
    /// This allows getting the totals per value type which is a required parameter when storing values.
    pub fn classify_values(&self, values: &Bound<'_, PyDict>) -> PyResult<NadaValuesClassification> {
        let nada_values = pydict_to_nada_values_clear(values)?;
        Ok(self.inner.classify_values(&nada_values).into())
    }

    /// Build a party jar for this masker.
    pub fn build_jar(&self) -> PartyJar {
        PartyJar::new(self.party_count, self.modulo)
    }
}
