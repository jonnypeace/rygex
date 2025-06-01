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
use pyo3::types::{PyIterator, PyTuple};
use std::collections::VecDeque;
use pyo3::types::PyString;
use std::io::Error as IOError;

/// A PyO3‐backed iterator that memory‐maps the given file and then yields
/// exactly one Python string each time the Rust regex finds a capture group.
/// No Python objects are created for non‐matching parts of the file, so memory
/// stays tiny when there are few matches.
///
/// Python usage:
///
///     gen = FileRegexGen("pattern", "ufw.test1")
///     for match_str in gen:
///         print(match_str)
///
/// `match_str` will be the substring of the capture (group 1 by default).
// #[pyclass]
// pub struct FileRegexGen {
//     /// The compiled Rust regex (group 1 must exist).
//     inner: RustRegex,

//     /// We keep the Mmap here so it does not get dropped/unmapped.
//     mmap: Mmap,

//     /// Leaked, `'static` string containing the entire file’s contents.
//     haystack: &'static str,

//     /// Current byte‐offset into `haystack`. We search from haystack[pos..].
//     pos: usize,
// }

#[pyclass]
pub struct FileRegexGen {
    inner:    RustRegex,    // the compiled regex (with at least one capture group)
    mmap:     Mmap,         // the OS memory‐map of the entire file (kept alive)
    haystack: &'static str, // a `'static` &str pointing directly into the mmap’s bytes
    start:    usize,        // the byte offset at which we begin searching
    end:      usize,        // the byte offset at which we must stop searching
    pos:      usize,        // the next byte offset from which we attempt to find a match
}


#[pymethods]
impl FileRegexGen {
    /// __new__(cls, pattern: str, filename: str) -> FileRegexGen
    #[new]
    fn new(pattern: &str, filename: &str) -> PyResult<Self> {
        // 1) Compile the regex
        let re = RustRegex::new(pattern)
            .map_err(|e| exceptions::PyValueError::new_err(e.to_string()))?;

        // 2) Open & mmap the file
        let file = File::open(filename)
            .map_err(|e: IOError| exceptions::PyIOError::new_err(e.to_string()))?;
        let mmap = unsafe {
            Mmap::map(&file)
                .map_err(|e| exceptions::PyIOError::new_err(e.to_string()))?
        };

        // 3) Convert to &str (error if any invalid UTF-8)
        let s: &str = std::str::from_utf8(&mmap)
            .map_err(|e| exceptions::PyUnicodeDecodeError::new_err(e.to_string()))?;

        // 4) Transmute to 'static &str
        let static_str: &'static str = unsafe { std::mem::transmute::<&str, &'static str>(s) };

        let len = static_str.len();
        Ok(FileRegexGen {
            inner:    re,
            mmap,                    // keep the mapping alive
            haystack: static_str,    // pointer to map’s UTF-8 bytes
            start:    0,             // we begin at byte 0
            end:      len,           // and end at haystack.len()
            pos:      0,             // cursor starts at 0 as well
        })
    }


    /// __iter__(self) -> self
    fn __iter__(slf: Py<FileRegexGen>) -> Py<FileRegexGen> {
        slf
    }

    /// __next__(self) -> Optional[Tuple[str, ...]]
    ///
    /// Each time this is called, we look at `haystack[pos..]`, run captures on it,
    /// build a Python tuple of (full_match, cap1, cap2, …), advance pos past the end
    /// of the full match, and return that tuple.  If no more matches remain, returns None.
    fn __next__(mut slf: PyRefMut<Self>, py: Python<'_>) -> PyResult<Option<PyObject>> {
        // 1) If pos has moved past `end`, we’re done.
        if slf.pos >= slf.end {
            return Ok(None);
        }

        // 2) Build a &str slice that only runs from pos..end
        let slice = &slf.haystack[slf.pos..slf.end];

        // 3) Attempt to find the next match in that slice
        if let Some(caps) = slf.inner.captures(slice) {
            // `caps.iter()` yields an iterator over Option<Match> for group0, group1, ...
            let mut py_items: Vec<PyObject> = Vec::new();
            for m_opt in caps.iter() {
                if let Some(mat) = m_opt {
                    // mat.as_str() is a borrowed &str for this group
                    py_items.push(PyString::new(py, mat.as_str()).to_object(py));
                } else {
                    // That group didn’t participate in this match → push None
                    py_items.push(py.None());
                }
            }

            // 4) Advance pos by the length (in bytes) of the full match (group 0)
            if let Some(m0) = caps.get(0) {
                // m0.end() is the end‐index **relative to `slice`**, so we add slf.pos
                slf.pos += m0.end();
            } else if let Some(m1) = caps.get(1) {
                // Fallback (rare): advance by group1’s end if group0 is absent
                slf.pos += m1.end();
            } else {
                // No match at all (shouldn’t happen if captures() returned Some)
                return Ok(None);
            }

            // 5) Pack all the captured strings (and Nones) into a Python tuple
            let tup = PyTuple::new(py, py_items);
            return Ok(Some(tup.to_object(py)));
        }

        // 6) If captures() returned None, we found no more matches in slice → StopIteration
        Ok(None)
    }

}


#[pyfunction]
fn from_file_range(
    py: Python<'_>,
    pattern: &str,
    filename: &str,
    start: usize,
    end: usize
) -> PyResult<FileRegexGen> {
    // 1) Compile the regex
    let re = RustRegex::new(pattern)
        .map_err(|e| exceptions::PyValueError::new_err(e.to_string()))?;

    // 2) Open & mmap the file, exactly like above
    let file = File::open(filename)
        .map_err(|e: IOError| exceptions::PyIOError::new_err(e.to_string()))?;
    let mmap = unsafe {
        Mmap::map(&file)
            .map_err(|e| exceptions::PyIOError::new_err(e.to_string()))?
    };

    // 3) Convert &[u8] → &str
    let s: &str = std::str::from_utf8(&mmap)
        .map_err(|e| exceptions::PyUnicodeDecodeError::new_err(e.to_string()))?;
    let static_str: &'static str = unsafe { std::mem::transmute::<&str, &'static str>(s) };

    // 4) Clip the user‐supplied byte offsets into [0..haystack.len()]
    let haylen = static_str.len();
    let s_off = start.min(haylen);
    let e_off = end.min(haylen);

    // 5) Initialize pos = s_off, and set start=s_off, end=e_off
    Ok(FileRegexGen {
        inner:    re,
        mmap,                     // keep the mapping alive 
        haystack: static_str,     // pointer into mapping
        start:    s_off,
        end:      e_off,
        pos:      s_off,          // we begin scanning at s_off
    })
}



/// A Python class that, when iterated, yields one Vec<Option<String>> per regex match,
/// across all the input strings supplied at construction time.
///
/// Example usage in Python:
///   it = regexgen.RustRegexGen(r"(\d+)-(\d+)", ["123-456 foo", "no match", "42-99"])
///   for match_vec in it:
///       print(match_vec[0], match_vec[1], match_vec[2])
#[pyclass]
pub struct RustRegexGen {
    inner: RustRegex,                 // the compiled Rust regex
    py_iter: Py<PyIterator>,          // Python iterator over the input strings
    pending: VecDeque<Vec<Option<String>>>, // queue of matches not yet yielded
}

#[pymethods]
impl RustRegexGen {
    #[new]
    fn new(pattern: &str, iterable: &PyAny) -> PyResult<Self> {
        let inner = RustRegex::new(pattern)
            .map_err(|e| exceptions::PyValueError::new_err(e.to_string()))?;

        let py = iterable.py();
        let py_iter = PyIterator::from_object(py, iterable).map_err(|_| {
            exceptions::PyTypeError::new_err("Second argument must be an iterable of strings")
        })?;

        Ok(RustRegexGen {
            inner,
            py_iter: py_iter.into(),
            pending: VecDeque::new(),
        })
    }

    fn __iter__(slf: Py<RustRegexGen>) -> Py<RustRegexGen> {
        slf
    }

    fn __next__(mut slf: PyRefMut<Self>) -> PyResult<Option<PyObject>> {
        // Acquire GIL once and store `py` so that we never call `slf.py()`.
        let gil = Python::acquire_gil();
        let py = gil.python();

        // 1) If there's already a queued match, pop and return it immediately.
        if let Some(group_vec) = slf.pending.pop_front() {
            // Build a Python tuple from `group_vec`.
            let py_items: Vec<PyObject> = group_vec
                .into_iter()
                .map(|opt_s| match opt_s {
                    Some(s) => s.to_object(py),
                    None => py.None(),
                })
                .collect();
            let tup = PyTuple::new(py, py_items);
            return Ok(Some(tup.to_object(py)));
        }

        // 2) Otherwise, keep pulling lines until we find a real capture or exhaust.
        loop {
            // 2a) Grab the next item from the Python iterator.
            let next_obj: PyObject = {
                // We only borrow `slf` mutably here to call `slf.py_iter.as_ref(py)`.
                let mut it_ref: &PyIterator = slf.py_iter.as_ref(py);
                match it_ref.next() {
                    Some(Ok(obj_any)) => obj_any.to_object(py),
                    Some(Err(err_py)) => {
                        // Propagate the Python exception.
                        return Err(err_py.clone_ref(py));
                    }
                    None => return Ok(None), // StopIteration
                }
            };

            // 2b) Convert that PyObject into &str (error if not a string)
            let text: &str = match next_obj.extract(py) {
                Ok(s) => s,
                Err(_) => {
                    return Err(exceptions::PyTypeError::new_err(
                        "All items in the iterable must be strings",
                    ))
                }
            };

            // 2c) Run captures_iter on `text`. Collect all capture‐groups from this line.
            let mut any_captured = false;
            let mut new_items_for_line: Vec<Vec<Option<String>>> = Vec::new();

            for caps in slf.inner.captures_iter(text) {
                any_captured = true;

                let mut group_vec: Vec<Option<String>> = Vec::new();
                for m_opt in caps.iter() {
                    group_vec.push(m_opt.map(|m| m.as_str().to_string()));
                }
                new_items_for_line.push(group_vec);
            }

            // 2d) If there was at least one capture, queue them in `pending`.
            if any_captured {
                for gv in new_items_for_line {
                    slf.pending.push_back(gv);
                }
                // Pop & return the first queued match:
                if let Some(first_match) = slf.pending.pop_front() {
                    let py_items: Vec<PyObject> = first_match
                        .into_iter()
                        .map(|opt_s| match opt_s {
                            Some(s) => s.to_object(py),
                            None => py.None(),
                        })
                        .collect();
                    let tup = PyTuple::new(py, py_items);
                    return Ok(Some(tup.to_object(py)));
                }
            }

            // 2e) If no captures on this line, loop again to fetch the next line.
            //     We never allocate any Python tuple or string here for non‐matches.
        }
    }
}





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
    m.add_function(wrap_pyfunction!(from_file_range, m)?)?;
    m.add_class::<RustRegexGen>()?;
    m.add_class::<FileRegexGen>()?;
    Ok(())
}
