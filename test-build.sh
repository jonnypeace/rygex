#!/bin/bash

maturin build --release
pip install target/wheels/rygex-*-cp313-cp313-manylinux_2_34_x86_64.whl --force-reinstall
