import { Component, inject } from '@angular/core';
import { SpeechRecognitionService } from '../../core/services/speech-recognition.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-chat',
  imports: [CommonModule, FormsModule],
  providers: [SpeechRecognitionService],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss'
})
export class ChatComponent {
  transcript = '';
  isListening = false;

  private transcriptSub!: Subscription;

  constructor(private speechService: SpeechRecognitionService) {}

  ngOnInit(): void {
    this.transcriptSub = this.speechService.getTranscript().subscribe({
      next: text => (this.transcript = text),
      error: err => {
        console.log(err)
        console.error('Speech recognition error:', err)},
    });
  }

  toggleListening(): void {
    if (this.speechService.isListening()) {
      this.speechService.stop();
    } else {
      this.speechService.start();
    }
    this.isListening = this.speechService.isListening();
  }

  ngOnDestroy(): void {
    this.transcriptSub.unsubscribe();
    this.speechService.stop();
  }
}
