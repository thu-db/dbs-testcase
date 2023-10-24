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
    DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y g++ cmake build-essential git curl apt-transport-https ca-certificates && \
    rm -rf /var/lib/apt/lists/

RUN useradd --create-home --shell /bin/bash tester

USER tester
WORKDIR /home/tester

RUN curl https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda.sh && \
    bash miniconda.sh -b && \
    rm miniconda.sh

ENV PATH="/home/tester/miniconda3/bin:$PATH"
ENV ANLTR_VERSION=4.13.1

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --upgrade pip && \
    pip install numpy pyyaml prettytable antlr4-python3-runtime==${ANLTR_VERSION} && \
    rm -rf .cache

WORKDIR /app
