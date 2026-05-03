using NUnit.Framework;
using Unity.Mathematics;

namespace Placeframe.Core.Tests
{
    public class LocationUtilitiesTests
    {
        [Test]
        public void ChangeBasisUnityFromEcef_AppliedTwice_ReturnsToEcef()
        {
            var translation = new double3(100, 200, 300);
            var rotation = new quaternion(0.1f, 0.2f, 0.3f, 0.927f).ToDouble3x3();

            var (translationOnce, rotationOnce) = LocationUtilities.ChangeBasisUnityFromEcef(translation, rotation);
            var (translationTwice, rotationTwice) = LocationUtilities.ChangeBasisEcefFromUnity(
                translationOnce,
                rotationOnce
            );

            Assert.That(translationTwice.x, Is.EqualTo(translation.x).Within(1e-9));
            Assert.That(translationTwice.y, Is.EqualTo(translation.y).Within(1e-9));
            Assert.That(translationTwice.z, Is.EqualTo(translation.z).Within(1e-9));
            for (int c = 0; c < 3; c++)
                for (int r = 0; r < 3; r++)
                    Assert.That(rotationTwice[c][r], Is.EqualTo(rotation[c][r]).Within(1e-9), $"rot[{c}][{r}]");
        }

        [Test]
        public void ChangeBasisUnityFromOpenCV_AppliedTwice_ReturnsToOpenCV()
        {
            var translation = new double3(1, 2, 3);
            var rotation = double3x3.identity;

            var (t1, r1) = LocationUtilities.ChangeBasisUnityFromOpenCV(translation, rotation);
            var (t2, r2) = LocationUtilities.ChangeBasisOpenCVFromUnity(t1, r1);

            Assert.That(t2.x, Is.EqualTo(translation.x).Within(1e-9));
            Assert.That(t2.y, Is.EqualTo(translation.y).Within(1e-9));
            Assert.That(t2.z, Is.EqualTo(translation.z).Within(1e-9));
        }

        [Test]
        public void UnityFromEcef_AndEcefFromUnity_RoundTrip()
        {
            // Use identity alignment: ECEF basis-changed to Unity is the same as Unity itself.
            var alignmentUnityFromEcef = double4x4.identity;
            var alignmentEcefFromUnity = double4x4.identity;

            var ecefPosition = new double3(10, 20, 30);
            var ecefRotation = quaternion.AxisAngle(new float3(0, 1, 0), 0.5f);

            var (unityPosition, unityRotation) = LocationUtilities.UnityFromEcef(
                alignmentUnityFromEcef,
                ecefPosition,
                ecefRotation
            );
            var (ecefPositionBack, _) = LocationUtilities.EcefFromUnity(
                alignmentEcefFromUnity,
                unityPosition,
                unityRotation
            );

            Assert.That(ecefPositionBack.x, Is.EqualTo(ecefPosition.x).Within(1e-7));
            Assert.That(ecefPositionBack.y, Is.EqualTo(ecefPosition.y).Within(1e-7));
            Assert.That(ecefPositionBack.z, Is.EqualTo(ecefPosition.z).Within(1e-7));
        }

        [Test]
        public void ChangeBasisUnityFromEcef_FlipsYSign()
        {
            // basisEcef = diag(1,-1,1), basisUnity = identity, so the change-of-basis flips Y.
            var translation = new double3(1, 2, 3);

            var (result, _) = LocationUtilities.ChangeBasisUnityFromEcef(translation, double3x3.identity);

            Assert.That(result.x, Is.EqualTo(1.0).Within(1e-12));
            Assert.That(result.y, Is.EqualTo(-2.0).Within(1e-12));
            Assert.That(result.z, Is.EqualTo(3.0).Within(1e-12));
        }
    }
}
