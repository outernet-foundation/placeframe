using System;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

namespace Outernet.Client
{
    [RequireComponent(typeof(RectTransform))]
    [RequireComponent(typeof(RawImage))]
    [RequireComponent(typeof(AspectRatioFitter))]
    public class ImageView : MonoBehaviour
    {
        private static readonly Queue<Func<UniTask>> loadQueue = new Queue<Func<UniTask>>();
        private static bool draining = false;

        public static void EnqueueLoad(Func<UniTask> loadFunc)
        {
            loadQueue.Enqueue(loadFunc);
            if (!draining)
            {
                draining = true;
                DrainQueueAsync().Forget();
            }
        }

        private static async UniTaskVoid DrainQueueAsync()
        {
            while (loadQueue.Count > 0)
            {
                var loadFunc = loadQueue.Dequeue();
                try
                {
                    await loadFunc();
                }
                catch (Exception ex)
                {
                    Debug.LogException(ex);
                }
            }

            draining = false;
        }

        public Action onRebuildLayout;

        private string uri;
        private RawImage image;
        private AspectRatioFitter aspectRatioFitter;
        private Texture2D missingTexture;
        private bool terminated = false;

        public void Initialize(string uri)
        {
            image = GetComponent<RawImage>();
            aspectRatioFitter = GetComponent<AspectRatioFitter>();
            missingTexture = Resources.Load<Texture2D>("Textures/failsafe");
            this.uri = uri;

            EnqueueLoad(Load);
        }

        public void Terminate() => terminated = true;

        public async UniTask Load()
        {
            if (terminated) return;

            if (uri == null)
            {
                ApplyTexture(missingTexture);
                return;
            }

            var request = UnityWebRequestTexture.GetTexture(uri);

            await request.SendWebRequest();

            if (terminated) return;

            if (request.result != UnityWebRequest.Result.Success)
            {
                Log.Error($"Failed to load image from url {uri ?? "'null'"}");
                ApplyTexture(missingTexture);
            }
            else
            {
                ApplyTexture((request.downloadHandler as DownloadHandlerTexture).texture);
            }
        }

        private void ApplyTexture(Texture2D texture)
        {
            image.texture = texture;
            aspectRatioFitter.aspectRatio = texture.width / (float)texture.height;

            if (onRebuildLayout != null)
            {
                onRebuildLayout();
            }
            else
            {
                LayoutRebuilder.ForceRebuildLayoutImmediate((RectTransform)transform);
            }
        }
    }
}
