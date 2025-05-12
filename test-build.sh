#!/bin/bash

maturin build --release
pip install target/wheels/rygex-0.1.0-cp313-cp313-manylinux_2_34_x86_64.whl --force-reinstall
