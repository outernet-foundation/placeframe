package io.placeframe.android;

import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.Socket;
import java.net.SocketAddress;

import javax.net.SocketFactory;

// Socket wrapping a UsbAccessory FD for OkHttp. The FD is owned by
// AoaAccessoryClient; on any pipe error it tears down the accessory rather
// than letting OkHttp recycle the Socket onto the same shared FD.
final class AoaSocketFactory extends SocketFactory {
    private final FileDescriptor fd;

    AoaSocketFactory(FileDescriptor fd) {
        this.fd = fd;
    }

    @Override public Socket createSocket() { return new AoaSocket(fd); }
    @Override public Socket createSocket(String host, int port) { return createSocket(); }
    @Override public Socket createSocket(String host, int port, InetAddress local, int localPort) { return createSocket(); }
    @Override public Socket createSocket(InetAddress host, int port) { return createSocket(); }
    @Override public Socket createSocket(InetAddress host, int port, InetAddress local, int localPort) { return createSocket(); }
}

final class AoaSocket extends Socket {
    private final FileInputStream in;
    private final FileOutputStream out;
    private volatile boolean closed;

    AoaSocket(FileDescriptor fd) {
        this.in = new FileInputStream(fd);
        this.out = new FileOutputStream(fd);
    }

    @Override public InputStream getInputStream() { return in; }
    @Override public OutputStream getOutputStream() { return out; }
    @Override public void connect(SocketAddress endpoint) {}
    @Override public void connect(SocketAddress endpoint, int timeout) {}
    @Override public boolean isConnected() { return !closed; }
    @Override public boolean isClosed() { return closed; }
    @Override public boolean isBound() { return !closed; }
    @Override public void close() throws IOException {
        // Intentionally empty: AoaAccessoryClient owns the FD lifecycle.
        closed = true;
    }
    @Override public void shutdownInput() {}
    @Override public void shutdownOutput() {}
    @Override public void setTcpNoDelay(boolean on) {}
    @Override public void setKeepAlive(boolean on) {}
    @Override public void setSoTimeout(int timeout) {}
    @Override public int getSoTimeout() { return 0; }
}
