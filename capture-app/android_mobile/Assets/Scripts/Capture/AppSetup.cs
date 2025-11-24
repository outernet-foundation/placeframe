using UnityEngine;
using FofX.Stateful;
using Nessle;
using Cysharp.Threading.Tasks;

namespace PlerionClient.Client
{
    public class AppSetup : MonoBehaviour
    {
        public CaptureController captureControllerPrefab;
        // public bool overridePlerionAPIBaseURL;
        // public string overrideDeviceName;
        public bool overridePlerionBaseURL;
        public string plerionBaseURL;
        public UIPrimitiveSet uiPrimitives;

        private void Awake()
        {
            UniTaskScheduler.UnobservedTaskException += Debug.LogException;

            Application.targetFrameRate = 120;
            UIBuilder.primitives = uiPrimitives;

            gameObject.AddComponent<App>();

#if UNITY_EDITOR
            var editorSettings = EditorSettings.GetOrCreateInstance();
            if (editorSettings.overrideEnvironment)
            {
                plerionBaseURL = editorSettings.plerionBaseURL;
            }
#endif

            App.state.plerionAPIBaseUrl.ExecuteSet(plerionBaseURL);

            LocalCaptureController.Initialize();
            ZedCaptureController.Initialize();
            Instantiate(captureControllerPrefab);

            Destroy(this);
        }
    }
}