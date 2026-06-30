use pyo3::prelude::*;
use pyo3::exceptions::{PyIOError, PyValueError, PyUnicodeDecodeError, PyTypeError, PyIndexError};
use pyo3::types::{PyDict, PyModule, PyString, PyTuple, PyIterator, PyList, PyAny};
use ::regex::Regex as RustRegex;
use ::regex::bytes::Regex as RustRegexBytes;
use ::regex::Captures as RustCaptures;
use memmap2::Mmap;
use std::fs::File;
use rayon::prelude::*;
use std::collections::{HashMap, VecDeque};
use memchr::memmem::Finder;
use std::io::Error as IOError;

// ---------------------------------------------------------------------------
// Python re-module flag handling.
//
// Python's `re` uses integer flags. We recognise the small subset that
// translates cleanly to Rust `regex` inline flags:
//   re.IGNORECASE / re.I = 2  -> (?i)
//   re.MULTILINE  / re.M = 8  -> (?m)
//   re.DOTALL     / re.S = 16 -> (?s)
//
// Other flags - re.UNICODE, re.VERBOSE, re.LOCALE, re.ASCII - have no
// direct counterpart (Rust regex is always Unicode-aware and never
// byte-oriented for the `&str` API). When a flag set includes one of
// those, it is silently ignored so that callers passing
// `flags=re.IGNORECASE | re.MULTILINE` etc. still get the behaviour they
// expect for the supported flags.
// ---------------------------------------------------------------------------

const PY_IGNORECASE: u32 = 2;
const PY_MULTILINE:  u32 = 8;
const PY_DOTALL:     u32 = 16;

fn apply_flags(pattern: &str, flags: u32) -> String {
    if flags == 0 {
        return pattern.to_string();
    }
    let mut prefix = String::new();
    if flags & PY_IGNORECASE != 0 { prefix.push('i'); }
    if flags & PY_MULTILINE  != 0 { prefix.push('m'); }
    if flags & PY_DOTALL     != 0 { prefix.push('s'); }
    if prefix.is_empty() {
        return pattern.to_string();
    }
    // Try to merge with an existing inline group at the very start of the
    // pattern, e.g. `(?m:...)` -> `(?mi:...)` or `(?m)...` -> `(?mi)...`.
    if pattern.starts_with("(?") {
        if let Some(idx) = pattern.find(|c| c == ':' || c == ')') {
            let (head, tail) = pattern.split_at(idx);
            // head looks like "(?xyz"
            let inner = &head[2..];
            // de-duplicate flags so we don't end up with (?ii...)
            let mut merged = String::from("(?");
            for ch in prefix.chars() {
                if !inner.contains(ch) {
                    merged.push(ch);
                }
            }
            merged.push_str(inner);
            merged.push_str(tail);
            return merged;
        }
    }
    format!("(?{}){}", prefix, pattern)
}

/// Snap a byte index to the nearest preceding UTF-8 char boundary in `s`.
fn snap_to_char_boundary(s: &str, idx: usize) -> usize {
    if idx >= s.len() { return s.len(); }
    let mut i = idx;
    while i > 0 && !s.is_char_boundary(i) {
        i -= 1;
    }
    i
}

/// Build a (name -> index) mapping for a compiled regex's named groups.
fn build_name_to_index(re: &RustRegex) -> Vec<(String, usize)> {
    re.capture_names()
        .enumerate()
        .filter_map(|(i, name)| name.map(|n| (n.to_string(), i)))
        .collect()
}

/// Expand a Python-style replacement template ("\1", "\g<name>") into a
/// Rust-regex `expand` template ("$1", "${name}").
fn py_repl_to_rust_repl(repl: &str) -> String {
    let bytes = repl.as_bytes();
    let mut out = String::with_capacity(repl.len());
    let mut i = 0;
    while i < bytes.len() {
        let b = bytes[i];
        if b == b'\\' && i + 1 < bytes.len() {
            let next = bytes[i + 1];
            if next == b'\\' { out.push('\\'); i += 2; continue; }
            if next.is_ascii_digit() {
                out.push('$');
                out.push(next as char);
                i += 2;
                continue;
            }
            if next == b'g' && i + 2 < bytes.len() && bytes[i + 2] == b'<' {
                if let Some(end) = repl[i + 3..].find('>') {
                    let inner = &repl[i + 3..i + 3 + end];
                    out.push_str("${");
                    out.push_str(inner);
                    out.push('}');
                    i += 3 + end + 1;
                    continue;
                }
            }
            // Unknown escape - keep verbatim.
            out.push('\\');
            out.push(next as char);
            i += 2;
            continue;
        }
        out.push(b as char);
        i += 1;
    }
    out
}

#[pyclass]
pub struct FileRegexGen {
    inner: RustRegex,
    #[allow(dead_code)]
    mmap: Mmap,
    haystack: &'static str,
    #[pyo3(get)]
    pub start: usize,
    #[pyo3(get)]
    pub end: usize,
    #[pyo3(get)]
    pub pos: usize,
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

// ===========================================================================
// Drop-in re-module replacements: PyMatch, PyPattern, iterators and module fns
// ===========================================================================

/// A `Match` object fully compatible with Python's `re.Match`.
///
/// Holds the byte spans of every capture group, the captured substrings, the
/// haystack, pos/endpos and the originating pattern/flags so that
/// `m.string`, `m.re.pattern`, `m.pos`, `m.endpos` and `m.flags` are all
/// available on the resulting object.
#[pyclass(module = "rygex_ext")]
pub struct PyMatch {
    /// byte offsets of each capture group, (usize::MAX, usize::MAX) when unmatched
    spans: Vec<(usize, usize)>,
    /// captured substrings, None when the group didn't participate
    groups: Vec<Option<String>>,
    /// ordered list of (name, index) for named capture groups
    name_to_index: Vec<(String, usize)>,
    /// the haystack string passed to search/match/finditer
    _string: String,
    /// the pos argument passed to search/match/finditer
    _pos: usize,
    /// the endpos argument (or len(string)) passed to search/match/finditer
    _endpos: usize,
    /// the source pattern string
    _pattern_str: String,
    /// the flags the pattern was compiled with
    _flags: u32,
}

#[pymethods]
impl PyMatch {
    /// m.start([group=0]) -> int. -1 if the group did not participate.
    /// Accepts int, str (named group), or None (defaults to group 0).
    #[pyo3(signature = (group=None))]
    fn start(&self, py: Python<'_>, group: Option<Bound<'_, PyAny>>) -> PyResult<isize> {
        let idx = self.group_index_opt(py, group)?;
        Ok(self.spans.get(idx)
            .filter(|(s, _)| *s != usize::MAX)
            .map(|(s, _)| *s as isize)
            .unwrap_or(-1))
    }

    /// m.end([group=0]) -> int. -1 if the group did not participate.
    #[pyo3(signature = (group=None))]
    fn end(&self, py: Python<'_>, group: Option<Bound<'_, PyAny>>) -> PyResult<isize> {
        let idx = self.group_index_opt(py, group)?;
        Ok(self.spans.get(idx)
            .filter(|(_, e)| *e != usize::MAX)
            .map(|(_, e)| *e as isize)
            .unwrap_or(-1))
    }

    /// m.span([group=0]) -> (start, end). (-1, -1) if the group didn't match.
    #[pyo3(signature = (group=None))]
    fn span(&self, py: Python<'_>, group: Option<Bound<'_, PyAny>>) -> PyResult<(isize, isize)> {
        let idx = self.group_index_opt(py, group)?;
        Ok(self.spans.get(idx)
            .filter(|(s, _)| *s != usize::MAX)
            .map(|(s, e)| (*s as isize, *e as isize))
            .unwrap_or((-1, -1)))
    }

    /// m.group(*args) -> str | tuple[str | None, ...]
    /// With no args returns group 0; with one arg returns that group; with
    /// several args returns a tuple.
    #[pyo3(signature = (*args))]
    fn group(&self, py: Python<'_>, args: &Bound<'_, PyTuple>) -> PyResult<Py<PyAny>> {
        if args.is_empty() {
            return Ok(self.group_str(0)
                .map(|s| PyString::new(py, s).into_any())
                .unwrap_or_else(|| py.None().into_bound(py).into_any())
                .unbind());
        }
        if args.len() == 1 {
            let item = args.get_borrowed_item(0)?;
            let idx = self.group_index(py, &item)?;
            return Ok(self.group_str(idx)
                .map(|s| PyString::new(py, s).into_any())
                .unwrap_or_else(|| py.None().into_bound(py).into_any())
                .unbind());
        }
        let mut out: Vec<Py<PyAny>> = Vec::with_capacity(args.len());
        for arg in args.iter() {
            let idx = self.group_index(py, &arg)?;
            let item = self.group_str(idx)
                .map(|s| PyString::new(py, s).into_any())
                .unwrap_or_else(|| py.None().into_bound(py).into_any())
                .unbind();
            out.push(item);
        }
        Ok(PyTuple::new(py, out)?.into_any().unbind())
    }

    /// m.groups([default=None]) -> tuple[str | None, ...]
    /// Groups 1..N, with `default` substituted for unmatched groups.
    #[pyo3(signature = (default=None))]
    fn groups<'py>(
        &self,
        py: Python<'py>,
        default: Option<Bound<'py, PyAny>>,
    ) -> PyResult<Bound<'py, PyTuple>> {
        let default_obj: Py<PyAny> = match default {
            Some(d) => d.as_any().clone().unbind(),
            None => py.None(),
        };
        let mut out: Vec<Py<PyAny>> = Vec::with_capacity(self.groups.len().saturating_sub(1));
        for g in self.groups.iter().skip(1) {
            match g {
                Some(s) => out.push(PyString::new(py, s).into_any().unbind()),
                None => out.push(default_obj.clone_ref(py)),
            }
        }
        Ok(PyTuple::new(py, out)?)
    }

    /// m.groupdict([default=None]) -> dict[str, str | None]
    /// Only named groups appear in the dict (Python behaviour).
    #[pyo3(signature = (default=None))]
    fn groupdict<'py>(
        &self,
        py: Python<'py>,
        default: Option<Bound<'py, PyAny>>,
    ) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        let default_obj: Py<PyAny> = match default {
            Some(d) => d.as_any().clone().unbind(),
            None => py.None(),
        };
        for (name, idx) in &self.name_to_index {
            if *idx == 0 { continue; }
            let value: Py<PyAny> = match self.group_str(*idx) {
                Some(s) => PyString::new(py, s).into_any().unbind(),
                None => default_obj.clone_ref(py),
            };
            dict.set_item(name, value)?;
        }
        Ok(dict)
    }

    /// Indexing the match object: m[0], m[1], m["name"].
    fn __getitem__(&self, py: Python<'_>, key: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let idx = self.group_index(py, key)?;
        Ok(self.group_str(idx)
            .map(|s| PyString::new(py, s).into_any())
            .unwrap_or_else(|| py.None().into_bound(py).into_any())
            .unbind())
    }

    /// Number of capturing groups (excl. group 0) - len(m) matches re.Match.
    fn __len__(&self) -> usize {
        self.groups.len().saturating_sub(1)
    }

    /// Iterating yields groups 1..N (group 0 excluded), like Python's match.
    fn __iter__(slf: PyRef<'_, Self>) -> PyMatchIter {
        PyMatchIter::new(slf)
    }

    /// m == m2 if spans and captured groups are identical.
    fn __eq__(&self, other: &Bound<'_, PyAny>) -> bool {
        if let Ok(other_m) = other.extract::<PyRef<'_, PyMatch>>() {
            self.spans == other_m.spans && self.groups == other_m.groups
        } else {
            false
        }
    }

    /// m.repr() -> "<rygex.Match object; span=(s, e); match='...'>"
    fn __repr__(&self) -> String {
        let (s, e) = self.spans.first().copied().unwrap_or((0, 0));
        let g0 = self.group_str(0).unwrap_or("");
        format!("<rygex.Match object; span=({}, {}); match={:?}>", s, e, g0)
    }

    /// The haystack string searched; mirrors re.Match.string.
    #[getter]
    fn string(&self) -> String { self._string.clone() }

    /// The pos argument; mirrors re.Match.pos.
    #[getter]
    fn pos(&self) -> usize { self._pos }

    /// The endpos argument; mirrors re.Match.endpos.
    #[getter]
    fn endpos(&self) -> usize { self._endpos }

    /// Highest matched group index, or None. Mirrors re.Match.lastindex.
    #[getter]
    fn lastindex(&self) -> Option<usize> {
        (1..self.groups.len())
            .rev()
            .find(|&i| self.groups[i].is_some())
    }

    /// Name of the last matched named group, or None. Mirrors re.Match.lastgroup.
    #[getter]
    fn lastgroup(&self) -> Option<String> {
        let last = self.lastindex()?;
        self.name_to_index.iter()
            .rev()
            .find(|(_, idx)| *idx == last)
            .map(|(name, _)| name.clone())
    }

    /// The pattern's source string. Mirrors re.Match.re.pattern.
    #[getter]
    fn pattern(&self) -> String { self._pattern_str.clone() }

    /// The flags the pattern was compiled with. Mirrors re.Match.re.flags.
    #[getter]
    fn flags(&self) -> u32 { self._flags }
}

impl PyMatch {
    /// Helper: return the substring of group `idx`, or None.
    fn group_str(&self, idx: usize) -> Option<&str> {
        self.groups.get(idx).and_then(|g| g.as_deref())
    }

    /// Resolve a Python group key (int or str) into a usize group index.
    /// `None` defaults to group 0 (the whole match).
    fn group_index_opt(
        &self,
        py: Python<'_>,
        key: Option<Bound<'_, PyAny>>,
    ) -> PyResult<usize> {
        match key {
            Some(k) => self.group_index(py, &k),
            None => Ok(0),
        }
    }

    /// Resolve a Python group key (int or str) into a usize group index.
    fn group_index(&self, _py: Python<'_>, key: &Bound<'_, PyAny>) -> PyResult<usize> {
        if let Ok(i) = key.extract::<isize>() {
            let len = self.groups.len();
            if i < 0 {
                let neg = (-i) as usize;
                if neg == 0 || neg > len {
                    return Err(PyIndexError::new_err(format!("no such group: {}", i)));
                }
                return Ok(len - neg);
            }
            let i = i as usize;
            if i >= len {
                return Err(PyIndexError::new_err(format!("no such group: {}", i)));
            }
            return Ok(i);
        }
        if let Ok(s) = key.extract::<String>() {
            for (name, idx) in &self.name_to_index {
                if name == &s { return Ok(*idx); }
            }
            return Err(PyIndexError::new_err(format!("no such group: {:?}", s)));
        }
        Err(PyTypeError::new_err("group index must be int or str"))
    }

    /// Build a PyMatch from a Rust Captures over a substring of `haystack`.
    /// `base` is added to every span so the reported offsets are absolute in
    /// `haystack` (Rust regex returns offsets relative to the slice).
    fn from_captures(
        caps: &RustCaptures<'_>,
        haystack: &str,
        base: usize,
        name_to_index: &[(String, usize)],
        pos: usize,
        endpos: usize,
        pattern_str: &str,
        flags: u32,
    ) -> Self {
        let mut spans = Vec::with_capacity(caps.len());
        let mut groups = Vec::with_capacity(caps.len());
        for i in 0..caps.len() {
            match caps.get(i) {
                Some(m) => {
                    spans.push((base + m.start(), base + m.end()));
                    groups.push(Some(m.as_str().to_string()));
                }
                None => {
                    spans.push((usize::MAX, usize::MAX));
                    groups.push(None);
                }
            }
        }
        PyMatch {
            spans,
            groups,
            name_to_index: name_to_index.to_vec(),
            _string: haystack.to_string(),
            _pos: pos,
            _endpos: endpos,
            _pattern_str: pattern_str.to_string(),
            _flags: flags,
        }
    }

    /// Build a "null" PyMatch used as the None return value for
    /// search/match/fullmatch (because the pymethod signatures return a
    /// Bound<'py, PyMatch> rather than Option<...>).
    fn null(
        string: &str,
        pos: usize,
        endpos: usize,
        pattern_str: &str,
        flags: u32,
    ) -> Self {
        PyMatch {
            spans: vec![(usize::MAX, usize::MAX)],
            groups: vec![None],
            name_to_index: Vec::new(),
            _string: string.to_string(),
            _pos: pos,
            _endpos: endpos,
            _pattern_str: pattern_str.to_string(),
            _flags: flags,
        }
    }

    /// True if this PyMatch is the null sentinel (i.e. represents None).
    fn is_null(&self) -> bool {
        self.spans.first().map(|(s, _)| *s == usize::MAX).unwrap_or(true)
    }
}

/// Iterator over a Match's groups (group 0 excluded), as in Python's `for g in m:`.
#[pyclass(module = "rygex_ext")]
pub struct PyMatchIter {
    /// Py<PyMatch> shared reference so we can borrow across __next__ calls.
    inner: Py<PyMatch>,
    pos: usize,
}

impl PyMatchIter {
    fn new(m: PyRef<'_, PyMatch>) -> Self {
        PyMatchIter {
            inner: Py::from(m),
            pos: 1,
        }
    }
}

#[pymethods]
impl PyMatchIter {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> { slf }
    fn __next__<'py>(&mut self, py: Python<'py>) -> PyResult<Option<Bound<'py, PyAny>>> {
        let m = self.inner.bind(py).borrow();
        if self.pos >= m.groups.len() {
            return Ok(None);
        }
        let item = match &m.groups[self.pos] {
            Some(s) => PyString::new(py, s).into_any(),
            None => py.None().into_bound(py).into_any(),
        };
        self.pos += 1;
        Ok(Some(item))
    }
}

/// Iterator yielding `Match` objects, returned by `finditer()`/`Pattern.finditer()`.
#[pyclass(module = "rygex_ext")]
pub struct PyFindIter {
    /// Owns the haystack string so that the leaked 'static captures remain valid.
    haystack: String,
    /// Pre-collected captures, made 'static by leaking a reference to
    /// `haystack` for the lifetime of this iterator.
    captures: VecDeque<RustCaptures<'static>>,
    base: usize,
    pos: usize,
    endpos: usize,
    pattern_str: String,
    flags: u32,
    name_to_index: Vec<(String, usize)>,
}

#[pymethods]
impl PyFindIter {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> { slf }
    fn __len__(&self) -> usize { self.captures.len() }
    fn __next__<'py>(
        mut slf: PyRefMut<'py, Self>,
        py: Python<'py>,
    ) -> PyResult<Option<Bound<'py, PyMatch>>> {
        let caps = match slf.captures.pop_front() {
            Some(c) => c,
            None => return Ok(None),
        };
        let m = PyMatch::from_captures(
            &caps, &slf.haystack, slf.base, &slf.name_to_index,
            slf.pos, slf.endpos, &slf.pattern_str, slf.flags
        );
        Ok(Some(Bound::new(py, m)?))
    }
}

/// A compiled regex pattern, fully compatible with Python's `re.Pattern`.
#[pyclass(module = "rygex_ext")]
pub struct PyPattern {
    inner: RustRegex,
    pattern_str: String,
    flags: u32,
    name_to_index: Vec<(String, usize)>,
}

impl PyPattern {
    fn new_with_flags(pattern: &str, flags: u32) -> PyResult<Self> {
        let processed = apply_flags(pattern, flags);
        let inner = RustRegex::new(&processed)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        let name_to_index = build_name_to_index(&inner);
        Ok(PyPattern {
            inner,
            pattern_str: pattern.to_string(),
            flags,
            name_to_index,
        })
    }

    /// Internal helper: search a slice of `string` from `start..end` and
    /// return a bound PyMatch (or the null sentinel if no match).
    fn do_search<'py>(
        &self,
        py: Python<'py>,
        string: &str,
        start: usize,
        end: usize,
        pos: usize,
        endpos: usize,
    ) -> PyResult<Bound<'py, PyMatch>> {
        let slice = &string[start..end];
        match self.inner.captures(slice) {
            Some(caps) => {
                let m = PyMatch::from_captures(
                    &caps, string, start, &self.name_to_index,
                    pos, endpos, &self.pattern_str, self.flags
                );
                Ok(Bound::new(py, m)?)
            }
            None => {
                let m = PyMatch::null(string, pos, endpos, &self.pattern_str, self.flags);
                Ok(Bound::new(py, m)?)
            }
        }
    }

    /// Internal helper for `match()`/`fullmatch()`: only accept the captures
    /// if group 0 (and for fullmatch, the end too) lines up with the anchor.
    fn do_anchored<'py>(
        &self,
        py: Python<'py>,
        string: &str,
        start: usize,
        end: usize,
        pos: usize,
        endpos: usize,
        full: bool,
    ) -> PyResult<Bound<'py, PyMatch>> {
        let slice = &string[start..end];
        if let Some(caps) = self.inner.captures(slice) {
            if let Some(m0) = caps.get(0) {
                if m0.start() == 0 && (!full || m0.end() == slice.len()) {
                    let m = PyMatch::from_captures(
                        &caps, string, start, &self.name_to_index,
                        pos, endpos, &self.pattern_str, self.flags
                    );
                    return Ok(Bound::new(py, m)?);
                }
            }
        }
        let m = PyMatch::null(string, pos, endpos, &self.pattern_str, self.flags);
        Ok(Bound::new(py, m)?)
    }

    /// Implementation shared by sub() and subn().
    fn sub_impl<'py>(
        &self,
        py: Python<'py>,
        repl: Bound<'py, PyAny>,
        string: &str,
        count: usize,
    ) -> PyResult<(String, usize)> {
        let is_callable = repl.is_callable();
        let repl_template: Option<String> = if !is_callable {
            Some(repl.extract::<String>()?)
        } else {
            None
        };

        let mut out = String::with_capacity(string.len() + 16);
        let mut last_end = 0;
        let mut n: usize = 0;

        for caps in self.inner.captures_iter(string) {
            if count > 0 && n >= count { break; }
            let m0 = caps.get(0).unwrap();
            out.push_str(&string[last_end..m0.start()]);

            let replacement: String = if is_callable {
                let m_obj = PyMatch::from_captures(
                    &caps, string, 0, &self.name_to_index,
                    0, string.len(), &self.pattern_str, self.flags
                );
                let bound = Bound::new(py, m_obj)?;
                let res = repl.call1((bound,))?;
                res.extract::<String>()?
            } else {
                let tpl = py_repl_to_rust_repl(repl_template.as_ref().unwrap());
                let mut s = String::new();
                caps.expand(&tpl, &mut s);
                s
            };
            out.push_str(&replacement);
            last_end = m0.end();
            n += 1;
        }
        out.push_str(&string[last_end..]);
        Ok((out, n))
    }
}

#[pymethods]
impl PyPattern {
    /// p.pattern -> the source pattern string (re.Pattern.pattern).
    #[getter]
    fn pattern(&self) -> String { self.pattern_str.clone() }

    /// p.flags -> the flag int this pattern was compiled with (re.Pattern.flags).
    #[getter]
    fn flags(&self) -> u32 { self.flags }

    /// p.groups -> number of capturing groups, excluding group 0
    /// (re.Pattern.groups).
    #[getter]
    fn groups(&self) -> usize {
        self.inner.captures_len().saturating_sub(1)
    }

    /// p.groupindex -> a fresh dict mapping named groups to their group number.
    fn groupindex<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        for (name, idx) in &self.name_to_index {
            if *idx == 0 { continue; }
            dict.set_item(name, *idx)?;
        }
        Ok(dict)
    }

    /// p.search(string[, pos[, endpos]]) -> Match or None.
    #[pyo3(signature = (string, pos=0, endpos=None))]
    fn search<'py>(
        &self,
        py: Python<'py>,
        string: &str,
        pos: usize,
        endpos: Option<usize>,
    ) -> PyResult<Bound<'py, PyMatch>> {
        let hay_len = string.len();
        let start = snap_to_char_boundary(string, pos.min(hay_len));
        let end = match endpos {
            Some(e) => snap_to_char_boundary(string, e.min(hay_len)),
            None => hay_len,
        };
        if start > end {
            return Err(PyValueError::new_err("pos must be <= endpos"));
        }
        self.do_search(py, string, start, end, pos, endpos.unwrap_or(hay_len))
    }

    /// p.match(string[, pos[, endpos]]) -> Match or None. Anchored at `pos`.
    #[pyo3(signature = (string, pos=0, endpos=None), name = "match")]
    fn match_fn<'py>(
        &self,
        py: Python<'py>,
        string: &str,
        pos: usize,
        endpos: Option<usize>,
    ) -> PyResult<Bound<'py, PyMatch>> {
        let hay_len = string.len();
        let start = snap_to_char_boundary(string, pos.min(hay_len));
        let end = match endpos {
            Some(e) => snap_to_char_boundary(string, e.min(hay_len)),
            None => hay_len,
        };
        if start > end {
            return Err(PyValueError::new_err("pos must be <= endpos"));
        }
        self.do_anchored(py, string, start, end, pos, endpos.unwrap_or(hay_len), false)
    }

    /// p.fullmatch(string[, pos[, endpos]]) -> Match or None. Anchored at both ends.
    #[pyo3(signature = (string, pos=0, endpos=None))]
    fn fullmatch<'py>(
        &self,
        py: Python<'py>,
        string: &str,
        pos: usize,
        endpos: Option<usize>,
    ) -> PyResult<Bound<'py, PyMatch>> {
        let hay_len = string.len();
        let start = snap_to_char_boundary(string, pos.min(hay_len));
        let end = match endpos {
            Some(e) => snap_to_char_boundary(string, e.min(hay_len)),
            None => hay_len,
        };
        if start > end {
            return Err(PyValueError::new_err("pos must be <= endpos"));
        }
        self.do_anchored(py, string, start, end, pos, endpos.unwrap_or(hay_len), true)
    }

    /// p.findall(string[, pos[, endpos]]) -> list
    /// Behaviour matches Python's `re.findall`:
    ///   - 0 groups: list[str]                    (whole matches)
    ///   - 1 group:  list[str | None]             (group 1)
    ///   - N groups: list[tuple[str | None; N]]   (groups 1..N)
    #[pyo3(signature = (string, pos=0, endpos=None))]
    fn findall<'py>(
        &self,
        py: Python<'py>,
        string: &str,
        pos: usize,
        endpos: Option<usize>,
    ) -> PyResult<Bound<'py, PyList>> {
        let hay_len = string.len();
        let start = snap_to_char_boundary(string, pos.min(hay_len));
        let end = match endpos {
            Some(e) => snap_to_char_boundary(string, e.min(hay_len)),
            None => hay_len,
        };
        let slice = &string[start..end];
        let list = PyList::empty(py);
        let n_groups = self.inner.captures_len().saturating_sub(1);

        for caps in self.inner.captures_iter(slice) {
            if n_groups == 0 {
                let s = caps.get(0).map(|m| m.as_str()).unwrap_or("");
                list.append(PyString::new(py, s))?;
            } else if n_groups == 1 {
                let item = match caps.get(1) {
                    Some(m) => PyString::new(py, m.as_str()).into_any(),
                    None => py.None().into_bound(py).into_any(),
                };
                list.append(item)?;
            } else {
                let mut row: Vec<Py<PyAny>> = Vec::with_capacity(n_groups);
                for i in 1..=n_groups {
                    let item: Py<PyAny> = match caps.get(i) {
                        Some(m) => PyString::new(py, m.as_str()).into_any().unbind(),
                        None => py.None(),
                    };
                    row.push(item);
                }
                list.append(PyTuple::new(py, row)?)?;
            }
        }
        Ok(list)
    }

    /// p.finditer(string[, pos[, endpos]]) -> iterator of Match
    #[pyo3(signature = (string, pos=0, endpos=None))]
    fn finditer(&self, string: &str, pos: usize, endpos: Option<usize>) -> PyResult<PyFindIter> {
        let hay_len = string.len();
        let start = snap_to_char_boundary(string, pos.min(hay_len));
        let end = match endpos {
            Some(e) => snap_to_char_boundary(string, e.min(hay_len)),
            None => hay_len,
        };
        let slice_str = string[start..end].to_string();
        let caps: Vec<RustCaptures<'static>> = unsafe {
            // SAFETY: slice_str is owned by PyFindIter and outlives the captures.
            let leaked: &'static str = std::mem::transmute::<&str, &'static str>(&slice_str);
            self.inner.captures_iter(leaked).collect()
        };
        Ok(PyFindIter {
            haystack: slice_str,
            captures: caps.into_iter().collect(),
            base: start,
            pos,
            endpos: endpos.unwrap_or(hay_len),
            pattern_str: self.pattern_str.clone(),
            flags: self.flags,
            name_to_index: self.name_to_index.clone(),
        })
    }

    /// p.findall_captures(string) -> list[tuple[str | None, ...]]
    /// Each match is returned as a tuple of (full, group1, group2, ...).
    #[pyo3(signature = (string, pos=0, endpos=None))]
    fn findall_captures<'py>(
        &self,
        py: Python<'py>,
        string: &str,
        pos: usize,
        endpos: Option<usize>,
    ) -> PyResult<Bound<'py, PyList>> {
        let hay_len = string.len();
        let start = snap_to_char_boundary(string, pos.min(hay_len));
        let end = match endpos {
            Some(e) => snap_to_char_boundary(string, e.min(hay_len)),
            None => hay_len,
        };
        let list = PyList::empty(py);
        for caps in self.inner.captures_iter(&string[start..end]) {
            let mut row: Vec<Py<PyAny>> = Vec::with_capacity(caps.len());
            for i in 0..caps.len() {
                let item: Py<PyAny> = match caps.get(i) {
                    Some(m) => PyString::new(py, m.as_str()).into_any().unbind(),
                    None => py.None(),
                };
                row.push(item);
            }
            list.append(PyTuple::new(py, row)?)?;
        }
        Ok(list)
    }

    /// p.findall_captures_named(string) -> list[dict[str, str | None]]
    /// Each match is returned as a dict with keys: 'full', '0', '1', ...,
    /// and any named-group names.
    #[pyo3(signature = (string))]
    fn findall_captures_named<'py>(
        &self,
        py: Python<'py>,
        string: &str,
    ) -> PyResult<Bound<'py, PyList>> {
        let results = PyList::empty(py);
        for caps in self.inner.captures_iter(string) {
            let dict = PyDict::new(py);
            if let Some(m) = caps.get(0) { dict.set_item("full", m.as_str())?; }
            for i in 1..caps.len() {
                let key = i.to_string();
                let val = caps.get(i).map(|m| m.as_str());
                dict.set_item(key, val)?;
            }
            for (name, idx) in &self.name_to_index {
                if *idx == 0 { continue; }
                let val = caps.get(*idx).map(|m| m.as_str());
                dict.set_item(name, val)?;
            }
            results.append(dict)?;
        }
        Ok(results)
    }

    /// p.sub(repl, string, count=0) -> str. `repl` may be a template
    /// ("\\1", "\\g<name>") or a callable taking a Match.
    #[pyo3(signature = (repl, string, count=0))]
    fn sub<'py>(
        &self,
        py: Python<'py>,
        repl: Bound<'py, PyAny>,
        string: &str,
        count: usize,
    ) -> PyResult<String> {
        self.sub_impl(py, repl, string, count).map(|(s, _)| s)
    }

    /// p.subn(repl, string, count=0) -> (new_string, n_subs)
    #[pyo3(signature = (repl, string, count=0))]
    fn subn<'py>(
        &self,
        py: Python<'py>,
        repl: Bound<'py, PyAny>,
        string: &str,
        count: usize,
    ) -> PyResult<(String, usize)> {
        self.sub_impl(py, repl, string, count)
    }

    /// p.split(string, maxsplit=0) -> list. Captured groups are inserted
    /// between the split chunks, like Python's `re.split`.
    #[pyo3(signature = (string, maxsplit=0))]
    fn split<'py>(
        &self,
        py: Python<'py>,
        string: &str,
        maxsplit: usize,
    ) -> PyResult<Bound<'py, PyList>> {
        let list = PyList::empty(py);
        let n_groups = self.inner.captures_len().saturating_sub(1);
        let mut last_end = 0;
        let mut nsplit = 0;

        for caps in self.inner.captures_iter(string) {
            if maxsplit > 0 && nsplit >= maxsplit { break; }
            let m0 = caps.get(0).unwrap();
            // Match Python's skip of an empty match at the same spot as last time.
            if m0.start() == m0.end() && m0.start() == last_end && last_end != 0 {
                continue;
            }
            list.append(PyString::new(py, &string[last_end..m0.start()]))?;
            for i in 1..=n_groups {
                let item = match caps.get(i) {
                    Some(m) => PyString::new(py, m.as_str()).into_any(),
                    None => py.None().into_bound(py).into_any(),
                };
                list.append(item)?;
            }
            last_end = m0.end();
            nsplit += 1;
        }
        list.append(PyString::new(py, &string[last_end..]))?;
        Ok(list)
    }

    /// p.is_match(string[, pos]) -> bool. Cheap; does not build a Match.
    #[pyo3(signature = (string, pos=0))]
    fn is_match(&self, string: &str, pos: usize) -> bool {
        let hay_len = string.len();
        let start = snap_to_char_boundary(string, pos.min(hay_len));
        self.inner.is_match(&string[start..])
    }

    /// p.count(string) -> usize. Number of non-overlapping matches.
    fn count(&self, string: &str) -> usize {
        self.inner.find_iter(string).count()
    }

    /// p.__repr__() -> "<rygex.Pattern...>"
    fn __repr__(&self) -> String {
        format!("<rygex.Pattern object; pattern={:?} flags={}>", self.pattern_str, self.flags)
    }
}

// ---------------------------------------------------------------------------
// Module-level functions mirroring re.search / re.match / re.fullmatch /
// re.findall / re.finditer / re.sub / re.subn / re.split / re.compile.
// ---------------------------------------------------------------------------

#[pyfunction]
#[pyo3(signature = (pattern, flags=0))]
fn compile_with_flags(pattern: &str, flags: u32) -> PyResult<PyPattern> {
    PyPattern::new_with_flags(pattern, flags)
}

#[pyfunction]
#[pyo3(signature = (pattern, string, pos=0, endpos=None, flags=0))]
fn search_re<'py>(
    py: Python<'py>,
    pattern: &str,
    string: &str,
    pos: usize,
    endpos: Option<usize>,
    flags: u32,
) -> PyResult<Bound<'py, PyMatch>> {
    let pat = PyPattern::new_with_flags(pattern, flags)?;
    pat.search(py, string, pos, endpos)
}

#[pyfunction]
#[pyo3(signature = (pattern, string, pos=0, endpos=None, flags=0), name = "match")]
fn match_re<'py>(
    py: Python<'py>,
    pattern: &str,
    string: &str,
    pos: usize,
    endpos: Option<usize>,
    flags: u32,
) -> PyResult<Bound<'py, PyMatch>> {
    let pat = PyPattern::new_with_flags(pattern, flags)?;
    pat.match_fn(py, string, pos, endpos)
}

#[pyfunction]
#[pyo3(signature = (pattern, string, pos=0, endpos=None, flags=0))]
fn fullmatch_re<'py>(
    py: Python<'py>,
    pattern: &str,
    string: &str,
    pos: usize,
    endpos: Option<usize>,
    flags: u32,
) -> PyResult<Bound<'py, PyMatch>> {
    let pat = PyPattern::new_with_flags(pattern, flags)?;
    pat.fullmatch(py, string, pos, endpos)
}

#[pyfunction]
#[pyo3(signature = (pattern, string, pos=0, endpos=None, flags=0))]
fn findall_re<'py>(
    py: Python<'py>,
    pattern: &str,
    string: &str,
    pos: usize,
    endpos: Option<usize>,
    flags: u32,
) -> PyResult<Bound<'py, PyList>> {
    let pat = PyPattern::new_with_flags(pattern, flags)?;
    pat.findall(py, string, pos, endpos)
}

#[pyfunction]
#[pyo3(signature = (pattern, string, pos=0, endpos=None, flags=0))]
fn finditer_re(
    pattern: &str,
    string: &str,
    pos: usize,
    endpos: Option<usize>,
    flags: u32,
) -> PyResult<PyFindIter> {
    let pat = PyPattern::new_with_flags(pattern, flags)?;
    pat.finditer(string, pos, endpos)
}

#[pyfunction]
#[pyo3(signature = (pattern, repl, string, count=0, flags=0))]
fn sub_re<'py>(
    py: Python<'py>,
    pattern: &str,
    repl: Bound<'py, PyAny>,
    string: &str,
    count: usize,
    flags: u32,
) -> PyResult<String> {
    let pat = PyPattern::new_with_flags(pattern, flags)?;
    pat.sub(py, repl, string, count)
}

#[pyfunction]
#[pyo3(signature = (pattern, repl, string, count=0, flags=0))]
fn subn_re<'py>(
    py: Python<'py>,
    pattern: &str,
    repl: Bound<'py, PyAny>,
    string: &str,
    count: usize,
    flags: u32,
) -> PyResult<(String, usize)> {
    let pat = PyPattern::new_with_flags(pattern, flags)?;
    pat.subn(py, repl, string, count)
}

#[pyfunction]
#[pyo3(signature = (pattern, string, maxsplit=0, flags=0))]
fn split_re<'py>(
    py: Python<'py>,
    pattern: &str,
    string: &str,
    maxsplit: usize,
    flags: u32,
) -> PyResult<Bound<'py, PyList>> {
    let pat = PyPattern::new_with_flags(pattern, flags)?;
    pat.split(py, string, maxsplit)
}

#[pyfunction]
fn purge() -> bool { true }

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

    /// Number of capturing groups (excl. group 0), mirroring `re.Pattern.groups`.
    #[getter]
    fn groups(&self) -> usize {
        self.inner.captures_len().saturating_sub(1)
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
    // Legacy classes - kept for backwards compatibility.
    m.add_class::<Regex>()?;
    m.add_class::<Match>()?;
    m.add_class::<RustRegexGen>()?;
    m.add_class::<FileRegexGen>()?;

    // New, re-compatible classes added for the drop-in replacement API.
    m.add_class::<PyMatch>()?;
    m.add_class::<PyMatchIter>()?;
    m.add_class::<PyPattern>()?;
    m.add_class::<PyFindIter>()?;

    // Legacy / pre-existing module-level functions.
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

    // New re-compatible module-level functions. These are aliased onto the
    // names that match Python's `re` module: search/match/fullmatch/findall/
    // finditer/sub/subn/split/compile. The original `compile` and `search`
    // (defined above) used the legacy Match type; the re-compatible versions
    // are exposed under distinct names so that both APIs remain usable.
    m.add_function(wrap_pyfunction!(compile_with_flags, m)?)?;
    m.add_function(wrap_pyfunction!(search_re, m)?)?;
    m.add_function(wrap_pyfunction!(match_re, m)?)?;
    m.add_function(wrap_pyfunction!(fullmatch_re, m)?)?;
    m.add_function(wrap_pyfunction!(findall_re, m)?)?;
    m.add_function(wrap_pyfunction!(finditer_re, m)?)?;
    m.add_function(wrap_pyfunction!(sub_re, m)?)?;
    m.add_function(wrap_pyfunction!(subn_re, m)?)?;
    m.add_function(wrap_pyfunction!(split_re, m)?)?;
    m.add_function(wrap_pyfunction!(purge, m)?)?;

    // Re-export the supported re-module flag constants so users can write
    // `rygex_ext.I`, `rygex_ext.M`, etc. without importing Python's re.
    m.add("I", PY_IGNORECASE)?;
    m.add("IGNORECASE", PY_IGNORECASE)?;
    m.add("M", PY_MULTILINE)?;
    m.add("MULTILINE", PY_MULTILINE)?;
    m.add("S", PY_DOTALL)?;
    m.add("DOTALL", PY_DOTALL)?;
    Ok(())
}