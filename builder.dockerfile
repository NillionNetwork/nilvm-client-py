FROM debian:12-slim

ENV SELF_VERSION=0.1.0

RUN apt update && \
    apt install -y --no-install-recommends cmake git ca-certificates curl build-essential

RUN mkdir /opt/macos-sdk && \
    git clone https://github.com/hexops-graveyard/sdk-macos-12.0.git /opt/macos-sdk/12.0

ENV SDKROOT=/opt/macos-sdk/12.0/root

RUN curl -LsSf https://astral.sh/uv/0.4.24/install.sh | sh

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ENV PATH=/root/.cargo/bin:$PATH

RUN cargo install just