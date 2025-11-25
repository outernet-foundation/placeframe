using UnityEngine;
using UnityEngine.UI;

namespace PlerionClient.Client
{
    [RequireComponent(typeof(Toggle))]
    public class SpriteSwapToggle : MonoBehaviour
    {
        public Image image;
        public Sprite onSprite;
        public Sprite offSprite;

        private Toggle _toggle;

        private void Awake()
        {
            _toggle = GetComponent<Toggle>();
            _toggle.onValueChanged.AddListener(x => image.sprite = x ? onSprite : offSprite);

            image.sprite = _toggle.isOn ? onSprite : offSprite;
        }
    }
}