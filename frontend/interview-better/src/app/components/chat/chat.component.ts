import { Component, inject } from '@angular/core';
import { SpeechRecognitionService } from '../../core/services/speech-recognition.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { InterviewBetterApiService } from '../../core/services/interview-better-api.service';

@Component({
  selector: 'app-chat',
  imports: [CommonModule, FormsModule, HttpClientModule],
  providers: [SpeechRecognitionService, InterviewBetterApiService],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss'
})
export class ChatComponent {
  transcript = '';
  isListening = false;
  private sessionId?: string; 

  private transcriptSub!: Subscription;
  private audioSub!: Subscription;

  private speechService = inject(SpeechRecognitionService)
  private interviewBetterService = inject(InterviewBetterApiService)

  ngOnInit(): void {
    this.transcriptSub = this.speechService.getTranscript().subscribe({
      next: text => (this.transcript = text),
      error: err => {
        console.log(err)
        console.error('Speech recognition error:', err)},
    });

    let start = performance.now();

    this.audioSub = this.speechService.getAudio().subscribe(blob => {
      if (this.sessionId && this.transcript.trim()) {
        let end = performance.now();

        console.log(`Czas wykonania: ${end - start} ms`);        
        start = end
        this.sendToBackend(this.transcript, blob);
        this.transcript = '';
      }
    });
  }

  startSession(): void {
    this.interviewBetterService.startSession().subscribe({
      next: res => {
        this.sessionId = res.session_id;
        this.speechService.start();
        this.speechService.startRecording();
        this.isListening = true;
      },
      error: err => console.error('Failed to start session', err)
    });
  }

  sendToBackend(transcript: string, audio: Blob): void {
    this.interviewBetterService
    .sendData(this.sessionId as string, transcript, audio).subscribe({
      next: () => console.log('Transcript and audio sent'),
      error: err => console.error('Failed to send data', err)
    });
  }

  toggleListening(): void {
    if (this.isListening) {
      this.speechService.stop();
      this.isListening = false
    } else {
      this.startSession();
    }
  }

  ngOnDestroy(): void {
    this.transcriptSub.unsubscribe();
    this.audioSub?.unsubscribe();
    this.speechService.stop();
  }
}
