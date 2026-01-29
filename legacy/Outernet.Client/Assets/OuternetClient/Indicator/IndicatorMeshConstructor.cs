using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[ExecuteAlways]
[RequireComponent(typeof(MeshRenderer))]
[RequireComponent(typeof(MeshFilter))]
public class IndicatorMeshConstructor : MonoBehaviour
{
    public float outerRadius;
    public float innerRadius;
    public float pointDistance;
    public float thickness;

    public int circleVerts;

    private MeshFilter _filter;

    private void Start()
    {
        _filter = GetComponent<MeshFilter>();
        if (_filter.sharedMesh == null)
            _filter.sharedMesh = new Mesh();

        _filter.sharedMesh.Clear();

        List<Vector3> verts = new List<Vector3>();
        List<int> tris = new List<int>();

        AddCircleVerts(verts, Matrix4x4.TRS(new Vector3(0, 0, thickness * 0.5f), Quaternion.identity, Vector3.one), outerRadius, circleVerts, pointDistance, out int frontOuterStartIndex);
        AddCircleVerts(verts, Matrix4x4.TRS(new Vector3(0, 0, thickness * 0.5f), Quaternion.identity, Vector3.one), innerRadius, circleVerts, 0, out int frontInnerStartIndex);
        AddStripTris(tris, frontOuterStartIndex, frontInnerStartIndex, circleVerts - 1, true);

        AddCircleVerts(verts, Matrix4x4.TRS(new Vector3(0, 0, -thickness * 0.5f), Quaternion.AngleAxis(180f, Vector3.up), Vector3.one), outerRadius, circleVerts, pointDistance, out int backOuterStartIndex);
        AddCircleVerts(verts, Matrix4x4.TRS(new Vector3(0, 0, -thickness * 0.5f), Quaternion.AngleAxis(180f, Vector3.up), Vector3.one), innerRadius, circleVerts, 0, out int backInnerStartIndex);
        AddStripTris(tris, backOuterStartIndex, backInnerStartIndex, circleVerts - 1, true);

        AddCircleVerts(verts, Matrix4x4.TRS(new Vector3(0, 0, -thickness * 0.5f), Quaternion.identity, Vector3.one), outerRadius, circleVerts, pointDistance, out int backOuterBorderStartIndex);
        AddCircleVerts(verts, Matrix4x4.TRS(new Vector3(0, 0, thickness * 0.5f), Quaternion.identity, Vector3.one), outerRadius, circleVerts, pointDistance, out int frontOuterBorderStartIndex);
        AddStripTris(tris, backOuterBorderStartIndex, frontOuterBorderStartIndex, circleVerts - 1, true);

        AddCircleVerts(verts, Matrix4x4.TRS(new Vector3(0, 0, -thickness * 0.5f), Quaternion.identity, Vector3.one), innerRadius, circleVerts, 0, out int backInnerBorderStartIndex);
        AddCircleVerts(verts, Matrix4x4.TRS(new Vector3(0, 0, thickness * 0.5f), Quaternion.identity, Vector3.one), innerRadius, circleVerts, 0, out int frontInnerBorderStartIndex);
        AddStripTris(tris, frontInnerBorderStartIndex, backInnerBorderStartIndex, circleVerts - 1, true);

        _filter.sharedMesh.vertices = verts.ToArray();
        _filter.sharedMesh.triangles = tris.ToArray();
        _filter.sharedMesh.RecalculateBounds();
        _filter.sharedMesh.RecalculateNormals();
        _filter.sharedMesh.RecalculateTangents();
    }

    private void AddCircleVerts(List<Vector3> verts, Matrix4x4 matrix, float radius, int circleVerts, float pointDistance, out int startIndex)
    {
        startIndex = verts.Count;
        for (int i = 0; i <= circleVerts; i++)
        {
            float deg = Mathf.Lerp(0f, 360f, i / (float)circleVerts);
            Vector3 circlePoint = new Vector3(
                Mathf.Cos(deg * Mathf.Deg2Rad),
                Mathf.Sin(deg * Mathf.Deg2Rad),
                0
            ).normalized * radius;

            if (pointDistance > 0 && deg > 195 && deg < 345)
            {
                if (deg < 270f)
                {
                    var startPoint = new Vector3(
                        Mathf.Cos(195 * Mathf.Deg2Rad),
                        Mathf.Sin(195 * Mathf.Deg2Rad),
                        0
                    ).normalized * radius;
                    var endPoint = new Vector3(0, -(radius + pointDistance), 0);
                    var t = (deg - 195) / 75f;
                    var linePoint = Vector3.Lerp(startPoint, endPoint, t);
                    circlePoint = Vector3.Lerp(circlePoint, linePoint, t);
                }
                else
                {
                    var startPoint = new Vector3(0, -(radius + pointDistance), 0);
                    var endPoint = new Vector3(
                        Mathf.Cos(345 * Mathf.Deg2Rad),
                        Mathf.Sin(345 * Mathf.Deg2Rad),
                        0
                    ).normalized * radius;
                    var t = (deg - 270f) / 75f;
                    var linePoint = Vector3.Lerp(startPoint, endPoint, t);
                    circlePoint = Vector3.Lerp(circlePoint, linePoint, 1 - t);
                }
            }

            verts.Add(matrix.MultiplyPoint(circlePoint));
        }
    }

    private void AddStripTris(List<int> tris, int startIndex1, int startIndex2, int segmentCount, bool loop)
    {
        for (int i = 0; i < segmentCount; i++)
        {
            tris.Add(startIndex2 + i);
            tris.Add(startIndex1 + i);
            tris.Add(startIndex1 + i + 1);
            tris.Add(startIndex2 + i + 1);
            tris.Add(startIndex2 + i);
            tris.Add(startIndex1 + i + 1);
        }

        if (loop)
        {
            tris.Add(startIndex2 + segmentCount);
            tris.Add(startIndex1 + segmentCount);
            tris.Add(startIndex1);

            tris.Add(startIndex2);
            tris.Add(startIndex2 + segmentCount);
            tris.Add(startIndex1);
        }
    }
}
