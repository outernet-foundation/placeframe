using UnityEngine;
using UnityEngine.UI;

namespace Placeframe.Client
{
    [RequireComponent(typeof(Toggle))]
    public class ObjectSwapToggle : MonoBehaviour
    {
        public GameObject onObject;
        public GameObject offObject;

        private Toggle _toggle;

        private void Awake()
        {
            _toggle = GetComponent<Toggle>();
            _toggle.onValueChanged.AddListener(x =>
            {
                onObject.SetActive(x);
                offObject.SetActive(!x);
            });

            onObject.SetActive(_toggle.isOn);
            offObject.SetActive(!_toggle.isOn);
        }
    }
}
