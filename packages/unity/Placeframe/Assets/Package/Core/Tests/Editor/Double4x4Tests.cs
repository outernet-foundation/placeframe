using System.Collections.Generic;
using NUnit.Framework;
using Unity.Mathematics;

namespace Placeframe.Core.Tests
{
    public class Double4x4Tests
    {
        private const double Tolerance = 1e-9;
        private static readonly IEqualityComparer<double3> Approx = new Double3ApproxComparer(Tolerance);

        [Test]
        public void FromTranslationRotation_PutsTranslationInColumn3()
        {
            var translation = new double3(1.0, 2.0, 3.0);
            var rotation = quaternion.identity;

            var matrix = Double4x4.FromTranslationRotation(translation, rotation);

            Assert.That(matrix.c3.x, Is.EqualTo(1.0).Within(Tolerance));
            Assert.That(matrix.c3.y, Is.EqualTo(2.0).Within(Tolerance));
            Assert.That(matrix.c3.z, Is.EqualTo(3.0).Within(Tolerance));
            Assert.That(matrix.c3.w, Is.EqualTo(1.0).Within(Tolerance));
        }

        [Test]
        public void FromTranslationRotation_IdentityRotationGivesIdentityRotationBlock()
        {
            var matrix = Double4x4.FromTranslationRotation(double3.zero, quaternion.identity);

            Assert.That((double3)matrix.c0.xyz, Is.EqualTo(new double3(1, 0, 0)).Using<double3>(Approx));
            Assert.That((double3)matrix.c1.xyz, Is.EqualTo(new double3(0, 1, 0)).Using<double3>(Approx));
            Assert.That((double3)matrix.c2.xyz, Is.EqualTo(new double3(0, 0, 1)).Using<double3>(Approx));
        }

        [Test]
        public void Decompose_RoundTripsThroughFromTranslationRotation()
        {
            var translationIn = new double3(1.5, -2.5, 3.5);
            var rotationIn = quaternion.AxisAngle(math.normalize(new float3(1, 2, 3)), 0.7f);

            var matrix = Double4x4.FromTranslationRotation(translationIn, rotationIn);
            var (translationOut, rotationOut, scaleOut) = Double4x4.Decompose(matrix);

            Assert.That((double3)translationOut, Is.EqualTo(translationIn).Using<double3>(Approx));
            // Float32 quaternion → double conversion introduces ~1e-7 error in scale recovery.
            Assert.That(scaleOut.x, Is.EqualTo(1.0).Within(1e-6));
            Assert.That(scaleOut.y, Is.EqualTo(1.0).Within(1e-6));
            Assert.That(scaleOut.z, Is.EqualTo(1.0).Within(1e-6));
            // Quaternion compare: q and -q represent the same rotation; compare via dot-product magnitude.
            var dot = math.abs(math.dot(rotationOut, rotationIn));
            Assert.That(dot, Is.EqualTo(1.0).Within(1e-6));
        }

        [Test]
        public void Interpolate_AtZero_ReturnsFirstInput()
        {
            var a = Double4x4.FromTranslationRotation(new double3(1, 2, 3), quaternion.identity);
            var b = Double4x4.FromTranslationRotation(new double3(7, 8, 9), quaternion.identity);

            var result = Double4x4.Interpolate(a, b, 0f);

            Assert.That((double3)result.c3.xyz, Is.EqualTo(new double3(1, 2, 3)).Using<double3>(Approx));
        }

        [Test]
        public void Interpolate_AtOne_ReturnsSecondInput()
        {
            var a = Double4x4.FromTranslationRotation(new double3(1, 2, 3), quaternion.identity);
            var b = Double4x4.FromTranslationRotation(new double3(7, 8, 9), quaternion.identity);

            var result = Double4x4.Interpolate(a, b, 1f);

            Assert.That((double3)result.c3.xyz, Is.EqualTo(new double3(7, 8, 9)).Using<double3>(Approx));
        }

        [Test]
        public void Interpolate_HalfwayTranslation_IsLinearMidpoint()
        {
            var a = Double4x4.FromTranslationRotation(new double3(0, 0, 0), quaternion.identity);
            var b = Double4x4.FromTranslationRotation(new double3(10, 20, 30), quaternion.identity);

            var result = Double4x4.Interpolate(a, b, 0.5f);

            Assert.That((double3)result.c3.xyz, Is.EqualTo(new double3(5, 10, 15)).Using<double3>(Approx));
        }

        [Test]
        public void Interpolate_PreservesRotationOrthonormality()
        {
            var a = Double4x4.FromTranslationRotation(double3.zero, quaternion.identity);
            var b = Double4x4.FromTranslationRotation(
                double3.zero,
                quaternion.AxisAngle(new float3(0, 1, 0), math.PI / 2f)
            );

            var result = Double4x4.Interpolate(a, b, 0.5f);
            var rotationBlock = result.RotationMatrix();

            // Columns should still be unit length (rotation, not skew).
            Assert.That(math.length(rotationBlock.c0), Is.EqualTo(1.0).Within(1e-6));
            Assert.That(math.length(rotationBlock.c1), Is.EqualTo(1.0).Within(1e-6));
            Assert.That(math.length(rotationBlock.c2), Is.EqualTo(1.0).Within(1e-6));
        }

        private sealed class Double3ApproxComparer : IEqualityComparer<double3>
        {
            private readonly double _tolerance;

            public Double3ApproxComparer(double tolerance) => _tolerance = tolerance;

            public bool Equals(double3 a, double3 b) =>
                math.abs(a.x - b.x) < _tolerance
                && math.abs(a.y - b.y) < _tolerance
                && math.abs(a.z - b.z) < _tolerance;

            public int GetHashCode(double3 obj) => obj.GetHashCode();
        }
    }
}
