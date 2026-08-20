# typings/

## What this is

Hand-vendored `.pyi` stub overrides for third-party C-extension packages that do not ship type information. Pyright/basedpyright reads `./typings/` as `stubPath` by default, ahead of any stubs the wheel ships, so anything in this tree shadows the package's bundled stubs.

## Shape

```
typings/
├── multipart.pyi       # python-multipart, no upstream stubs
├── pyzed/              # Stereolabs ZED SDK Python bindings, no upstream stubs
└── usb1/               # libusb1, no upstream stubs
```

Every package in this tree is one we use that does not publish its own typed surface. They're stable and rarely change. When upstream starts shipping a `py.typed`-marked package, drop our override and use theirs.
