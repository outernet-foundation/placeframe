using TMPro;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.EventSystems;

namespace Outernet.Client.AuthoringTools
{
    public class EditableLabel : ViewBase, IPointerClickHandler
    {
        public string text
        {
            get => _text;
            set
            {
                if (_text == value)
                    return;

                _text = value;
                _label.text = value;
                _inputField.text = value;
                onValueChanged.Invoke(value);
            }
        }

        private string _text;

        [SerializeField] private TextMeshProUGUI _label;
        [SerializeField] private TMP_InputField _inputField;

        public UnityEvent<string> onValueChanged = new UnityEvent<string>();

        private void Awake()
        {
            _inputField.gameObject.SetActive(false);
            _inputField.onEndEdit.AddListener(s =>
            {
                text = s;
                _inputField.gameObject.SetActive(false);
            });
        }

        public void OnPointerClick(PointerEventData eventData)
        {
            if (eventData.clickCount > 1)
            {
                _inputField.gameObject.SetActive(true);
                _inputField.Select();
            }
        }
    }
}