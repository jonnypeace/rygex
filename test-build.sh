#!/bin/bash

maturin build --release
pip install target/wheels/rygex-*.whl --force-reinstall
