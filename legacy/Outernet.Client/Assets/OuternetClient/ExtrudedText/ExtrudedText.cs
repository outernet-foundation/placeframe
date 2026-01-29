using UnityEngine;
using TMPro;
using System.Collections.Generic;
using System.Linq;

namespace Outernet.Client
{
    [RequireComponent(typeof(TextMeshPro))]
    public class ExtrudedTextMeshPro : MonoBehaviour
    {
        class MeshData
        {
            public Mesh mesh = new Mesh();
            public Vector3[] vertices;
            public Vector2[] uvs;
            public Vector2[] fontStyles;
            public Vector3[] depths;
            public Vector4[] quadUVBounds;
            public Vector4[] quadBounds;
            public Vector2[] skews;
            public Color32[] colors;
            public int[] triangles;

            public void Update()
            {
                mesh.Clear();
                mesh.SetVertices(vertices);
                mesh.SetUVs(1, fontStyles);
                mesh.SetUVs(2, depths);
                mesh.SetUVs(3, quadUVBounds);
                mesh.SetUVs(4, quadBounds);
                mesh.SetUVs(5, skews);
                mesh.SetColors(colors);
                mesh.SetTriangles(triangles, 0);
                mesh.RecalculateNormals();
                mesh.RecalculateBounds();
            }
        }

        TextMeshPro textMeshPro;
        Vector3[] depths = null;
        List<MeshData> meshesData = new List<MeshData>();

        public float defaultDepth = 1;

        void Awake()
        {
            textMeshPro = GetComponent<TextMeshPro>();

            // Disable the default TextMeshPro mesh renderer, because we're going to render the text ourselves using new extruded meshes
            GetComponent<MeshRenderer>().enabled = false;
        }

        void OnEnable()
        {
            TMPro_EventManager.TEXT_CHANGED_EVENT.Add(HandleTextChanged);
        }

        void OnDisable()
        {
            TMPro_EventManager.TEXT_CHANGED_EVENT.Remove(HandleTextChanged);
        }

        void HandleTextChanged(Object obj)
        {
            if (obj != textMeshPro || textMeshPro.textInfo == null) return;

            depths = Enumerable.Repeat(new Vector3(defaultDepth, 0, 1), textMeshPro.textInfo.characterCount).ToArray();

            for (int i = 0; i < textMeshPro.textInfo.meshInfo.Length; i++)
            {
                if (meshesData.Count <= i)
                {
                    meshesData.Add(new MeshData());
                    GameObject extrudedMeshObject = new GameObject($"ExtrudedMesh_{i}");
                    extrudedMeshObject.transform.SetParent(transform, false);
                    extrudedMeshObject.AddComponent<MeshFilter>().mesh = meshesData[i].mesh;

#if UNITY_EDITOR
                    extrudedMeshObject.AddComponent<MeshRenderer>().sharedMaterial = GetComponent<MeshRenderer>().sharedMaterial;
#else
                    extrudedMeshObject.AddComponent<MeshRenderer>().material = GetComponent<MeshRenderer>().material;
#endif
                }

                var meshData = meshesData[i];
                var vertexCount = textMeshPro.textInfo.meshInfo[i].vertexCount * 6;
                var triangleCount = textMeshPro.textInfo.meshInfo[i].vertexCount * 9;

                meshData.vertices = new Vector3[vertexCount];
                meshData.uvs = new Vector2[vertexCount];
                meshData.fontStyles = new Vector2[vertexCount];
                meshData.depths = new Vector3[vertexCount];
                meshData.quadUVBounds = new Vector4[vertexCount];
                meshData.quadBounds = new Vector4[vertexCount];
                meshData.skews = new Vector2[vertexCount];
                meshData.colors = new Color32[vertexCount];
                meshData.triangles = new int[triangleCount];
            }

            UpdateMeshes();
        }

        public void SetDepthData(Vector3[] depths)
        {
            if (depths.Count() != textMeshPro.textInfo.characterCount)
            {
                throw new System.ArgumentException("Depth data count must match character count");
            }

            if (depths.SequenceEqual(this.depths)) return;

            this.depths = depths;

            UpdateMeshes();
        }

        // Extrude each character quad into a cube, with duplicated vertices for each face (because
        // raymarching requires face-specific boundary data)
        public void UpdateMeshes()
        {
            var vertexIndex = 0;
            var triangleIndex = 0;
            for (int characterIndex = 0; characterIndex < textMeshPro.textInfo.characterCount; characterIndex++)
            {
                var charInfo = textMeshPro.textInfo.characterInfo[characterIndex];

                // Skip spaces
                if (!charInfo.isVisible) continue;

                var bottomLeft = charInfo.vertex_BL;
                var topLeft = charInfo.vertex_TL;
                var topRight = charInfo.vertex_TR;
                var bottomRight = charInfo.vertex_BR;
                var fontStyle = bottomLeft.uv2;

                var depth = depths == null ? new Vector3(defaultDepth, 0, 1) : depths[characterIndex];
                var depthOffset = depth.x * -Vector3.Cross(topRight.position - bottomLeft.position, topLeft.position - bottomLeft.position).normalized;
                var skew = new Vector2(Mathf.Abs(topLeft.position.x - bottomLeft.position.x), 0);
                var color = bottomLeft.color;

                float minXPos = Mathf.Min(bottomLeft.position.x, topLeft.position.x);
                float minYPos = Mathf.Min(bottomLeft.position.y, topLeft.position.y);
                float width = topRight.position.x - topLeft.position.x;
                float height = topRight.position.y - bottomRight.position.y;
                Vector4 quadBounds = new Vector4(minXPos, minYPos, width, height);

                float minX = Mathf.Min(bottomLeft.uv.x, topLeft.uv.x);
                float minY = Mathf.Min(bottomLeft.uv.y, bottomRight.uv.y);
                float widthUV = topRight.uv.x - topLeft.uv.x;
                float heightUV = topRight.uv.y - bottomRight.uv.y;
                Vector4 quadUVBounds = new Vector4(minX, minY, widthUV, heightUV);

                var meshData = meshesData[charInfo.materialReferenceIndex];

                for (int face = 0; face < 6; face++)
                {
                    switch (face)
                    {
                        // Front face
                        case 0:
                            meshData.vertices[vertexIndex + 0] = bottomLeft.position + depthOffset;
                            meshData.vertices[vertexIndex + 1] = topLeft.position + depthOffset;
                            meshData.vertices[vertexIndex + 2] = topRight.position + depthOffset;
                            meshData.vertices[vertexIndex + 3] = bottomRight.position + depthOffset;
                            break;
                        // Back face
                        case 1:
                            meshData.vertices[vertexIndex + 0] = bottomRight.position;
                            meshData.vertices[vertexIndex + 1] = topRight.position;
                            meshData.vertices[vertexIndex + 2] = topLeft.position;
                            meshData.vertices[vertexIndex + 3] = bottomLeft.position;
                            break;
                        // Left face
                        case 2:
                            meshData.vertices[vertexIndex + 0] = bottomLeft.position;
                            meshData.vertices[vertexIndex + 1] = topLeft.position;
                            meshData.vertices[vertexIndex + 2] = topLeft.position + depthOffset;
                            meshData.vertices[vertexIndex + 3] = bottomLeft.position + depthOffset;
                            break;
                        // Right face
                        case 3:
                            meshData.vertices[vertexIndex + 0] = bottomRight.position + depthOffset;
                            meshData.vertices[vertexIndex + 1] = topRight.position + depthOffset;
                            meshData.vertices[vertexIndex + 2] = topRight.position;
                            meshData.vertices[vertexIndex + 3] = bottomRight.position;
                            break;
                        // Top face
                        case 4:
                            meshData.vertices[vertexIndex + 0] = topLeft.position + depthOffset;
                            meshData.vertices[vertexIndex + 1] = topLeft.position;
                            meshData.vertices[vertexIndex + 2] = topRight.position;
                            meshData.vertices[vertexIndex + 3] = topRight.position + depthOffset;
                            break;
                        // Bottom face
                        case 5:
                            meshData.vertices[vertexIndex + 0] = bottomLeft.position;
                            meshData.vertices[vertexIndex + 1] = bottomLeft.position + depthOffset;
                            meshData.vertices[vertexIndex + 2] = bottomRight.position + depthOffset;
                            meshData.vertices[vertexIndex + 3] = bottomRight.position;
                            break;
                    }

                    for (int i = 0; i < 4; i++)
                    {
                        meshData.fontStyles[vertexIndex + i] = fontStyle;
                        meshData.depths[vertexIndex + i] = depth;
                        meshData.quadUVBounds[vertexIndex + i] = quadUVBounds;
                        meshData.quadBounds[vertexIndex + i] = quadBounds;
                        meshData.skews[vertexIndex + i] = skew;
                        meshData.colors[vertexIndex + i] = color;
                    }

                    meshData.triangles[triangleIndex + 0] = vertexIndex + 0;
                    meshData.triangles[triangleIndex + 1] = vertexIndex + 1;
                    meshData.triangles[triangleIndex + 2] = vertexIndex + 2;
                    meshData.triangles[triangleIndex + 3] = vertexIndex + 2;
                    meshData.triangles[triangleIndex + 4] = vertexIndex + 3;
                    meshData.triangles[triangleIndex + 5] = vertexIndex + 0;

                    vertexIndex += 4;
                    triangleIndex += 6;
                }
            }

            foreach (var meshData in meshesData)
            {
                meshData.Update();
            }
        }
    }
}
