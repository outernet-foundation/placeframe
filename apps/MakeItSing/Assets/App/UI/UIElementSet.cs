using Nessle;
using UnityEngine;

namespace Plerion.MakeItSing
{
    [CreateAssetMenu(fileName = "UIElementSet", menuName = "Scriptable Objects/UIElementSet")]
    public class UIElementSet : ScriptableObject
    {
        public Sprite background;
        public Color backgroundColor;
        public Color elementColor;
        public AnimatedListControl animatedList;
        public TagalongControl tagalong;
        public PressableControl pressable;
        public Sprite hamburgerMenu;
        public Sprite circle;
    }
}