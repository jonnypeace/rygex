use pyo3::prelude::*;
use pyo3::exceptions;
use pyo3::wrap_pyfunction;
use pyo3::types::PyDict;
use ::regex::Regex as RustRegex;
use ::regex::bytes::Regex as RustRegexBytes;
use memmap2::Mmap;
use std::fs::File;
use rayon::prelude::*;
use std::collections::HashMap;
use pyo3::exceptions::PyIOError;
use memchr::memmem::Finder;
use pyo3::exceptions::PyValueError;

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


fn compute_ranges(data: &[u8], n_threads: usize, target_chunks_per_thread: usize) 
    -> Vec<(usize, usize)> 
{
    let size = data.len();
    let total_chunks = (n_threads * target_chunks_per_thread).max(1);
    let mut ranges = Vec::with_capacity(total_chunks);
    let mut start = 0;
    let chunk_bytes = (size + total_chunks - 1) / total_chunks;

    while start < size {
        let mut end = (start + chunk_bytes).min(size);
        // advance to next newline
        while end < size && data[end] != b'\n' {
            end += 1;
        }
        if end < size { end += 1; } // include the '\n'
        ranges.push((start, end));
        start = end;
    }
    ranges
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

    // // Split the file into lines by newline byte (b'\n') without copying.
    // let lines: Vec<&[u8]> = bytes.split(|&b| b == b'\n').collect();

    // Compile the regex pattern using the bytes API.
    let regex = RustRegexBytes::new(pattern)
        .map_err(|e| exceptions::PyValueError::new_err(format!("Regex compile error: {}", e)))?;

    // Process each line in parallel.
    // If groups is provided, for each match in the line join the specified groups.
    // If groups is None, then if the line matches the regex, return the entire line.
    let data: &[u8] = &mmap;
    let ranges = compute_ranges(data, rayon::current_num_threads(), 4);

    let results: Vec<String> = ranges.par_iter()
        .flat_map(|&(s,e)| {
            let slice = &data[s..e];
            if let Some(ref indices) = groups {
                regex.captures_iter(slice)
                    .map(|caps| {
                        indices.iter()
                            .filter_map(|&idx| caps.get(idx))
                            .map(|m| String::from_utf8_lossy(m.as_bytes()))
                            .collect::<Vec<_>>()
                            .join(" ")
                    })
                    .collect::<Vec<_>>()
            } else {
                // split the chunk into lines, test each line
                slice.split(|&b| b == b'\n')
                    .filter_map(|slice| {
                        if regex.is_match(slice) {
                            // emit exactly that one matching slice
                            Some(String::from_utf8_lossy(slice).into_owned())
                        } else {
                            None
                        }
                    })
                    .collect::<Vec<String>>()
            }
        })
        .collect();


    Ok(results)
}


/// find the nth occurrence of `needle` in `haystack`
fn nth_index(haystack: &str, needle: &str, n: usize) -> Option<usize> {
    let mut pos = 0;
    for _ in 0..n {
        match haystack[pos..].find(needle) {
            Some(i) => pos += i + needle.len(),
            None    => return None,
        }
    }
    Some(pos - needle.len())
}

#[pyfunction]
#[pyo3(signature = (
    file_path,
    start_delim,
    start_index      = 1,
    end_delim        = None,
    end_index        = 1,
    omit_first       = None,
    omit_last        = None,
    print_line_on_match = false,
    case_insensitive = false
))]
fn extract_fixed_spans(
    file_path: &str,
    start_delim: &str,
    start_index: usize,
    end_delim: Option<&str>,
    end_index: usize,
    omit_first: Option<usize>,
    omit_last: Option<usize>,
    print_line_on_match: bool,
    case_insensitive: bool,
) -> PyResult<Vec<String>> {
    let file = File::open(file_path).map_err(|e| PyIOError::new_err(e.to_string()))?;
    let mmap = unsafe { Mmap::map(&file).map_err(|e| PyIOError::new_err(e.to_string()))? };

    let s_key = if case_insensitive {
        start_delim.to_ascii_lowercase()
    } else {
        start_delim.to_string()
    };
    let e_key = end_delim.map(|ed| {
        if case_insensitive { ed.to_ascii_lowercase() } else { ed.to_string() }
    });

    // simple: 0 when None, or whatever Python handed over
    let omit_f = omit_first.unwrap_or(0);
    let omit_l = omit_last.unwrap_or(0);

    let mut out = Vec::new();
    for chunk in mmap.split(|&b| b == b'\n') {
        let line = std::str::from_utf8(chunk).unwrap_or("");
        let hay  = if case_insensitive {
            line.to_ascii_lowercase()
        } else {
            line.to_string()
        };

        if let Some(s_pos) = nth_index(&hay, &s_key, start_index) {
            if let Some(ref ed) = e_key {
                if let Some(e_start) = nth_index(&hay, ed, end_index) {
                    let e_pos = e_start + ed.len();
                    if e_pos > s_pos {
                        let mut slice = &line[s_pos .. e_pos];
                        // strip exactly omit_f / omit_l
                        if omit_f < slice.len() { slice = &slice[omit_f ..]; }
                        if omit_l < slice.len() {
                            slice = &slice[.. slice.len() - omit_l];
                        }
                        out.push(slice.to_string());
                        continue;
                    }
                }
            } else if print_line_on_match {
                out.push(line.to_string());
                continue;
            }
        }
    }
    Ok(out)
}

#[pyfunction]
#[pyo3(signature = (
    file_path,
    start_delim,
    start_index      = 1,
    end_delim        = None,
    end_index        = 1,
    omit_first       = None,
    omit_last        = None,
    print_line_on_match = false,
    case_insensitive = false
))]
fn extract_fixed_spans_parallel(
    file_path: &str,
    start_delim: &str,
    start_index: usize,
    end_delim: Option<&str>,
    end_index: usize,
    omit_first: Option<usize>,
    omit_last: Option<usize>,
    print_line_on_match: bool,
    case_insensitive: bool,
) -> PyResult<Vec<String>> {
    // memory-map the file
    let file = File::open(file_path)
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
    let mmap = unsafe {
        Mmap::map(&file)
            .map_err(|e| PyIOError::new_err(e.to_string()))?
    };
    let data = &mmap[..];

    // normalize delimiters
    let s_key = if case_insensitive {
        start_delim.to_ascii_lowercase()
    } else {
        start_delim.to_string()
    };
    let e_key = end_delim.map(|ed| {
        if case_insensitive { ed.to_ascii_lowercase() } else { ed.to_string() }
    });

    let omit_f = omit_first.unwrap_or(0);
    let omit_l = omit_last.unwrap_or(0);

    // determine number of threads
    let threads = rayon::current_num_threads();

    // compute newline-aligned ranges (1 chunk per thread)
    let ranges = compute_ranges(data, threads, 1);

    // process each range in parallel
    let results: Vec<String> = ranges
        .into_par_iter()
        .flat_map(|(start, end)| {
            let slice = &data[start..end];
            slice
                .split(|&b| b == b'\n')
                .filter_map(|chunk| {
                    let line = std::str::from_utf8(chunk).unwrap_or("");
                    let hay = if case_insensitive {
                        line.to_ascii_lowercase()
                    } else {
                        line.to_string()
                    };

                    nth_index(&hay, &s_key, start_index).and_then(|s_pos| {
                        if let Some(ref ed) = e_key {
                            nth_index(&hay, ed, end_index).and_then(|e_start| {
                                let e_pos = e_start + ed.len();
                                if e_pos > s_pos {
                                    let mut matched = &line[s_pos..e_pos];
                                    if omit_f < matched.len() {
                                        matched = &matched[omit_f..];
                                    }
                                    if omit_l < matched.len() {
                                        matched = &matched[..matched.len() - omit_l];
                                    }
                                    Some(matched.to_string())
                                } else {
                                    None
                                }
                            })
                        } else if print_line_on_match {
                            Some(line.to_string())
                        } else {
                            None
                        }
                    })
                })
                .collect::<Vec<_>>()
        })
        .collect();

    Ok(results)
}



/// Standalone counter: takes a Vec<String>, returns Vec<(String, usize)> sorted desc.
#[pyfunction]
fn count_string_occurrences(items: Vec<String>) -> PyResult<Vec<(String, usize)>> {
    let mut map = HashMap::new();
    for s in items {
        *map.entry(s).or_insert(0) += 1;
    }
    let mut sorted: Vec<_> = map.into_iter().collect();
    sorted.sort_unstable_by(|a, b| b.1.cmp(&a.1));
    Ok(sorted)
}


// Single‐threaded fixed‐string → full‐line extractor
#[pyfunction]
#[pyo3(signature=(
    file_path,
    pattern,
    case_insensitive = false
))]
fn extract_fixed_lines(
    file_path: &str,
    pattern: &str,
    case_insensitive: bool,
) -> PyResult<Vec<String>> {
    let file = File::open(file_path)
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
    let mmap = unsafe { Mmap::map(&file).map_err(|e| PyIOError::new_err(e.to_string()))? };

    // Precompute the finder on the pattern (lowercased if needed)
    let pat_bytes = if case_insensitive {
        pattern.to_ascii_lowercase().into_bytes()
    } else {
        pattern.as_bytes().to_vec()
    };
    let finder = Finder::new(&pat_bytes);

    let mut out = Vec::new();
    for chunk in mmap.split(|&b| b == b'\n') {
        if case_insensitive {
            // only allocate lowercase when needed
            let hay = String::from_utf8_lossy(chunk).to_ascii_lowercase();
            if finder.find(hay.as_bytes()).is_some() {
                out.push(String::from_utf8_lossy(chunk).into_owned());
            }
        } else {
            // zero allocation: search raw bytes
            if finder.find(chunk).is_some() {
                // only now convert to UTF-8 string once
                out.push(std::str::from_utf8(chunk).unwrap_or("").to_string());
            }
        }
    }
    Ok(out)
}

// Parallel fixed‐string → full‐line extractor (same logic)
#[pyfunction]
#[pyo3(signature=(
    file_path,
    pattern,
    case_insensitive = false
))]
fn extract_fixed_lines_parallel(
    file_path: &str,
    pattern: &str,
    case_insensitive: bool,
) -> PyResult<Vec<String>> {
    // 1) Open & mmap the file
    let file = File::open(file_path)
        .map_err(|e| PyIOError::new_err(format!("Failed to open file: {}", e)))?;
    let mmap = unsafe {
        Mmap::map(&file)
            .map_err(|e| PyIOError::new_err(format!("Failed to mmap file: {}", e)))?
    };
    let data: &[u8] = &mmap;

    // 2) Prepare the Finder (byte-based)
    let pat_bytes = if case_insensitive {
        pattern.to_ascii_lowercase().into_bytes()
    } else {
        pattern.as_bytes().to_vec()
    };
    let finder = Finder::new(&pat_bytes);

    // 3) Compute balanced, newline-aligned ranges
    let n_threads = rayon::current_num_threads();
    let ranges = compute_ranges(data, n_threads, 4);

    // 4) Parallel extract matching lines
    let results: Vec<String> = ranges.par_iter()
        .flat_map(|&(start, end)| {
            // For each chunk, split into individual lines
            let slice = &data[start..end];
            slice.split(|&b| b == b'\n')
                 .filter_map(|line| {
                     if line.is_empty() {
                         return None;
                     }

                     // For case-insensitive, lowercase the line before searching
                     let hay = if case_insensitive {
                         // decode lossily, lowercase, re-encode as bytes
                         String::from_utf8_lossy(line)
                             .to_ascii_lowercase()
                             .into_bytes()
                     } else {
                         line.to_vec()
                     };

                     // If found, return the original line as a String
                     if finder.find(&hay).is_some() {
                         // decode original (not lowercased) line for output
                         Some(String::from_utf8_lossy(line).into_owned())
                     } else {
                         None
                     }
                 })
                 .collect::<Vec<String>>()
        })
        .collect();

    Ok(results)
}


/// Count total number of matches (across all lines) for the given regex.
/// Returns a one‐element Vec<String> containing the numeric total.
#[pyfunction]
fn total_count(
    pattern: &str,
    file_path: &str,
    parallel: bool,
) -> PyResult<Vec<String>> {
    // Open & mmap
    let file = File::open(file_path)
        .map_err(|e| PyIOError::new_err(format!("open error: {}", e)))?;
    let mmap = unsafe {
        Mmap::map(&file)
            .map_err(|e| PyIOError::new_err(format!("mmap error: {}", e)))?
    };
    let data: &[u8] = &mmap;

    // Compile regex (UTF-8 API)
    let regex = RustRegex::new(pattern)
        .map_err(|e| PyValueError::new_err(format!("regex error: {}", e)))?;

    // Compute chunks (4 per thread)
    let n_threads = rayon::current_num_threads();
    let ranges = compute_ranges(data, n_threads, 4);

    // Count matches across chunks
    let total: usize = if parallel {
        ranges.par_iter()
            .map(|&(s, e)| {
                let slice = &data[s..e];
                // SAFETY: slicing at newline boundaries; any invalid UTF-8 yields 0 matches
                let text = std::str::from_utf8(slice).unwrap_or("");
                regex.find_iter(text).count()
            })
            .sum()
    } else {
        ranges.iter()
            .map(|&(s, e)| {
                let slice = &data[s..e];
                let text = std::str::from_utf8(slice).unwrap_or("");
                regex.find_iter(text).count()
            })
            .sum()
    };

    Ok(vec![ total.to_string() ])
}

#[pyfunction]
fn total_count_fixed_str(
    pattern: &str,
    file_path: &str,
    parallel: bool,
    case_insensitive: bool,
) -> PyResult<Vec<String>> {
    // Open & mmap file
    let file = File::open(file_path)
        .map_err(|e| PyIOError::new_err(format!("Failed to open file: {}", e)))?;
    let mmap = unsafe {
        Mmap::map(&file)
            .map_err(|e| PyIOError::new_err(format!("Failed to mmap file: {}", e)))?
    };
    let data: &[u8] = &mmap;

    // Prepare byte-pattern (lowercased if needed)
    let pat_bytes = if case_insensitive {
        pattern.to_ascii_lowercase().into_bytes()
    } else {
        pattern.as_bytes().to_vec()
    };
    let finder = Finder::new(&pat_bytes);

    // Compute balanced, newline-aligned ranges
    let n_threads = rayon::current_num_threads();
    let ranges = compute_ranges(data, n_threads, 4);

    // Count matches per chunk
    let total: usize = if parallel {
        ranges.par_iter()
            .map(|&(s, e)| {
                let slice = &data[s..e];
                // For case-insensitive, lowercase the slice first
                if case_insensitive {
                    let lower = slice.iter()
                        .map(|&b| (b as char).to_ascii_lowercase() as u8)
                        .collect::<Vec<u8>>();
                    finder.find_iter(&lower).count()
                } else {
                    finder.find_iter(slice).count()
                }
            })
            .sum()
    } else {
        ranges.iter()
            .map(|&(s, e)| {
                let slice = &data[s..e];
                if case_insensitive {
                    let lower = slice.iter()
                        .map(|&b| (b as char).to_ascii_lowercase() as u8)
                        .collect::<Vec<u8>>();
                    finder.find_iter(&lower).count()
                } else {
                    finder.find_iter(slice).count()
                }
            })
            .sum()
    };

    Ok(vec![ total.to_string() ])
}



#[pymodule]
fn rygex_ext(_py: Python, m: &PyModule) -> PyResult<()> {
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
    m.add_function(wrap_pyfunction!(extract_fixed_spans, m)?)?;
    m.add_function(wrap_pyfunction!(extract_fixed_spans_parallel, m)?)?;
    m.add_function(wrap_pyfunction!(count_string_occurrences, m)?)?;
    m.add_function(wrap_pyfunction!(extract_fixed_lines, m)?)?;
    m.add_function(wrap_pyfunction!(extract_fixed_lines_parallel, m)?)?;
    m.add_function(wrap_pyfunction!(total_count, m)?)?;
    m.add_function(wrap_pyfunction!(total_count_fixed_str, m)?)?;
    Ok(())
}
