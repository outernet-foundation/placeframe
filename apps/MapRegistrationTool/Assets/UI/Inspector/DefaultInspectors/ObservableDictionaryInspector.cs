using System;

using FofX.Stateful;

namespace Placeframe.MapRegistrationTool
{
    public class ObservableDictionaryInspector : ObservableNodeInspector<IObservableDictionary>
    {
        private ValueControl _addValueInputField;

        protected override IDisposable BindTarget(IObservableDictionary target)
        {
            var addValueInputField = UIBuilder.ValueControl(target.keyType, interactable: props.interactable.value);
            var addValueInputRegion = UIBuilder.HorizontalLayout(
                addValueInputField,
                UIBuilder.Button(
                    "Add",
                    () =>
                    {
                        UndoRedoManager.RegisterUndo($"Add {_addValueInputField.valueAsObject}");
                        target.context.ExecuteAction(target, new AddKeyAction(_addValueInputField.valueAsObject));
                    },
                    interactable: props.interactable.value
                )
            );

            addValueInputRegion.transform.SetParent(rect, false);

            return Bindings.Compose(
                addValueInputField,
                target.EachRaw(entry =>
                {
                    var kvp = (IKVP)entry;
                    var element = UIBuilder.ListElement(
                        props.interactable.value,
                        () =>
                        {
                            UndoRedoManager.RegisterUndo($"Remove {kvp.keyAsObject}");
                            target.context.ExecuteAction(target, new RemoveKeyAction(kvp.keyAsObject));
                        },
                        UIBuilder.NodeInspector(kvp.keyAsObject.ToString(), (IObservableNode)kvp.valueAsObject, interactable: props.interactable.value)
                    );

                    element.transform.SetParent(rect, false);

                    addValueInputRegion.transform.SetAsLastSibling();

                    return element;
                })
            );
        }

        private class AddKeyAction : ObservableNodeAction<IObservableDictionary>
        {
            private object _key;

            public AddKeyAction(object key)
            {
                _key = key;
            }

            public override void Execute(IObservableDictionary target)
            {
                target.Add(_key);
            }
        }

        private class RemoveKeyAction : ObservableNodeAction<IObservableDictionary>
        {
            private object _key;

            public RemoveKeyAction(object key)
            {
                _key = key;
            }

            public override void Execute(IObservableDictionary target)
            {
                target.Remove(_key);
            }
        }
    }
}