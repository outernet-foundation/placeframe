using UnityEngine;
using UnityEngine.UI;
using Nessle;
using TMPro;

using static Nessle.UIBuilder;

namespace PlerionClient.Client
{
    public static class UIPresets
    {
        public static ScrollRectControl VerticalScrollRect()
            => ScrollRect().Style(StyleVerticalScrollRect);

        public static void StyleVerticalScrollRect(ScrollRectControl scrollRect)
        {
            scrollRect.EnableHorizontalScroll(false);

            scrollRect.content
                .FitContentVertical(ContentSizeFitter.FitMode.PreferredSize)
                .SetPivot(new Vector2(0, 1))
                .AnchorToTop()
                .FillParentWidth();
        }

        public static ButtonControl PillButton()
            => Button().Style(StylePillButton);

        public static void StylePillButton(ButtonControl button)
        {
            StylePill(button.background);
            button.background.Color(UIResources.ButtonColor);
            button.contentLayout.Padding(new RectOffset(13, 13, 5, 5)).Alignment(TextAnchor.MiddleCenter);
        }

        public static InputFieldControl PillInputField()
            => InputField().Style(StylePillInputField);

        public static void StylePillInputField(InputFieldControl inputField)
        {
            StylePill(inputField.background);
            inputField.background.PixelsPerUnitMultiplier(1.4f).Color(UIResources.InputFieldColor);
            inputField.inputText.Margin(new Vector4(25, 0, 0, 0));
            inputField.placeholderText.Margin(new Vector4(25, 0, 0, 0));
        }

        public static ScrollbarControl RoundedScrollBar()
            => Scrollbar().Style(StyleRoundedScrollBar);

        public static void StyleRoundedScrollBar(ScrollbarControl scrollbar)
        {
            StylePill(scrollbar.handle);
            StylePill(scrollbar.background);

            scrollbar.handle.PixelsPerUnitMultiplier(8).Color(UIResources.ScrollBarHandleColor);
            scrollbar.background.PixelsPerUnitMultiplier(8).Color(UIResources.ScrollBarBackgroundColor);
        }

        public static UnityComponentControl<TextMeshProUGUI> StandardText()
            => Label().Style(StyleStandardText);

        public static void StyleStandardText(IUnityComponentControl<TextMeshProUGUI> text)
        {
            text.Color(UIResources.TextColor).FontSize(14);
        }

        public static ScrollRectControl StandardScrollRect()
            => ScrollRect().Style(StyleStandardScrollRect);

        public static void StyleStandardScrollRect(ScrollRectControl scrollRect)
        {
            scrollRect.background.Color(UIResources.PanelColor);
        }

        public static ScrollingDropdownControl StandardDropdown()
            => ScrollingDropdown().Style(StyleStandardDropdown);

        public static void StyleStandardDropdown(ScrollingDropdownControl dropdown)
        {
            StylePill(dropdown.background);

            dropdown.background.Color(UIResources.ButtonColor);
            dropdown.template.background.Color(UIResources.ButtonColor);
            dropdown.itemBackground.Color(UIResources.ButtonColor);
        }

        public static IUnityComponentControl<Image> Pill()
            => Image().Style(StylePill);

        public static void StylePill(IUnityComponentControl<Image> image)
            => image.Sprite(UIResources.RoundedBox).ImageType(UnityEngine.UI.Image.Type.Sliced).PixelsPerUnitMultiplier(2.8f);

        public static IUnityComponentControl<HorizontalLayoutGroup> Row()
            => HorizontalLayout().Style(StyleRow);

        public static void StyleRow(IUnityComponentControl<HorizontalLayoutGroup> horizontalLayout)
            => horizontalLayout.ControlChildSize(true).Alignment(TextAnchor.MiddleLeft).Spacing(10).ChildForceExpand(false);

        public static IUnityComponentControl<TextMeshProUGUI> PropertyLabel()
            => Label().Style(StylePropertyLabel);

        public static void StylePropertyLabel(IUnityComponentControl<TextMeshProUGUI> label)
            => label.MinWidth(100).PreferredWidth(300).TextWrappingMode(TextWrappingModes.NoWrap).OverflowMode(TextOverflowModes.Ellipsis);

        public static IUnityComponentControl<TextMeshProUGUI> Title()
            => Label().Style(StyleTitle);

        public static void StyleTitle(IUnityComponentControl<TextMeshProUGUI> label)
            => label.FontSize(64).Alignment(TextAlignmentOptions.MidlineGeoAligned);

        public static IUnityComponentControl<SafeArea> SafeArea()
            => ComponentControl<SafeArea>();
    }
}