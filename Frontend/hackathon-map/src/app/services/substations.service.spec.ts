import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { SubstationsService } from './substations.service';

describe('SubstationsService', () => {
  let service: SubstationsService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(SubstationsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});