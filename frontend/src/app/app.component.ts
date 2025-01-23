import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LogService } from './log.service';

@Component({
  selector: 'app-root',
  imports: [ReactiveFormsModule, CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent implements OnInit {
  users: any[] = [];
  userForm: FormGroup;
  isEdit = false;
  selectedUserId: number | null = null;
  logs: any[] = [];
  newLog = { rfid: '', name: '', message: '' };
  selectedLog: any = null;

  constructor(
    private http: HttpClient,
    private fb: FormBuilder,
    private logService: LogService
  ) {
    this.userForm = this.fb.group({
      name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      rfid: ['', Validators.required],
    });
  }

  ngOnInit() {
    this.loadUsers();
    this.loadLogs();
  }

  loadLogs(): void {
    this.logService.getLogs().subscribe((data) => {
      this.logs = data;
      console.log('Logs:', this.logs);
    });
  }

  createLog(): void {
    this.logService.createLog(this.newLog).subscribe(() => {
      this.loadLogs();
      this.newLog = { rfid: '', name: '', message: '' }; // Clear form
    });
  }

  selectLog(log: any): void {
    this.selectedLog = { ...log }; // Copy selected log to edit
  }

  updateLog(): void {
    if (this.selectedLog) {
      this.logService
        .updateLog(this.selectedLog.id, this.selectedLog)
        .subscribe(() => {
          this.loadLogs();
          this.selectedLog = null; // Clear selection
        });
    }
  }

  deleteLog(id: number): void {
    this.logService.deleteLog(id).subscribe(() => {
      this.loadLogs();
    });
  }

  loadUsers() {
    this.http.get<any[]>('http://localhost:5000/users').subscribe(
      (data) => (this.users = data),
      (error) => console.error('Error fetching users', error)
    );
  }

  onSubmit() {
    const userData = this.userForm.value;

    if (this.isEdit && this.selectedUserId !== null) {
      // Update user
      this.http.put(`/users/${this.selectedUserId}`, userData).subscribe(
        () => {
          this.loadUsers();
          this.resetForm();
        },
        (error) => console.error('Error updating user', error)
      );
    } else {
      // Create user
      this.http.post('/users', userData).subscribe(
        () => {
          this.loadUsers();
          this.resetForm();
        },
        (error) => console.error('Error creating user', error)
      );
    }
  }

  editUser(user: any) {
    this.isEdit = true;
    this.selectedUserId = user.id;
    this.userForm.setValue({
      name: user.name,
      email: user.email,
      rfid: user.rfid,
    });
  }

  resetForm() {
    this.isEdit = false;
    this.selectedUserId = null;
    this.userForm.reset();
  }
}
