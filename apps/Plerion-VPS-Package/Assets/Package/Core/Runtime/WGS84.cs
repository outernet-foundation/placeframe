using Unity.Mathematics;

namespace Plerion.Core
{
    // Simple container for WGS84 cartographic coordinates, intended to make lat/long vs long/lat mistakes harder to make
    public readonly struct CartographicCoordinates
    {
        public readonly double Longitude;
        public readonly double Latitude;
        public readonly double Height;

        private CartographicCoordinates(double longitude, double latitude, double height)
        {
            Longitude = longitude;
            Latitude = latitude;
            Height = height;
        }

        public static CartographicCoordinates FromLongitudeLatitudeHeight(double longitudeDegrees, double latitudeDegrees, double height)
        {
            return new CartographicCoordinates(longitudeDegrees, latitudeDegrees, height);
        }

        public static CartographicCoordinates FromLatitudeLongitudeHeight(double latitudeDegrees, double longitudeDegrees, double height)
        {
            return new CartographicCoordinates(longitudeDegrees, latitudeDegrees, height);
        }
    }

    public static class WGS84
    {
        private const double EquatorialRadius = 6378137.0;
        private const double PolarRadius = 6356752.314245;

        private static readonly double EquatorialRadiusSquared = EquatorialRadius * EquatorialRadius;
        private static readonly double PolarRadiusSquared = PolarRadius * PolarRadius;

        private static readonly double FirstEccentricitySquared =
            (EquatorialRadiusSquared - PolarRadiusSquared) / EquatorialRadiusSquared;

        private static readonly double SecondEccentricitySquared =
            (EquatorialRadiusSquared - PolarRadiusSquared) / PolarRadiusSquared;

        // Gradient-based WGS84 geodetic surface normal.
        public static double3 GeodeticSurfaceNormal(double3 ecefPosition)
        {
            double xScaled = ecefPosition.x / EquatorialRadiusSquared;
            double yScaled = ecefPosition.y / EquatorialRadiusSquared;
            double zScaled = ecefPosition.z / PolarRadiusSquared;

            double lengthSquared = xScaled * xScaled + yScaled * yScaled + zScaled * zScaled;
            double inverseLength = 1.0 / math.sqrt(lengthSquared);

            double xNormalized = xScaled * inverseLength;
            double yNormalized = yScaled * inverseLength;
            double zNormalized = zScaled * inverseLength;

            return new double3(xNormalized, yNormalized, zNormalized);
        }

        // Local East-North-Up frame from WGS84 geodetic normal.
        public static double3x3 GetEastNorthUpFrameInEcef(double3 ecefPosition)
        {
            double3 upDirection = GeodeticSurfaceNormal(ecefPosition);

            double3 worldZAxis = new double3(0.0, 0.0, 1.0);
            double3 worldYAxis = new double3(0.0, 1.0, 0.0);

            double3 referenceAxis =
                math.abs(upDirection.z) < 0.99
                    ? worldZAxis
                    : worldYAxis;

            double3 eastDirection = math.normalize(math.cross(referenceAxis, upDirection));
            double3 northDirection = math.normalize(math.cross(upDirection, eastDirection));

            return new double3x3(eastDirection, northDirection, upDirection);
        }

        // Standard WGS84 cartographic (lon, lat, h) to ECEF.
        public static double3 CartographicToEcef(CartographicCoordinates cartographic)
        {
            double longitudeRadians = math.radians(cartographic.Longitude);
            double latitudeRadians = math.radians(cartographic.Latitude);

            double sinLatitude = math.sin(latitudeRadians);
            double cosLatitude = math.cos(latitudeRadians);
            double sinLongitude = math.sin(longitudeRadians);
            double cosLongitude = math.cos(longitudeRadians);

            double radiusOfCurvature =
                EquatorialRadius / math.sqrt(1.0 - FirstEccentricitySquared * sinLatitude * sinLatitude);

            double x = (radiusOfCurvature + cartographic.Height) * cosLatitude * cosLongitude;
            double y = (radiusOfCurvature + cartographic.Height) * cosLatitude * sinLongitude;
            double z = (radiusOfCurvature * (1.0 - FirstEccentricitySquared) + cartographic.Height) * sinLatitude;

            return new double3(x, y, z);
        }

        // Bowring-style WGS84 ECEF to cartographic container.
        public static CartographicCoordinates EcefToCartographic(double3 ecefPosition)
        {
            double x = ecefPosition.x;
            double y = ecefPosition.y;
            double z = ecefPosition.z;

            double horizontalDistance = math.sqrt(x * x + y * y);

            double longitudeRadians = math.atan2(y, x);

            double auxiliaryAngle =
                math.atan2(EquatorialRadius * z, PolarRadius * horizontalDistance);

            double sinAuxiliaryAngle = math.sin(auxiliaryAngle);
            double cosAuxiliaryAngle = math.cos(auxiliaryAngle);

            double latitudeNumerator =
                z + SecondEccentricitySquared * PolarRadius * sinAuxiliaryAngle * sinAuxiliaryAngle * sinAuxiliaryAngle;

            double latitudeDenominator =
                horizontalDistance -
                FirstEccentricitySquared * EquatorialRadius * cosAuxiliaryAngle * cosAuxiliaryAngle * cosAuxiliaryAngle;

            double latitudeRadians =
                math.atan2(latitudeNumerator, latitudeDenominator);

            double sinLatitude = math.sin(latitudeRadians);

            double radiusOfCurvature =
                EquatorialRadius / math.sqrt(1.0 - FirstEccentricitySquared * sinLatitude * sinLatitude);

            double height =
                horizontalDistance / math.cos(latitudeRadians) -
                radiusOfCurvature;

            double longitudeDegrees = math.degrees(longitudeRadians);
            double latitudeDegrees = math.degrees(latitudeRadians);

            return CartographicCoordinates.FromLongitudeLatitudeHeight(longitudeDegrees, latitudeDegrees, height);
        }
    }
}
