using Unity.Mathematics;
using UnityEngine;


namespace Outernet.Client
{
    public static class MathUtils
    {
        public static Quaternion SmoothDampQuaternion(
            Quaternion current,
            Quaternion target,
            ref Vector3 currentVelocity,
            float smoothTime)
        {
            if (Time.deltaTime == 0) return current;
            if (smoothTime == 0) return target;

            return Quaternion.Euler(
                Mathf.SmoothDampAngle(current.eulerAngles.x, target.eulerAngles.x, ref currentVelocity.x, smoothTime),
                Mathf.SmoothDampAngle(current.eulerAngles.y, target.eulerAngles.y, ref currentVelocity.y, smoothTime),
                Mathf.SmoothDampAngle(current.eulerAngles.z, target.eulerAngles.z, ref currentVelocity.z, smoothTime)
            );
        }

        public static double3 SmoothDampDouble3(
            double3 current,
            double3 target,
            ref double3 currentVelocity,
            double smoothTime)
        {
            var deltaTime = Time.deltaTime;
            var maxSpeed = float.PositiveInfinity;

            smoothTime = math.max(0.0001, smoothTime);
            var omega = 2.0 / smoothTime;

            double3 diff = current - target;
            var maxMove = maxSpeed * smoothTime;
            var sqrDist = math.lengthsq(diff);
            if (sqrDist > maxMove * maxMove)
            {
                diff = math.normalize(diff) * maxMove;
            }

            target = current - diff;
            var temp = (currentVelocity + omega * diff) * deltaTime;
            currentVelocity = (currentVelocity - omega * temp) * (1.0 / (1.0 + omega * deltaTime + 0.48 * omega * deltaTime * deltaTime + 0.235 * omega * deltaTime * deltaTime * deltaTime));

            var result = target + (diff + temp) * (1.0 / (1.0 + omega * deltaTime + 0.48 * omega * deltaTime * deltaTime + 0.235 * omega * deltaTime * deltaTime * deltaTime));

            var originalTargetDiff = target - current;
            var resultTargetDiff = result - target;
            if (math.dot(originalTargetDiff, resultTargetDiff) > 0.0)
            {
                result = target;
                currentVelocity = (result - target) / deltaTime;
            }

            return result;
        }

        public static double3 LerpDouble3(double3 a, double3 b, double t)
        {
            return a + (b - a) * t;
        }
    }
}