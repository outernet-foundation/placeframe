using FofX.Stateful;
using FofX;

namespace PlerionClient.Client
{
    public class App : AppBase<AppState>
    {
        protected override void InitializeState(AppState state)
            => state.Initialize("root", new ObservableNodeContext(new UnityLogger() { logLevel = FofX.LogLevel.Trace }));
    }
}