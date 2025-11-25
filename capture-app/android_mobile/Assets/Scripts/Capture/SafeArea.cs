using UnityEngine;

[RequireComponent(typeof(RectTransform))]
public class SafeArea : MonoBehaviour
{
    private Rect _safeArea = new Rect(0, 0, 1080, 1920);
    private RectTransform _rectTransform;

    private void Awake()
    {
        _rectTransform = GetComponent<RectTransform>();
        _rectTransform.anchorMin = Vector2.one * 0.5f;
        _rectTransform.anchorMax = Vector2.one * 0.5f;
        _rectTransform.offsetMin = Vector2.zero;
        _rectTransform.offsetMax = Vector2.zero;
    }

    private void Update()
    {
        _safeArea = Screen.safeArea;

        var scale = new Vector2(1f / transform.lossyScale.x, 1f / transform.lossyScale.y);
        var delta = _safeArea.max - _safeArea.min;

        _rectTransform.sizeDelta = Vector2.Scale(scale, delta);
    }
}
