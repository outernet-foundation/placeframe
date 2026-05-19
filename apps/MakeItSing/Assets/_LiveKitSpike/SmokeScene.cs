using System;
using Cysharp.Threading.Tasks;
using LiveKit;
using LiveKit.Proto;
using Outernet.Logging;
using UnityEngine;
using UnityEngine.UI;

namespace Plerion.MakeItSing.LiveKitSpike
{
    public class SmokeScene : MonoBehaviour
    {
        public string defaultUrl = "ws://10.0.0.1:7880";
        public string defaultToken = "";

        private InputField _urlInput;
        private InputField _tokenInput;
        private Text _logText;
        private Room _room;

        private void Awake()
        {
            BuildUi();
            Append("Ready. Enter URL + token, press Connect.");
        }

        private void BuildUi()
        {
            var canvasObject = new GameObject(
                "SpikeCanvas",
                typeof(Canvas),
                typeof(CanvasScaler),
                typeof(GraphicRaycaster)
            );
            var canvas = canvasObject.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasObject.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1080, 1920);

            new GameObject("EventSystem", typeof(UnityEngine.EventSystems.EventSystem), typeof(UnityEngine.EventSystems.StandaloneInputModule));

            _urlInput = MakeInputField(canvasObject.transform, "UrlInput", new Vector2(0, 700), defaultUrl);
            _tokenInput = MakeInputField(canvasObject.transform, "TokenInput", new Vector2(0, 580), defaultToken);

            var buttonObject = new GameObject("ConnectButton", typeof(RectTransform), typeof(Image), typeof(Button));
            buttonObject.transform.SetParent(canvasObject.transform, false);
            var buttonRect = (RectTransform)buttonObject.transform;
            buttonRect.anchoredPosition = new Vector2(0, 440);
            buttonRect.sizeDelta = new Vector2(400, 100);
            buttonObject.GetComponent<Image>().color = new Color(0.2f, 0.5f, 0.8f);
            buttonObject.GetComponent<Button>().onClick.AddListener(() => RunSmoke().Forget());

            var buttonLabelObject = new GameObject("Label", typeof(RectTransform), typeof(Text));
            buttonLabelObject.transform.SetParent(buttonObject.transform, false);
            var buttonLabel = buttonLabelObject.GetComponent<Text>();
            buttonLabel.text = "Connect";
            buttonLabel.alignment = TextAnchor.MiddleCenter;
            buttonLabel.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            buttonLabel.fontSize = 36;
            buttonLabel.color = Color.white;
            var buttonLabelRect = (RectTransform)buttonLabelObject.transform;
            buttonLabelRect.anchorMin = Vector2.zero;
            buttonLabelRect.anchorMax = Vector2.one;
            buttonLabelRect.sizeDelta = Vector2.zero;

            var logObject = new GameObject("LogText", typeof(RectTransform), typeof(Text));
            logObject.transform.SetParent(canvasObject.transform, false);
            _logText = logObject.GetComponent<Text>();
            _logText.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            _logText.fontSize = 22;
            _logText.alignment = TextAnchor.UpperLeft;
            _logText.color = Color.white;
            var logRect = (RectTransform)logObject.transform;
            logRect.anchoredPosition = new Vector2(0, -200);
            logRect.sizeDelta = new Vector2(960, 1200);
        }

        private static InputField MakeInputField(Transform parent, string objectName, Vector2 position, string value)
        {
            var fieldObject = new GameObject(objectName, typeof(RectTransform), typeof(Image), typeof(InputField));
            fieldObject.transform.SetParent(parent, false);
            var fieldRect = (RectTransform)fieldObject.transform;
            fieldRect.anchoredPosition = position;
            fieldRect.sizeDelta = new Vector2(960, 90);
            fieldObject.GetComponent<Image>().color = new Color(0.15f, 0.15f, 0.15f);

            var input = fieldObject.GetComponent<InputField>();

            var textObject = new GameObject("Text", typeof(RectTransform), typeof(Text));
            textObject.transform.SetParent(fieldObject.transform, false);
            var text = textObject.GetComponent<Text>();
            text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            text.alignment = TextAnchor.MiddleLeft;
            text.color = Color.white;
            text.fontSize = 24;
            var textRect = (RectTransform)textObject.transform;
            textRect.anchorMin = Vector2.zero;
            textRect.anchorMax = Vector2.one;
            textRect.sizeDelta = new Vector2(-20, 0);
            textRect.anchoredPosition = new Vector2(10, 0);

            input.textComponent = text;
            input.text = value;
            return input;
        }

        private async UniTaskVoid RunSmoke()
        {
            try
            {
                Append("Creating Room");
                _room = new Room();
                _room.DataReceived += OnDataReceived;
                _room.Disconnected += _ => Append("DISCONNECTED");
                _room.Connected += _ => Append("CONNECTED event fired");

                Append($"Connecting url={_urlInput.text}");
                await _room.Connect(_urlInput.text, _tokenInput.text, new RoomOptions()).ToUniTask();
                Append($"Connect returned. identity={_room.LocalParticipant?.Identity}");

                await UniTask.Delay(250);

                var payload = new byte[] { 0x01, 0x02, 0x03 };
                Append($"SEND {BitConverter.ToString(payload)} topic=smoke");
                _room.LocalParticipant?.PublishData(payload, reliable: true, topic: "smoke");
            }
            catch (Exception exception)
            {
                Log<LogGroup>.Error(LogGroup.PhotonConnection, exception, "Spike failure");
                Append($"ERROR {exception.GetType().Name}: {exception.Message}");
            }
        }

        private void OnDataReceived(byte[] data, Participant participant, DataPacketKind kind, string topic)
        {
            Append($"RECV from={participant?.Identity} topic={topic} {BitConverter.ToString(data)}");
        }

        private void Append(string line)
        {
            Debug.Log($"[Spike] {line}");
            Log<LogGroup>.Info(LogGroup.PhotonConnection, "[Spike] {Line}", line);
            if (_logText != null)
            {
                _logText.text += line + "\n";
            }
        }
    }
}
