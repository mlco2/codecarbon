import { TestBed } from '@angular/core/testing';

import { CarbonApiService } from './carbon-api.service';

describe('CarbonApiService', () => {
  let service: CarbonApiService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(CarbonApiService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
