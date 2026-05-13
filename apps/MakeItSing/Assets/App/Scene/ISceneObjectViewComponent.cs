using UnityEngine;

namespace Plerion.MakeItSing
{
    public interface ISceneObjectViewComponent
    {
        GameObject gameObject { get; }

        void Setup(SceneObjectId objectId);
        void Teardown();
        void WriteInitialState(SceneState state, SceneObjectId id);
    }
}