using System.Collections.Generic;
using System.Threading.Tasks;

namespace Sotex_Hackathon.Domain
{
    public interface IRepository<T> where T : class, IEntity
    {
        Task<IEnumerable<T>> GetAllAsync(int pageNumber = 1, int pageSize = 100);
        Task<T> GetByIdAsync(int id);
        Task<T> AddAsync(T entity);
        Task UpdateAsync(T entity);
        Task DeleteAsync(int id);
    }
}
