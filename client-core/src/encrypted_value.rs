use nillion_client_core::{
    generic_ec::{serde::CurveName, Curve, NonZero, Point, Scalar, SecretScalar},
    key_share::{DirtyCoreKeyShare, DirtyKeyInfo, Validate},
    privatekey::ThresholdPrivateKeyShare,
    signature::{EcdsaSignatureShare, EddsaSignature},
    values::{BlobPrimitiveType, Encoded, EncodedModularNumber, EncodedModulo, Encrypted, NadaValue},
};

use pyo3::{
    exceptions::PyValueError,
    pyclass, pymethods,
    types::{PyModule, PyModuleMethods},
    Bound, IntoPy, Py, PyAny, PyResult, Python,
};

pub fn add_module(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<EncryptedNadaValue>()?;
    m.add_class::<EncryptedNadaType>()?;
    Ok(())
}

/// A nada value that has been encrypted/secret shared.
#[pyclass]
#[derive(Clone)]
pub enum EncryptedNadaValue {
    ShamirShareInteger { value: Vec<u8> },
    ShamirShareUnsignedInteger { value: Vec<u8> },
    ShamirShareBoolean { value: Vec<u8> },
    ShamirSharesBlob { values: Vec<Vec<u8>>, original_size: u64 },
    PublicInteger { value: Vec<u8> },
    PublicUnsignedInteger { value: Vec<u8> },
    PublicBoolean { value: Vec<u8> },
    Array { inner_type: EncryptedNadaType, values: Vec<EncryptedNadaValue> },
    Tuple { left: Py<EncryptedNadaValue>, right: Py<EncryptedNadaValue> },
    EcdsaMessageDigest { value: Vec<u8> },
    EcdsaSignature { r: Vec<u8>, sigma: Vec<u8> },
    EcdsaPrivateKey { i: u16, x: Vec<u8>, shared_public_key: Vec<u8>, public_shares: Vec<Vec<u8>> },
    EcdsaPublicKey { value: Vec<u8> },
    StoreId { value: Vec<u8> },
    EddsaPrivateKey { i: u16, x: Vec<u8>, shared_public_key: Vec<u8>, public_shares: Vec<Vec<u8>> },
    EddsaPublicKey { value: Vec<u8> },
    EddsaSignature { value: Vec<u8> },
    EddsaMessage { value: Vec<u8> },
}

impl EncryptedNadaValue {
    pub(crate) fn new(py: Python<'_>, value: NadaValue<Encrypted<Encoded>>) -> PyResult<Self> {
        let value = match value {
            NadaValue::ShamirShareInteger(value) => Self::ShamirShareInteger { value: value.as_bytes().to_vec() },
            NadaValue::ShamirShareUnsignedInteger(value) => {
                Self::ShamirShareUnsignedInteger { value: value.as_bytes().to_vec() }
            }
            NadaValue::ShamirShareBoolean(value) => Self::ShamirShareBoolean { value: value.as_bytes().to_vec() },
            NadaValue::Integer(value) => Self::PublicInteger { value: value.as_bytes().to_vec() },
            NadaValue::UnsignedInteger(value) => Self::PublicUnsignedInteger { value: value.as_bytes().to_vec() },
            NadaValue::Boolean(value) => Self::PublicBoolean { value: value.as_bytes().to_vec() },
            NadaValue::SecretBlob(value) => Self::ShamirSharesBlob {
                values: value.value.into_iter().map(|m| m.as_bytes().to_vec()).collect(),
                original_size: value.unencoded_size,
            },
            NadaValue::Array { inner_type, values } => {
                let values = values.into_iter().map(|v| Self::new(py, v)).collect::<Result<Vec<_>, _>>()?;
                Self::Array { values, inner_type: EncryptedNadaType::new(py, inner_type)? }
            }
            NadaValue::Tuple { left, right } => {
                Self::Tuple { left: Py::new(py, Self::new(py, *left)?)?, right: Py::new(py, Self::new(py, *right)?)? }
            }
            NadaValue::EcdsaDigestMessage(value) => Self::EcdsaMessageDigest { value: value.to_vec() },
            NadaValue::EcdsaPublicKey(value) => Self::EcdsaPublicKey { value: value.0.to_vec() },
            NadaValue::EcdsaSignature(signature) => Self::EcdsaSignature {
                r: signature.r.to_le_bytes().to_vec(),
                sigma: signature.sigma.to_le_bytes().to_vec(),
            },
            NadaValue::EcdsaPrivateKey(key) => {
                let key = key.into_inner();
                Self::EcdsaPrivateKey {
                    i: key.i,
                    x: key.x.clone().into_inner().as_ref().to_le_bytes().to_vec(),
                    shared_public_key: key.key_info.shared_public_key.to_bytes(true).to_vec(),
                    public_shares: key.key_info.public_shares.iter().map(|s| s.to_bytes(true).to_vec()).collect(),
                }
            }
            NadaValue::StoreId(value) => Self::StoreId { value: value.to_vec() },
            NadaValue::EddsaPrivateKey(key) => {
                let key = key.into_inner();
                Self::EddsaPrivateKey {
                    i: key.i,
                    x: key.x.clone().into_inner().as_ref().to_le_bytes().to_vec(),
                    shared_public_key: key.key_info.shared_public_key.to_bytes(true).to_vec(),
                    public_shares: key.key_info.public_shares.iter().map(|s| s.to_bytes(true).to_vec()).collect(),
                }
            }
            NadaValue::EddsaPublicKey(value) => Self::EddsaPublicKey { value: value.to_vec() },
            NadaValue::EddsaSignature(signature) => {
                let mut out = vec![0u8; signature.serialized_len()];
                signature.signature.write_to_slice(&mut out);
                Self::EddsaSignature { value: out }
            }
            NadaValue::EddsaMessage(message) => Self::EddsaMessage { value: message },
            _ => Err(PyValueError::new_err("Unsupported NadaValue variant for conversion to PyObject"))?,
        };
        Ok(value)
    }

    pub(crate) fn into_nada_value(
        self,
        py: Python<'_>,
        modulo: EncodedModulo,
    ) -> PyResult<NadaValue<Encrypted<Encoded>>> {
        use EncryptedNadaValue as E;
        let value = match self {
            E::ShamirShareInteger { value } => {
                NadaValue::new_shamir_share_integer(EncodedModularNumber::new_unchecked(value, modulo))
            }
            E::ShamirShareUnsignedInteger { value } => {
                NadaValue::new_shamir_share_unsigned_integer(EncodedModularNumber::new_unchecked(value, modulo))
            }
            E::ShamirShareBoolean { value } => {
                NadaValue::new_shamir_share_boolean(EncodedModularNumber::new_unchecked(value, modulo))
            }
            E::ShamirSharesBlob { values, original_size } => NadaValue::new_secret_blob(BlobPrimitiveType {
                value: values.into_iter().map(|s| EncodedModularNumber::new_unchecked(s, modulo)).collect(),
                unencoded_size: original_size,
            }),
            E::PublicInteger { value } => NadaValue::new_integer(EncodedModularNumber::new_unchecked(value, modulo)),
            E::PublicUnsignedInteger { value } => {
                NadaValue::new_unsigned_integer(EncodedModularNumber::new_unchecked(value, modulo))
            }
            E::PublicBoolean { value } => NadaValue::new_boolean(EncodedModularNumber::new_unchecked(value, modulo)),
            E::Array { inner_type, values } => {
                let values = values.into_iter().map(|v| v.into_nada_value(py, modulo)).collect::<Result<_, _>>()?;
                NadaValue::new_array(inner_type.into_nada_type(py)?, values)
                    .map_err(|e| PyValueError::new_err(format!("failed to create array: {e}")))?
            }
            E::Tuple { left, right } => NadaValue::new_tuple(
                left.get().clone().into_nada_value(py, modulo)?,
                right.get().clone().into_nada_value(py, modulo)?,
            )
            .map_err(|e| PyValueError::new_err(format!("failed to create tuple: {e}")))?,
            E::EcdsaMessageDigest { value } => {
                let value: [u8; 32] =
                    value.try_into().map_err(|_| PyValueError::new_err("invalid digest message length"))?;
                NadaValue::new_ecdsa_digest_message(value)
            }
            E::EcdsaPublicKey { value } => {
                let value: [u8; 33] =
                    value.try_into().map_err(|_| PyValueError::new_err("invalid public key length"))?;
                NadaValue::new_ecdsa_public_key(value)
            }
            E::StoreId { value } => {
                let value: [u8; 16] = value.try_into().map_err(|_| PyValueError::new_err("invalid store id length"))?;
                NadaValue::new_store_id(value)
            }
            E::EcdsaSignature { r, sigma } => {
                let r =
                    Scalar::from_le_bytes(r).map_err(|e| PyValueError::new_err(format!("invalid signature r: {e}")))?;
                let sigma = Scalar::from_le_bytes(sigma)
                    .map_err(|e| PyValueError::new_err(format!("invalid signature sigma: {e}")))?;
                NadaValue::new_ecdsa_signature(EcdsaSignatureShare { r, sigma })
            }
            E::EcdsaPrivateKey { i, x, shared_public_key, public_shares } => {
                let share = DirtyCoreKeyShare {
                    i,
                    key_info: DirtyKeyInfo {
                        curve: CurveName::new(),
                        shared_public_key: non_zero_point_from_bytes(&shared_public_key)?,
                        public_shares: public_shares
                            .iter()
                            .map(|s| non_zero_point_from_bytes(s))
                            .collect::<Result<_, _>>()?,
                        vss_setup: None,
                    },
                    x: non_zero_secret_scalar_from_bytes(&x)?,
                }
                .validate()
                .map_err(|e| PyValueError::new_err(e.to_string()))?;
                NadaValue::new_ecdsa_private_key(ThresholdPrivateKeyShare::new(share))
            }
            E::EddsaPrivateKey { i, x, shared_public_key, public_shares } => {
                let share = DirtyCoreKeyShare {
                    i,
                    key_info: DirtyKeyInfo {
                        curve: CurveName::new(),
                        shared_public_key: non_zero_point_from_bytes(&shared_public_key)?,
                        public_shares: public_shares
                            .iter()
                            .map(|s| non_zero_point_from_bytes(s))
                            .collect::<Result<_, _>>()?,
                        vss_setup: None,
                    },
                    x: non_zero_secret_scalar_from_bytes(&x)?,
                }
                .validate()
                .map_err(|e| PyValueError::new_err(e.to_string()))?;
                NadaValue::new_eddsa_private_key(ThresholdPrivateKeyShare::new(share))
            }
            E::EddsaPublicKey { value } => {
                let value: [u8; 32] =
                    value.try_into().map_err(|_| PyValueError::new_err("invalid public key length"))?;
                NadaValue::new_eddsa_public_key(value)
            }
            E::EddsaSignature { value } => {
                let signature = EddsaSignature::from_bytes(&value)
                    .map_err(|_| PyValueError::new_err("Failed to deserialize EdDSA signature"))?;

                NadaValue::new_eddsa_signature(signature)
            }
            E::EddsaMessage { value } => NadaValue::new_eddsa_message(value),
        };
        Ok(value)
    }
}

#[pymethods]
impl EncryptedNadaValue {
    fn __str__(&self) -> String {
        match self {
            Self::ShamirShareInteger { .. } => "ShamirShareInteger {..}".into(),
            Self::ShamirShareUnsignedInteger { .. } => "ShamirShareUnsignedInteger {..}".into(),
            Self::ShamirShareBoolean { .. } => "ShamirShareBoolean {..}".into(),
            Self::ShamirSharesBlob { original_size, .. } => {
                format!("ShamirSharesBlob({original_size})")
            }
            Self::PublicInteger { .. } => "Integer".into(),
            Self::PublicUnsignedInteger { .. } => "UnsignedInteger".into(),
            Self::PublicBoolean { .. } => "Boolean".into(),
            Self::Array { .. } => "Array {..}".into(),
            Self::Tuple { .. } => "Tuple {..}".into(),
            Self::EcdsaMessageDigest { .. } => "EcdsaMessageDigest {..}".into(),
            Self::EcdsaSignature { .. } => "EcdsaSignature".into(),
            Self::EcdsaPrivateKey { .. } => "EcdsaPrivateKey {..}".into(),
            Self::EcdsaPublicKey { .. } => "EcdsaPublicKey {..}".into(),
            Self::StoreId { .. } => "StoreId {..}".into(),
            Self::EddsaPrivateKey { .. } => "EddsaPrivateKey {..}".into(),
            Self::EddsaPublicKey { .. } => "EddsaPublicKey {..}".into(),
            Self::EddsaSignature { .. } => "EddsaSignature {..}".into(),
            Self::EddsaMessage { .. } => "EddsaMessage {..}".into(),
        }
    }
}

fn non_zero_point_from_bytes<C: Curve>(bytes: &[u8]) -> PyResult<NonZero<Point<C>>> {
    let point = Point::from_bytes(bytes).map_err(|_| PyValueError::new_err("invalid bytes"))?;
    NonZero::from_point(point).ok_or_else(|| PyValueError::new_err("point is zero"))
}

fn non_zero_secret_scalar_from_bytes<C: Curve>(bytes: &[u8]) -> PyResult<NonZero<SecretScalar<C>>> {
    let scalar = SecretScalar::from_le_bytes(bytes).map_err(|_| PyValueError::new_err("invalid bytes"))?;
    NonZero::from_secret_scalar(scalar).ok_or_else(|| PyValueError::new_err("scalar is zero"))
}

#[pyclass]
#[derive(Clone)]
pub enum EncryptedNadaType {
    Integer(),
    UnsignedInteger(),
    Boolean(),
    ShamirShareInteger(),
    ShamirShareUnsignedInteger(),
    ShamirShareBoolean(),
    ShamirShareSecretBlob(),
    Array { inner_type: Py<PyAny>, size: u64 },
    Tuple { left: Py<PyAny>, right: Py<PyAny> },
    EcdsaMessageDigest(),
    EcdsaSignature(),
    EcdsaPrivateKey(),
    EcdsaPublicKey(),
    StoreId(),
    EddsaPrivateKey(),
    EddsaPublicKey(),
    EddsaSignature(),
    EddsaMessage(),
}

impl EncryptedNadaType {
    fn new(py: Python<'_>, t: nillion_client_core::values::NadaType) -> PyResult<Self> {
        use nillion_client_core::values::NadaType as T;
        let inner_type = match t {
            T::Integer => Self::Integer(),
            T::UnsignedInteger => Self::UnsignedInteger(),
            T::Boolean => Self::Boolean(),
            T::SecretBlob => Self::ShamirShareSecretBlob(),
            T::ShamirShareInteger => Self::ShamirShareInteger(),
            T::ShamirShareUnsignedInteger => Self::ShamirShareUnsignedInteger(),
            T::ShamirShareBoolean => Self::ShamirShareBoolean(),
            T::Array { inner_type, size } => {
                Self::Array { inner_type: Self::new(py, *inner_type)?.into_py(py), size: size as u64 }
            }
            T::Tuple { left_type, right_type } => Self::Tuple {
                left: Self::new(py, *left_type)?.into_py(py),
                right: Self::new(py, *right_type)?.into_py(py),
            },
            T::EcdsaPrivateKey => Self::EcdsaPrivateKey(),
            T::EcdsaDigestMessage => Self::EcdsaMessageDigest(),
            T::EcdsaSignature => Self::EcdsaSignature(),
            T::EcdsaPublicKey => Self::EcdsaPublicKey(),
            T::StoreId => Self::StoreId(),
            T::EddsaPrivateKey => Self::EddsaPrivateKey(),
            T::EddsaPublicKey => Self::EddsaPublicKey(),
            T::EddsaSignature => Self::EddsaSignature(),
            T::EddsaMessage => Self::EddsaMessage(),
            T::SecretInteger | T::SecretUnsignedInteger | T::SecretBoolean | T::NTuple { .. } | T::Object { .. } => {
                return Err(PyValueError::new_err(format!("unsupported type: {t}",)));
            }
        };
        Ok(inner_type)
    }

    fn into_nada_type(self, py: Python<'_>) -> PyResult<nillion_client_core::values::NadaType> {
        use nillion_client_core::values::NadaType as T;
        let output = match self {
            EncryptedNadaType::Integer() => T::Integer,
            EncryptedNadaType::UnsignedInteger() => T::UnsignedInteger,
            EncryptedNadaType::Boolean() => T::Boolean,
            EncryptedNadaType::ShamirShareInteger() => T::ShamirShareInteger,
            EncryptedNadaType::ShamirShareUnsignedInteger() => T::ShamirShareUnsignedInteger,
            EncryptedNadaType::ShamirShareBoolean() => T::ShamirShareBoolean,
            EncryptedNadaType::ShamirShareSecretBlob() => T::SecretBlob,
            EncryptedNadaType::Array { inner_type, size } => {
                let inner_type = inner_type.extract::<EncryptedNadaType>(py)?;
                T::Array { inner_type: Box::new(inner_type.into_nada_type(py)?), size: size as usize }
            }
            EncryptedNadaType::Tuple { left, right } => {
                let left = left.extract::<EncryptedNadaType>(py)?;
                let right = right.extract::<EncryptedNadaType>(py)?;
                T::Tuple {
                    left_type: Box::new(left.into_nada_type(py)?),
                    right_type: Box::new(right.into_nada_type(py)?),
                }
            }
            EncryptedNadaType::EcdsaMessageDigest() => T::EcdsaDigestMessage,
            EncryptedNadaType::EcdsaSignature() => T::EcdsaSignature,
            EncryptedNadaType::EcdsaPrivateKey() => T::EcdsaPrivateKey,
            EncryptedNadaType::EcdsaPublicKey() => T::EcdsaPublicKey,
            EncryptedNadaType::StoreId() => T::StoreId,
            EncryptedNadaType::EddsaPrivateKey() => T::EddsaPrivateKey,
            EncryptedNadaType::EddsaPublicKey() => T::EddsaPublicKey,
            EncryptedNadaType::EddsaSignature() => T::EddsaSignature,
            EncryptedNadaType::EddsaMessage() => T::EddsaMessage,
        };
        Ok(output)
    }
}

#[pymethods]
impl EncryptedNadaType {
    fn __str__(&self) -> String {
        match self {
            Self::ShamirShareInteger { .. } => "ShamirShareInteger {..}".into(),
            Self::ShamirShareUnsignedInteger { .. } => "ShamirShareUnsignedInteger {..}".into(),
            Self::ShamirShareBoolean { .. } => "ShamirShareBoolean {..}".into(),
            Self::ShamirShareSecretBlob { .. } => "ShamirSharesSecretBlob {..}".into(),
            Self::Integer { .. } => "Integer".into(),
            Self::UnsignedInteger { .. } => "UnsignedInteger".into(),
            Self::Boolean { .. } => "Boolean".into(),
            Self::Array { .. } => "Array {..}".into(),
            Self::Tuple { .. } => "Tuple {..}".into(),
            Self::EcdsaMessageDigest { .. } => "EcdsaMessageDigest {..}".into(),
            Self::EcdsaSignature { .. } => "EcdsaSignature".into(),
            Self::EcdsaPrivateKey { .. } => "EcdsaPrivateKey {..}".into(),
            Self::EcdsaPublicKey { .. } => "EcdsaPublicKey {..}".into(),
            Self::StoreId { .. } => "StoreId {..}".into(),
            Self::EddsaPrivateKey { .. } => "EddsaPrivateKey {..}".into(),
            Self::EddsaPublicKey { .. } => "EddsaPublicKey {..}".into(),
            Self::EddsaSignature { .. } => "EddsaSignature {..}".into(),
            Self::EddsaMessage { .. } => "EddsaMessage {..}".into(),
        }
    }
}
