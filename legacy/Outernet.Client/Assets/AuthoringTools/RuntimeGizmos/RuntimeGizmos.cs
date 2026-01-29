using UnityEngine;

namespace Outernet.Client.AuthoringTools
{
    public static class RuntimeGizmos
    {
        public static Matrix4x4 matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, Vector3.one);

        private static void DrawGizmo(Mesh mesh, Vector3 position, Quaternion rotation, Vector3 scale, Color color, bool zTest = true)
        {
            var properties = new MaterialPropertyBlock();
            properties.SetColor("_Color", color);

            Graphics.DrawMesh(
                mesh: mesh,
                matrix: matrix * Matrix4x4.TRS(position, rotation, scale),
                material: zTest ? AuthoringToolsPrefabs.GizmoMaterial : AuthoringToolsPrefabs.GizmoMaterialNoZTest,
                layer: 0,
                camera: null,
                submeshIndex: 0,
                properties: properties,
                castShadows: UnityEngine.Rendering.ShadowCastingMode.Off,
                receiveShadows: false,
                probeAnchor: null,
                lightProbeUsage: UnityEngine.Rendering.LightProbeUsage.Off,
                lightProbeProxyVolume: null
            );
        }

        public static void DrawCircle(Vector3 position, Vector3 normal, float radius, Color color, bool zTest = true)
                => DrawGizmo(AuthoringToolsPrefabs.TorusMesh, position, Quaternion.LookRotation(normal), Vector3.one * radius, color, zTest);

        public static void DrawPlane(Vector3 position, Vector3 xDirection, Vector3 yDirection, Vector2 size, Color color, bool zTest = true)
        {
            var zDirection = Vector3.Cross(-xDirection, -yDirection);
            DrawGizmo(AuthoringToolsPrefabs.QuadMesh, position, Quaternion.LookRotation(zDirection, yDirection), new Vector3(size.x, size.y, 1), color, zTest);
            DrawGizmo(AuthoringToolsPrefabs.QuadMesh, position, Quaternion.LookRotation(-zDirection, yDirection), new Vector3(size.x, size.y, 1), color, zTest);
        }

        public static void DrawArrow(Vector3 origin, Vector3 direction, Color color, float thickness, bool zTest = true)
        {
            var rotation = Quaternion.LookRotation(direction);
            var stemLength = direction.magnitude * 0.75f;
            var coneLength = direction.magnitude * 0.25f;

            DrawGizmo(AuthoringToolsPrefabs.CylinderMesh, origin, rotation, new Vector3(thickness, thickness, stemLength), color, zTest);
            DrawGizmo(AuthoringToolsPrefabs.ConeMesh, origin + (direction.normalized * stemLength), rotation, new Vector3(coneLength * 0.25f, coneLength * 0.25f, coneLength), color, zTest);
        }

        public static void DrawRay(Vector3 from, Vector3 direction, float thickness, Color color, bool zTest = true)
        {
            if (direction == Vector3.zero)
                return;

            DrawLine(from, from + direction, thickness, color, zTest);
        }

        public static void DrawLine(Vector3 from, Vector3 to, float thickness, Color color, bool zTest = true)
        {
            if (from == to)
                return;

            DrawGizmo(
                AuthoringToolsPrefabs.CylinderMesh,
                from,
                Quaternion.LookRotation(to - from),
                new Vector3(thickness, thickness, Vector3.Magnitude(from - to)),
                color,
                zTest
            );
        }

        public static void DrawCube(Vector3 position, Vector3 extents, float thickness, Color color, bool zTest = true)
        {
            DrawLine(position + -extents, position + new Vector3(extents.x, -extents.y, -extents.z), thickness, color, zTest);
            DrawLine(position + -extents, position + new Vector3(-extents.x, extents.y, -extents.z), thickness, color, zTest);
            DrawLine(position + -extents, position + new Vector3(-extents.x, -extents.y, extents.z), thickness, color, zTest);

            DrawLine(position + extents, position + new Vector3(-extents.x, extents.y, extents.z), thickness, color, zTest);
            DrawLine(position + extents, position + new Vector3(extents.x, -extents.y, extents.z), thickness, color, zTest);
            DrawLine(position + extents, position + new Vector3(extents.x, extents.y, -extents.z), thickness, color, zTest);

            DrawLine(position + new Vector3(extents.x, -extents.y, -extents.z), position + new Vector3(extents.x, extents.y, -extents.z), thickness, color, zTest);
            DrawLine(position + new Vector3(extents.x, -extents.y, -extents.z), position + new Vector3(extents.x, -extents.y, extents.z), thickness, color, zTest);

            DrawLine(position + new Vector3(-extents.x, extents.y, -extents.z), position + new Vector3(extents.x, extents.y, -extents.z), thickness, color, zTest);
            DrawLine(position + new Vector3(-extents.x, extents.y, -extents.z), position + new Vector3(-extents.x, extents.y, extents.z), thickness, color, zTest);

            DrawLine(position + new Vector3(-extents.x, -extents.y, extents.z), position + new Vector3(-extents.x, extents.y, extents.z), thickness, color, zTest);
            DrawLine(position + new Vector3(-extents.x, -extents.y, extents.z), position + new Vector3(extents.x, -extents.y, extents.z), thickness, color, zTest);
        }

        public static void DrawHalfTorus(Vector3 position, Vector3 lookDirection, Vector3 up, float radius, Color color, bool zTest = true)
            => DrawGizmo(AuthoringToolsPrefabs.HalfTorusMesh, position, Quaternion.LookRotation(lookDirection, up), Vector3.one * radius, color, zTest);
    }
}