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
import java.util.concurrent.atomic.AtomicBoolean;

import javax.net.SocketFactory;

// Socket wrapping a UsbAccessory FD for OkHttp. The FD is owned by
// AoaAccessoryClient; on any pipe error it tears down the accessory rather
// than letting OkHttp recycle the Socket onto the same shared FD.
//
// One factory instance per accessory FD lifetime. `socketIssued` enforces
// that at most one live AoaSocket wraps the FD at a time: a second
// createSocket() while the first is alive throws AoaConcurrentConnectionException
// so OkHttp's pool can't silently open a parallel h2c connection over the
// same wire (which would interleave preface bytes and produce a
// FRAME_SIZE_ERROR GOAWAY). AoaSocket.close() releases the flag, so the
// next OkHttp connection attempt (after the live one drops) is allowed.
final class AoaSocketFactory extends SocketFactory {
    private final FileDescriptor fd;
    private final AtomicBoolean socketIssued = new AtomicBoolean(false);

    AoaSocketFactory(FileDescriptor fd) {
        this.fd = fd;
    }

    @Override public Socket createSocket() throws IOException {
        if (!socketIssued.compareAndSet(false, true)) {
            throw new AoaConcurrentConnectionException(
                "AoaSocketFactory: refusing concurrent socket on shared AOA FD"
            );
        }
        return new AoaSocket(fd, () -> socketIssued.set(false));
    }
    @Override public Socket createSocket(String host, int port) throws IOException { return createSocket(); }
    @Override public Socket createSocket(String host, int port, InetAddress local, int localPort) throws IOException { return createSocket(); }
    @Override public Socket createSocket(InetAddress host, int port) throws IOException { return createSocket(); }
    @Override public Socket createSocket(InetAddress host, int port, InetAddress local, int localPort) throws IOException { return createSocket(); }
}

// Marker IOException for "OkHttp asked for a second socket while one is
// already live on this FD." Distinguished from a real pipe error so
// AoaAccessoryClient.execute() can fail just this request without tearing
// down the surviving connection that holds the FD.
final class AoaConcurrentConnectionException extends IOException {
    AoaConcurrentConnectionException(String message) { super(message); }
}

final class AoaSocket extends Socket {
    private final FileInputStream in;
    private final FileOutputStream out;
    private final Runnable onClose;
    private volatile boolean closed;

    AoaSocket(FileDescriptor fd, Runnable onClose) {
        this.in = new FileInputStream(fd);
        this.out = new FileOutputStream(fd);
        this.onClose = onClose;
    }

    @Override public InputStream getInputStream() { return in; }
    @Override public OutputStream getOutputStream() { return out; }
    @Override public void connect(SocketAddress endpoint) {}
    @Override public void connect(SocketAddress endpoint, int timeout) {}
    @Override public boolean isConnected() { return !closed; }
    @Override public boolean isClosed() { return closed; }
    @Override public boolean isBound() { return !closed; }
    @Override public void close() throws IOException {
        // FD lifecycle is owned by AoaAccessoryClient; the close hook only
        // releases the factory's single-socket guard so a subsequent OkHttp
        // connection attempt can proceed.
        if (closed) return;
        closed = true;
        onClose.run();
    }
    @Override public void shutdownInput() {}
    @Override public void shutdownOutput() {}
    @Override public void setTcpNoDelay(boolean on) {}
    @Override public void setKeepAlive(boolean on) {}
    @Override public void setSoTimeout(int timeout) {}
    @Override public int getSoTimeout() { return 0; }
}
