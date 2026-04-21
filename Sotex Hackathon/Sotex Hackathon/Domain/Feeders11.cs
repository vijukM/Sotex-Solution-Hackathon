using System.ComponentModel.DataAnnotations.Schema;

namespace Sotex_Hackathon.Domain
{
    [Table("Feeders11")]
    public class Feeders11 : IEntity
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public int? SsId { get; set; }
        public int? MeterId { get; set; }
        public int? Feeder33Id { get; set; }
        public int? NameplateRating { get; set; }
        public int? TsId { get; set; }
    }
}
