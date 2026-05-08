using UnityEngine;

namespace Plerion.MakeItSing
{
    public class ToggleGroupAttribute : PropertyAttribute
    {
        public string toggleProperty;
        public bool invert;
        public bool disable;

        public ToggleGroupAttribute(string toggleProperty, bool invert = false, bool disable = false)
        {
            this.toggleProperty = toggleProperty;
            this.invert = invert;
            this.disable = disable;
        }
    }
}