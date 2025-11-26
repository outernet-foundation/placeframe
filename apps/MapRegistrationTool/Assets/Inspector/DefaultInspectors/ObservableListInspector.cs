using System;

using FofX.Stateful;

namespace Outernet.MapRegistrationTool
{
    public class ObservableListInspector : ObservableNodeInspector<IObservableList>
    {
        protected override IDisposable BindTarget(IObservableList target)
        {
            var addButton = UIBuilder.Button(
                "Add",
                () =>
                {
                    UndoRedoManager.RegisterUndo("Add Item");
                    target.context.ExecuteAction(target, new AddElementAction());
                },
                props.interactable.value
            );

            addButton.transform.SetParent(rect, false);

            return Bindings.Compose(
                addButton,
                target.EachRaw(obj =>
                {
                    var node = (IObservableNode)obj;
                    var element = UIBuilder.ListElement(
                        props.interactable.value,
                        () =>
                        {
                            UndoRedoManager.RegisterUndo($"Remove Item {target.IndexOf(node)}");
                            target.context.ExecuteAction(target, new RemoveElementAction(node));
                        },
                        UIBuilder.NodeInspector(node.nodeName, node, interactable: props.interactable.value)
                    );

                    element.transform.SetParent(rect, false);
                    element.transform.SetSiblingIndex(target.IndexOf(node));

                    addButton.transform.SetAsLastSibling();

                    return element;
                })
            );
        }

        private class AddElementAction : ObservableNodeAction<IObservableList>
        {
            public override void Execute(IObservableList target)
            {
                target.Add();
            }
        }

        private class RemoveElementAction : ObservableNodeAction<IObservableList>
        {
            private IObservableNode _element;

            public RemoveElementAction(IObservableNode element)
            {
                _element = element;
            }

            public override void Execute(IObservableList target)
            {
                target.Remove(_element);
            }
        }
    }
}