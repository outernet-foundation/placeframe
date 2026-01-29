using FofX;
using FofX.Stateful;

namespace Placeframe.Client
{
    public class App : AppBase<AppState>
    {
        protected override void InitializeState(AppState state) =>
            state.Initialize("root", new ObservableNodeContext(new UnityLogger() { logLevel = FofX.LogLevel.Trace }));
    }
}
