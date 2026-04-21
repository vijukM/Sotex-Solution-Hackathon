using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Linq;
using System.Threading.Tasks;
using Sotex_Hackathon.Domain;
using Sotex_Hackathon.Application;
using Sotex_Hackathon.Infrastructure;

namespace Sotex_Hackathon.API
{
    [Route("api/[controller]")]
    [ApiController]
    public class TransmissionStationsController : ControllerBase
    {
        private readonly IGenericService<TransmissionStations> _service;
        private readonly AppDbContext _context;

        public TransmissionStationsController(IGenericService<TransmissionStations> service, AppDbContext context)
        {
            _service = service;
            _context = context;
        }

        [HttpGet("by-bounds")]
        public async Task<IActionResult> GetByBounds([FromQuery] decimal minLat, [FromQuery] decimal maxLat, [FromQuery] decimal minLon, [FromQuery] decimal maxLon)
        {
            var data = await _context.TransmissionStations
                .Where(t => t.Latitude >= minLat && t.Latitude <= maxLat && t.Longitude >= minLon && t.Longitude <= maxLon)
                .ToListAsync();
            return Ok(data);
        }

        [HttpGet]
        public async Task<IActionResult> GetAll([FromQuery] int pageNumber = 1, [FromQuery] int pageSize = 100) => Ok(await _service.GetAllAsync(pageNumber, pageSize));

        [HttpGet("{id}")]
        public async Task<IActionResult> Get(int id)
        {
            var entity = await _service.GetByIdAsync(id);
            if (entity == null) return NotFound();
            return Ok(entity);
        }

        [HttpPost]
        public async Task<IActionResult> Create([FromBody] TransmissionStations entity)
        {
            var created = await _service.AddAsync(entity);
            return CreatedAtAction(nameof(Get), new { id = created.Id }, created);
        }

        [HttpPut("{id}")]
        public async Task<IActionResult> Update(int id, [FromBody] TransmissionStations entity)
        {
            if (id != entity.Id) return BadRequest();
            await _service.UpdateAsync(entity);
            return NoContent();
        }

        [HttpDelete("{id}")]
        public async Task<IActionResult> Delete(int id)
        {
            await _service.DeleteAsync(id);
            return NoContent();
        }

        [HttpGet("{id}/details")]
        public async Task<IActionResult> GetTsDetails(int id)
        {
            var ts = await _context.TransmissionStations.FirstOrDefaultAsync(x => x.Id == id);
            if (ts == null) return NotFound();

            var connectedSsCount = await (from f in _context.Feeders33
                                          join fss in _context.Feeder33Substation on f.Id equals fss.Feeders33Id
                                          where f.TsId == id
                                          select fss.SubstationsId).Distinct().CountAsync();

            var dtF33Count = await (from dt in _context.DistributionSubstations
                                    join f in _context.Feeders33 on dt.Feeder33Id equals f.Id
                                    where f.TsId == id
                                    select dt).CountAsync();
                
            var dtF11Count = await (from dt in _context.DistributionSubstations
                                    join f in _context.Feeders11 on dt.Feeder11Id equals f.Id
                                    where f.TsId == id
                                    select dt).CountAsync();

            return Ok(new StationDetailsDto
            {
                Id = ts.Id,
                Name = ts.Name,
                ConnectedSsCount = connectedSsCount,
                ConnectedDtCount = dtF33Count + dtF11Count
            });
        }

        [HttpGet("{id}/feeders")]
        public async Task<IActionResult> GetTsFeeders(int id, [FromQuery] bool showF33 = true, [FromQuery] bool showF11 = true)
        {
            var ts = await _context.TransmissionStations.FindAsync(id);
            if (ts == null) return NotFound();

            var result = new System.Collections.Generic.List<FeederLineWithLengthDto>();

            if (showF33)
            {
                // SS veze
                var f33Ss = await (from f in _context.Feeders33
                                   join fss in _context.Feeder33Substation on f.Id equals fss.Feeders33Id
                                   join ss in _context.Substations on fss.SubstationsId equals ss.Id
                                   where f.TsId == id
                                   select new { f, ss }).ToListAsync();
                                   
                foreach (var item in f33Ss)
                {
                    var dist = GeoHelper.CalculateDistance((double)ts.Latitude, (double)ts.Longitude, (double)item.ss.Latitude, (double)item.ss.Longitude);
                    result.Add(new FeederLineWithLengthDto { FeederId = item.f.Id, FeederName = item.f.Name, FeederType = "F33", AverageLengthKm = dist, SourceLat = (double)ts.Latitude, SourceLon = (double)ts.Longitude, TargetLat = (double)item.ss.Latitude, TargetLon = (double)item.ss.Longitude });
                }
                
                // DT veze
                var f33Dt = await (from f in _context.Feeders33
                                   join dt in _context.DistributionSubstations on f.Id equals dt.Feeder33Id
                                   where f.TsId == id
                                   select new { f, dt }).ToListAsync();
                                   
                foreach (var item in f33Dt)
                {
                    var dist = GeoHelper.CalculateDistance((double)ts.Latitude, (double)ts.Longitude, (double)item.dt.Latitude, (double)item.dt.Longitude);
                    result.Add(new FeederLineWithLengthDto { FeederId = item.f.Id, FeederName = item.f.Name, FeederType = "F33", AverageLengthKm = dist, SourceLat = (double)ts.Latitude, SourceLon = (double)ts.Longitude, TargetLat = (double)item.dt.Latitude, TargetLon = (double)item.dt.Longitude });
                }
            }

            if (showF11)
            {
                // DT veze direktno sa TS (ako F11 ima TsId)
                var f11Dt_direct = await (from f in _context.Feeders11
                                          join dt in _context.DistributionSubstations on f.Id equals dt.Feeder11Id
                                          where f.TsId == id
                                          select new { f, dt }).ToListAsync();
                                   
                foreach (var item in f11Dt_direct)
                {
                    var dist = GeoHelper.CalculateDistance((double)ts.Latitude, (double)ts.Longitude, (double)item.dt.Latitude, (double)item.dt.Longitude);
                    result.Add(new FeederLineWithLengthDto { FeederId = item.f.Id, FeederName = item.f.Name, FeederType = "F11 (Direktno)", AverageLengthKm = dist, SourceLat = (double)ts.Latitude, SourceLon = (double)ts.Longitude, TargetStationName = item.dt.Name, TargetLat = (double)item.dt.Latitude, TargetLon = (double)item.dt.Longitude });
                }

                // DT veze preko SS (F33 -> SS -> F11 -> DT)
                // Nalazimo prvo sve F11 vodove koji kreću iz SS stanica, a te SS stanice su vezane na ovu TS
                var f11Dt_indirect = await (from f33 in _context.Feeders33
                                            join fss in _context.Feeder33Substation on f33.Id equals fss.Feeders33Id
                                            join ss in _context.Substations on fss.SubstationsId equals ss.Id
                                            join f11 in _context.Feeders11 on ss.Id equals f11.SsId
                                            join dt in _context.DistributionSubstations on f11.Id equals dt.Feeder11Id
                                            where f33.TsId == id
                                            select new { f11, dt, ss }).ToListAsync();

                foreach (var item in f11Dt_indirect)
                {
                    // Udaljenost računamo od SS stanice sa koje kreće Feeder11 do DT stanice
                    var dist = GeoHelper.CalculateDistance((double)item.ss.Latitude, (double)item.ss.Longitude, (double)item.dt.Latitude, (double)item.dt.Longitude);
                    result.Add(new FeederLineWithLengthDto { FeederId = item.f11.Id, FeederName = item.f11.Name, FeederType = "F11 (Preko SS)", AverageLengthKm = dist, SourceLat = (double)item.ss.Latitude, SourceLon = (double)item.ss.Longitude, TargetStationName = item.dt.Name, TargetLat = (double)item.dt.Latitude, TargetLon = (double)item.dt.Longitude });
                }
            }

            return Ok(result);
        }
    }
}