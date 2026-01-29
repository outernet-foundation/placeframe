using UnityEngine;

using TMPro;

namespace Outernet.Client
{
    public class NodeTextView : ViewBase
    {
        public TextMeshPro text => _text;

        [SerializeField]
        private TextMeshPro _text;
    }
}