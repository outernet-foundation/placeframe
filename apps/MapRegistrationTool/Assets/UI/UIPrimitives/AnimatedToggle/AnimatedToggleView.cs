using UnityEngine;
using UnityEngine.UI;

using FofX;

namespace Placeframe.MapRegistrationTool
{
    [RequireComponent(typeof(Toggle))]
    [RequireComponent(typeof(Animator))]
    public class AnimatedToggleView : ViewBase
    {
        public string animatorIsOnID = "isOn";
        private Toggle _toggle;
        private Animator _animator;

        private void Awake()
        {
            _toggle = GetComponent<Toggle>();
            _animator = GetComponent<Animator>();
            _toggle.onValueChanged.AddListener(HandleToggleChanged);
            HandleToggleChanged(_toggle.isOn);
        }

        private void OnEnable()
        {
            HandleToggleChanged(_toggle.isOn);
        }

        private void HandleToggleChanged(bool isOn)
        {
            _animator.SetBool(animatorIsOnID, isOn);
        }
    }
}