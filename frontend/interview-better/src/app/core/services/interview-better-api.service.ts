import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { StartSessionModel } from '../models/start-session.model';
import { StartInterviewModel } from '../models/start-inteview.model';
import { AddMessageModel } from '../models/add-message.model';
import { InterviewGradeModel } from '../models/interview-grade.model';

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

  startInterview(sessionId: string, questionType: string): Observable<StartInterviewModel> {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('question_type', questionType);

    return this.httpClient.post<StartInterviewModel>('/api/interview/start_interview', formData)
  }

  addMessage(sessionId: string): Observable<AddMessageModel> {
    const formData = new FormData();
    formData.append('session_id', sessionId);

    return this.httpClient.post<AddMessageModel>('/api/interview/add_message', formData)
  }

  nextQuestion(sessionId: string): Observable<StartInterviewModel> {
    const params = new HttpParams().set('session_id', sessionId);

    return this.httpClient.get<StartInterviewModel>(
      '/api/interview/next_question',
      { params }  
    );  
  }

  getFeedback(sessionId: string): Observable<InterviewGradeModel> {
    const params = new HttpParams().set('session_id', sessionId);

    return this.httpClient.get<InterviewGradeModel>(
      '/api/interview/feedback',
      { params }  
    );  
  }
}
