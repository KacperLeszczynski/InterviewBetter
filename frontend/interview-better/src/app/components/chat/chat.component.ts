import { Component, inject, OnDestroy, OnInit } from '@angular/core';
import { SpeechRecognitionService } from '../../core/services/speech-recognition.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription, Subject } from 'rxjs';
import { filter, concatMap, takeUntil, switchMap, tap } from 'rxjs/operators';
import { take } from 'rxjs/operators';
import { HttpClientModule } from '@angular/common/http';
import { InterviewBetterApiService } from '../../core/services/interview-better-api.service';
import { StartInterviewModel } from '../../core/models/start-inteview.model';
import { InterviewGradeModel } from '../../core/models/interview-grade.model';

@Component({
  selector: 'app-chat',
  imports: [CommonModule, FormsModule, HttpClientModule],
  providers: [SpeechRecognitionService, InterviewBetterApiService],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss'
})
export class ChatComponent implements OnInit, OnDestroy {
  fullTranscript = '';
  lastSentTranscript = '';
  isListening = false;
  private sessionId?: string;

  private transcriptSub!: Subscription;
  private audioSub?: Subscription;
  private stopAudio$ = new Subject<void>();

  private speechService = inject(SpeechRecognitionService);
  private interviewBetterService = inject(InterviewBetterApiService);

  private start$ = new Subject<void>();
  private nextQuestion$ = new Subject<void>();
  private finalizeInterview$ = new Subject<void>();

  question?: string;
  introduction?: string;
  follow_up?: string;
  grade?: number;
  explanation?: string;
  finalGrade?: InterviewGradeModel

  ngOnInit(): void {
    this.transcriptSub = this.speechService.getTranscript().subscribe({
      next: text => this.fullTranscript = text,
      error: err => console.error('Speech recognition error:', err),
    });

    this.start$.pipe(
      switchMap(() => this.interviewBetterService.startSession()),
      switchMap(res => {
        this.sessionId = res.session_id;
        return this.interviewBetterService.startInterview(res.session_id, 'llm');
      })
    ).subscribe(interview => this.assistantSpeak(interview));

    this.nextQuestion$.pipe(
      switchMap(() => this.interviewBetterService.nextQuestion(this.sessionId!))
    ).subscribe(interview => this.assistantSpeak(interview));

    this.finalizeInterview$.pipe(
      switchMap(() => this.interviewBetterService.getFeedback(this.sessionId!))
    ).subscribe(interviewGrade => this.showFeedback(interviewGrade));
  }

  startSession(): void {
    this.interviewBetterService.startSession().subscribe({
      next: res => {
        this.sessionId = res.session_id;
        this.startListening();
      },
      error: err => console.error('Failed to start session', err)
    });
  }

  startInterview(): void {
    this.start$.next();
  }

  private startListening(): void {
    this.speechService.start();
    this.speechService.startRecording();
    this.isListening = true;

    this.stopAudio$.next();
    this.audioSub = this.speechService.getAudio().pipe(
      takeUntil(this.stopAudio$),
      filter(() => {
        if (!this.sessionId) return false;
        const newText = this.fullTranscript.replace(this.lastSentTranscript, '').trim();
        return newText.length > 0;
      }),
      concatMap(blob => {
        const newTranscript = this.fullTranscript.replace(this.lastSentTranscript, '').trim();
        this.lastSentTranscript = this.fullTranscript;
        return this.interviewBetterService.sendData(this.sessionId!, newTranscript, blob).pipe(
          tap(() => console.log('Audio + transcript sent:', newTranscript))
        );
      })
    ).subscribe({
      next: () => {},
      error: err => console.error('Error sending audio:', err)
    });
  }

  gradeAnswer(): void {
    this.interviewBetterService.addMessage(this.sessionId!).subscribe({
      next: grade => {
        if (grade.explanation_of_grade === 'DONE' && grade.follow_up_question === 'DONE') {
          this.nextQuestion$.next();
          return;
        }

        if (grade.explanation_of_grade === 'FINISH' && grade.follow_up_question === 'FINISH') {
          this.finalizeInterview$.next();
          return;
        }
        this.follow_up = grade.follow_up_question;
        this.grade = grade.grade;
        this.explanation = grade.explanation_of_grade;
        this.speakAssistant(grade.follow_up_question);
        console.log('Graded answer:', grade);
      },
      error: err => console.error('Failed to send grade request', err)
    });
  }

  showFeedback(interviewGrade: InterviewGradeModel) {
    this.finalGrade = interviewGrade
  }

  assistantSpeak(interview: StartInterviewModel): void {
    this.introduction = interview.introduction;
    this.question = interview.question;
    this.speakAssistant(this.introduction);
    this.speakAssistant(this.question);
  }

  speakAssistant(message: string): void {
    const msg = new SpeechSynthesisUtterance(message);
    msg.lang = 'en-US';
    speechSynthesis.speak(msg);
  }

  toggleListening(): void {
    if (this.isListening) {
      this.speechService.stop();
      this.isListening = false;
      this.stopAudio$.next();

      this.speechService.getAudio().pipe(
        take(1),
        filter(() => !!this.sessionId && this.fullTranscript.trim().length > 0),
        switchMap(blob => {
          const newTranscript = this.fullTranscript.replace(this.lastSentTranscript, '').trim();
          this.lastSentTranscript = this.fullTranscript;
          return this.interviewBetterService.sendData(this.sessionId!, newTranscript, blob).pipe(
            tap(() => console.log('Final audio + transcript sent:', newTranscript))
          );
        })
      ).subscribe({
        next: () => {
          console.log('Final send done, now invoking gradeAnswer()');
          this.gradeAnswer();
        },
        error: err => console.error('Error sending final audio:', err)
      });
    } else {
      this.startListening();
    }
  }

  ngOnDestroy(): void {
    this.transcriptSub.unsubscribe();
    this.stopAudio$.next();
    this.audioSub?.unsubscribe();
    this.speechService.stop();
  }
}
