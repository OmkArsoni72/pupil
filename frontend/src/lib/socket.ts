import { io, Socket } from 'socket.io-client';

const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:8080';

class SocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(token: string): void {
    if (this.socket?.connected) {
      return;
    }

    this.socket = io(SOCKET_URL, {
      auth: {
        token,
      },
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: this.maxReconnectAttempts,
    });

    this.socket.on('connect', () => {
      console.log('Socket connected');
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', () => {
      console.log('Socket disconnected');
    });

    this.socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
      this.reconnectAttempts++;
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
        this.disconnect();
      }
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  // Join a class room
  joinClass(classId: string): void {
    if (this.socket) {
      this.socket.emit('join_class', { class_id: classId });
    }
  }

  // Leave a class room
  leaveClass(classId: string): void {
    if (this.socket) {
      this.socket.emit('leave_class', { class_id: classId });
    }
  }

  // Listen to question pushed event
  onQuestionPushed(callback: (data: any) => void): void {
    if (this.socket) {
      this.socket.on('question_pushed', callback);
    }
  }

  // Listen to student answered event
  onStudentAnswered(callback: (data: any) => void): void {
    if (this.socket) {
      this.socket.on('student_answered', callback);
    }
  }

  // Listen to session started event
  onSessionStarted(callback: (data: any) => void): void {
    if (this.socket) {
      this.socket.on('session_started', callback);
    }
  }

  // Listen to session ended event
  onSessionEnded(callback: (data: any) => void): void {
    if (this.socket) {
      this.socket.on('session_ended', callback);
    }
  }

  // Listen to job progress updates
  onJobProgress(callback: (data: any) => void): void {
    if (this.socket) {
      this.socket.on('job_progress', callback);
    }
  }

  // Push a question to students
  pushQuestion(sessionId: string, questionId: string): void {
    if (this.socket) {
      this.socket.emit('push_question', {
        session_id: sessionId,
        question_id: questionId,
      });
    }
  }

  // Submit an answer
  submitAnswer(sessionId: string, questionId: string, answer: any): void {
    if (this.socket) {
      this.socket.emit('submit_answer', {
        session_id: sessionId,
        question_id: questionId,
        answer,
      });
    }
  }

  // Generic event listener
  on(event: string, callback: (data: any) => void): void {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  // Generic event emitter
  emit(event: string, data: any): void {
    if (this.socket) {
      this.socket.emit(event, data);
    }
  }

  // Remove event listener
  off(event: string, callback?: (data: any) => void): void {
    if (this.socket) {
      if (callback) {
        this.socket.off(event, callback);
      } else {
        this.socket.off(event);
      }
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const socketService = new SocketService();
export default socketService;
