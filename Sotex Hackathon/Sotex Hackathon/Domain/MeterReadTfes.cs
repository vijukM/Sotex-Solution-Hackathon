using System;
using System.ComponentModel.DataAnnotations.Schema;

namespace Sotex_Hackathon.Domain
{
    [Table("MeterReadTfes")]
    public class MeterReadTfes : IEntity
    {
        public int Id { get; set; }
        public int? Mid { get; set; }
        public decimal? Val { get; set; }
        public DateTime? Ts { get; set; }
    }
}
