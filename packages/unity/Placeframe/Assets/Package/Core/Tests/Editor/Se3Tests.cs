using MathNet.Numerics.LinearAlgebra;
using NUnit.Framework;
using Unity.Mathematics;

namespace Placeframe.Core.Tests
{
    public class Se3Tests
    {
        [Test]
        public void Exp_ZeroVector_GivesIdentity()
        {
            var xi = Vector<double>.Build.Dense(6);

            var transform = Se3.Exp(xi);

            AssertNearIdentity(transform, 1e-9);
        }

        [Test]
        public void Log_Identity_GivesZeroVector()
        {
            var xi = Se3.Log(double4x4.identity);

            for (int i = 0; i < 6; i++)
                Assert.That(xi[i], Is.EqualTo(0.0).Within(1e-9), $"xi[{i}]");
        }

        [Test]
        public void LogExp_RoundTripsTinyTangent()
        {
            // Smaller than SmallAngle threshold; exercises the linear branch.
            var xi = Vector<double>.Build.DenseOfArray(new[] { 1e-8, 2e-8, -3e-8, 0.001, -0.002, 0.003 });

            var roundTrip = Se3.Log(Se3.Exp(xi));

            for (int i = 0; i < 6; i++)
                Assert.That(roundTrip[i], Is.EqualTo(xi[i]).Within(1e-7), $"xi[{i}]");
        }

        [Test]
        public void LogExp_RoundTripsModerateTangent()
        {
            var xi = Vector<double>.Build.DenseOfArray(new[] { 0.3, -0.4, 0.5, 1.2, -0.7, 2.1 });

            var roundTrip = Se3.Log(Se3.Exp(xi));

            for (int i = 0; i < 6; i++)
                Assert.That(roundTrip[i], Is.EqualTo(xi[i]).Within(1e-9), $"xi[{i}]");
        }

        [Test]
        public void Exp_PureTranslation_PutsRhoInColumn3()
        {
            var xi = Vector<double>.Build.DenseOfArray(new[] { 0.0, 0.0, 0.0, 1.5, -2.5, 3.5 });

            var transform = Se3.Exp(xi);

            Assert.That(transform.c3.x, Is.EqualTo(1.5).Within(1e-9));
            Assert.That(transform.c3.y, Is.EqualTo(-2.5).Within(1e-9));
            Assert.That(transform.c3.z, Is.EqualTo(3.5).Within(1e-9));
        }

        [Test]
        public void Exp_PureZRotation_RotatesByExpectedAngle()
        {
            var theta = math.PI_DBL / 4.0;
            var xi = Vector<double>.Build.DenseOfArray(new[] { 0.0, 0.0, theta, 0.0, 0.0, 0.0 });

            var transform = Se3.Exp(xi);

            Assert.That(transform.c0.x, Is.EqualTo(math.cos(theta)).Within(1e-9));
            Assert.That(transform.c0.y, Is.EqualTo(math.sin(theta)).Within(1e-9));
            Assert.That(transform.c1.x, Is.EqualTo(-math.sin(theta)).Within(1e-9));
            Assert.That(transform.c1.y, Is.EqualTo(math.cos(theta)).Within(1e-9));
        }

        private static void AssertNearIdentity(double4x4 m, double tol)
        {
            for (int c = 0; c < 4; c++)
            for (int r = 0; r < 4; r++)
            {
                var expected = c == r ? 1.0 : 0.0;
                Assert.That(m[c][r], Is.EqualTo(expected).Within(tol), $"m[{c}][{r}]");
            }
        }
    }
}
