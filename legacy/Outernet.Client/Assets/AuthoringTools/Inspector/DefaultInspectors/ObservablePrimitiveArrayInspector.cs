using System;
using System.Linq;
using System.Collections.Generic;

using UnityEngine;
using UnityEngine.UI;

using FofX.Stateful;
using TMPro;

namespace Outernet.Client.AuthoringTools
{
    public class ObservablePrimitiveArrayInspector : ObservableNodeInspector<IObservablePrimitiveArray>
    {
        private List<ComponentView<TextMeshProUGUI>> _listElements = new List<ComponentView<TextMeshProUGUI>>();

        protected override IDisposable BindTarget(IObservablePrimitiveArray target)
        {
            return Bindings.Compose(
                Bindings.Observer(
                    _ =>
                    {
                        while (_listElements.Count > target.count)
                        {
                            Destroy(_listElements[_listElements.Count - 1].gameObject);
                            _listElements.RemoveAt(_listElements.Count - 1);
                        }

                        while (_listElements.Count < target.count)
                        {
                            ComponentView<TextMeshProUGUI> label = UIBuilder.Text();
                            label.component.textWrappingMode = TextWrappingModes.NoWrap;
                            label.component.overflowMode = TextOverflowModes.Ellipsis;
                            _listElements.Add(label);
                            label.transform.SetParent(rect, false);
                        }

                        var index = 0;

                        foreach (var element in target.Cast<object>())
                        {
                            _listElements[index].component.text = element.ToString();
                            index++;
                        }
                    },
                    ObservationScope.Self,
                    props
                ),
                Bindings.OnRelease(() =>
                {
                    foreach (var element in _listElements)
                        Destroy(element.gameObject);
                })
            );
        }
    }
}