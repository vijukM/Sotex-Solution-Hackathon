using Microsoft.AspNetCore.Mvc;
using System.Threading.Tasks;
using Sotex_Hackathon.Domain;
using Sotex_Hackathon.Application;

namespace Sotex_Hackathon.API
{
    [Route("api/[controller]")]
    [ApiController]
    public class Feeders11Controller : ControllerBase
    {
        private readonly IGenericService<Feeders11> _service;

        public Feeders11Controller(IGenericService<Feeders11> service)
        {
            _service = service;
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
        public async Task<IActionResult> Create([FromBody] Feeders11 entity)
        {
            var created = await _service.AddAsync(entity);
            return CreatedAtAction(nameof(Get), new { id = created.Id }, created);
        }

        [HttpPut("{id}")]
        public async Task<IActionResult> Update(int id, [FromBody] Feeders11 entity)
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
    }
}
