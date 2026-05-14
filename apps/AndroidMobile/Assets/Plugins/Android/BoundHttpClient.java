package io.placeframe.android;

import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.NetworkRequest;

import java.io.IOException;
import java.io.InputStream;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

import okhttp3.Dns;
import okhttp3.Headers;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import okio.BufferedSink;

// Java façade over okhttp 5.x consumed by AndroidBoundHttpHandler.cs via JNI.
// AndroidBoundHttpHandler.cs documents the why; this class does the how. The
// split exists because every JNI hop has measurable overhead in tight loops
// (response-header walks, body-read chunks), so the Java side both owns the
// connectivity API surface and pre-marshals results into JNI-cheap shapes.
//
// One OkHttpClient per android.net.Network — equality on Network keys off netid,
// so getAllNetworks() returning the same logical network in successive lookups
// hits the cache and the client's pool. socketFactory and dns are both pinned
// to the Network: the SocketFactory binds every outbound TCP socket to that
// Network, and the Dns implementation routes hostname resolution through
// Network.getAllByName so DNS lookups can't escape to a different bearer.
// IP-literal URLs (e.g. ZED at 192.168.55.1:9000) skip resolution and go
// straight to socketFactory.
public final class BoundHttpClient {
    private static final ConcurrentHashMap<Network, OkHttpClient> clients = new ConcurrentHashMap<>();

    private BoundHttpClient() {}

    public static List<ConnectivityManager.NetworkCallback> requestNetworks(ConnectivityManager cm, int[] transports) {
        List<ConnectivityManager.NetworkCallback> callbacks = new ArrayList<>();
        for (int transport : transports) {
            ConnectivityManager.NetworkCallback callback = new ConnectivityManager.NetworkCallback();
            cm.requestNetwork(
                new NetworkRequest.Builder()
                    .addTransportType(transport)
                    .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
                    .build(),
                callback
            );
            callbacks.add(callback);
        }
        return callbacks;
    }

    public static Network findMatchingNetwork(ConnectivityManager cm, int[] transports) {
        for (int transport : transports) {
            for (Network network : cm.getAllNetworks()) {
                NetworkCapabilities caps = cm.getNetworkCapabilities(network);
                if (caps != null
                    && caps.hasTransport(transport)
                    && caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)) {
                    return network;
                }
            }
        }
        return null;
    }

    // Per-chunk progress callbacks invoke during the body write to the okhttp sink,
    // which happens on the okhttp dispatcher thread — not the calling thread. Callers
    // that touch UI from the callback must marshal back themselves. A null callback
    // disables progress reporting and uses okhttp's default fixed-buffer write path.
    public interface ProgressCallback {
        void onProgress(long bytesWritten, long totalBytes);
    }

    public static HttpResult execute(
        Network network,
        String method,
        String url,
        String[] headerNames,
        String[] headerValues,
        byte[] body,
        String contentType,
        ProgressCallback progressCallback
    ) throws IOException {
        Request.Builder builder = new Request.Builder().url(url);
        for (int i = 0; i < headerNames.length; i++) {
            builder.addHeader(headerNames[i], headerValues[i]);
        }

        boolean methodRequiresBody = method.equals("POST") || method.equals("PUT") || method.equals("PATCH");
        RequestBody requestBody;
        if (body != null) {
            MediaType mediaType = contentType != null ? MediaType.parse(contentType) : null;
            if (progressCallback != null) {
                requestBody = new ProgressRequestBody(body, mediaType, progressCallback);
            } else {
                requestBody = RequestBody.create(body, mediaType);
            }
        } else if (methodRequiresBody) {
            requestBody = RequestBody.create(new byte[0], null);
        } else {
            requestBody = null;
        }
        builder.method(method, requestBody);

        Response response = clients.computeIfAbsent(network, n -> new OkHttpClient.Builder()
            .socketFactory(n.getSocketFactory())
            .dns(hostname -> Arrays.asList(n.getAllByName(hostname)))
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .pingInterval(30, TimeUnit.SECONDS)
            .followRedirects(false)
            .build()
        ).newCall(builder.build()).execute();

        Headers responseHeaders = response.headers();
        String[] respNames = new String[responseHeaders.size()];
        String[] respValues = new String[responseHeaders.size()];
        for (int i = 0; i < responseHeaders.size(); i++) {
            respNames[i] = responseHeaders.name(i);
            respValues[i] = responseHeaders.value(i);
        }
        return new HttpResult(
            response.code(),
            respNames,
            respValues,
            response,
            response.body() != null ? response.body().byteStream() : null
        );
    }

    // Reads up to maxSize bytes; returns the (trimmed) chunk or null at EOF.
    // Unity's byte[] auto-marshal copies the array into the managed heap.
    // okhttp's ResponseBody#byteStream is not safe to call repeatedly (each call
    // wraps the underlying source in a fresh InputStream that races on shared
    // state), so HttpResult.bodyStream is extracted exactly once and that same
    // InputStream is fed back here per chunk.
    public static byte[] readChunk(InputStream stream, int maxSize) throws IOException {
        byte[] buffer = new byte[maxSize];
        int read = stream.read(buffer);
        if (read <= 0) return null;
        return read < maxSize ? Arrays.copyOf(buffer, read) : buffer;
    }

    public static void closeResponse(Response response) {
        try { response.close(); } catch (Exception ignored) {}
    }

    public static final class HttpResult {
        public final int statusCode;
        public final String[] headerNames;
        public final String[] headerValues;
        public final Response response;
        public final InputStream bodyStream;

        HttpResult(int statusCode, String[] headerNames, String[] headerValues, Response response, InputStream bodyStream) {
            this.statusCode = statusCode;
            this.headerNames = headerNames;
            this.headerValues = headerValues;
            this.response = response;
            this.bodyStream = bodyStream;
        }
    }

    // Custom RequestBody that walks the in-memory byte[] in 64KB chunks, flushing
    // after each chunk so the bytes hit the okhttp BufferedSink (and from there
    // the socket) before the next progress callback fires. okhttp's default
    // byte[] RequestBody writes the whole array in one sink.write() call with
    // no intermediate sink.flush(), so we never observe partial-write progress.
    private static final class ProgressRequestBody extends RequestBody {
        private static final int CHUNK_SIZE = 64 * 1024;

        private final byte[] data;
        private final MediaType mediaType;
        private final ProgressCallback callback;

        ProgressRequestBody(byte[] data, MediaType mediaType, ProgressCallback callback) {
            this.data = data;
            this.mediaType = mediaType;
            this.callback = callback;
        }

        @Override public MediaType contentType() { return mediaType; }
        @Override public long contentLength() { return data.length; }

        @Override
        public void writeTo(BufferedSink sink) throws IOException {
            long total = data.length;
            long written = 0;
            while (written < total) {
                int n = (int) Math.min(CHUNK_SIZE, total - written);
                sink.write(data, (int) written, n);
                written += n;
                sink.flush();
                callback.onProgress(written, total);
            }
        }
    }
}
