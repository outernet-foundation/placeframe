using System;
using FofX.Stateful;

namespace Outernet.MapRegistrationTool
{
    public class ObservablePrimitiveMapInspector : ObservableNodeInspector<IObservablePrimitiveMap>
    {
        protected override IDisposable BindTarget(IObservablePrimitiveMap target)
        {
            var addLeftInputControl = UIBuilder.ValueControl(target.leftType, interactable: props.interactable.value);
            var addRightInputControl = UIBuilder.ValueControl(target.rightType, interactable: props.interactable.value);
            var addValueInputRegion = UIBuilder.HorizontalLayout(
                addLeftInputControl,
                addRightInputControl,
                UIBuilder.Button("Add", () =>
                {
                    UndoRedoManager.RegisterUndo($"Add ({addLeftInputControl.valueAsObject}, {addRightInputControl.valueAsObject})");
                    target.context.ExecuteAction(target, new AddPairAction(addLeftInputControl.valueAsObject, addRightInputControl.valueAsObject));
                },
                interactable: props.interactable.value)
            );

            return Bindings.Compose(
                target.EachRaw(value =>
                {
                    var element = UIBuilder.ListElement(
                        props.interactable.value,
                        () =>
                        {
                            UndoRedoManager.RegisterUndo($"Remove {value}");
                            target.context.ExecuteAction(target, new RemoveLeftAction(((IPrimitiveMapPair)value).left));
                        },
                        UIBuilder.Text(value.ToString())
                    );

                    element.transform.SetParent(rect, false);

                    addValueInputRegion.transform.SetAsLastSibling();

                    return element;
                }),
                addLeftInputControl,
                addLeftInputControl,
                addValueInputRegion
            );
        }

        private class AddPairAction : ObservableNodeAction<IObservablePrimitiveMap>
        {
            private object _left;
            private object _right;

            public AddPairAction(object left, object right)
            {
                _left = left;
                _right = right;
            }

            public override void Execute(IObservablePrimitiveMap target)
            {
                target.Add(_left, _right);
            }
        }

        private class RemoveLeftAction : ObservableNodeAction<IObservablePrimitiveMap>
        {
            private object _left;

            public RemoveLeftAction(object left)
            {
                _left = left;
            }

            public override void Execute(IObservablePrimitiveMap target)
            {
                target.RemoveLeft(_left);
            }
        }
    }
}