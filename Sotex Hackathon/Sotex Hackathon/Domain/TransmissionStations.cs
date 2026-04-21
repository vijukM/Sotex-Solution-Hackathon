using System.ComponentModel.DataAnnotations.Schema;

namespace Sotex_Hackathon.Domain
{
    [Table("TransmissionStations")]
    public class TransmissionStations : IEntity
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public decimal? Latitude { get; set; }
        public decimal? Longitude { get; set; }
    }
}
