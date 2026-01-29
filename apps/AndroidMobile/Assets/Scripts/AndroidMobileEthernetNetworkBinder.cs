#if !UNITY_EDITOR && UNITY_ANDROID
using UnityEngine;
using Cysharp.Threading.Tasks;

public static class AndroidMobileEthernetNetworkBinder
{
    private static AndroidJavaObject connectivityManager;

    public static void Initialize()
    {
        var activity   = new AndroidJavaClass("com.unity3d.player.UnityPlayer")
            .GetStatic<AndroidJavaObject>("currentActivity");
        var appContext = activity.Call<AndroidJavaObject>("getApplicationContext");
        connectivityManager = appContext.Call<AndroidJavaObject>("getSystemService", new object[] { "connectivity" });
    }

    // Fail-fast: returns false if no ethernet network is currently up.
    public static UniTask<bool> Enter()
    {
        if (connectivityManager == null) throw new System.InvalidOperationException("Call Initialize() first.");

        var capsClass = new AndroidJavaClass("android.net.NetworkCapabilities");
        int TRANSPORT_ETHERNET = capsClass.GetStatic<int>("TRANSPORT_ETHERNET");

        // connectivityManager.getAllNetworks()
        var networks = connectivityManager.Call<AndroidJavaObject[]>("getAllNetworks");
        if (networks != null)
        {
            foreach (var n in networks)
            {
                // connectivityManager.getNetworkCapabilities(network)
                var caps = connectivityManager.Call<AndroidJavaObject>("getNetworkCapabilities", new object[] { n });
                if (caps != null && caps.Call<bool>("hasTransport", new object[] { TRANSPORT_ETHERNET }))
                {
                    bool ok = connectivityManager.Call<bool>("bindProcessToNetwork", new object[] { n });
                    return UniTask.FromResult(ok);
                }
            }
        }
        return UniTask.FromResult(false);
    }

    public static void Exit()
    {
        if (connectivityManager == null) throw new System.InvalidOperationException("Call Initialize() first.");
        connectivityManager.Call<bool>("bindProcessToNetwork", new object[] { null });
    }
}

#endif