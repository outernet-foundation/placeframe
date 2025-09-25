
using Cysharp.Threading.Tasks;

namespace Plerion
{
    public class NoOpCameraProvider : ICameraProvider
    {
        public UniTask<CameraImage?> GetFrame()
            => UniTask.FromResult(default(CameraImage?));

        public void Start() { }
        public void Stop() { }
    }
}