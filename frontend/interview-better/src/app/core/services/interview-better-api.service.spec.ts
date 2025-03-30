import { TestBed } from '@angular/core/testing';

import { InterviewBetterApiService } from './interview-better-api.service';

describe('InterviewBetterApiService', () => {
  let service: InterviewBetterApiService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(InterviewBetterApiService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
