using System;
using FofX.Stateful;

namespace Placeframe.MapRegistrationTool
{
    public class ObservableSetInspector : ObservableNodeInspector<IObservableSet>
    {
        protected override IDisposable BindTarget(IObservableSet target)
        {
            var addValueInputField = UIBuilder.ValueControl(target.itemType, interactable: props.interactable.value);
            var addValueInputRegion = UIBuilder.HorizontalLayout(
                addValueInputField,
                UIBuilder.Button(
                    "Add",
                    () =>
                    {
                        UndoRedoManager.RegisterUndo($"Add {addValueInputField.valueAsObject}");
                        target.context.ExecuteAction(target, new AddItemAction(addValueInputField.valueAsObject));
                    },
                    interactable: props.interactable.value
                )
            );

            addValueInputRegion.transform.SetParent(rect, false);

            return Bindings.Compose(
                addValueInputRegion,
                target.EachRaw(value =>
                {
                    var element = UIBuilder.ListElement(
                        props.interactable.value,
                        () =>
                        {
                            UndoRedoManager.RegisterUndo($"Remove {value}");
                            target.context.ExecuteAction(target, new RemoveItemAction(value));
                        },
                        UIBuilder.Text(value.ToString())
                    );

                    element.transform.SetParent(rect, false);

                    addValueInputRegion.transform.SetAsLastSibling();

                    return element;
                })
            );
        }

        private class AddItemAction : ObservableNodeAction<IObservableSet>
        {
            private object _item;

            public AddItemAction(object item)
            {
                _item = item;
            }

            public override void Execute(IObservableSet target)
            {
                target.Add(_item);
            }
        }

        private class RemoveItemAction : ObservableNodeAction<IObservableSet>
        {
            private object _item;

            public RemoveItemAction(object item)
            {
                _item = item;
            }

            public override void Execute(IObservableSet target)
            {
                target.Remove(_item);
            }
        }
    }
}