using System;
using FofX.Stateful;
using TMPro;

namespace Outernet.Client.AuthoringTools
{
    public class DefaultObservableNodeInspector : ObservableNodeInspector<IObservableNode>
    {
        protected override IDisposable BindTarget(IObservableNode target)
        {
            var json = UIBuilder.Text();
            json.transform.SetParent(rect, false);
            json.AddBinding(Bindings.Observer(
                _ => json.component.text = props.ToJSON(x => true).ToString(),
                ObservationScope.All,
                props
            ));

            return json;
        }
    }
}