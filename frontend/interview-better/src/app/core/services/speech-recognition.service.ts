import { HttpClient, HttpClientModule } from '@angular/common/http';
import { inject, Injectable, NgZone } from '@angular/core';
import { Observable, Subject } from 'rxjs';

interface IWindow extends Window {
  webkitSpeechRecognition: any;
}

@Injectable({
  providedIn: 'root',
})
export class SpeechRecognitionService {
  private recognition?: SpeechRecognition;
  private transcriptSubject = new Subject<string>();
  private audioSubject = new Subject<Blob>();
  private listening = false;
  private intervalId?: number;
  private mediaRecorder?: MediaRecorder;
  private audioChunks: Blob[] = [];

  private ngZone = inject(NgZone)
  

  private initRecognition(): boolean {
    if (typeof window === 'undefined') {
      console.warn('SpeechRecognition: Not running in browser environment.');
      return false;
    }

    if (!this.recognition) {
      const SpeechRecognition =
        (window as any).SpeechRecognition ||
        (window as any).webkitSpeechRecognition;

      if (!SpeechRecognition) {
        console.error('SpeechRecognition is not supported in this browser.');
        return false;
      }

      this.recognition = new SpeechRecognition();
      if (this.recognition != null) {
        this.recognition.lang = 'en-US';
        this.recognition.continuous = true;
        this.recognition.interimResults = true;

        this.recognition.onresult = (event: SpeechRecognitionEvent) => {
          const transcript = Array.from(event.results)
            .map((result) => result[0].transcript)
            .join('');

          this.ngZone.run(() => {
            this.transcriptSubject.next(transcript);
          });
        };

        this.recognition.onerror = (event: any) => {
          this.ngZone.run(() => {
            this.transcriptSubject.error(event.error);
          });
        };

        this.recognition.onend = () => {
          this.ngZone.run(() => {
            this.listening = false;
          });
        };
      }
    }
    return true;
  }

  async startRecording(): Promise<void> {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.mediaRecorder = new MediaRecorder(stream);
    this.audioChunks = [];

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        this.audioChunks.push(event.data);
      }
    };

    this.mediaRecorder.onstop = () => {
      console.log("media recorder on stop")
      const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
      this.audioChunks = [];
      this.ngZone.run(() => this.audioSubject.next(audioBlob));
    };

    this.mediaRecorder.start();

    this.intervalId = window.setInterval(() => {
      if (this.mediaRecorder?.state === 'recording') {
        this.mediaRecorder.stop();
        this.mediaRecorder.start();
      }
    }, 10_000);
  }

  start(): void {
    if (this.initRecognition() && !this.listening) {
      this.recognition!.start();
      this.listening = true;
    }
  }

  stop(): void {
    if (this.recognition && this.listening) {
      this.recognition.stop();
      this.mediaRecorder?.stop();
      this.listening = false;
    }

    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = undefined;
    }
  }

  getTranscript(): Observable<string> {
    return this.transcriptSubject.asObservable();
  }

  getAudio(): Observable<Blob> {
    return this.audioSubject.asObservable();
  }

  isListening(): boolean {
    return this.listening;
  }
}