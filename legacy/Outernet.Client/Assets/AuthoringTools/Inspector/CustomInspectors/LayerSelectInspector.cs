using FofX.Stateful;
using System;
using System.Collections.Generic;
using System.Linq;

namespace Outernet.Client.AuthoringTools
{
    public class LayerSelectInspector : CustomObservableNodeInspector
    {
        private List<Guid> _layersInOrder = new List<Guid>();
        private bool _settingFromState = false;

        protected override IDisposable BindTarget(IObservableNode target)
        {
            var layer = (ObservablePrimitive<Guid>)target;
            var dropdown = UIBuilder.Dropdown();

            dropdown.transform.SetParent(rect, false);

            dropdown.AddBinding(
                App.state.layers.Observe(_ =>
                {
                    _settingFromState = true;

                    _layersInOrder.Clear();
                    _layersInOrder.AddRange(App.state.layers
                        .Where(x => x.key != Guid.Empty)
                        .OrderBy(x => x.value.layerName.value)
                        .Select(x => x.key)
                        .Prepend(Guid.Empty)
                    );

                    dropdown.component.ClearOptions();
                    dropdown.component.AddOptions(App.state.layers
                        .Where(x => x.key != Guid.Empty)
                        .Select(x => x.value.layerName.value)
                        .OrderBy(x => x)
                        .Prepend("Default")
                        .ToList()
                    );

                    dropdown.component.value = _layersInOrder.IndexOf(layer.value);

                    _settingFromState = false;
                }),
                layer.OnChange(x =>
                {
                    _settingFromState = true;
                    dropdown.component.value = _layersInOrder.IndexOf(x);
                    _settingFromState = false;
                }),
                dropdown.component.onValueChanged.OnRaised(index =>
                {
                    if (_settingFromState)
                        return;

                    layer.ExecuteSetOrDelay(_layersInOrder[index]);
                })
            );

            return dropdown;
        }
    }
}