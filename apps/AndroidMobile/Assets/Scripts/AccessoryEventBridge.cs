#if !UNITY_EDITOR && UNITY_ANDROID
using System;
using System.Threading;
using UnityEngine;

namespace Placeframe.Client
{
    public sealed class AccessoryEventBridge : AndroidJavaProxy
    {
        private readonly SynchronizationContext mainThread;
        private readonly Action attached;
        private readonly Action detached;
        private readonly Action<bool> permissionResult;

        public AccessoryEventBridge(
            Action onAttached,
            Action onDetached,
            Action<bool> onPermissionResult
        ) : base("io.placeframe.android.AoaAccessoryClient$AccessoryEventListener")
        {
            mainThread = SynchronizationContext.Current;
            this.attached = onAttached;
            this.detached = onDetached;
            this.permissionResult = onPermissionResult;
        }

        public void onAttached() => mainThread.Post(_ => attached?.Invoke(), null);
        public void onDetached() => mainThread.Post(_ => detached?.Invoke(), null);
        public void onPermissionResult(bool granted) =>
            mainThread.Post(_ => permissionResult?.Invoke(granted), null);
    }
}
#endif
