#!/bin/bash

rm -rf target/wheels/rygex-*
maturin build --release
pip install target/wheels/rygex-*.whl --force-reinstall
