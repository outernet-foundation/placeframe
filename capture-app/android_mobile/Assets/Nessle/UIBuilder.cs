using System;
using System.Collections.Generic;
using System.Linq;
using ObserveThing;
using TMPro;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;

namespace Nessle
{
    public static class UIBuilder
    {
        public static Action<ButtonControl> DefaultButtonStyle;
        public static Action<UnityComponentControl<TextMeshProUGUI>> DefaultLabelStyle;
        public static Action<InputFieldControl> DefaultInputFieldStyle;
        public static Action<ScrollbarControl> DefaultScrollbarStyle;
        public static Action<ScrollRectControl> DefaultScrollRectStyle;
        public static Action<ScrollingDropdownControl> DefaultDropdownStyle;

        private static T StyleIfNecessary<T>(this T control, Action<T> defaultStyle)
        {
            defaultStyle?.Invoke(control);
            return control;
        }

        public static T GameObject<T>(params Type[] additionalComponents)
            where T : Component => GameObject<T>(typeof(T).Name, additionalComponents);

        public static T GameObject<T>(string name, params Type[] additionalComponents)
            where T : Component
        {
            var component = new GameObject(name, additionalComponents).GetOrAddComponent<T>();
            var rectTransform = component.GetOrAddComponent<RectTransform>();
            rectTransform.SetSizeWithCurrentAnchors(UnityEngine.RectTransform.Axis.Horizontal, 100);
            rectTransform.SetSizeWithCurrentAnchors(UnityEngine.RectTransform.Axis.Vertical, 100);
            return component;
        }

        public static T GetOrAddComponent<T>(this Component component)
            where T : Component => component.gameObject.GetOrAddComponent<T>();

        public static T GetOrAddComponent<T>(this GameObject gameObject)
            where T : Component
        {
            if (!gameObject.TryGetComponent<T>(out var component))
                component = gameObject.AddComponent<T>();

            return component;
        }

        public static Color WithAlpha(this Color color, float alpha)
        {
            color.a = alpha;
            return color;
        }

        public static UnityComponentControl<T> ComponentControl<T>(string name)
            where T : Component => new UnityComponentControl<T>(GameObject<T>(name));

        public static UnityComponentControl<T> ComponentControl<T>()
            where T : Component => new UnityComponentControl<T>(GameObject<T>());

        public static CanvasControl Canvas()
            => new CanvasControl();

        public static UnityComponentControl<RectTransform> RectTransform()
            => ComponentControl<RectTransform>();

        public static UnityComponentControl<Image> Image()
            => ComponentControl<Image>().Color(UnityEngine.Color.white);

        public static UnityComponentControl<TextMeshProUGUI> Label()
            => ComponentControl<TextMeshProUGUI>().StyleIfNecessary(DefaultLabelStyle);

        public static UnityComponentControl<RectTransform> Space()
            => ComponentControl<RectTransform>();

        public static ButtonControl Button()
            => new ButtonControl().StyleIfNecessary(DefaultButtonStyle);

        public static UnityComponentControl<HorizontalLayoutGroup> HorizontalLayout()
            => ComponentControl<HorizontalLayoutGroup>().ChildForceExpand(false).ControlChildSize(false);

        public static UnityComponentControl<VerticalLayoutGroup> VerticalLayout()
            => ComponentControl<VerticalLayoutGroup>().ChildForceExpand(false).ControlChildSize(false);

        public static UnityComponentControl<RectMask2D> RectMask()
            => ComponentControl<RectMask2D>();

        public static ScrollingDropdownControl ScrollingDropdown(
            IUnityComponentControl<Image> background = default,
            IUnityComponentControl<TextMeshProUGUI> captionText = default,
            IUnityComponentControl<Image> arrow = default,
            ScrollRectControl template = default,
            IUnityComponentControl<Toggle> itemToggle = default,
            IUnityComponentControl<Image> itemBackground = default,
            IUnityComponentControl<TextMeshProUGUI> itemLabel = default,
            IUnityComponentControl<Image> itemCheckmark = default
        ) => new ScrollingDropdownControl(background, captionText, arrow, template, itemToggle, itemBackground, itemLabel, itemCheckmark).StyleIfNecessary(DefaultDropdownStyle);

        public static ScrollRectControl ScrollRect(
            IUnityComponentControl<Image> background = default,
            ScrollbarControl horizontalScrollbar = default,
            ScrollbarControl verticalScrollbar = default,
            ImageMaskControl viewport = default,
            IUnityControl content = default
        ) => new ScrollRectControl(background, horizontalScrollbar, verticalScrollbar, viewport, content).StyleIfNecessary(DefaultScrollRectStyle);

        public static ScrollbarControl Scrollbar(
            UnityComponentControl<Image> background = default,
            UnityComponentControl<RectTransform> slidingArea = default,
            UnityComponentControl<Image> handle = default
        ) => new ScrollbarControl(background, slidingArea, handle).StyleIfNecessary(DefaultScrollbarStyle);

        public static ToggleControl Toggle()
            => new ToggleControl();

        public static InputFieldControl InputField(
            UnityComponentControl<RectTransform> textViewport = default,
            UnityComponentControl<TextMeshProUGUI> inputText = default,
            UnityComponentControl<TextMeshProUGUI> placeholderText = default
        ) => new InputFieldControl(textViewport, inputText, placeholderText).StyleIfNecessary(DefaultInputFieldStyle);

        public static Vector3Control Vector3(
            UnityComponentControl<HorizontalLayoutGroup> layout = default,
            UnityComponentControl<TextMeshProUGUI> xLabel = default, InputFieldControl xField = default,
            UnityComponentControl<TextMeshProUGUI> yLabel = default, InputFieldControl yField = default,
            UnityComponentControl<TextMeshProUGUI> zLabel = default, InputFieldControl zField = default
        ) => new Vector3Control(layout, xLabel, xField, yLabel, yField, zLabel, zField);

        public static ImageMaskControl ImageMask()
            => new ImageMaskControl();

        public static T Style<T>(this T control, Action<T> applyStyle)
            where T : IControl
        {
            applyStyle(control);
            return control;
        }

        public static T Children<T>(this T control, params IControl[] children)
            where T : IControl => control.Children((IEnumerable<IControl>)children);

        public static T Children<T>(this T control, IEnumerable<IControl> children)
            where T : IControl
        {
            if (children == null)
                return control;

            foreach (var child in children)
                child.SetParent(control);

            return control;
        }

        public static TParent Children<TParent, TChildren>(this TParent control, IListObservable<TChildren> children)
            where TParent : IControl where TChildren : IControl
        {
            control.AddBinding(children.Subscribe(
                args =>
                {
                    switch (args.operationType)
                    {
                        case OpType.Add:
                            args.element.SetParent(control);
                            args.element.SetSiblingIndex(args.index);
                            break;

                        case OpType.Remove:
                            args.element.SetParent(null);
                            break;
                    }
                }
            ));

            return control;
        }

        public static ControlWithMetadata<TControl, TData> WithMetadata<TControl, TData>(this TControl control, TData data)
            where TControl : IControl => new ControlWithMetadata<TControl, TData>() { control = control, metadata = data };

        public static T OnChange<T, U>(this T control, Action<U> onChange)
            where T : IValueControl<U>
        {
            control.onChange += onChange;
            return control;
        }

        public static T Active<T>(this T control, IValueObservable<bool> active)
            where T : IUnityControl
        {
            control.AddBinding(active.Subscribe(x => control.gameObject.SetActive(x.currentValue)));
            return control;
        }

        public static T Active<T>(this T control, bool active)
            where T : IUnityControl
        {
            control.gameObject.SetActive(active);
            return control;
        }

        public static T Name<T>(this T control, IValueObservable<string> name)
            where T : IUnityControl
        {
            control.AddBinding(name.Subscribe(x => control.gameObject.name = x.currentValue));
            return control;
        }

        public static T Name<T>(this T control, string name)
            where T : IUnityControl
        {
            control.gameObject.name = name;
            return control;
        }

        public static T FillParent<T>(this T control)
            where T : IUnityControl
        {
            var rectTransform = control.gameObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(0, 0);
            rectTransform.anchorMax = new Vector2(1, 1);
            rectTransform.offsetMin = new Vector2(0, 0);
            rectTransform.offsetMax = new Vector2(0, 0);
            return control;
        }

        public static T FillParentWidth<T>(this T control)
            where T : IUnityControl
        {
            var rectTransform = control.gameObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(0, rectTransform.anchorMin.y);
            rectTransform.anchorMax = new Vector2(1, rectTransform.anchorMax.y);
            rectTransform.offsetMin = new Vector2(0, rectTransform.offsetMin.y);
            rectTransform.offsetMax = new Vector2(0, rectTransform.offsetMax.y);
            return control;
        }

        public static T FillParentHeight<T>(this T control)
            where T : IUnityControl
        {
            var rectTransform = control.gameObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(rectTransform.anchorMin.x, 0);
            rectTransform.anchorMax = new Vector2(rectTransform.anchorMax.x, 1);
            rectTransform.offsetMin = new Vector2(rectTransform.offsetMin.x, 0);
            rectTransform.offsetMax = new Vector2(rectTransform.offsetMax.x, 0);
            return control;
        }

        public static T AnchorToTop<T>(this T control)
            where T : IUnityControl
        {
            var rectTransform = control.gameObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(rectTransform.anchorMin.x, 1);
            rectTransform.anchorMax = new Vector2(rectTransform.anchorMax.x, 1);
            return control;
        }

        public static T AnchorToBottom<T>(this T control)
            where T : IUnityControl
        {
            var rectTransform = control.gameObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(rectTransform.anchorMin.x, 0);
            rectTransform.anchorMax = new Vector2(rectTransform.anchorMax.x, 0);
            return control;
        }

        public static T AnchorToLeft<T>(this T control)
            where T : IUnityControl
        {
            var rectTransform = control.gameObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(0, rectTransform.anchorMin.y);
            rectTransform.anchorMax = new Vector2(0, rectTransform.anchorMax.y);
            return control;
        }

        public static T AnchorToRight<T>(this T control)
            where T : IUnityControl
        {
            var rectTransform = control.gameObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(1, rectTransform.anchorMin.y);
            rectTransform.anchorMax = new Vector2(1, rectTransform.anchorMax.y);
            return control;
        }

        public static T AnchorToTopLeft<T>(this T control)
            where T : IUnityControl
        {
            var rectTransform = control.gameObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(0, 1);
            rectTransform.anchorMax = new Vector2(0, 1);
            return control;
        }

        public static T AnchorToTopRight<T>(this T control)
            where T : IUnityControl
        {
            var rectTransform = control.gameObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(1, 1);
            rectTransform.anchorMax = new Vector2(1, 1);
            return control;
        }

        public static T AnchorToBottomLeft<T>(this T control)
            where T : IUnityControl
        {
            var rectTransform = control.gameObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(0, 0);
            rectTransform.anchorMax = new Vector2(0, 0);
            return control;
        }

        public static T AnchorToBottomRight<T>(this T control)
            where T : IUnityControl
        {
            var rectTransform = control.gameObject.GetComponent<RectTransform>();
            rectTransform.anchorMin = new Vector2(1, 0);
            rectTransform.anchorMax = new Vector2(1, 0);
            return control;
        }

        public static T SetPivot<T>(this T control, Vector2 pivot)
            where T : IUnityControl
        {
            var rectTransform = control.gameObject.GetComponent<RectTransform>();
            rectTransform.pivot = pivot;
            return control;
        }

        public static T LocalPosition<T>(this T control, Vector3 localPosition)
            where T : IUnityControl
        {
            var rectTransform = control.gameObject.GetComponent<RectTransform>();
            rectTransform.localPosition = localPosition;
            return control;
        }

        public static T AnchorMin<T>(this T control, Vector2 anchorMin)
            where T : IUnityControl
        {
            control.gameObject.GetComponent<RectTransform>().anchorMin = anchorMin;
            return control;
        }

        public static T AnchorMin<T>(this T control, IValueObservable<Vector2> anchorMin)
            where T : IUnityControl
        {
            control.AddBinding(anchorMin.Subscribe(x => control.gameObject.GetComponent<RectTransform>().anchorMin = x.currentValue));
            return control;
        }

        public static T AnchorMax<T>(this T control, Vector2 anchorMax)
            where T : IUnityControl
        {
            control.gameObject.GetComponent<RectTransform>().anchorMax = anchorMax;
            return control;
        }

        public static T AnchorMax<T>(this T control, IValueObservable<Vector2> anchorMax)
            where T : IUnityControl
        {
            control.AddBinding(anchorMax.Subscribe(x => control.gameObject.GetComponent<RectTransform>().anchorMax = x.currentValue));
            return control;
        }

        public static T OffsetMin<T>(this T control, Vector2 offsetMin)
            where T : IUnityControl
        {
            control.gameObject.GetComponent<RectTransform>().offsetMin = offsetMin;
            return control;
        }

        public static T OffsetMin<T>(this T control, IValueObservable<Vector2> offsetMin)
            where T : IUnityControl
        {
            control.AddBinding(offsetMin.Subscribe(x => control.gameObject.GetComponent<RectTransform>().offsetMin = x.currentValue));
            return control;
        }

        public static T OffsetMax<T>(this T control, Vector2 offsetMax)
            where T : IUnityControl
        {
            control.gameObject.GetComponent<RectTransform>().offsetMax = offsetMax;
            return control;
        }

        public static T OffsetMax<T>(this T control, IValueObservable<Vector2> offsetMax)
            where T : IUnityControl
        {
            control.AddBinding(offsetMax.Subscribe(x => control.gameObject.GetComponent<RectTransform>().offsetMax = x.currentValue));
            return control;
        }

        public static T SizeDelta<T>(this T control, Vector2 sizeDelta)
            where T : IUnityControl
        {
            control.gameObject.GetComponent<RectTransform>().sizeDelta = sizeDelta;
            return control;
        }

        public static T SizeDelta<T>(this T control, IValueObservable<Vector2> sizeDelta)
            where T : IUnityControl
        {
            control.AddBinding(sizeDelta.Subscribe(x => control.gameObject.GetComponent<RectTransform>().sizeDelta = x.currentValue));
            return control;
        }

        public static T WidthFitMode<T>(this T control, ContentSizeFitter.FitMode fitMode)
            where T : IUnityControl
        {
            control.gameObject.GetOrAddComponent<ContentSizeFitter>().horizontalFit = fitMode;
            return control;
        }

        public static T WidthFitMode<T>(this T control, IValueObservable<ContentSizeFitter.FitMode> fitMode)
            where T : IUnityControl
        {
            control.AddBinding(fitMode.Subscribe(x => control.gameObject.GetOrAddComponent<ContentSizeFitter>().horizontalFit = x.currentValue));
            return control;
        }

        public static T HeightFitMode<T>(this T control, ContentSizeFitter.FitMode fitMode)
            where T : IUnityControl
        {
            control.gameObject.GetOrAddComponent<ContentSizeFitter>().verticalFit = fitMode;
            return control;
        }

        public static T HeightFitMode<T>(this T control, IValueObservable<ContentSizeFitter.FitMode> fitMode)
            where T : IUnityControl
        {
            control.AddBinding(fitMode.Subscribe(x => control.gameObject.GetOrAddComponent<ContentSizeFitter>().verticalFit = x.currentValue));
            return control;
        }

        public static T IgnoreLayout<T>(this T control, bool ignoreLayout)
            where T : IUnityControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().ignoreLayout = ignoreLayout;
            return control;
        }

        public static T IgnoreLayout<T>(this T control, IValueObservable<bool> ignoreLayout)
            where T : IUnityControl
        {
            control.AddBinding(ignoreLayout.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().ignoreLayout = x.currentValue));
            return control;
        }

        public static T MinWidth<T>(this T control, float minWidth)
            where T : IUnityControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().minWidth = minWidth;
            return control;
        }

        public static T MinWidth<T>(this T control, IValueObservable<float> minWidth)
            where T : IUnityControl
        {
            control.AddBinding(minWidth.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().minWidth = x.currentValue));
            return control;
        }

        public static T MinHeight<T>(this T control, float minHeight)
            where T : IUnityControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().minHeight = minHeight;
            return control;
        }

        public static T MinHeight<T>(this T control, IValueObservable<float> minHeight)
            where T : IUnityControl
        {
            control.AddBinding(minHeight.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().minHeight = x.currentValue));
            return control;
        }

        public static T PreferredWidth<T>(this T control, float preferredWidth)
            where T : IUnityControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().preferredWidth = preferredWidth;
            return control;
        }

        public static T PreferredWidth<T>(this T control, IValueObservable<float> preferredWidth)
            where T : IUnityControl
        {
            control.AddBinding(preferredWidth.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().preferredWidth = x.currentValue));
            return control;
        }

        public static T PreferredHeight<T>(this T control, float preferredHeight)
            where T : IUnityControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().preferredHeight = preferredHeight;
            return control;
        }

        public static T PreferredHeight<T>(this T control, IValueObservable<float> preferredHeight)
            where T : IUnityControl
        {
            control.AddBinding(preferredHeight.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().preferredHeight = x.currentValue));
            return control;
        }

        public static T FlexibleWidth<T>(this T control, bool flexibleWidth)
            where T : IUnityControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().flexibleWidth = flexibleWidth ? 1 : 0;
            return control;
        }

        public static T FlexibleWidth<T>(this T control, IValueObservable<bool> flexibleWidth)
            where T : IUnityControl
        {
            control.AddBinding(flexibleWidth.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().flexibleWidth = x.currentValue ? 1 : 0));
            return control;
        }

        public static T FlexibleHeight<T>(this T control, bool flexibleHeight)
            where T : IUnityControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().flexibleHeight = flexibleHeight ? 1 : 0;
            return control;
        }

        public static T FlexibleHeight<T>(this T control, IValueObservable<bool> flexibleHeight)
            where T : IUnityControl
        {
            control.AddBinding(flexibleHeight.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().flexibleHeight = x.currentValue ? 1 : 0));
            return control;
        }

        public static T LayoutPriority<T>(this T control, int layoutPriority)
            where T : IUnityControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().layoutPriority = layoutPriority;
            return control;
        }

        public static T LayoutPriority<T>(this T control, IValueObservable<int> layoutPriority)
            where T : IUnityControl
        {
            control.AddBinding(layoutPriority.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().layoutPriority = x.currentValue));
            return control;
        }

        public static T FitContent<T>(this T control, ContentSizeFitter.FitMode fitContent)
            where T : IUnityControl
        {
            var fitter = control.gameObject.GetOrAddComponent<ContentSizeFitter>();
            fitter.verticalFit = fitContent;
            fitter.horizontalFit = fitContent;
            return control;
        }

        public static T FitContent<T>(this T control, IValueObservable<ContentSizeFitter.FitMode> fitContent)
            where T : IUnityControl
        {
            control.AddBinding(fitContent.Subscribe(x =>
            {
                var fitter = control.gameObject.GetOrAddComponent<ContentSizeFitter>();
                fitter.verticalFit = x.currentValue;
                fitter.horizontalFit = x.currentValue;
            }));
            return control;
        }

        public static T FitContentVertical<T>(this T control, ContentSizeFitter.FitMode fitContentVertical)
            where T : IUnityControl
        {
            control.gameObject.GetOrAddComponent<ContentSizeFitter>().verticalFit = fitContentVertical;
            return control;
        }

        public static T FitContentVertical<T>(this T control, IValueObservable<ContentSizeFitter.FitMode> fitContentVertical)
            where T : IUnityControl
        {
            control.AddBinding(fitContentVertical.Subscribe(x => control.gameObject.GetOrAddComponent<ContentSizeFitter>().verticalFit = x.currentValue));
            return control;
        }

        public static T FitContentHorizontal<T>(this T control, ContentSizeFitter.FitMode fitContentHorizontal)
            where T : IUnityControl
        {
            control.gameObject.GetOrAddComponent<ContentSizeFitter>().horizontalFit = fitContentHorizontal;
            return control;
        }

        public static T FitContentHorizontal<T>(this T control, IValueObservable<ContentSizeFitter.FitMode> fitContentHorizontal)
            where T : IUnityControl
        {
            control.AddBinding(fitContentHorizontal.Subscribe(x => control.gameObject.GetOrAddComponent<ContentSizeFitter>().horizontalFit = x.currentValue));
            return control;
        }

        public static T SetSiblingOrder<T>(this T control, int index)
            where T : IUnityControl
        {
            control.rectTransform.SetSiblingIndex(index);
            return control;
        }

        public static T RenderMode<T>(this T control, RenderMode renderMode)
            where T : IUnityComponentControl<Canvas>
        {
            control.component.renderMode = renderMode;
            return control;
        }

        public static T RenderMode<T>(this T control, IValueObservable<RenderMode> renderMode)
            where T : IUnityComponentControl<Canvas>
        {
            control.AddBinding(renderMode.Subscribe(x => control.component.renderMode = x.currentValue));
            return control;
        }

        public static T PixelPerfect<T>(this T control, bool pixelPerfect)
            where T : IUnityComponentControl<Canvas>
        {
            control.component.pixelPerfect = pixelPerfect;
            return control;
        }

        public static T PixelPerfect<T>(this T control, IValueObservable<bool> pixelPerfect)
            where T : IUnityComponentControl<Canvas>
        {
            control.AddBinding(pixelPerfect.Subscribe(x => control.component.pixelPerfect = x.currentValue));
            return control;
        }

        public static T SortOrder<T>(this T control, int sortingOrder)
            where T : IUnityComponentControl<Canvas>
        {
            control.component.sortingOrder = sortingOrder;
            return control;
        }

        public static T SortOrder<T>(this T control, IValueObservable<int> sortingOrder)
            where T : IUnityComponentControl<Canvas>
        {
            control.AddBinding(sortingOrder.Subscribe(x => control.component.sortingOrder = x.currentValue));
            return control;
        }

        public static T TargetDisplay<T>(this T control, int targetDisplay)
            where T : IUnityComponentControl<Canvas>
        {
            control.component.targetDisplay = targetDisplay;
            return control;
        }

        public static T TargetDisplay<T>(this T control, IValueObservable<int> targetDisplay)
            where T : IUnityComponentControl<Canvas>
        {
            control.AddBinding(targetDisplay.Subscribe(x => control.component.targetDisplay = x.currentValue));
            return control;
        }

        public static T AdditionalShaderChannels<T>(this T control, AdditionalCanvasShaderChannels additionalShaderChannels)
            where T : IUnityComponentControl<Canvas>
        {
            control.component.additionalShaderChannels = additionalShaderChannels;
            return control;
        }

        public static T AdditionalShaderChannels<T>(this T control, IValueObservable<AdditionalCanvasShaderChannels> additionalShaderChannels)
            where T : IUnityComponentControl<Canvas>
        {
            control.AddBinding(additionalShaderChannels.Subscribe(x => control.component.additionalShaderChannels = x.currentValue));
            return control;
        }

        public static T UIScaleMode<T>(this T control, CanvasScaler.ScaleMode uiScaleMode)
            where T : IUnityComponentControl<CanvasScaler>
        {
            control.component.uiScaleMode = uiScaleMode;
            return control;
        }

        public static T UIScaleMode<T>(this T control, IValueObservable<CanvasScaler.ScaleMode> uiScaleMode)
            where T : IUnityComponentControl<CanvasScaler>
        {
            control.AddBinding(uiScaleMode.Subscribe(x => control.component.uiScaleMode = x.currentValue));
            return control;
        }

        public static T ScaleFactor<T>(this T control, float scaleFactor)
            where T : IUnityComponentControl<CanvasScaler>
        {
            control.component.scaleFactor = scaleFactor;
            return control;
        }

        public static T ScaleFactor<T>(this T control, IValueObservable<float> scaleFactor)
            where T : IUnityComponentControl<CanvasScaler>
        {
            control.AddBinding(scaleFactor.Subscribe(x => control.component.scaleFactor = x.currentValue));
            return control;
        }

        public static T ReferencePixelsPerUnit<T>(this T control, float referencePixelsPerUnit)
            where T : IUnityComponentControl<CanvasScaler>
        {
            control.component.referencePixelsPerUnit = referencePixelsPerUnit;
            return control;
        }

        public static T ReferencePixelsPerUnit<T>(this T control, IValueObservable<float> referencePixelsPerUnit)
            where T : IUnityComponentControl<CanvasScaler>
        {
            control.AddBinding(referencePixelsPerUnit.Subscribe(x => control.component.referencePixelsPerUnit = x.currentValue));
            return control;
        }

        public static T IgnoreReversedGraphics<T>(this T control, bool ignoreReversedGraphics)
            where T : IUnityComponentControl<GraphicRaycaster>
        {
            control.component.ignoreReversedGraphics = ignoreReversedGraphics;
            return control;
        }

        public static T IgnoreReversedGraphics<T>(this T control, IValueObservable<bool> ignoreReversedGraphics)
            where T : IUnityComponentControl<GraphicRaycaster>
        {
            control.AddBinding(ignoreReversedGraphics.Subscribe(x => control.component.ignoreReversedGraphics = x.currentValue));
            return control;
        }

        public static T BlockingObjects<T>(this T control, GraphicRaycaster.BlockingObjects blockingObjects)
            where T : IUnityComponentControl<GraphicRaycaster>
        {
            control.component.blockingObjects = blockingObjects;
            return control;
        }

        public static T BlockingObjects<T>(this T control, IValueObservable<GraphicRaycaster.BlockingObjects> blockingObjects)
            where T : IUnityComponentControl<GraphicRaycaster>
        {
            control.AddBinding(blockingObjects.Subscribe(x => control.component.blockingObjects = x.currentValue));
            return control;
        }

        public static T BlockingMask<T>(this T control, LayerMask blockingMask)
            where T : IUnityComponentControl<GraphicRaycaster>
        {
            control.component.blockingMask = blockingMask;
            return control;
        }

        public static T BlockingMask<T>(this T control, IValueObservable<LayerMask> blockingMask)
            where T : IUnityComponentControl<GraphicRaycaster>
        {
            control.AddBinding(blockingMask.Subscribe(x => control.component.blockingMask = x.currentValue));
            return control;
        }

        public static T OnClick<T>(this T control, UnityAction onClick)
            where T : IUnityComponentControl<Button>
        {
            control.component.onClick.AddListener(onClick);
            return control;
        }

        public static T Interactable<T>(this T control, bool interactable)
            where T : IUnityComponentControl<Selectable>
        {
            control.component.interactable = interactable;
            return control;
        }

        public static T Sprite<T>(this T control, Sprite sprite)
            where T : IUnityComponentControl<Image>
        {
            control.component.sprite = sprite;
            return control;
        }

        public static T Sprite<T>(this T control, IValueObservable<Sprite> sprite)
            where T : IUnityComponentControl<Image>
        {
            control.AddBinding(sprite.Subscribe(x => control.component.sprite = x.currentValue));
            return control;
        }

        public static T ImageType<T>(this T control, Image.Type imageType)
            where T : IUnityComponentControl<Image>
        {
            control.component.type = imageType;
            return control;
        }

        public static T ImageType<T>(this T control, IValueObservable<Image.Type> imageType)
            where T : IUnityComponentControl<Image>
        {
            control.AddBinding(imageType.Subscribe(x => control.component.type = x.currentValue));
            return control;
        }

        public static T PixelsPerUnitMultiplier<T>(this T control, float pixelsPerUnitMultiplier)
            where T : IUnityComponentControl<Image>
        {
            control.component.pixelsPerUnitMultiplier = pixelsPerUnitMultiplier;
            return control;
        }

        public static T PixelsPerUnitMultiplier<T>(this T control, IValueObservable<float> pixelsPerUnitMultiplier)
            where T : IUnityComponentControl<Image>
        {
            control.AddBinding(pixelsPerUnitMultiplier.Subscribe(x => control.component.pixelsPerUnitMultiplier = x.currentValue));
            return control;
        }

        public static T PreserveAspect<T>(this T control, bool preserveAspect)
            where T : IUnityComponentControl<Image>
        {
            control.component.preserveAspect = preserveAspect;
            return control;
        }

        public static T PreserveAspect<T>(this T control, IValueObservable<bool> preserveAspect)
            where T : IUnityComponentControl<Image>
        {
            control.AddBinding(preserveAspect.Subscribe(x => control.component.preserveAspect = x.currentValue));
            return control;
        }

        public static T Color<T>(this T control, Color color)
            where T : IUnityComponentControl<Graphic>
        {
            control.component.color = color;
            return control;
        }

        public static T Color<T>(this T control, IValueObservable<Color> color)
            where T : IUnityComponentControl<Graphic>
        {
            control.AddBinding(color.Subscribe(x => control.component.color = x.currentValue));
            return control;
        }

        public static T Alpha<T>(this T control, float alpha)
            where T : IUnityComponentControl<Graphic>
        {
            control.component.color = control.component.color.WithAlpha(alpha);
            return control;
        }

        public static T Alpha<T>(this T control, IValueObservable<float> alpha)
            where T : IUnityComponentControl<Graphic>
        {
            control.AddBinding(alpha.Subscribe(x => control.component.color = control.component.color.WithAlpha(x.currentValue)));
            return control;
        }

        public static TComponent Text<TComponent, TContent>(this TComponent control, TContent text)
            where TComponent : IUnityComponentControl<TMP_Text>
        {
            control.component.text = text.ToString();
            return control;
        }

        public static TComponent Text<TComponent, TContent>(this TComponent control, IValueObservable<TContent> text)
            where TComponent : IUnityComponentControl<TMP_Text>
        {
            control.AddBinding(text.Subscribe(x => control.component.text = x.currentValue.ToString()));
            return control;
        }

        public static T FontSize<T>(this T control, float fontSize)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.component.fontSize = fontSize;
            return control;
        }

        public static T FontSize<T>(this T control, IValueObservable<float> fontSize)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.AddBinding(fontSize.Subscribe(x => control.component.fontSize = x.currentValue));
            return control;
        }

        public static T Alignment<T>(this T control, TextAlignmentOptions alignment)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.component.alignment = alignment;
            return control;
        }

        public static T Alignment<T>(this T control, IValueObservable<TextAlignmentOptions> alignment)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.AddBinding(alignment.Subscribe(x => control.component.alignment = x.currentValue));
            return control;
        }

        public static T Font<T>(this T control, TMP_FontAsset font)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.component.font = font;
            return control;
        }

        public static T Font<T>(this T control, IValueObservable<TMP_FontAsset> font)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.AddBinding(font.Subscribe(x => control.component.font = x.currentValue));
            return control;
        }

        public static T FontStyle<T>(this T control, FontStyles fontStyle)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.component.fontStyle = fontStyle;
            return control;
        }

        public static T FontStyle<T>(this T control, IValueObservable<FontStyles> fontStyle)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.AddBinding(fontStyle.Subscribe(x => control.component.fontStyle = x.currentValue));
            return control;
        }

        public static T FontWeight<T>(this T control, FontWeight fontWeight)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.component.fontWeight = fontWeight;
            return control;
        }

        public static T FontWeight<T>(this T control, IValueObservable<FontWeight> fontWeight)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.AddBinding(fontWeight.Subscribe(x => control.component.fontWeight = x.currentValue));
            return control;
        }

        public static T TextWrappingMode<T>(this T control, TextWrappingModes textWrappingMode)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.component.textWrappingMode = textWrappingMode;
            return control;
        }

        public static T TextWrappingMode<T>(this T control, IValueObservable<TextWrappingModes> textWrappingMode)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.AddBinding(textWrappingMode.Subscribe(x => control.component.textWrappingMode = x.currentValue));
            return control;
        }

        public static T OverflowMode<T>(this T control, TextOverflowModes overflowMode)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.component.overflowMode = overflowMode;
            return control;
        }

        public static T OverflowMode<T>(this T control, IValueObservable<TextOverflowModes> overflowMode)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.AddBinding(overflowMode.Subscribe(x => control.component.overflowMode = x.currentValue));
            return control;
        }

        public static T Margin<T>(this T control, Vector4 margin)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.component.margin = margin;
            return control;
        }

        public static T Margin<T>(this T control, IValueObservable<Vector4> margin)
            where T : IUnityComponentControl<TMP_Text>
        {
            control.AddBinding(margin.Subscribe(x => control.component.margin = x.currentValue));
            return control;
        }

        public static T Padding<T>(this T control, RectOffset padding)
            where T : IUnityComponentControl<LayoutGroup>
        {
            control.component.padding = padding;
            return control;
        }

        public static T Padding<T>(this T control, IValueObservable<RectOffset> padding)
            where T : IUnityComponentControl<LayoutGroup>
        {
            control.AddBinding(padding.Subscribe(x => control.component.padding = x.currentValue));
            return control;
        }

        public static T Alignment<T>(this T control, TextAnchor childAlignment)
            where T : IUnityComponentControl<LayoutGroup>
        {
            control.component.childAlignment = childAlignment;
            return control;
        }

        public static T Alignment<T>(this T control, IValueObservable<TextAnchor> childAlignment)
            where T : IUnityComponentControl<LayoutGroup>
        {
            control.AddBinding(childAlignment.Subscribe(x => control.component.childAlignment = x.currentValue));
            return control;
        }

        public static T Spacing<T>(this T control, float spacing)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.component.spacing = spacing;
            return control;
        }

        public static T Spacing<T>(this T control, IValueObservable<float> spacing)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.AddBinding(spacing.Subscribe(x => control.component.spacing = x.currentValue));
            return control;
        }

        public static T ReverseArrangement<T>(this T control, bool reverseArrangement)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.component.reverseArrangement = reverseArrangement;
            return control;
        }

        public static T ReverseArrangement<T>(this T control, IValueObservable<bool> reverseArrangement)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.AddBinding(reverseArrangement.Subscribe(x => control.component.reverseArrangement = x.currentValue));
            return control;
        }

        public static T ControlChildSize<T>(this T control, bool controlChildSize)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.component.childControlWidth = controlChildSize;
            control.component.childControlHeight = controlChildSize;
            return control;
        }

        public static T ControlChildSize<T>(this T control, IValueObservable<bool> controlChildSize)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.AddBinding(controlChildSize.Subscribe(x =>
            {
                bool value = x.currentValue;
                control.component.childControlWidth = value;
                control.component.childControlHeight = value;
            }));
            return control;
        }

        public static T ControlChildHeight<T>(this T control, bool controlChildHeight)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.component.childControlHeight = controlChildHeight;
            return control;
        }

        public static T ControlChildHeight<T>(this T control, IValueObservable<bool> controlChildHeight)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.AddBinding(controlChildHeight.Subscribe(x => control.component.childControlHeight = x.currentValue));
            return control;
        }

        public static T ControlChildWidth<T>(this T control, bool controlChildWidth)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.component.childControlWidth = controlChildWidth;
            return control;
        }

        public static T ControlChildWidth<T>(this T control, IValueObservable<bool> controlChildWidth)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.AddBinding(controlChildWidth.Subscribe(x => control.component.childControlWidth = (bool)x.currentValue));
            return control;
        }

        public static T ChildForceExpand<T>(this T control, bool forceExpand)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.component.childForceExpandHeight = forceExpand;
            control.component.childForceExpandWidth = forceExpand;
            return control;
        }

        public static T ChildForceExpand<T>(this T control, IValueObservable<bool> forceExpand)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.AddBinding(forceExpand.Subscribe(x =>
            {
                bool value = x.currentValue;
                control.component.childForceExpandHeight = value;
                control.component.childForceExpandWidth = value;
            }));
            return control;
        }

        public static T ChildForceExpandHeight<T>(this T control, bool forceExpandHeight)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.component.childForceExpandHeight = forceExpandHeight;
            return control;
        }

        public static T ChildForceExpandHeight<T>(this T control, IValueObservable<bool> forceExpandHeight)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.AddBinding(forceExpandHeight.Subscribe(x => control.component.childForceExpandHeight = x.currentValue));
            return control;
        }

        public static T ChildForceExpandWidth<T>(this T control, bool forceExpandWidth)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.component.childForceExpandWidth = forceExpandWidth;
            return control;
        }

        public static T ChildForceExpandWidth<T>(this T control, IValueObservable<bool> forceExpandWidth)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.AddBinding(forceExpandWidth.Subscribe(x => control.component.childForceExpandWidth = x.currentValue));
            return control;
        }

        public static T UseChildScale<T>(this T control, bool useChildScale)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.component.childScaleWidth = useChildScale;
            control.component.childScaleHeight = useChildScale;
            return control;
        }

        public static T UseChildScale<T>(this T control, IValueObservable<bool> useChildScale)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.AddBinding(useChildScale.Subscribe(x =>
            {
                bool value = x.currentValue;
                control.component.childScaleWidth = value;
                control.component.childScaleHeight = value;
            }));
            return control;
        }

        public static T UseChildScaleHeight<T>(this T control, bool useChildScaleHeight)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.component.childScaleHeight = useChildScaleHeight;
            return control;
        }

        public static T UseChildScaleHeight<T>(this T control, IValueObservable<bool> useChildScaleHeight)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.AddBinding(useChildScaleHeight.Subscribe(x => control.component.childScaleHeight = x.currentValue));
            return control;
        }

        public static T UseChildScaleWidth<T>(this T control, bool useChildScaleWidth)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.component.childScaleWidth = useChildScaleWidth;
            return control;
        }

        public static T UseChildScaleWidth<T>(this T control, IValueObservable<bool> useChildScaleWidth)
            where T : IUnityComponentControl<HorizontalOrVerticalLayoutGroup>
        {
            control.AddBinding(useChildScaleWidth.Subscribe(x => control.component.childScaleWidth = x.currentValue));
            return control;
        }

        public static T EnableVerticalScroll<T>(this T control, bool enableVerticalScroll)
            where T : IUnityComponentControl<ScrollRect>
        {
            control.component.vertical = enableVerticalScroll;
            return control;
        }

        public static T EnableVerticalScroll<T>(this T control, IValueObservable<bool> enableVerticalScroll)
            where T : IUnityComponentControl<ScrollRect>
        {
            control.AddBinding(enableVerticalScroll.Subscribe(x => control.component.vertical = x.currentValue));
            return control;
        }

        public static T EnableHorizontalScroll<T>(this T control, bool enableHorizontalScroll)
            where T : IUnityComponentControl<ScrollRect>
        {
            control.component.horizontal = enableHorizontalScroll;
            return control;
        }

        public static T EnableHorizontalScroll<T>(this T control, IValueObservable<bool> enableHorizontalScroll)
            where T : IUnityComponentControl<ScrollRect>
        {
            control.AddBinding(enableHorizontalScroll.Subscribe(x => control.component.horizontal = x.currentValue));
            return control;
        }

        public static T MovementType<T>(this T control, ScrollRect.MovementType movementType)
            where T : IUnityComponentControl<ScrollRect>
        {
            control.component.movementType = movementType;
            return control;
        }

        public static T MovementType<T>(this T control, IValueObservable<ScrollRect.MovementType> movementType)
            where T : IUnityComponentControl<ScrollRect>
        {
            control.AddBinding(movementType.Subscribe(x => control.component.movementType = x.currentValue));
            return control;
        }

        public static T Inertia<T>(this T control, bool inertia)
            where T : IUnityComponentControl<ScrollRect>
        {
            control.component.inertia = inertia;
            return control;
        }

        public static T Inertia<T>(this T control, IValueObservable<bool> inertia)
            where T : IUnityComponentControl<ScrollRect>
        {
            control.AddBinding(inertia.Subscribe(x => control.component.inertia = x.currentValue));
            return control;
        }

        public static T DecelerationRate<T>(this T control, float decelerationRate)
            where T : IUnityComponentControl<ScrollRect>
        {
            control.component.decelerationRate = decelerationRate;
            return control;
        }

        public static T DecelerationRate<T>(this T control, IValueObservable<float> decelerationRate)
            where T : IUnityComponentControl<ScrollRect>
        {
            control.AddBinding(decelerationRate.Subscribe(x => control.component.decelerationRate = x.currentValue));
            return control;
        }

        public static T ScrollSensitivity<T>(this T control, float scrollSensitivity)
            where T : IUnityComponentControl<ScrollRect>
        {
            control.component.scrollSensitivity = scrollSensitivity;
            return control;
        }

        public static T ScrollSensitivity<T>(this T control, IValueObservable<float> scrollSensitivity)
            where T : IUnityComponentControl<ScrollRect>
        {
            control.AddBinding(scrollSensitivity.Subscribe(x => control.component.scrollSensitivity = x.currentValue));
            return control;
        }

        public static TComponent InputText<TComponent, TContent>(this TComponent control, TContent text)
            where TComponent : IUnityComponentControl<TMP_InputField>
        {
            control.component.text = text?.ToString();
            return control;
        }

        public static TComponent InputText<TComponent, TContent>(this TComponent control, IValueObservable<TContent> text)
            where TComponent : IUnityComponentControl<TMP_InputField>
        {
            control.AddBinding(text.Subscribe(x => control.component.text = x.currentValue?.ToString()));
            return control;
        }

        public static T PointSize<T>(this T control, int pointSize)
            where T : IUnityComponentControl<TMP_InputField>
        {
            control.component.pointSize = pointSize;
            return control;
        }

        public static T PointSize<T>(this T control, IValueObservable<int> pointSize)
            where T : IUnityComponentControl<TMP_InputField>
        {
            control.AddBinding(pointSize.Subscribe(x => control.component.pointSize = x.currentValue));
            return control;
        }

        public static T ContentType<T>(this T control, TMP_InputField.ContentType contentType)
            where T : IUnityComponentControl<TMP_InputField>
        {
            control.component.contentType = contentType;
            return control;
        }

        public static T ContentType<T>(this T control, IValueObservable<TMP_InputField.ContentType> contentType)
            where T : IUnityComponentControl<TMP_InputField>
        {
            control.AddBinding(contentType.Subscribe(x => control.component.contentType = x.currentValue));
            return control;
        }

        public static T ReadOnly<T>(this T control, bool readOnly)
            where T : IUnityComponentControl<TMP_InputField>
        {
            control.component.readOnly = readOnly;
            return control;
        }

        public static T ReadOnly<T>(this T control, IValueObservable<bool> readOnly)
            where T : IUnityComponentControl<TMP_InputField>
        {
            control.AddBinding(readOnly.Subscribe(x => control.component.readOnly = x.currentValue));
            return control;
        }

        public static T LineType<T>(this T control, TMP_InputField.LineType lineType)
            where T : IUnityComponentControl<TMP_InputField>
        {
            control.component.lineType = lineType;
            return control;
        }

        public static T LineType<T>(this T control, IValueObservable<TMP_InputField.LineType> lineType)
            where T : IUnityComponentControl<TMP_InputField>
        {
            control.AddBinding(lineType.Subscribe(x => control.component.lineType = x.currentValue));
            return control;
        }

        public static T CharacterLimit<T>(this T control, int characterLimit)
            where T : IUnityComponentControl<TMP_InputField>
        {
            control.component.characterLimit = characterLimit;
            return control;
        }

        public static T CharacterLimit<T>(this T control, IValueObservable<int> characterLimit)
            where T : IUnityComponentControl<TMP_InputField>
        {
            control.AddBinding(characterLimit.Subscribe(x => control.component.characterLimit = x.currentValue));
            return control;
        }

        public static T OnValueChanged<T>(this T control, UnityAction<string> onValueChanged)
            where T : IUnityComponentControl<TMP_InputField>
        {
            control.component.onValueChanged.AddListener(onValueChanged);
            return control;
        }

        public static T OnEndEdit<T>(this T control, UnityAction<string> onEndEdit)
            where T : IUnityComponentControl<TMP_InputField>
        {
            control.component.onEndEdit.AddListener(onEndEdit);
            return control;
        }

        public static T OnSelect<T>(this T control, UnityAction<string> onSelect)
            where T : IUnityComponentControl<TMP_InputField>
        {
            control.component.onSelect.AddListener(onSelect);
            return control;
        }

        public static T OnDeselect<T>(this T control, UnityAction<string> onDeselect)
            where T : IUnityComponentControl<TMP_InputField>
        {
            control.component.onDeselect.AddListener(onDeselect);
            return control;
        }

        public static T Direction<T>(this T control, Scrollbar.Direction direction)
            where T : IUnityComponentControl<Scrollbar>
        {
            control.component.direction = direction;
            return control;
        }

        public static T Direction<T>(this T control, IValueObservable<Scrollbar.Direction> direction)
            where T : IUnityComponentControl<Scrollbar>
        {
            control.AddBinding(direction.Subscribe(x => control.component.direction = x.currentValue));
            return control;
        }

        public static T Value<T>(this T control, float value)
            where T : IUnityComponentControl<Scrollbar>
        {
            control.component.value = value;
            return control;
        }

        public static T Value<T>(this T control, IValueObservable<float> value)
            where T : IUnityComponentControl<Scrollbar>
        {
            control.AddBinding(value.Subscribe(x => control.component.value = x.currentValue));
            return control;
        }

        public static T Size<T>(this T control, float size)
            where T : IUnityComponentControl<Scrollbar>
        {
            control.component.size = size;
            return control;
        }

        public static T Size<T>(this T control, IValueObservable<float> size)
            where T : IUnityComponentControl<Scrollbar>
        {
            control.AddBinding(size.Subscribe(x => control.component.size = x.currentValue));
            return control;
        }

        public static T NumberOfSteps<T>(this T control, int numberOfSteps)
            where T : IUnityComponentControl<Scrollbar>
        {
            control.component.numberOfSteps = numberOfSteps;
            return control;
        }

        public static T NumberOfSteps<T>(this T control, IValueObservable<int> numberOfSteps)
            where T : IUnityComponentControl<Scrollbar>
        {
            control.AddBinding(numberOfSteps.Subscribe(x => control.component.numberOfSteps = x.currentValue));
            return control;
        }

        public static T OnValueChanged<T>(this T control, UnityAction<float> onValueChanged)
            where T : IUnityComponentControl<Scrollbar>
        {
            control.component.onValueChanged.AddListener(onValueChanged);
            return control;
        }

        public static T Value<T>(this T control, int value)
            where T : IUnityComponentControl<TMP_Dropdown>
        {
            control.component.value = value;
            return control;
        }

        public static T Value<T>(this T control, IValueObservable<int> value)
            where T : IUnityComponentControl<TMP_Dropdown>
        {
            control.AddBinding(value.Subscribe(x => control.component.value = x.currentValue));
            return control;
        }

        public static T Options<T>(this T control, params string[] options)
            where T : IUnityComponentControl<TMP_Dropdown> => control.Options(options.Select(x => new TMP_Dropdown.OptionData(x)).ToList());

        public static T Options<T>(this T control, params Sprite[] options)
            where T : IUnityComponentControl<TMP_Dropdown> => control.Options(options.Select(x => new TMP_Dropdown.OptionData(x)).ToList());

        public static T Options<T>(this T control, params TMP_Dropdown.OptionData[] options)
            where T : IUnityComponentControl<TMP_Dropdown> => control.Options(options.ToList());

        public static T Options<T>(this T control, IEnumerable<string> options)
            where T : IUnityComponentControl<TMP_Dropdown> => control.Options(options.Select(x => new TMP_Dropdown.OptionData(x)).ToList());

        public static T Options<T>(this T control, IEnumerable<Sprite> options)
            where T : IUnityComponentControl<TMP_Dropdown> => control.Options(options.Select(x => new TMP_Dropdown.OptionData(x)).ToList());

        public static T Options<T>(this T control, IEnumerable<TMP_Dropdown.OptionData> options)
            where T : IUnityComponentControl<TMP_Dropdown> => control.Options(options.ToList());

        public static T Options<T>(this T control, List<TMP_Dropdown.OptionData> options)
            where T : IUnityComponentControl<TMP_Dropdown>
        {
            control.component.options = options;
            return control;
        }

        public static T Value<T>(this T control, IListObservable<TMP_Dropdown.OptionData> options)
            where T : IUnityComponentControl<TMP_Dropdown>
        {
            List<TMP_Dropdown.OptionData> opts = new List<TMP_Dropdown.OptionData>();
            control.AddBinding(options.Subscribe(x =>
            {
                switch (x.operationType)
                {
                    case OpType.Add: opts.Insert(x.index, x.element); break;
                    case OpType.Remove: opts.RemoveAt(x.index); break;
                }

                control.component.options = opts;
            }));
            return control;
        }

        public static T Content<T>(this T control, params IControl[] children)
            where T : ScrollRectControl
        {
            control.content.Children((IEnumerable<IControl>)children);
            return control;
        }

        public static T Content<T>(this T control, IEnumerable<IControl> children)
            where T : ScrollRectControl
        {
            control.content.Children(children);
            return control;
        }

        public static TParent Content<TParent, TChildren>(this TParent control, IListObservable<TChildren> children)
            where TParent : ScrollRectControl where TChildren : IControl
        {
            control.content.Children(children);
            return control;
        }
    }
}
