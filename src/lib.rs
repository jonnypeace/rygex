use pyo3::prelude::*;
use pyo3::exceptions::{PyIOError, PyValueError, PyUnicodeDecodeError, PyTypeError};
use pyo3::types::{PyDict, PyModule, PyString, PyTuple, PyIterator, PyList};
use ::regex::Regex as RustRegex;
use ::regex::bytes::Regex as RustRegexBytes;
use memmap2::Mmap;
use std::fs::File;
use rayon::prelude::*;
use std::collections::{HashMap, VecDeque};
use memchr::memmem::Finder;
use std::io::Error as IOError;

#[pyclass]
pub struct FileRegexGen {
    inner: RustRegex,
    mmap: Mmap,
    haystack: &'static str,
    start: usize,
    end: usize,
    pos: usize,
}

#[pymethods]
impl FileRegexGen {
    #[new]
    fn new(pattern: &str, filename: &str) -> PyResult<Self> {
        let re = RustRegex::new(pattern)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        let file = File::open(filename)
            .map_err(|e: IOError| PyIOError::new_err(e.to_string()))?;
        let mmap = unsafe {
            Mmap::map(&file)
                .map_err(|e| PyIOError::new_err(e.to_string()))?
        };
        let s: &str = std::str::from_utf8(&mmap)
            .map_err(|e| PyUnicodeDecodeError::new_err(e.to_string()))?;
        let static_str: &'static str = unsafe { std::mem::transmute::<&str, &'static str>(s) };
        let len = static_str.len();
        Ok(FileRegexGen {
            inner: re,
            mmap,
            haystack: static_str,
            start: 0,
            end: len,
            pos: 0,
        })
    }

    fn __iter__(slf: Py<FileRegexGen>) -> Py<FileRegexGen> {
        slf
    }

    fn __next__<'py>(mut slf: PyRefMut<'_, Self>, py: Python<'py>) -> PyResult<Option<Bound<'py, PyTuple>>> {
        if slf.pos >= slf.end {
            return Ok(None);
        }
        let slice = &slf.haystack[slf.pos..slf.end];
        if let Some(caps) = slf.inner.captures(slice) {
            let mut py_items = Vec::new();
            for m_opt in caps.iter() {
                if let Some(mat) = m_opt {
                    py_items.push(PyString::new(py, mat.as_str()).into_any());
                } else {
                    py_items.push(py.None().into_bound(py).into_any());
                }
            }
            if let Some(m0) = caps.get(0) {
                slf.pos += m0.end();
            } else if let Some(m1) = caps.get(1) {
                slf.pos += m1.end();
            } else {
                return Ok(None);
            }
            let tup = PyTuple::new(py, py_items)?;
            return Ok(Some(tup));
        }
        Ok(None)
    }
}

#[pyfunction]
fn from_file_range(
    pattern: &str,
    filename: &str,
    start: usize,
    end: usize
) -> PyResult<FileRegexGen> {
    let re = RustRegex::new(pattern)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let file = File::open(filename)
        .map_err(|e: IOError| PyIOError::new_err(e.to_string()))?;
    let mmap = unsafe {
        Mmap::map(&file)
            .map_err(|e| PyIOError::new_err(e.to_string()))?
    };
    let s: &str = std::str::from_utf8(&mmap)
        .map_err(|e| PyUnicodeDecodeError::new_err(e.to_string()))?;
    let static_str: &'static str = unsafe { std::mem::transmute::<&str, &'static str>(s) };
    let haylen = static_str.len();
    let s_off = start.min(haylen);
    let e_off = end.min(haylen);
    Ok(FileRegexGen {
        inner: re,
        mmap,
        haystack: static_str,
        start: s_off,
        end: e_off,
        pos: s_off,
    })
}

#[pyclass]
pub struct RustRegexGen {
    inner: RustRegex,
    py_iter: Py<PyIterator>,
    pending: VecDeque<Vec<Option<String>>>,
}

#[pymethods]
impl RustRegexGen {
    #[new]
    fn new(pattern: &str, iterable: Bound<'_, PyAny>) -> PyResult<Self> {
        let inner = RustRegex::new(pattern)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        
        let py_iter = iterable.try_iter().map_err(|_| {
            PyTypeError::new_err("Second argument must be an iterable")
        })?;

        Ok(RustRegexGen {
            inner,
            py_iter: py_iter.unbind(),
            pending: VecDeque::new(),
        })
    }

    fn __iter__(slf: Py<RustRegexGen>) -> Py<RustRegexGen> {
        slf
    }

    fn __next__<'py>(mut slf: PyRefMut<'_, Self>, py: Python<'py>) -> PyResult<Option<Bound<'py, PyTuple>>> {
        // 1) If there's already a queued match, return it.
        if let Some(group_vec) = slf.pending.pop_front() {
            let mut py_items = Vec::new();
            for opt_s in group_vec {
                match opt_s {
                    Some(s) => py_items.push(PyString::new(py, &s).into_any()),
                    None => py_items.push(py.None().into_bound(py).into_any()),
                }
            }
            return Ok(Some(PyTuple::new(py, py_items)?));
        }

        // 2) Keep pulling lines until we find a match or exhaust.
        // We clone the iterator handle to avoid a borrow conflict with slf.pending
        let it_handle = slf.py_iter.clone_ref(py);
        let mut it_bound = it_handle.into_bound(py);

        loop {
            let next_obj = match it_bound.next() {
                Some(Ok(obj)) => obj,
                Some(Err(e)) => return Err(e),
                None => return Ok(None),
            };

            let text: String = next_obj.extract()?;
            let mut any_captured = false;
            let mut new_items_for_line = Vec::new();

            for caps in slf.inner.captures_iter(&text) {
                any_captured = true;
                let mut group_vec = Vec::new();
                for m_opt in caps.iter() {
                    group_vec.push(m_opt.map(|m| m.as_str().to_string()));
                }
                new_items_for_line.push(group_vec);
            }

            if any_captured {
                for gv in new_items_for_line {
                    slf.pending.push_back(gv);
                }
                
                if let Some(first_match) = slf.pending.pop_front() {
                    let mut py_items = Vec::new();
                    for opt_s in first_match {
                        match opt_s {
                            Some(s) => py_items.push(PyString::new(py, &s).into_any()),
                            None => py_items.push(py.None().into_bound(py).into_any()),
                        }
                    }
                    return Ok(Some(PyTuple::new(py, py_items)?));
                }
            }
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
            Err(e) => Err(PyValueError::new_err(e.to_string())),
        }
    }

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

#[pyfunction]
fn findall_captures_str(pattern: &str, text: &str) -> PyResult<Vec<Vec<Option<String>>>> {
    let regex = RustRegex::new(pattern)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let results: Vec<Vec<Option<String>>> = regex.captures_iter(text)
        .map(|caps| {
            caps.iter().map(|m| m.map(|mat| mat.as_str().to_string())).collect()
        })
        .collect();
    Ok(results)
}

#[pyfunction]
fn findall_captures_list(pattern: &str, texts: Vec<String>) -> PyResult<Vec<Vec<Vec<Option<String>>>>> {
    let regex = RustRegex::new(pattern)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let results: Vec<Vec<Vec<Option<String>>>> = texts
        .into_iter()
        .map(|text| {
            regex.captures_iter(&text)
                .map(|caps| {
                    caps.iter().map(|m| m.map(|mat| mat.as_str().to_string())).collect()
                })
                .collect()
        })
        .collect();
    Ok(results)
}

#[pyfunction]
fn findall_captures_list_parallel(pattern: &str, texts: Vec<String>) -> PyResult<Vec<Vec<Vec<Option<String>>>>> {
    let regex = RustRegex::new(pattern)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let results: Vec<Vec<Vec<Option<String>>>> = texts.into_par_iter()
        .map(|text| {
            regex.captures_iter(&text)
                .map(|caps| {
                    caps.iter().map(|m| m.map(|mat| mat.as_str().to_string())).collect()
                })
                .collect()
        })
        .collect();
    Ok(results)
}

#[pyfunction]
fn findall_captures_named_str<'py>(pattern: &str, text: &str, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
    let regex = RustRegex::new(pattern)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let results = PyList::empty(py);
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
        results.append(dict)?;
    }
    Ok(results)
}

#[pyfunction]
fn findall_captures_named_list_parallel<'py>(pattern: &str, texts: Vec<String>, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
    let regex = RustRegex::new(pattern)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let name_to_index: Vec<(String, usize)> = regex.capture_names()
        .enumerate()
        .filter_map(|(i, name)| name.map(|n| (n.to_string(), i)))
        .collect();

    let raw_results: Vec<Vec<Vec<Option<String>>>> = texts.into_par_iter()
        .map(|text| {
            regex.captures_iter(&text)
                .map(|caps| {
                    caps.iter().map(|m| m.map(|mat| mat.as_str().to_string())).collect()
                })
                .collect()
        })
        .collect();

    let py_results = PyList::empty(py);
    for matches in raw_results {
        let text_matches = PyList::empty(py);
        for caps in matches {
            let dict = PyDict::new(py);
            if let Some(full_match) = caps.get(0).and_then(|x| x.as_ref()) {
                dict.set_item("full", full_match)?;
            }
            for (i, cap) in caps.iter().enumerate().skip(1) {
                let key = i.to_string();
                dict.set_item(key, cap)?;
            }
            for (name, idx) in &name_to_index {
                if *idx == 0 { continue; }
                let value = caps.get(*idx).cloned().flatten();
                dict.set_item(name, value)?;
            }
            text_matches.append(dict)?;
        }
        py_results.append(text_matches)?;
    }
    Ok(py_results)
}

#[pyfunction]
fn find_joined_matches_in_file_by_line_bytes_parallel(
    pattern: &str,
    file_path: &str,
    groups: Option<Vec<usize>>,
) -> PyResult<Vec<String>> {
    let file = File::open(file_path)
        .map_err(|e| PyIOError::new_err(format!("Failed to open file: {}", e)))?;
    let mmap = unsafe { Mmap::map(&file) }
        .map_err(|e| PyIOError::new_err(format!("Failed to mmap file: {}", e)))?;
    let bytes = &mmap[..];
    let lines: Vec<&[u8]> = bytes.split(|&b| b == b'\n').collect();
    let regex = RustRegexBytes::new(pattern)
        .map_err(|e| PyValueError::new_err(format!("Regex compile error: {}", e)))?;
    let results: Vec<String> = lines.par_iter()
        .flat_map(|line| {
            if let Some(ref indices) = groups {
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
    let file = File::open(file_path)
        .map_err(|e| PyIOError::new_err(format!("Failed to open file: {}", e)))?;
    let mmap = unsafe { Mmap::map(&file) }
        .map_err(|e| PyIOError::new_err(format!("Failed to mmap file: {}", e)))?;
    let bytes = &mmap[..];
    let lines: Vec<&[u8]> = bytes.split(|&b| b == b'\n').collect();
    let regex = RustRegexBytes::new(pattern)
        .map_err(|e| PyValueError::new_err(format!("Regex compile error: {}", e)))?;
    let mut results = Vec::new();
    for line in lines {
        if let Some(ref indices) = groups {
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
    let file = File::open(file_path)
        .map_err(|e| PyIOError::new_err(format!("Failed to open file: {}", e)))?;
    let mmap = unsafe { Mmap::map(&file) }
        .map_err(|e| PyIOError::new_err(format!("Failed to mmap file: {}", e)))?;
    let bytes = &mmap[..];
    let lines: Vec<&[u8]> = bytes.split(|&b| b == b'\n').collect();
    let regex = RustRegexBytes::new(pattern)
        .map_err(|e| PyValueError::new_err(format!("Regex compile error: {}", e)))?;
    let mut results = Vec::new();
    for line in lines {
        if let Some(ref indices) = groups {
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
        while end < size && data[end] != b'\n' {
            end += 1;
        }
        if end < size { end += 1; }
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
    let file = File::open(file_path)
        .map_err(|e| PyIOError::new_err(format!("Failed to open file: {}", e)))?;
    let mmap = unsafe { Mmap::map(&file) }
        .map_err(|e| PyIOError::new_err(format!("Failed to mmap file: {}", e)))?;
    let regex = RustRegexBytes::new(pattern)
        .map_err(|e| PyValueError::new_err(format!("Regex compile error: {}", e)))?;
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
                slice.split(|&b| b == b'\n')
                    .filter_map(|slice| {
                        if regex.is_match(slice) {
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
    let file = File::open(file_path)
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
    let mmap = unsafe {
        Mmap::map(&file)
            .map_err(|e| PyIOError::new_err(e.to_string()))?
    };
    let data = &mmap[..];
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
    let threads = rayon::current_num_threads();
    let ranges = compute_ranges(data, threads, 1);
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
    let pat_bytes = if case_insensitive {
        pattern.to_ascii_lowercase().into_bytes()
    } else {
        pattern.as_bytes().to_vec()
    };
    let finder = Finder::new(&pat_bytes);
    let mut out = Vec::new();
    for chunk in mmap.split(|&b| b == b'\n') {
        if case_insensitive {
            let hay = String::from_utf8_lossy(chunk).to_ascii_lowercase();
            if finder.find(hay.as_bytes()).is_some() {
                out.push(String::from_utf8_lossy(chunk).into_owned());
            }
        } else {
            if finder.find(chunk).is_some() {
                out.push(std::str::from_utf8(chunk).unwrap_or("").to_string());
            }
        }
    }
    Ok(out)
}

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
    let file = File::open(file_path)
        .map_err(|e| PyIOError::new_err(format!("Failed to open file: {}", e)))?;
    let mmap = unsafe {
        Mmap::map(&file)
            .map_err(|e| PyIOError::new_err(format!("Failed to mmap file: {}", e)))?
    };
    let data: &[u8] = &mmap;
    let pat_bytes = if case_insensitive {
        pattern.to_ascii_lowercase().into_bytes()
    } else {
        pattern.as_bytes().to_vec()
    };
    let finder = Finder::new(&pat_bytes);
    let n_threads = rayon::current_num_threads();
    let ranges = compute_ranges(data, n_threads, 4);
    let results: Vec<String> = ranges.par_iter()
        .flat_map(|&(start, end)| {
            let slice = &data[start..end];
            slice.split(|&b| b == b'\n')
                 .filter_map(|line| {
                     if line.is_empty() {
                         return None;
                     }
                     let hay = if case_insensitive {
                         String::from_utf8_lossy(line)
                             .to_ascii_lowercase()
                             .into_bytes()
                     } else {
                         line.to_vec()
                     };
                     if finder.find(&hay).is_some() {
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

#[pyfunction]
fn total_count(
    pattern: &str,
    file_path: &str,
    parallel: bool,
) -> PyResult<Vec<String>> {
    let file = File::open(file_path)
        .map_err(|e| PyIOError::new_err(format!("open error: {}", e)))?;
    let mmap = unsafe {
        Mmap::map(&file)
            .map_err(|e| PyIOError::new_err(format!("mmap error: {}", e)))?
    };
    let data: &[u8] = &mmap;
    let regex = RustRegex::new(pattern)
        .map_err(|e| PyValueError::new_err(format!("regex error: {}", e)))?;
    let n_threads = rayon::current_num_threads();
    let ranges = compute_ranges(data, n_threads, 4);
    let total: usize = if parallel {
        ranges.par_iter()
            .map(|&(s, e)| {
                let slice = &data[s..e];
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
    let file = File::open(file_path)
        .map_err(|e| PyIOError::new_err(format!("Failed to open file: {}", e)))?;
    let mmap = unsafe {
        Mmap::map(&file)
            .map_err(|e| PyIOError::new_err(format!("Failed to mmap file: {}", e)))?
    };
    let data: &[u8] = &mmap;
    let pat_bytes = if case_insensitive {
        pattern.to_ascii_lowercase().into_bytes()
    } else {
        pattern.as_bytes().to_vec()
    };
    let finder = Finder::new(&pat_bytes);
    let n_threads = rayon::current_num_threads();
    let ranges = compute_ranges(data, n_threads, 4);
    let total: usize = if parallel {
        ranges.par_iter()
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
fn rygex_ext(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Regex>()?;
    m.add_class::<Match>()?;
    m.add_class::<RustRegexGen>()?;
    m.add_class::<FileRegexGen>()?;
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
    Ok(())
}