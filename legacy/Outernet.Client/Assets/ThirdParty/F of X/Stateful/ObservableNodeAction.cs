using System;
using System.Collections.Generic;
using System.Reflection;

namespace FofX.Stateful
{
    public abstract class ObservableNodeAction<T> where T : IObservableNode
    {
        public abstract void Execute(T target);

        public override string ToString()
        {
            return $"{this.GetType().Name}[{string.Join(", ", GetFieldsAndValues())}]";
        }

        private IEnumerable<string> GetFieldsAndValues()
        {
            Type type = GetType();
            while (type != typeof(object))
            {
                foreach (var field in type.GetFields(BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public))
                    yield return ($"{field.Name}={field.GetValue(this)}").Replace("_", null);

                type = type.BaseType;
            }
        }
    }
}
