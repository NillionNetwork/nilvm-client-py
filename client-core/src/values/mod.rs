use self::{
    array::Array,
    blob::SecretBlob,
    bool::{Boolean, SecretBoolean},
    ecdsa_digest_message::EcdsaDigestMessage,
    ecdsa_private_key::EcdsaPrivateKey,
    ecdsa_public_key::EcdsaPublicKey,
    ecdsa_signature::EcdsaSignature,
    integer::{Integer, SecretInteger},
    store_id::StoreId,
    unsigned_integer::{SecretUnsignedInteger, UnsignedInteger},
};
use nillion_client_core::values::{Clear, NadaValue};
use pyo3::{exceptions::PyValueError, prelude::*, types::PyDict};
use std::collections::HashMap;

pub mod array;
pub mod blob;
pub mod bool;
pub mod ecdsa_digest_message;
pub mod ecdsa_private_key;
pub mod ecdsa_public_key;
pub mod ecdsa_signature;
pub mod integer;
pub mod store_id;
pub mod unsigned_integer;

pub(crate) fn nada_value_clear_to_pyobject(py: Python<'_>, value: NadaValue<Clear>) -> PyResult<PyObject> {
    let object = match value {
        NadaValue::Integer(value) => Integer::try_from(NadaValue::Integer(value))?.into_py(py),
        NadaValue::UnsignedInteger(value) => UnsignedInteger::try_from(NadaValue::UnsignedInteger(value))?.into_py(py),
        NadaValue::Boolean(value) => Boolean::try_from(NadaValue::Boolean(value))?.into_py(py),
        NadaValue::SecretInteger(value) => SecretInteger::try_from(NadaValue::SecretInteger(value))?.into_py(py),
        NadaValue::SecretUnsignedInteger(value) => {
            SecretUnsignedInteger::try_from(NadaValue::SecretUnsignedInteger(value))?.into_py(py)
        }
        NadaValue::SecretBoolean(value) => SecretBoolean::try_from(NadaValue::SecretBoolean(value))?.into_py(py),
        NadaValue::SecretBlob(value) => SecretBlob::try_from(NadaValue::SecretBlob(value))?.into_py(py),
        NadaValue::EcdsaPrivateKey(value) => EcdsaPrivateKey::try_from(NadaValue::EcdsaPrivateKey(value))?.into_py(py),
        NadaValue::EcdsaSignature(value) => EcdsaSignature::try_from(NadaValue::EcdsaSignature(value))?.into_py(py),
        NadaValue::EcdsaDigestMessage(value) => {
            EcdsaDigestMessage::try_from(NadaValue::EcdsaDigestMessage(value))?.into_py(py)
        }
        NadaValue::EcdsaPublicKey(value) => EcdsaPublicKey::try_from(NadaValue::EcdsaPublicKey(value))?.into_py(py),
        NadaValue::StoreId(value) => StoreId::try_from(NadaValue::StoreId(value))?.into_py(py),
        NadaValue::Array { values, inner_type } => {
            Array::try_from(NadaValue::Array { values, inner_type })?.into_py(py)
        }
        NadaValue::Tuple { .. }
        | NadaValue::NTuple { .. }
        | NadaValue::Object { .. }
        | NadaValue::ShamirShareInteger(_)
        | NadaValue::ShamirShareUnsignedInteger(_)
        | NadaValue::ShamirShareBoolean(_) => {
            Err(PyValueError::new_err("Unsupported NadaValue variant for conversion to PyObject"))?
        }
    };
    Ok(object)
}

fn pyany_to_nada_value_clear(value: Bound<PyAny>) -> Result<NadaValue<Clear>, PyErr> {
    let value = if let Ok(value) = value.extract::<Integer>() {
        value.inner
    } else if let Ok(value) = value.extract::<SecretInteger>() {
        value.inner
    } else if let Ok(value) = value.extract::<UnsignedInteger>() {
        value.inner
    } else if let Ok(value) = value.extract::<SecretUnsignedInteger>() {
        value.inner
    } else if let Ok(value) = value.extract::<Boolean>() {
        value.inner
    } else if let Ok(value) = value.extract::<SecretBoolean>() {
        value.inner
    } else if let Ok(value) = value.extract::<SecretBlob>() {
        value.inner
    } else if let Ok(value) = value.extract::<EcdsaPrivateKey>() {
        value.inner
    } else if let Ok(value) = value.extract::<EcdsaDigestMessage>() {
        value.inner
    } else if let Ok(value) = value.extract::<EcdsaPublicKey>() {
        value.inner
    } else if let Ok(value) = value.extract::<EcdsaSignature>() {
        value.inner
    } else if let Ok(value) = value.extract::<StoreId>() {
        value.inner
    } else if let Ok(value) = value.extract::<Array>() {
        value.inner
    } else {
        Err(PyValueError::new_err("Unsupported NadaValue variant for conversion to PyObject"))?
    };
    Ok(value)
}

pub(crate) fn pydict_to_nada_values_clear(values: &Bound<'_, PyDict>) -> PyResult<HashMap<String, NadaValue<Clear>>> {
    values
        .into_iter()
        .map(|(key, value)| {
            let key = key.extract::<String>()?;
            let value = pyany_to_nada_value_clear(value)?;
            Ok((key, value))
        })
        .collect::<Result<HashMap<_, _>, _>>()
}

pub fn nada_values_clear_to_pydict(
    py: Python<'_>,
    values: HashMap<String, NadaValue<Clear>>,
) -> PyResult<Bound<'_, PyDict>> {
    let res = PyDict::new_bound(py);
    for (key, value) in values {
        res.set_item(key, nada_value_clear_to_pyobject(py, value)?)?;
    }
    Ok(res)
}

pub fn add_module(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<SecretUnsignedInteger>()?;
    m.add_class::<SecretInteger>()?;
    m.add_class::<SecretBoolean>()?;
    m.add_class::<Array>()?;
    m.add_class::<SecretBlob>()?;
    m.add_class::<UnsignedInteger>()?;
    m.add_class::<Integer>()?;
    m.add_class::<Boolean>()?;
    m.add_class::<EcdsaPrivateKey>()?;
    m.add_class::<EcdsaDigestMessage>()?;
    m.add_class::<EcdsaPublicKey>()?;
    m.add_class::<EcdsaSignature>()?;
    m.add_class::<StoreId>()?;
    Ok(())
}
