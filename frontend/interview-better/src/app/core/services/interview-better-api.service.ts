import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { StartSessionModel } from '../models/start-session.model';

@Injectable({
  providedIn: 'root'
})
export class InterviewBetterApiService {
  private httpClient = inject(HttpClient)

  startSession(): Observable<StartSessionModel> {
    return this.httpClient.post<StartSessionModel>('/api/interview/start_session', {})
  }

  sendData(sessionId: string, transcript: string, audio: Blob): Observable<any> {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('transcript', transcript);
    formData.append('audio', audio, 'audio.webm');

    return this.httpClient.post('/api/interview/send_audio', formData)
  }
}
