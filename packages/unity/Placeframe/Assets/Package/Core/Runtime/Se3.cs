using MathNet.Numerics.LinearAlgebra;
using Unity.Mathematics;

namespace Placeframe.Core
{
    public static class Se3
    {
        // Tangent-vector convention: (ω_x, ω_y, ω_z, ρ_x, ρ_y, ρ_z) — rotation block first,
        // matching pycolmap's PnP covariance ordering for consistent Σ_meas reuse.
        private const double SmallAngle = 1e-6;

        public static double4x4 Exp(Vector<double> xi)
        {
            var omega = new double3(xi[0], xi[1], xi[2]);
            var rho = new double3(xi[3], xi[4], xi[5]);
            var theta = math.length(omega);

            double3x3 R;
            double3x3 V;
            if (theta < SmallAngle)
            {
                var skew = Skew(omega);
                R = double3x3.identity + skew;
                V = double3x3.identity + 0.5 * skew;
            }
            else
            {
                var skew = Skew(omega);
                var skew2 = math.mul(skew, skew);
                var sinT = math.sin(theta);
                var cosT = math.cos(theta);
                var s = sinT / theta;
                var c = (1.0 - cosT) / (theta * theta);
                var v = (theta - sinT) / (theta * theta * theta);
                R = double3x3.identity + s * skew + c * skew2;
                V = double3x3.identity + c * skew + v * skew2;
            }

            var t = math.mul(V, rho);
            return Double4x4.FromTranslationRotation(t, R);
        }

        public static Vector<double> Log(double4x4 transform)
        {
            var R = transform.RotationMatrix();
            var t = transform.Position();

            var trace = R.c0.x + R.c1.y + R.c2.z;
            var cosTheta = math.clamp((trace - 1.0) / 2.0, -1.0, 1.0);
            var theta = math.acos(cosTheta);

            double3 omega;
            double3x3 vInv;
            if (theta < SmallAngle)
            {
                omega = SkewInverse(R - double3x3.identity);
                vInv = double3x3.identity - 0.5 * Skew(omega);
            }
            else
            {
                omega = (theta / (2.0 * math.sin(theta))) * SkewInverse(R - math.transpose(R));
                var skew = Skew(omega);
                var skew2 = math.mul(skew, skew);
                var b = 1.0 / (theta * theta) - (1.0 + math.cos(theta)) / (2.0 * theta * math.sin(theta));
                vInv = double3x3.identity - 0.5 * skew + b * skew2;
            }

            var rho = math.mul(vInv, t);
            return Vector<double>.Build.DenseOfArray(new[] { omega.x, omega.y, omega.z, rho.x, rho.y, rho.z });
        }

        // Skew(v) returns the 3x3 matrix M such that M * x = v × x for any vector x.
        private static double3x3 Skew(double3 v) =>
            new double3x3(new double3(0, v.z, -v.y), new double3(-v.z, 0, v.x), new double3(v.y, -v.x, 0));

        // Recovers v from the antisymmetric part of m. Robust to symmetric numerical noise.
        private static double3 SkewInverse(double3x3 m) =>
            new double3((m.c1.z - m.c2.y) * 0.5, (m.c2.x - m.c0.z) * 0.5, (m.c0.y - m.c1.x) * 0.5);
    }
}
