using System;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public static class SceneSerialization
    {
        public static Guid GetSceneObjectID(GameObject view)
        {
            // TODO: return ID for the view if one already exists, or generate one if it doesn't
            return Guid.Empty;
        }
    }

    public interface ISerializableView
    {
        void Serialize(Guid sceneObjectID, SceneState state);
    }
}