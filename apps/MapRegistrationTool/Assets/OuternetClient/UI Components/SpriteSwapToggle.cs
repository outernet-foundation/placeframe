using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace Outernet.MapRegistrationTool
{
    public class SpriteSwapToggle : MonoBehaviour
    {
        public Toggle toggle;
        public GameObject onSprite;
        public GameObject offSprite;

        private void Awake()
        {
            toggle.onValueChanged.AddListener(HandleValueChanged);
            HandleValueChanged(toggle.isOn);
        }

        private void HandleValueChanged(bool isOn)
        {
            onSprite.SetActive(isOn);
            offSprite.SetActive(!isOn);
        }
    }
}