using System.ComponentModel.DataAnnotations.Schema;

namespace Sotex_Hackathon.Domain
{
    [Table("Meters")]
    public class Meters : IEntity
    {
        public int Id { get; set; }
        public string MSN { get; set; }
        public decimal? MultiplierFactor { get; set; }
    }
}
