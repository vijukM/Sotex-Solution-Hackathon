using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Sotex_Hackathon.Infrastructure;

namespace Sotex_Hackathon.Controllers
{
    public class StationIdsRequest
    {
        public List<int> TsIds { get; set; } = new List<int>();
        public List<int> SsIds { get; set; } = new List<int>();
        public List<int> DtIds { get; set; } = new List<int>();

        // Novi flagovi koji osiguravaju strogu proveru
        public bool ShowTS { get; set; }
        public bool ShowSS { get; set; }
        public bool ShowDT { get; set; }
    }

    public class FeederLineDto
    {
        public int FeederId { get; set; }
        public string FeederName { get; set; }
        public string FeederType { get; set; }
        public int SourceStationId { get; set; }
        public string SourceStationName { get; set; }
        public double SourceLat { get; set; }
        public double SourceLon { get; set; }
        public int TargetStationId { get; set; }
        public string TargetStationName { get; set; }
        public double TargetLat { get; set; }
        public double TargetLon { get; set; }
    }

    [Route("api/[controller]")]
    [ApiController]
    public class FeedersController : ControllerBase
    {
        private readonly AppDbContext _context;

        public FeedersController(AppDbContext context)
        {
            _context = context;
        }

        [HttpPost("F33/by-stations")]
        public async Task<IActionResult> GetF33ByStations([FromBody] StationIdsRequest req)
        {
            var reqTsIds = req?.TsIds ?? new List<int>();
            var reqSsIds = req?.SsIds ?? new List<int>();
            var reqDtIds = req?.DtIds ?? new List<int>();

            var result = new List<FeederLineDto>();

            // Slucaj 1: Vod ide iz TS u SS (Oba moraju biti upaljena GUI-u)
            if (req.ShowTS && req.ShowSS)
            {
                var f33TsSs = await (from f in _context.Feeders33
                                     join ts in _context.TransmissionStations on f.TsId equals ts.Id
                                     join fss in _context.Feeder33Substation on f.Id equals fss.Feeders33Id
                                     join ss in _context.Substations on fss.SubstationsId equals ss.Id
                                     where reqTsIds.Contains(ts.Id) && reqSsIds.Contains(ss.Id) // Zamenjeno || sa &&
                                     select new FeederLineDto
                                     {
                                         FeederId = f.Id,
                                         FeederName = f.Name,
                                         FeederType = "F33",
                                         SourceStationId = ts.Id,
                                         SourceStationName = ts.Name,
                                         SourceLat = (double)(ts.Latitude ?? 0),
                                         SourceLon = (double)(ts.Longitude ?? 0),
                                         TargetStationId = ss.Id,
                                         TargetStationName = ss.Name,
                                         TargetLat = (double)(ss.Latitude ?? 0),
                                         TargetLon = (double)(ss.Longitude ?? 0)
                                     }).ToListAsync();

                result.AddRange(f33TsSs);
            }

            // Slucaj 2: Vod ide direktno iz TS u DT
            if (req.ShowTS && req.ShowDT)
            {
                var f33TsDt = await (from f in _context.Feeders33
                                     join ts in _context.TransmissionStations on f.TsId equals ts.Id
                                     join dt in _context.DistributionSubstations on f.Id equals dt.Feeder33Id
                                     where reqTsIds.Contains(ts.Id) && reqDtIds.Contains(dt.Id) // Zamenjeno || sa &&
                                     select new FeederLineDto
                                     {
                                         FeederId = f.Id,
                                         FeederName = f.Name,
                                         FeederType = "F33",
                                         SourceStationId = ts.Id,
                                         SourceStationName = ts.Name,
                                         SourceLat = (double)(ts.Latitude ?? 0),
                                         SourceLon = (double)(ts.Longitude ?? 0),
                                         TargetStationId = dt.Id,
                                         TargetStationName = dt.Name,
                                         TargetLat = (double)(dt.Latitude ?? 0),
                                         TargetLon = (double)(dt.Longitude ?? 0)
                                     }).ToListAsync();

                result.AddRange(f33TsDt);
            }

            return Ok(result);
        }

        [HttpPost("F11/by-stations")]
        public async Task<IActionResult> GetF11ByStations([FromBody] StationIdsRequest req)
        {
            var reqTsIds = req?.TsIds ?? new List<int>();
            var reqSsIds = req?.SsIds ?? new List<int>();
            var reqDtIds = req?.DtIds ?? new List<int>();

            var result = new List<FeederLineDto>();

            // Slucaj 1: 11kV vod ide iz SS u DT
            if (req.ShowSS && req.ShowDT)
            {
                var f11SsDt = await (from f in _context.Feeders11
                                     join ss in _context.Substations on f.SsId equals ss.Id
                                     join dt in _context.DistributionSubstations on f.Id equals dt.Feeder11Id
                                     where reqSsIds.Contains(ss.Id) && reqDtIds.Contains(dt.Id) // Zamenjeno || sa &&
                                     select new FeederLineDto
                                     {
                                         FeederId = f.Id,
                                         FeederName = f.Name,
                                         FeederType = "F11",
                                         SourceStationId = ss.Id,
                                         SourceStationName = ss.Name,
                                         SourceLat = (double)(ss.Latitude ?? 0),
                                         SourceLon = (double)(ss.Longitude ?? 0),
                                         TargetStationId = dt.Id,
                                         TargetStationName = dt.Name,
                                         TargetLat = (double)(dt.Latitude ?? 0),
                                         TargetLon = (double)(dt.Longitude ?? 0)
                                     }).ToListAsync();

                result.AddRange(f11SsDt);
            }

            // Slucaj 2: 11kV vod ide iz TS u DT
            if (req.ShowTS && req.ShowDT)
            {
                var f11TsDt = await (from f in _context.Feeders11
                                     join ts in _context.TransmissionStations on f.TsId equals ts.Id
                                     join dt in _context.DistributionSubstations on f.Id equals dt.Feeder11Id
                                     where reqTsIds.Contains(ts.Id) && reqDtIds.Contains(dt.Id) // Zamenjeno || sa &&
                                     select new FeederLineDto
                                     {
                                         FeederId = f.Id,
                                         FeederName = f.Name,
                                         FeederType = "F11",
                                         SourceStationId = ts.Id,
                                         SourceStationName = ts.Name,
                                         SourceLat = (double)(ts.Latitude ?? 0),
                                         SourceLon = (double)(ts.Longitude ?? 0),
                                         TargetStationId = dt.Id,
                                         TargetStationName = dt.Name,
                                         TargetLat = (double)(dt.Latitude ?? 0),
                                         TargetLon = (double)(dt.Longitude ?? 0)
                                     }).ToListAsync();

                result.AddRange(f11TsDt);
            }

            return Ok(result);
        }
    }
}