use std::collections::HashMap;

use nillion_client_core::programs;
use pyo3::{exceptions::PyTypeError, prelude::*};

#[derive(Clone)]
#[pyclass]
pub struct ProgramRequirements {
    /// The map of runtime elements
    #[pyo3(get)]
    pub runtime_elements: HashMap<String, usize>,
}

#[pymethods]
impl ProgramRequirements {
    fn __repr__(&self) -> String {
        format!("ProgramRequirements(runtime_elements='{:?}')", self.runtime_elements)
    }
}

impl From<nillion_client_core::programs::MPCProgramRequirements> for ProgramRequirements {
    fn from(value: nillion_client_core::programs::MPCProgramRequirements) -> Self {
        Self {
            runtime_elements: value
                .runtime_elements()
                .iter()
                .map(|(key, value)| (key.to_string(), *value))
                .collect::<HashMap<_, _>>(),
        }
    }
}

#[pyclass]
pub struct ProgramMetadata {
    /// The program memory size
    #[pyo3(get)]
    pub memory_size: u64,
    /// The total number of instructions
    #[pyo3(get)]
    pub total_instructions: u64,
    /// The program instructions
    #[pyo3(get)]
    pub instructions: HashMap<String, u64>,
    // The program preprocessing requirements
    #[pyo3(get)]
    pub preprocessing_requirements: ProgramRequirements,
}

#[pymethods]
impl ProgramMetadata {
    fn __repr__(&self) -> String {
        format!(
            "ProgramMetadata(memory_size='{}', total_instructions='{}', instructions='{:?}', preprocessing_requirements={})",
            self.memory_size,
            self.total_instructions,
            self.instructions,
            self.preprocessing_requirements.__repr__()
        )
    }
}

impl From<nillion_client_core::programs::ProgramAuditorRequest> for ProgramMetadata {
    fn from(value: nillion_client_core::programs::ProgramAuditorRequest) -> Self {
        Self {
            memory_size: value.memory_size,
            total_instructions: value.total_instructions,
            instructions: value.instructions,
            preprocessing_requirements: value.preprocessing_requirements.into(),
        }
    }
}

#[pyfunction]
fn extract_program_metadata(program: &[u8]) -> PyResult<ProgramMetadata> {
    let result = programs::extract_program_metadata(program).map_err(|err| PyTypeError::new_err(err.to_string()))?;
    Ok(result.into())
}

pub(crate) fn add_module(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ProgramRequirements>()?;
    m.add_class::<ProgramMetadata>()?;
    m.add_function(wrap_pyfunction!(extract_program_metadata, m)?)?;
    Ok(())
}
