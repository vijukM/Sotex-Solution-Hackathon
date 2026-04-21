using System.ComponentModel.DataAnnotations.Schema;

namespace Sotex_Hackathon.Domain
{
    [Table("Feeders33")]
    public class Feeders33 : IEntity
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public int? TsId { get; set; }
        public int? MeterId { get; set; }
        public int? NameplateRating { get; set; }
    }
}
