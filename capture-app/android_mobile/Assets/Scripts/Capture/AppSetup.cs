using UnityEngine;
using FofX.Stateful;
using Nessle;

namespace PlerionClient.Client
{
    public class AppSetup : MonoBehaviour
    {
        public CaptureController captureControllerPrefab;
        public bool overridePlerionAPIBaseURL;
        public string overrideDeviceName;
        public UIPrimitiveSet uiPrimitives;

        private void Awake()
        {
            Application.targetFrameRate = 120;
            UIBuilder.primitives = uiPrimitives;

            gameObject.AddComponent<App>();
            var plerionAPIBaseUrl = overridePlerionAPIBaseURL ?
                $"https://{overrideDeviceName}-api.outernetfoundation.org" : "https://api.outernetfoundation.org";
            var keycloakBaseUrl = overridePlerionAPIBaseURL ?
                $"https://{overrideDeviceName}-keycloak.outernetfoundation.org" : "https://keycloak.outernetfoundation.org";

#if UNITY_EDITOR
            var editorSettings = EditorSettings.GetOrCreateInstance();
            if (editorSettings.overrideEnvironment)
            {
                plerionAPIBaseUrl = $"https://{editorSettings.overrideDeviceName}-api.outernetfoundation.org";
                keycloakBaseUrl = $"https://{editorSettings.overrideDeviceName}-keycloak.outernetfoundation.org";
            }
#endif

            App.state.plerionAPIBaseUrl.ExecuteSet(plerionAPIBaseUrl);
            App.state.plerionKeycloakUrl.ExecuteSet(keycloakBaseUrl);

            LocalCaptureController.Initialize();
            ZedCaptureController.Initialize();
            Instantiate(captureControllerPrefab);

            Destroy(this);
        }
    }
}