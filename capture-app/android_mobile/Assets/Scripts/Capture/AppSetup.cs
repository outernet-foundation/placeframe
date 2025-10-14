using UnityEngine;
using FofX.Stateful;
using Nessle;

namespace PlerionClient.Client
{
    public class AppSetup : MonoBehaviour
    {
        public CaptureController captureControllerPrefab;
        public bool overridePlerionAPIBaseURL;
        public string plerionAPIBaseURL;
        public UIPrimitiveSet uiPrimitives;

        private void Awake()
        {
            Application.targetFrameRate = 120;
            UIBuilder.primitives = uiPrimitives;

            gameObject.AddComponent<App>();
            var plerionAPIBaseUrl = overridePlerionAPIBaseURL ?
                plerionAPIBaseURL : "https://api.outernetfoundation.org";

#if UNITY_EDITOR
            var editorSettings = EditorSettings.GetOrCreateInstance();
            if (editorSettings.overrideEnvironment)
                plerionAPIBaseUrl = editorSettings.overrideEnvironmentURL;
#endif

            App.state.plerionAPIBaseUrl.ExecuteSet(plerionAPIBaseUrl);

            ZedCaptureController.Initialize();
            Instantiate(captureControllerPrefab);

            Destroy(this);
        }
    }
}