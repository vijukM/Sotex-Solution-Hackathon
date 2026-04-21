using System.Collections.Generic;
using System.Threading.Tasks;
using Sotex_Hackathon.Domain;

namespace Sotex_Hackathon.Application
{
    public class GenericService<T> : IGenericService<T> where T : class, IEntity
    {
        private readonly IRepository<T> _repository;

        public GenericService(IRepository<T> repository)
        {
            _repository = repository;
        }

        public async Task<IEnumerable<T>> GetAllAsync(int pageNumber = 1, int pageSize = 100) => await _repository.GetAllAsync(pageNumber, pageSize);
        public async Task<T> GetByIdAsync(int id) => await _repository.GetByIdAsync(id);
        public async Task<T> AddAsync(T entity) => await _repository.AddAsync(entity);
        public async Task UpdateAsync(T entity) => await _repository.UpdateAsync(entity);
        public async Task DeleteAsync(int id) => await _repository.DeleteAsync(id);
    }
}
