using System;
namespace Sotex_Hackathon.API
{
    public class StationDetailsDto
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public int ConnectedSsCount { get; set; }
        public int ConnectedDtCount { get; set; }
    }

    public class FeederLineWithLengthDto
    {
        public int FeederId { get; set; }
        public string FeederName { get; set; }
        public string FeederType { get; set; }
        public double AverageLengthKm { get; set; }
        public double SourceLat { get; set; }
        public double SourceLon { get; set; }
        public string TargetStationName { get; set; }
        public double TargetLat { get; set; }
        public double TargetLon { get; set; }
    }

    public static class GeoHelper
    {
        public static double CalculateDistance(double lat1, double lon1, double lat2, double lon2)
        {
            var R = 6371d;
            var dLat = (lat2 - lat1) * Math.PI / 180.0d;
            var dLon = (lon2 - lon1) * Math.PI / 180.0d;
            var a = Math.Sin(dLat / 2d) * Math.Sin(dLat / 2d) +
                    Math.Cos(lat1 * Math.PI / 180.0d) * Math.Cos(lat2 * Math.PI / 180.0d) *
                    Math.Sin(dLon / 2d) * Math.Sin(dLon / 2d);
            var c = 2d * Math.Atan2(Math.Sqrt(a), Math.Sqrt(1d - a));
            return R * c;
        }
    }
}
