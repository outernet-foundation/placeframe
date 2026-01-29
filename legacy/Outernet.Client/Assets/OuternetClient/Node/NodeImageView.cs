using UnityEngine;
using UnityEngine.UI;

namespace Outernet.Client
{
    public class NodeImageView : ViewBase
    {
        [SerializeField]
        private Canvas _canvas;

        [SerializeField]
        private Image _image;

        [SerializeField]
        private AspectRatioFitter _aspectRatioFitter;

        private bool _generatedSpriteInternally;

        public void SetMaxDimensions(Vector2 maxDimensions)
            => ((RectTransform)_canvas.transform).sizeDelta = maxDimensions;

        public void SetImage(Texture2D image)
        {
            SetImageInternal(
                Sprite.Create(image, new Rect(0, 0, image.width, image.height), Vector2.one * 0.5f),
                true
            );
        }

        public void SetImage(Sprite image)
        {
            SetImageInternal(image, false);
        }

        public void ClearImage()
        {
            SetImageInternal(null, false);
        }

        private void SetImageInternal(Sprite image, bool generatedSpriteInternally)
        {
            if (_generatedSpriteInternally)
                Destroy(_image.sprite);

            _image.sprite = image;
            _generatedSpriteInternally = generatedSpriteInternally;
            _aspectRatioFitter.aspectRatio = image == null ?
                1f : (float)image.rect.width / (float)image.rect.height;
        }
    }
}