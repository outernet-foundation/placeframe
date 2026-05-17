# Rebuild libusb-1.0 with --disable-udev so its hotplug source is a
# NETLINK_KOBJECT_UEVENT socket instead of libudev. The Debian package's
# libudev path needs a udev daemon (not present in containers), so
# libusb_get_device_list returns a frozen snapshot from libusb_init time
# and never reflects subsequent hotplugs — phone replugs and the AOA pid
# flip from 0x4EE2 to 0x2D0x are invisible to the long-running bridge.
# The netlink backend works in any container that shares the host's user
# namespace (plain Docker without userns-remap); it does not work in
# rootless or user-namespaced containers, where uevents are filtered by
# the kernel before they reach the container.
FROM python:3.13-slim@sha256:dc1546eefcbe8caaa1f004f16ab76b204b5e1dbd58ff81b899f21cd40541232f AS libusb-builder

ARG LIBUSB_COMMIT=a61afe5f75d969c4561a1d0ad753aa23cee6329a

RUN apt-get update -qq \
    && apt-get install -y --no-install-recommends \
        autoconf \
        automake \
        build-essential \
        ca-certificates \
        git \
        libtool \
        m4 \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
# NOCONFIGURE=1 stops autogen.sh from execing ./configure itself with its
# own arg set (which omits --disable-udev and so fails on missing libudev).
RUN git clone https://github.com/libusb/libusb.git . \
    && git checkout ${LIBUSB_COMMIT} \
    && NOCONFIGURE=1 ./autogen.sh \
    && ./configure --disable-udev --prefix=/usr/local \
    && make -j"$(nproc)" \
    && make install DESTDIR=/staging


FROM python:3.13-slim@sha256:dc1546eefcbe8caaa1f004f16ab76b204b5e1dbd58ff81b899f21cd40541232f

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app/aoa-bridge

ENV \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_INSTALLER_METADATA=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/uv/venv \
    VIRTUAL_ENV=/opt/uv/venv \
    PATH=/opt/uv/venv/bin:$PATH

# pyusb resolves libusb via ctypes.util.find_library, which uses the
# dynamic linker cache; ldconfig picks up the netlink-built .so in
# /usr/local/lib. Base stays slim (glibc) rather than alpine (musl)
# because find_library is a no-op on musl.
COPY --from=libusb-builder /staging/usr/local/lib/ /usr/local/lib/
RUN ldconfig

RUN uv venv $UV_PROJECT_ENVIRONMENT

COPY docker/aoa-bridge/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

COPY docker/aoa-bridge /app/aoa-bridge
RUN uv pip install --no-deps --no-sources /app/aoa-bridge

RUN uv pip check

CMD ["aoa-bridge"]
