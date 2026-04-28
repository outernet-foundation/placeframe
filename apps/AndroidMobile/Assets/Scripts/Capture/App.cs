using FofX.Stateful;
using FofX;
using ObserveThing;

namespace Placeframe.Client
{
    public class App : AppBase<AppState>
    {
        protected override void InitializeState(AppState state)
            => state.Initialize(
                Settings.DefaultObservationContext,
                new UnityLogger() { logLevel = FofX.LogLevel.Trace },
                "root");
    }
}