package io.placeframe.android;

import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.hardware.usb.UsbAccessory;
import android.hardware.usb.UsbManager;
import android.os.Build;
import android.os.ParcelFileDescriptor;

import java.io.IOException;
import java.io.InputStream;
import java.net.InetAddress;
import java.util.Arrays;
import java.util.Collections;
import java.util.concurrent.TimeUnit;

import okhttp3.ConnectionPool;
import okhttp3.Dispatcher;
import okhttp3.Headers;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Protocol;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

// Vendored OkHttp + custom SocketFactory because HttpURLConnection has no
// public API to inject a SocketFactory for plain HTTP, so it can't be
// aimed at the accessory FD.
public final class AoaAccessoryClient {
    private static final String PERMISSION_ACTION = "io.placeframe.android.USB_ACCESSORY_PERMISSION";
    private static final long PERMISSION_REQUEST_COOLDOWN_MS = 5_000L;

    private static final Object lock = new Object();
    private static volatile ParcelFileDescriptor currentPfd;
    private static volatile OkHttpClient currentClient;
    private static long lastPermissionRequestMs;

    private AoaAccessoryClient() {}

    public static HttpResult execute(
        Context context,
        String method,
        String url,
        String[] headerNames,
        String[] headerValues,
        byte[] body,
        String contentType
    ) throws IOException {
        synchronized (lock) {
            String openError = tryOpenLocked(context);
            if (openError != null) {
                throw new IOException("AOA accessory not ready (" + openError + ")");
            }

            OkHttpClient client = currentClient;
            Request.Builder builder = new Request.Builder().url(url);
            for (int i = 0; i < headerNames.length; i++) {
                builder.addHeader(headerNames[i], headerValues[i]);
            }
            boolean methodRequiresBody = method.equals("POST") || method.equals("PUT") || method.equals("PATCH");
            RequestBody requestBody;
            if (body != null) {
                requestBody = RequestBody.create(body, contentType != null ? MediaType.parse(contentType) : null);
            } else if (methodRequiresBody) {
                requestBody = RequestBody.create(new byte[0], null);
            } else {
                requestBody = null;
            }
            builder.method(method, requestBody);

            Response response;
            try {
                response = client.newCall(builder.build()).execute();
            } catch (IOException e) {
                // Pipe error poisons the FD; reopen on next execute.
                OkHttpClient oldClient = currentClient;
                ParcelFileDescriptor oldPfd = currentPfd;
                currentClient = null;
                currentPfd = null;
                if (oldClient != null) {
                    oldClient.dispatcher().executorService().shutdown();
                    oldClient.connectionPool().evictAll();
                }
                if (oldPfd != null) {
                    try { oldPfd.close(); } catch (IOException ignored) {}
                }
                throw e;
            }

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
    }

    public static byte[] readChunk(InputStream stream, int maxSize) throws IOException {
        byte[] buffer = new byte[maxSize];
        int read = stream.read(buffer);
        if (read <= 0) return null;
        return read < maxSize ? Arrays.copyOf(buffer, read) : buffer;
    }

    public static void closeResponse(Response response) {
        if (response == null) return;
        try { response.close(); } catch (Exception ignored) {}
    }

    // Returns null on success, an error description on failure.
    // Caller must hold `lock`.
    private static String tryOpenLocked(Context context) {
        if (currentPfd != null) return null;
        UsbManager manager = (UsbManager) context.getSystemService(Context.USB_SERVICE);
        if (manager == null) return "UsbManager=null";
        UsbAccessory[] list = manager.getAccessoryList();
        if (list == null || list.length == 0) return "accessoryList=empty";
        UsbAccessory accessory = list[0];

        if (!manager.hasPermission(accessory)) {
            String error = "accessory=" + accessory.getManufacturer() + "/" + accessory.getModel()
                + "/" + accessory.getVersion() + " hasPermission=false";
            long now = System.currentTimeMillis();
            if (now - lastPermissionRequestMs < PERMISSION_REQUEST_COOLDOWN_MS) return error;
            lastPermissionRequestMs = now;
            // FLAG_MUTABLE required on Android 12+ for
            // EXTRA_PERMISSION_GRANTED to attach to the broadcast.
            int flags = PendingIntent.FLAG_UPDATE_CURRENT;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                flags |= PendingIntent.FLAG_MUTABLE;
            }
            Intent intent = new Intent(PERMISSION_ACTION);
            // Android 14 rejects implicit broadcasts.
            intent.setPackage(context.getPackageName());
            PendingIntent pi = PendingIntent.getBroadcast(context, 0, intent, flags);
            manager.requestPermission(accessory, pi);
            return error;
        }

        ParcelFileDescriptor pfd = manager.openAccessory(accessory);
        if (pfd == null) return "openAccessory returned null";
        currentPfd = pfd;

        Dispatcher dispatcher = new Dispatcher();
        dispatcher.setMaxRequests(1);
        dispatcher.setMaxRequestsPerHost(1);
        currentClient = new OkHttpClient.Builder()
            .socketFactory(new AoaSocketFactory(pfd.getFileDescriptor()))
            // OkHttp resolves the URL hostname before invoking the
            // SocketFactory, even when the resolved address is never
            // dialled. The accessory FD has no IP identity, so feed
            // OkHttp a synthetic loopback address keyed on the host
            // name — AoaSocket.connect() ignores it.
            .dns(host -> Collections.singletonList(InetAddress.getByAddress(host, new byte[] {127, 0, 0, 1})))
            // Pin HTTP/1.1: defends against OkHttp default-changes; uvicorn
            // doesn't speak HTTP/2 anyway.
            .protocols(Collections.singletonList(Protocol.HTTP_1_1))
            .dispatcher(dispatcher)
            // One connection, never evicted — the AOA FD can't back a fresh
            // Socket on reconnect. On any pipe error execute() tears the
            // whole client down.
            .connectionPool(new ConnectionPool(1, 1, TimeUnit.DAYS))
            .retryOnConnectionFailure(false)
            .followRedirects(false)
            .connectTimeout(2, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(15, TimeUnit.SECONDS)
            .build();
        return null;
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
}
