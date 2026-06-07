using UnityEngine;
using UnityEngine.UI;

namespace Nessle
{
    [RequireComponent(typeof(Toggle))]
    [RequireComponent(typeof(Animator))]
    public class AnimatedToggle : MonoBehaviour
    {
        public string animatorTrigger = "isOn";
        private Toggle _toggle;
        private Animator _animator;

        private void Awake()
        {
            _toggle = GetComponent<Toggle>();
            _animator = GetComponent<Animator>();

            _toggle.onValueChanged.AddListener(x => _animator.SetBool(animatorTrigger, x));
            _animator.SetBool(animatorTrigger, _toggle.isOn);
        }

        private void OnEnable()
        {
            if (_animator != null && _toggle != null)
                _animator.SetBool(animatorTrigger, _toggle.isOn);
        }
    }
}