#if !UNITY_EDITOR && OUTERNET_ANDROID_MOBILE
using UnityEngine;

namespace Outernet.Client
{
    class Platform : MonoBehaviour
    {
        private void Awake()
        {
            PrefabSystem.Create(PrefabSystem.settingsSystemMobile);
        }
    }
}
#endif