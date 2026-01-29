using UnityEngine;
using TMPro;
using UnityEngine.UI;
using System.Collections.Generic;
using System.Linq;
using Cysharp.Threading.Tasks;
using Unity.VisualScripting;
using System.Threading;

namespace Outernet.Client
{
    public class Toast : MonoBehaviour
    {
        private const float fadeDuration = 0.5f;
        private const float holdDuration = 3.0f;
        private const float zOffset = 1.0f;
        private const float startYOffset = -0.35f;
        private const float endYOffset = -0.2f;
        private const float stackPadding = 0.005f;

        private TextMeshPro textMesh;
        private Image backgroundImage;

        private bool initialized = false;
        private float totalLifetime;
        private float elapsedTime;
        private Vector3 startPosition;
        private Vector3 endPosition;

        static List<Toast> toastStack = new List<Toast>();

        private void OnDestroy() => toastStack.Remove(this);

        static public void ShowToast(string message)
        {
            async UniTask CreateToast(string message)
            {
                await UniTask.SwitchToMainThread();
                var toast = PrefabSystem.Create(PrefabSystem.toast);
                await toast.Initialize(message, toast.GetCancellationTokenOnDestroy());
            }

            UniTask.Create(() => CreateToast(message)).Forget();
        }

        static public void AddToast(Toast newToast)
        {
            var stackOffset = 0.0f;

            toastStack.Add(newToast);
            foreach (var toast in toastStack.Reverse<Toast>())
            {
                toast.endPosition = new Vector3(0f, endYOffset + stackOffset, zOffset);
                stackOffset += (((RectTransform)toast.GetComponentInChildren<Image>().transform).rect.height * toast.transform.localScale.y) + stackPadding;
            }

            newToast.initialized = true;
        }

        public async UniTask Initialize(string message, CancellationToken token)
        {
            textMesh = GetComponentInChildren<TextMeshPro>(true);
            backgroundImage = GetComponentInChildren<Image>(true);
            textMesh.fontMaterial = new Material(textMesh.fontSharedMaterial);
            textMesh.sortingOrder = 100;

            Color txtColor = textMesh.color;
            txtColor.a = 0f;
            textMesh.color = txtColor;

            Color bgColor = backgroundImage.color;
            bgColor.a = 0f;
            backgroundImage.color = bgColor;

            totalLifetime = 2 * fadeDuration + holdDuration;
            elapsedTime = 0f;

            Camera cam = Camera.main;
            transform.SetParent(cam.transform, worldPositionStays: false);

            startPosition = new Vector3(0f, startYOffset, zOffset);
            endPosition = new Vector3(0f, endYOffset, zOffset);

            transform.localPosition = startPosition;
            transform.localRotation = Quaternion.identity;

            textMesh.text = message;

            // Hack to ensure image height is updated before calculating stack offset
            await UniTask.DelayFrame(2);

            if (token.IsCancellationRequested) throw new System.OperationCanceledException(token);

            AddToast(this);
        }

        private void FixedUpdate()
        {
            if (!initialized) return;

            elapsedTime += Time.deltaTime;

            float fadeInEnd = fadeDuration;
            float holdEnd = fadeInEnd + holdDuration;

            float alpha;
            Vector3 position;

            if (elapsedTime < fadeInEnd)
            {
                float t = elapsedTime / fadeDuration;
                float smoothT = Mathf.SmoothStep(0f, 1f, t);

                alpha = smoothT;
                position = Vector3.Lerp(startPosition, endPosition, smoothT);
            }
            else if (elapsedTime < holdEnd)
            {
                alpha = 1f;
                position = endPosition;
            }
            else if (elapsedTime < totalLifetime)
            {
                float timeSinceFadeOut = elapsedTime - holdEnd;
                float t = timeSinceFadeOut / fadeDuration;
                float smoothT = Mathf.SmoothStep(0f, 1f, t);

                alpha = 1f - smoothT;
                position = Vector3.Lerp(endPosition, startPosition, smoothT);
            }
            else
            {
                PrefabSystem.Destroy(this);
                return;
            }

            transform.localPosition = position;

            Color txtColor = textMesh.color;
            txtColor.a = alpha;
            textMesh.color = txtColor;

            Color bgColor = backgroundImage.color;
            bgColor.a = alpha;
            backgroundImage.color = bgColor;
        }
    }
}
