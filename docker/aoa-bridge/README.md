# aoa-bridge

USB-host daemon that handshakes a connected Android phone into [AOA accessory mode](https://source.android.com/docs/core/interaction/accessories/aoa) and forwards the bulk-endpoint bytes to `zed-capture`'s HTTP server at `127.0.0.1:9000`. The phone app speaks HTTP/1.1 directly to the accessory FD with no IP layer between them.

See `docker/aoa-bridge/CLAUDE.md` for protocol, deployment, and operational notes.
