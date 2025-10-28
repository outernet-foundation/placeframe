using System;
using UnityEngine;

[Serializable]
public class RigConfig
{
    [Serializable]
    public struct PinholeIntrinsics
    {
        public PinholeIntrinsics(
            int width,
            int height,
            float fx,
            float fy,
            float cx,
            float cy)
        {
            model = "PINHOLE";
            this.width = width;
            this.height = height;
            this.fx = fx;
            this.fy = fy;
            this.cx = cx;
            this.cy = cy;
        }

        public string model;
        public int width;
        public int height;
        public float fx;
        public float fy;
        public float cx;
        public float cy;
    }

    [Serializable]
    public struct RigCamera
    {
        public string id;
        public bool ref_sensor;
        public Quaternion rotation; // w.r.t. rig
        public Vector3 translation; // w.r.t. rig
        public PinholeIntrinsics intrinsics;
    }

    [Serializable]
    public class Rig
    {
        public string id;
        public RigCamera[] cameras;
    }

    public Rig[] rigs;
}