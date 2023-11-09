FROM debian:12

RUN rm /etc/apt/sources.list.d/debian.sources && \
    printf '\
deb http://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware \n\
deb http://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware \n\
deb http://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-backports main contrib non-free non-free-firmware \n\
deb http://mirrors.tuna.tsinghua.edu.cn/debian-security/ bookworm-security main contrib non-free non-free-firmware \
' > /etc/apt/sources.list

RUN apt-get update && \
    apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y g++ cmake build-essential git curl apt-transport-https ca-certificates libc6-dev pkg-config && \
    rm -rf /var/lib/apt/lists/

RUN useradd --create-home --shell /bin/bash tester

USER tester
WORKDIR /home/tester

RUN curl https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda.sh && \
    bash miniconda.sh -b && \
    rm miniconda.sh

ENV PATH="/home/tester/miniconda3/bin:/home/tester/.cargo/bin:$PATH"

# modified from https://github.com/rust-lang/docker-rust/blob/master/1.73.0/bookworm/Dockerfile
ENV RUST_VERSION=1.73.0

RUN dpkgArch="$(dpkg --print-architecture)"; \
    case "${dpkgArch##*-}" in \
        amd64) rustArch='x86_64-unknown-linux-gnu'; rustupSha256='0b2f6c8f85a3d02fde2efc0ced4657869d73fccfce59defb4e8d29233116e6db' ;; \
        armhf) rustArch='armv7-unknown-linux-gnueabihf'; rustupSha256='f21c44b01678c645d8fbba1e55e4180a01ac5af2d38bcbd14aa665e0d96ed69a' ;; \
        arm64) rustArch='aarch64-unknown-linux-gnu'; rustupSha256='673e336c81c65e6b16dcdede33f4cc9ed0f08bde1dbe7a935f113605292dc800' ;; \
        i386) rustArch='i686-unknown-linux-gnu'; rustupSha256='e7b0f47557c1afcd86939b118cbcf7fb95a5d1d917bdd355157b63ca00fc4333' ;; \
        *) echo >&2 "unsupported architecture: ${dpkgArch}"; exit 1 ;; \
    esac; \
    url="https://mirrors.tuna.tsinghua.edu.cn/rustup/rustup/archive/1.26.0/${rustArch}/rustup-init"; \
    curl "$url" -o rustup-init; \
    echo "${rustupSha256} *rustup-init" | sha256sum -c -; \
    chmod +x rustup-init; \
    ./rustup-init -y --no-modify-path --profile minimal --default-toolchain $RUST_VERSION --default-host ${rustArch}; \
    rm rustup-init; \
    rustup --version; \
    cargo --version; \
    rustc --version; 

# from https://mirrors.tuna.tsinghua.edu.cn/help/crates.io-index/
RUN echo '[source.crates-io]\n\
replace-with = "mirror"\n\
\n\
[source.mirror]\n\
registry = "sparse+https://mirrors.tuna.tsinghua.edu.cn/crates.io-index/"' >> .cargo/config

ENV ANLTR_VERSION=4.13.1

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --upgrade pip && \
    pip install numpy pyyaml prettytable antlr4-python3-runtime==${ANLTR_VERSION} && \
    rm -rf .cache

WORKDIR /app
