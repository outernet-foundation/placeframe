using UnityEngine;
using UnityEngine.UI;

using TMPro;

namespace Placeframe.MapRegistrationTool
{
    public class Foldout : PropertyLabel
    {
        public GameObject header;
        public Toggle foldout;

        private void Awake()
        {
            content.gameObject.SetActive(foldout.isOn);
            foldout.onValueChanged.AddListener(x => content.gameObject.SetActive(x));
        }
    }
}