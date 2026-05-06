using FofX.Stateful;
using FofX;
using Nessle;
using ObserveThing;
using UnityEngine;
using static Placeframe.Client.UIElements;

namespace Placeframe.Client
{
    public class App : AppBase<AppState>
    {
        private IControl ui;

        protected override void InitializeState(AppState state)
            => state.Initialize(
                Settings.DefaultObservationContext,
                new UnityLogger() { logLevel = FofX.LogLevel.Trace },
                "root");

        protected override void Awake()
        {
            base.Awake();
            ui = AppUI();
        }

        void OnDestroy()
        {
            ui?.Dispose();
        }
    }
}
