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
    public class SubstationsController : ControllerBase
    {
        private readonly IGenericService<Substations> _service;
        private readonly AppDbContext _context;

        public SubstationsController(IGenericService<Substations> service, AppDbContext context)
        {
            _service = service;
            _context = context;
        }

        [HttpGet("by-bounds")]
        public async Task<IActionResult> GetByBounds([FromQuery] decimal minLat, [FromQuery] decimal maxLat, [FromQuery] decimal minLon, [FromQuery] decimal maxLon)
        {
            var data = await _context.Substations
                .Where(s => s.Latitude >= minLat && s.Latitude <= maxLat && s.Longitude >= minLon && s.Longitude <= maxLon)
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
        public async Task<IActionResult> Create([FromBody] Substations entity)
        {
            var created = await _service.AddAsync(entity);
            return CreatedAtAction(nameof(Get), new { id = created.Id }, created);
        }

        [HttpPut("{id}")]
        public async Task<IActionResult> Update(int id, [FromBody] Substations entity)
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
        public async Task<IActionResult> GetSsDetails(int id)
        {
            var ss = await _context.Substations.FirstOrDefaultAsync(x => x.Id == id);
            if (ss == null) return NotFound();

            var dtCount = await (from dt in _context.DistributionSubstations
                                 join f in _context.Feeders11 on dt.Feeder11Id equals f.Id
                                 where f.SsId == id
                                 select dt).CountAsync();

            return Ok(new StationDetailsDto
            {
                Id = ss.Id,
                Name = ss.Name,
                ConnectedSsCount = 0,
                ConnectedDtCount = dtCount
            });
        }

        [HttpGet("{id}/feeders")]
        public async Task<IActionResult> GetSsFeeders(int id)
        {
            var ss = await _context.Substations.FindAsync(id);
            if (ss == null) return NotFound();

            var result = new System.Collections.Generic.List<FeederLineWithLengthDto>();

            var f11Dt = await (from f in _context.Feeders11
                               join dt in _context.DistributionSubstations on f.Id equals dt.Feeder11Id
                               where f.SsId == id
                               select new { f, dt }).ToListAsync();

            foreach (var item in f11Dt)
            {
                var dist = GeoHelper.CalculateDistance((double)ss.Latitude, (double)ss.Longitude, (double)item.dt.Latitude, (double)item.dt.Longitude);
                result.Add(new FeederLineWithLengthDto { FeederId = item.f.Id, FeederName = item.f.Name, FeederType = "F11", AverageLengthKm = dist, SourceLat = (double)ss.Latitude, SourceLon = (double)ss.Longitude, TargetLat = (double)item.dt.Latitude, TargetLon = (double)item.dt.Longitude });
            }

            return Ok(result);
        }
    }
}