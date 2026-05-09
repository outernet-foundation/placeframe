using NUnit.Framework;
using Unity.Mathematics;

namespace Placeframe.Core.Tests
{
    public class WGS84Tests
    {
        private const double EquatorialRadius = 6378137.0;

        [Test]
        public void CartographicToEcef_AtOriginPrimeMeridian_PutsPointOnEquatorialRadiusXAxis()
        {
            var coords = CartographicCoordinates.FromLongitudeLatitudeHeight(0, 0, 0);

            var ecef = WGS84.CartographicToEcef(coords);

            Assert.That(ecef.x, Is.EqualTo(EquatorialRadius).Within(1e-3));
            Assert.That(ecef.y, Is.EqualTo(0.0).Within(1e-6));
            Assert.That(ecef.z, Is.EqualTo(0.0).Within(1e-6));
        }

        [Test]
        public void CartographicToEcef_AtNorthPole_PutsPointOnPolarRadiusZAxis()
        {
            var coords = CartographicCoordinates.FromLongitudeLatitudeHeight(0, 90, 0);
            const double polarRadius = 6356752.314245;

            var ecef = WGS84.CartographicToEcef(coords);

            Assert.That(ecef.x, Is.EqualTo(0.0).Within(1e-3));
            Assert.That(ecef.y, Is.EqualTo(0.0).Within(1e-3));
            Assert.That(ecef.z, Is.EqualTo(polarRadius).Within(1e-3));
        }

        [Test]
        public void EcefToCartographic_RoundTripsThroughCartographicToEcef()
        {
            var input = CartographicCoordinates.FromLongitudeLatitudeHeight(-122.4194, 37.7749, 50.0);

            var ecef = WGS84.CartographicToEcef(input);
            var roundTrip = WGS84.EcefToCartographic(ecef);

            Assert.That(roundTrip.Longitude, Is.EqualTo(input.Longitude).Within(1e-9));
            Assert.That(roundTrip.Latitude, Is.EqualTo(input.Latitude).Within(1e-9));
            Assert.That(roundTrip.Height, Is.EqualTo(input.Height).Within(1e-3));
        }

        [Test]
        public void GeodeticSurfaceNormal_AtSurface_HasUnitLength()
        {
            var ecef = WGS84.CartographicToEcef(
                CartographicCoordinates.FromLongitudeLatitudeHeight(20, 40, 0)
            );

            var normal = WGS84.GeodeticSurfaceNormal(ecef);

            Assert.That(math.length(normal), Is.EqualTo(1.0).Within(1e-12));
        }

        [Test]
        public void GetEastNorthUpFrameInEcef_AtPrimeMeridianEquator_HasExpectedAxes()
        {
            var ecef = WGS84.CartographicToEcef(
                CartographicCoordinates.FromLongitudeLatitudeHeight(0, 0, 0)
            );

            var enu = WGS84.GetEastNorthUpFrameInEcef(ecef);
            // East at (lon=0, lat=0) points along +Y in ECEF; North along +Z; Up along +X.
            AssertAxis(enu.c0, new double3(0, 1, 0), "east");
            AssertAxis(enu.c1, new double3(0, 0, 1), "north");
            AssertAxis(enu.c2, new double3(1, 0, 0), "up");
        }

        private static void AssertAxis(double3 actual, double3 expected, string label)
        {
            Assert.That(actual.x, Is.EqualTo(expected.x).Within(1e-9), $"{label}.x");
            Assert.That(actual.y, Is.EqualTo(expected.y).Within(1e-9), $"{label}.y");
            Assert.That(actual.z, Is.EqualTo(expected.z).Within(1e-9), $"{label}.z");
        }
    }
}
