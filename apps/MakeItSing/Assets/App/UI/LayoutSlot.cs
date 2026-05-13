using UnityEngine;
using UnityEngine.UI;

public class LayoutSlot : MonoBehaviour, ILayoutElement, ILayoutGroup
{
    public RectTransform target;

    public float minWidth { get; private set; }

    public float preferredWidth { get; private set; }

    public float flexibleWidth { get; private set; }

    public float minHeight { get; private set; }

    public float preferredHeight { get; private set; }

    public float flexibleHeight { get; private set; }

    public int layoutPriority => _layoutPriority;

    public int _layoutPriority;

    private DrivenRectTransformTracker _tracker;

    public void CalculateLayoutInputHorizontal()
    {
        if (target == null)
        {
            minWidth = 0;
            preferredWidth = 0;
            flexibleWidth = 0;
            return;
        }

        foreach (var element in target.GetComponents<ILayoutElement>())
            element.CalculateLayoutInputHorizontal();

        minWidth = LayoutUtility.GetMinWidth(target);
        preferredWidth = LayoutUtility.GetPreferredWidth(target);
        flexibleWidth = LayoutUtility.GetFlexibleWidth(target);
        _tracker.Clear();
    }

    public void CalculateLayoutInputVertical()
    {
        if (target == null)
        {
            minHeight = 0;
            preferredHeight = 0;
            flexibleHeight = 0;
            return;
        }

        foreach (var element in target.GetComponents<ILayoutElement>())
            element.CalculateLayoutInputVertical();

        minHeight = LayoutUtility.GetMinHeight(target);
        preferredHeight = LayoutUtility.GetPreferredHeight(target);
        flexibleHeight = LayoutUtility.GetFlexibleHeight(target);
    }

    public void SetLayoutHorizontal()
    {
        _tracker.Add(this, target, DrivenTransformProperties.SizeDeltaX);
        target.SetSizeWithCurrentAnchors(RectTransform.Axis.Horizontal, ((RectTransform)transform).rect.width);
    }

    public void SetLayoutVertical()
    {
        _tracker.Add(this, target, DrivenTransformProperties.SizeDeltaY);
        target.SetSizeWithCurrentAnchors(RectTransform.Axis.Vertical, ((RectTransform)transform).rect.height);
    }
}
