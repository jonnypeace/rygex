# .devcontainer/Dockerfile
FROM python:3.13

# 1) Install OS deps + Rust toolchain
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      git \
      curl \
      pkg-config \
      libssl-dev \
      gawk \
      perl \
      sed \
      ripgrep \
 && rm -rf /var/lib/apt/lists/*

ARG USER=vscode
ARG UID=1000
RUN useradd -m --uid $UID $USER

# 4) Switch to non-root
USER $USER
WORKDIR /workspace

# 5) Install the latest Rust toolchain via rustup
#    -y = agree to defaults, installs to $HOME/.cargo
RUN curl https://sh.rustup.rs -sSf \
    | sh -s -- -y --default-toolchain stable \
    && ~/.cargo/bin/rustup default stable

# 6) Ensure Cargo/Rust are on your PATH
ENV PATH=/home/${USER}/.cargo/bin:${PATH}

# 5) Ensure user-local bin is on PATH
ENV PATH=/home/${USER}/.local/bin:${PATH}

# 6) Copy dependency manifests & install Python libs
COPY . .
RUN pip install --upgrade pip \
  && pip install --user --no-cache-dir -r requirements.txt

USER root
RUN chown -R $USER:$USER .
USER $USER
RUN ls -l /workspace && cat /workspace/Cargo.toml
# 8) Build your Rust/Python hybrid and install the wheel
RUN maturin build --release \
 && pip install --user target/wheels/rygex-*.whl --force-reinstall

# 9) Drop into bash
ENTRYPOINT ["bash"]
