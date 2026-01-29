using System;
using System.Linq;
using FofX.Stateful;

namespace Outernet.Client.AuthoringTools
{
    public class ObservableObjectInspector : ObservableNodeInspector<ObservableObject>
    {
        protected override IDisposable BindTarget(ObservableObject target)
        {
            return Bindings.Compose(target.children.Select(x =>
            {
                var element = UIBuilder.NodeInspector(x.nodeName, x, interactable: props.interactable.value);
                element.transform.SetParent(rect, false);
                return element;
            }));
        }
    }
}