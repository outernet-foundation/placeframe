using System;
using System.Linq;
using FofX.Stateful;

namespace Outernet.MapRegistrationTool
{
    public class ObservablePrimitiveInspector : ObservableNodeInspector<IObservablePrimitive>
    {
        private bool _applyingStateChanges;

        protected override IDisposable BindTarget(IObservablePrimitive target)
        {
            var control = UIBuilder.ValueControl(target.primitiveType, interactable: props.interactable.value, attributes: target.attributes.ToArray());

            control.transform.SetParent(rect, false);
            control.valueAsObject = target.GetValue();
            control.onValueChanged += () =>
            {
                if (_applyingStateChanges)
                    return;

                UndoRedoManager.RegisterUndo($"Set {target.nodeName}");
                target.context.ExecuteActionOrDelay(target, new SetPrimitiveValueAction(control.valueAsObject));
            };

            control.AddBinding(target.OnChange(x =>
            {
                _applyingStateChanges = true;
                control.valueAsObject = x;
                _applyingStateChanges = false;
            }));

            return control;
        }

        private class SetPrimitiveValueAction : ObservableNodeAction<IObservablePrimitive>
        {
            private object _value;

            public SetPrimitiveValueAction(object value)
            {
                _value = value;
            }

            public override void Execute(IObservablePrimitive target)
            {
                target.SetValue(_value);
            }
        }
    }
}