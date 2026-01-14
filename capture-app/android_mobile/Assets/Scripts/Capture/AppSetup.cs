using Cysharp.Threading.Tasks;
using FofX.Stateful;
using Nessle;
using UnityEngine;

namespace PlerionClient.Client
{
    public class AppSetup : MonoBehaviour
    {
        public SceneReferences sceneReferences;
        public LocalizationManager localizationManager;
        public UIPrimitiveSet uiPrimitives;
        public UIElementSet uiElements;

        private void Awake()
        {
            UniTaskScheduler.UnobservedTaskException += Debug.LogException;

            sceneReferences.Initialize();

            Application.targetFrameRate = 120;
            UIBuilder.primitives = uiPrimitives;
            UIElements.elements = uiElements;

            gameObject.AddComponent<App>();

            var env = UnityEnv.GetOrCreateInstance();

            App.state.plerionApiUrl.ExecuteSet(env.plerionApiUrl);
            App.state.plerionAuthTokenUrl.ExecuteSet(env.plerionAuthTokenUrl);
            App.state.plerionAuthAudience.ExecuteSet(env.plerionAuthAudience);

            if (env.loginAutomatically)
                App.ExecuteAction(new LogInAction(env.username, env.password));

            LocalCaptureController.Initialize();
            ZedCaptureController.Initialize();

            Instantiate(localizationManager);

            gameObject.AddComponent<AuthManager>();
            gameObject.AddComponent<CaptureController>();

            Destroy(this);
        }
    }
}
