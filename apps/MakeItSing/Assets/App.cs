using FofX;
using FofX.Stateful;

namespace Plerion.MakeItSing
{
    public class App : AppBase<AppState>
    {
        protected override void InitializeState(AppState state)
        {
            state.Initialize("root", new ObservableNodeContext());
        }
    }
}