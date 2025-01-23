// src/app/log.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LogService {
  private apiUrl = 'http://localhost:5000/logs';  // Flask API URL

  constructor(private http: HttpClient) {}

  // Get all logs
  getLogs(): Observable<any> {
    return this.http.get<any>(this.apiUrl);
  }

  // Get a specific log by ID
  getLog(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${id}`);
  }

  // Create a new log
  createLog(log: any): Observable<any> {
    return this.http.post<any>(this.apiUrl, log);
  }

  // Update an existing log
  updateLog(id: number, log: any): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/${id}`, log);
  }

  // Delete a log
  deleteLog(id: number): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/${id}`);
  }
}
