import { Component, inject } from '@angular/core';
import { SpeechRecognitionService } from '../../core/services/speech-recognition.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { firstValueFrom, Subject, Subscription, switchMap, tap } from 'rxjs';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { InterviewBetterApiService } from '../../core/services/interview-better-api.service';
import { StartInterviewModel } from '../../core/models/start-inteview.model';

@Component({
  selector: 'app-chat',
  imports: [CommonModule, FormsModule, HttpClientModule],
  providers: [SpeechRecognitionService, InterviewBetterApiService],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss'
})
export class ChatComponent {
  fullTranscript = '';
  lastSentTranscript = '';
  isListening = false;
  private sessionId?: string; 

  private transcriptSub!: Subscription;
  private audioSub!: Subscription;

  private speechService = inject(SpeechRecognitionService)
  private interviewBetterService = inject(InterviewBetterApiService)

  private start$ = new Subject<void>();
  private nextQuestion$ = new Subject<void>();
  private stop$ = new Subject<void>();
  private sendDataInProgress: Promise<void> = Promise.resolve();
  private sendDataPromises: Promise<any>[] = [];


  question?: string
  introduction?: string
  follow_up?: string
  grade?: number
  explanation?: string

  ngOnInit(): void {
    this.transcriptSub = this.speechService.getTranscript().subscribe({
      next: text => (this.fullTranscript = text),
      error: err => {
        console.log(err)
        console.error('Speech recognition error:', err)},
    });

    let start = performance.now();

    this.audioSub = this.speechService.getAudio().subscribe(blob => {
      if (this.sessionId && this.fullTranscript.trim()) {
        let end = performance.now();

        console.log(`Czas wykonania: ${end - start} ms`);        
        start = end
        this.sendToBackend(blob);
      }
    });
    

    this.start$.pipe(
      switchMap(() => this.interviewBetterService.startSession()),
      tap(res => this.sessionId = res.session_id),
      switchMap(res => this.interviewBetterService.startInterview(res.session_id, 'llm'))
    ).subscribe(interview => {
      this.assistantSpeak(interview)
    });

    this.nextQuestion$.pipe(
      switchMap(() => this.interviewBetterService.nextQuestion(this.sessionId as string))
    ).subscribe(interview => {
      this.assistantSpeak(interview)
    })
  }

  assistantSpeak(interview: StartInterviewModel) {
    this.introduction = interview.introduction;
    this.question = interview.question;
    this.speakAssistant(this.introduction);
    this.speakAssistant(this.question);
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

  startInterview(): void {
    this.start$.next();
  }

  sendToBackend(audio: Blob): void {
    const newTranscript = this.fullTranscript.replace(this.lastSentTranscript, '').trim();

    if (!newTranscript) {
      console.log('No new text to send');
      return;
    }

    console.log("sending to backend", newTranscript)
    const send$ = this.interviewBetterService
    .sendData(this.sessionId as string, newTranscript, audio)
    .pipe(tap(() => console.log('Transcript and audio sent')));

    this.lastSentTranscript = this.fullTranscript;
    this.sendDataInProgress = firstValueFrom(send$).then(() => {
      console.log('Status OK (2xx)');
    })
    this.sendDataInProgress.catch(() => {});

    console.log("adding sendAudio to array of promises")

  }

  gradeAnswer(): void {
    this.interviewBetterService
    .addMessage(this.sessionId as string).subscribe({
      next: (grade) => {
        if (grade.explanation_of_grade === "DONE" && grade.follow_up_question === "DONE") {
          this.nextQuestion$.next()
          return; 
        }
        this.follow_up = grade.follow_up_question
        this.grade = grade.grade
        this.explanation = grade.explanation_of_grade
        this.speakAssistant(grade.follow_up_question)
        console.log("graded answer", grade) 
      },
      error: err => console.error('Failed to send data', err)
    })
  }

  speakAssistant(message: string): void {
    const msg = new SpeechSynthesisUtterance(message);
    msg.lang = 'en-US';
    speechSynthesis.speak(msg);
  }

  async toggleListening() {
    if (this.isListening) {
      this.speechService.stop();
      this.isListening = false

      this.sendDataInProgress.then(() => {
        console.log("grading answer")
        this.gradeAnswer()
      })
      // })
      // try {
      //   Promise.all(this.sendDataPromises);

      // } finally {
      //   this.sendDataPromises = [];
      // }
    } else {
      this.speechService.start();
      this.speechService.startRecording();
      this.isListening = true;
    }
  }

  ngOnDestroy(): void {
    this.transcriptSub.unsubscribe();
    this.audioSub?.unsubscribe();
    this.speechService.stop();
  }
}
