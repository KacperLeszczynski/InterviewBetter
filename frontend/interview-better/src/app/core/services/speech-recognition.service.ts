import { Injectable, NgZone } from '@angular/core';
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
  private listening = false;

  constructor(private ngZone: NgZone) {}

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

  start(): void {
    if (this.initRecognition() && !this.listening) {
      this.recognition!.start();
      this.listening = true;
    }
  }

  stop(): void {
    if (this.recognition && this.listening) {
      this.recognition.stop();
      this.listening = false;
    }
  }

  getTranscript(): Observable<string> {
    return this.transcriptSubject.asObservable();
  }

  isListening(): boolean {
    return this.listening;
  }
}