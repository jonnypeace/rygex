use pyo3::prelude::*;
use pyo3::exceptions;
use pyo3::wrap_pyfunction;
use pyo3::types::PyDict;
use ::regex::Regex as RustRegex;
use ::regex::bytes::Regex as RustRegexBytes;
use pyo3::buffer::PyBuffer;
use memmap2::Mmap;
use std::fs::File;
use rayon::prelude::*;


#[pyclass]
struct Regex {
    inner: RustRegex,
}

#[pymethods]
impl Regex {
    #[new]
    fn new(pattern: &str) -> PyResult<Self> {
        match RustRegex::new(pattern) {
            Ok(inner) => Ok(Regex { inner }),
            Err(e) => Err(exceptions::PyValueError::new_err(e.to_string())),
        }
    }

    /// Returns the first match in the text.
    fn search(&self, text: &str) -> Option<Match> {
        self.inner.find(text).map(|m| Match {
            start: m.start() as isize,
            end: m.end() as isize,
            group: m.as_str().to_string(),
        })
    }
}

#[pyclass]
struct Match {
    #[pyo3(get)]
    start: isize,
    #[pyo3(get)]
    end: isize,
    #[pyo3(get)]
    group: String,
}

#[pyfunction]
fn compile(pattern: &str) -> PyResult<Regex> {
    Regex::new(pattern)
}

#[pyfunction]
fn search(pattern: &str, text: &str) -> PyResult<Option<Match>> {
    let regex = Regex::new(pattern)?;
    Ok(regex.search(text))
}

/// Process a single string and return all capture groups as a list of lists.
/// Each inner list is a vector of Option<String> for group 0 (full match) and numbered groups.
#[pyfunction]
fn findall_captures_str(pattern: &str, text: &str) -> PyResult<Vec<Vec<Option<String>>>> {
    let regex = RustRegex::new(pattern)
        .map_err(|e| exceptions::PyValueError::new_err(e.to_string()))?;
    let results: Vec<Vec<Option<String>>> = regex.captures_iter(text)
        .map(|caps| {
            caps.iter().map(|m| m.map(|mat| mat.as_str().to_string())).collect()
        })
        .collect();
    Ok(results)
}


/// Single-threaded version
#[pyfunction]
fn findall_captures_list(pattern: &str, texts: Vec<&str>) -> PyResult<Vec<Vec<Vec<Option<String>>>>> {
    let regex = RustRegex::new(pattern)
        .map_err(|e| exceptions::PyValueError::new_err(e.to_string()))?;

    // Process texts sequentially
    let results: Vec<Vec<Vec<Option<String>>>> = texts
        .into_iter()
        .map(|text| {
            regex
                .captures_iter(text)
                .map(|caps| {
                    caps.iter()
                        .map(|m| m.map(|mat| mat.as_str().to_string()))
                        .collect()
                })
                .collect()
        })
        .collect();
    Ok(results)
}


/// Process a list of texts in parallel and return for each text all capture groups as a list of lists.
#[pyfunction]
fn findall_captures_list_parallel(pattern: &str, texts: Vec<&str>) -> PyResult<Vec<Vec<Vec<Option<String>>>>> {
    use rayon::prelude::*;
    let regex = RustRegex::new(pattern)
        .map_err(|e| exceptions::PyValueError::new_err(e.to_string()))?;
    let results: Vec<Vec<Vec<Option<String>>>> = texts.into_par_iter()
        .map(|text| {
            regex.captures_iter(text)
                .map(|caps| {
                    caps.iter().map(|m| m.map(|mat| mat.as_str().to_string())).collect()
                })
                .collect()
        })
        .collect();
    Ok(results)
}

/// Process a single string and return all capture groups as dictionaries with names.
/// Each dictionary contains:
///  - "full": full match,
///  - numeric keys ("1", "2", …) for numbered groups,
///  - named keys for any named capture groups.
#[pyfunction]
fn findall_captures_named_str(pattern: &str, text: &str, py: Python) -> PyResult<PyObject> {
    let regex = RustRegex::new(pattern)
        .map_err(|e| exceptions::PyValueError::new_err(e.to_string()))?;
    let mut results = Vec::new();
    // Precompute mapping from group names to their indices.
    let name_to_index: Vec<(String, usize)> = regex.capture_names()
        .enumerate()
        .filter_map(|(i, name)| name.map(|n| (n.to_string(), i)))
        .collect();
    for caps in regex.captures_iter(text) {
        let dict = PyDict::new(py);
        if let Some(m) = caps.get(0) {
            dict.set_item("full", m.as_str())?;
        }
        for i in 1..caps.len() {
            let key = i.to_string();
            let value = caps.get(i).map(|m| m.as_str());
            dict.set_item(key, value)?;
        }
        for (name, idx) in &name_to_index {
            if *idx == 0 { continue; }
            let value = caps.get(*idx).map(|m| m.as_str());
            dict.set_item(name, value)?;
        }
        results.push(dict.to_object(py));
    }
    Ok(results.to_object(py))
}

/// Process a list of texts in parallel and return for each text all capture groups as dictionaries with names.
/// Returns a nested list (one list per input text) of dictionaries (one dictionary per match).
#[pyfunction]
fn findall_captures_named_list_parallel(pattern: &str, texts: Vec<&str>, py: Python) -> PyResult<PyObject> {
    use rayon::prelude::*;
    let regex = RustRegex::new(pattern)
        .map_err(|e| exceptions::PyValueError::new_err(e.to_string()))?;
    // Precompute mapping from group names to indices.
    let name_to_index: Vec<(String, usize)> = regex.capture_names()
        .enumerate()
        .filter_map(|(i, name)| name.map(|n| (n.to_string(), i)))
        .collect();
    // Process texts in parallel, but only compute raw capture results (Vec<Vec<Option<String>>>)
    let raw_results: Vec<Vec<Vec<Option<String>>>> = texts.into_par_iter()
        .map(|text| {
            regex.captures_iter(text)
                .map(|caps| {
                    caps.iter().map(|m| m.map(|mat| mat.as_str().to_string())).collect()
                })
                .collect()
        })
        .collect();
    // Now, on the main thread (holding the GIL), convert raw results to a Vec<Vec<PyObject>>.
    let mut py_results = Vec::with_capacity(raw_results.len());
    for matches in raw_results {
        let mut text_matches = Vec::with_capacity(matches.len());
        for caps in matches {
            let dict = PyDict::new(py);
            if let Some(full_match) = caps.get(0) {
                dict.set_item("full", full_match)?;
            }
            for (i, cap) in caps.iter().enumerate().skip(1) {
                let key = i.to_string();
                dict.set_item(key, cap)?;
            }
            for (name, idx) in &name_to_index {
                if *idx == 0 { continue; }
                let value = caps.get(*idx).cloned().unwrap_or(None);
                dict.set_item(name, value)?;
            }
            text_matches.push(dict.to_object(py));
        }
        py_results.push(text_matches);
    }
    Ok(py_results.to_object(py))
}

#[pyfunction]
fn find_joined_matches_in_file_by_line_bytes_parallel(
    pattern: &str,
    file_path: &str,
    groups: Option<Vec<usize>>,
) -> PyResult<Vec<String>> {
    use rayon::prelude::*;
    use ::regex::bytes::Regex as RustRegexBytes;
    use memmap2::Mmap;
    use std::fs::File;
    use pyo3::exceptions;

    // Open the file.
    let file = File::open(file_path)
        .map_err(|e| exceptions::PyIOError::new_err(format!("Failed to open file: {}", e)))?;
    // Memory-map the file.
    let mmap = unsafe { Mmap::map(&file) }
        .map_err(|e| exceptions::PyIOError::new_err(format!("Failed to mmap file: {}", e)))?;
    let bytes = &mmap[..];

    // Split the file into lines by b'\n'
    let lines: Vec<&[u8]> = bytes.split(|&b| b == b'\n').collect();

    // Compile the regex pattern using the bytes API.
    let regex = RustRegexBytes::new(pattern)
        .map_err(|e| exceptions::PyValueError::new_err(format!("Regex compile error: {}", e)))?;

    // Process each line in parallel.
    let results: Vec<String> = lines.par_iter()
        .flat_map(|line| {
            if let Some(ref indices) = groups {
                // For each match in the line, join the specified capture groups.
                regex.captures_iter(line)
                    .map(|caps| {
                        let mut parts = Vec::new();
                        for &idx in indices {
                            if let Some(mat) = caps.get(idx) {
                                let s = String::from_utf8_lossy(mat.as_bytes()).into_owned();
                                parts.push(s);
                            }
                        }
                        parts.join(" ")
                    })
                    .collect::<Vec<String>>()
            } else {
                // If no group indices provided, return the entire line if it matches.
                if regex.is_match(line) {
                    vec![String::from_utf8_lossy(line).into_owned()]
                } else {
                    Vec::new()
                }
            }
        })
        .collect();

    Ok(results)
}


#[pyfunction]
fn find_joined_matches_in_file_by_line_bytes(
    pattern: &str,
    file_path: &str,
    groups: Option<Vec<usize>>,
) -> PyResult<Vec<String>> {
    use ::regex::bytes::Regex as RustRegexBytes;
    use memmap2::Mmap;
    use std::fs::File;
    use pyo3::exceptions;

    // Open the file.
    let file = File::open(file_path)
        .map_err(|e| exceptions::PyIOError::new_err(format!("Failed to open file: {}", e)))?;
    // Memory-map the file.
    let mmap = unsafe { Mmap::map(&file) }
        .map_err(|e| exceptions::PyIOError::new_err(format!("Failed to mmap file: {}", e)))?;
    let bytes = &mmap[..];

    // Split the file into lines by b'\n'
    let lines: Vec<&[u8]> = bytes.split(|&b| b == b'\n').collect();

    // Compile the regex pattern using the bytes API.
    let regex = RustRegexBytes::new(pattern)
        .map_err(|e| exceptions::PyValueError::new_err(format!("Regex compile error: {}", e)))?;

    let mut results = Vec::new();
    // Process each line sequentially.
    for line in lines {
        if let Some(ref indices) = groups {
            // For each match in the line, join the specified capture groups.
            for caps in regex.captures_iter(line) {
                let mut parts = Vec::new();
                for &idx in indices {
                    if let Some(mat) = caps.get(idx) {
                        let s = String::from_utf8_lossy(mat.as_bytes()).into_owned();
                        parts.push(s);
                    }
                }
                if !parts.is_empty() {
                    results.push(parts.join(" "));
                }
            }
        } else {
            // If no group indices provided, return the entire line if it matches.
            if regex.is_match(line) {
                results.push(String::from_utf8_lossy(line).into_owned());
            }
        }
    }

    Ok(results)
}



#[pyfunction]
fn find_joined_matches_in_file(
    pattern: &str,
    file_path: &str,
    groups: Option<Vec<usize>>,
) -> PyResult<Vec<String>> {
    // Open the file.
    let file = File::open(file_path)
        .map_err(|e| exceptions::PyIOError::new_err(format!("Failed to open file: {}", e)))?;
    // Memory-map the file.
    let mmap = unsafe { Mmap::map(&file) }
        .map_err(|e| exceptions::PyIOError::new_err(format!("Failed to mmap file: {}", e)))?;
    let bytes = &mmap[..];

    // Split the file by newline (b'\n') into lines (without copying).
    let lines: Vec<&[u8]> = bytes.split(|&b| b == b'\n').collect();

    // Compile the regex pattern using the bytes API.
    let regex = RustRegexBytes::new(pattern)
        .map_err(|e| exceptions::PyValueError::new_err(format!("Regex compile error: {}", e)))?;

    let mut results = Vec::new();

    // Process each line sequentially.
    for line in lines {
        if let Some(ref indices) = groups {
            // For each match in the line, join the specified capture groups.
            for caps in regex.captures_iter(line) {
                let mut parts = Vec::new();
                for &idx in indices {
                    if let Some(mat) = caps.get(idx) {
                        let s = String::from_utf8_lossy(mat.as_bytes()).into_owned();
                        parts.push(s);
                    }
                }
                // Only add if there is at least one non-empty part.
                if !parts.is_empty() {
                    results.push(parts.join(" "));
                }
            }
        } else {
            // If no group indices provided, return the entire line if it matches.
            if regex.is_match(line) {
                results.push(String::from_utf8_lossy(line).into_owned());
            }
        }
    }
    
    Ok(results)
}




#[pyfunction]
fn find_joined_matches_in_file_by_line_parallel(
    pattern: &str,
    file_path: &str,
    groups: Option<Vec<usize>>,
) -> PyResult<Vec<String>> {
    // Open the file.
    let file = File::open(file_path)
        .map_err(|e| exceptions::PyIOError::new_err(format!("Failed to open file: {}", e)))?;
    // Memory-map the file.
    let mmap = unsafe { Mmap::map(&file) }
        .map_err(|e| exceptions::PyIOError::new_err(format!("Failed to mmap file: {}", e)))?;
    let bytes = &mmap[..];

    // Split the file into lines by newline byte (b'\n') without copying.
    let lines: Vec<&[u8]> = bytes.split(|&b| b == b'\n').collect();

    // Compile the regex pattern using the bytes API.
    let regex = RustRegexBytes::new(pattern)
        .map_err(|e| exceptions::PyValueError::new_err(format!("Regex compile error: {}", e)))?;

    // Process each line in parallel.
    // If groups is provided, for each match in the line join the specified groups.
    // If groups is None, then if the line matches the regex, return the entire line.
    let results: Vec<String> = lines.par_iter()
        .flat_map(|line| {
            if let Some(ref indices) = groups {
                // If specific capture groups are requested, run the regex and join them.
                regex.captures_iter(line)
                    .map(|caps| {
                        let mut parts = Vec::new();
                        for &idx in indices {
                            if let Some(mat) = caps.get(idx) {
                                let s = String::from_utf8_lossy(mat.as_bytes()).into_owned();
                                parts.push(s);
                            }
                        }
                        parts.join(" ")
                    })
                    .collect::<Vec<String>>()
            } else {
                // If no capture groups are specified, check if the line matches.
                if regex.is_match(line) {
                    // Return the entire line (decoded from UTF-8).
                    vec![String::from_utf8_lossy(line).into_owned()]
                } else {
                    Vec::new()
                }
            }
        })
        .collect();

    Ok(results)
}



#[pymodule]
fn pygrep_ext(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Regex>()?;
    m.add_class::<Match>()?;
    m.add_function(wrap_pyfunction!(compile, m)?)?;
    m.add_function(wrap_pyfunction!(search, m)?)?;
    m.add_function(wrap_pyfunction!(findall_captures_str, m)?)?;
    m.add_function(wrap_pyfunction!(findall_captures_list_parallel, m)?)?;
    m.add_function(wrap_pyfunction!(findall_captures_list, m)?)?;
    m.add_function(wrap_pyfunction!(findall_captures_named_str, m)?)?;
    m.add_function(wrap_pyfunction!(findall_captures_named_list_parallel, m)?)?;
    m.add_function(wrap_pyfunction!(find_joined_matches_in_file_by_line_bytes, m)?)?;
    m.add_function(wrap_pyfunction!(find_joined_matches_in_file_by_line_bytes_parallel, m)?)?;
    m.add_function(wrap_pyfunction!(find_joined_matches_in_file, m)?)?;
    m.add_function(wrap_pyfunction!(find_joined_matches_in_file_by_line_parallel, m)?)?;
    Ok(())
}
