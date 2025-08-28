import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
import json
import os
import pyaudio
import wave
import base64
import io
from openai import OpenAI
import numpy as np
from datetime import datetime

class RealtimeVoiceTranslator:
    def __init__(self):
        self.setup_config()
        self.setup_audio()
        self.setup_openai()
        self.setup_gui()
        
        # Threading
        self.audio_queue = queue.Queue()
        self.translation_queue = queue.Queue()
        self.is_recording = False
        self.is_translating = False
        
        # Audio settings
        self.chunk_size = 1024
        self.sample_rate = 16000
        self.channels = 1
        self.audio_format = pyaudio.paInt16
        self.record_seconds = 3  # Process audio every 3 seconds
        
        # Start background processing
        self.start_background_threads()
    
    def setup_config(self):
        """Load or create configuration"""
        try:
            with open('translator_config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                'openai_api_key': '',
                'source_language': 'auto',  # auto-detect
                'target_language': 'English',
                'audio_threshold': 500,  # Minimum audio level to process
                'translation_model': 'gpt-4o-audio-preview'
            }
            self.save_config()
    
    def save_config(self):
        """Save configuration"""
        with open('translator_config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def setup_audio(self):
        """Initialize audio system"""
        self.audio = pyaudio.PyAudio()
        
    def setup_openai(self):
        """Initialize OpenAI client"""
        api_key = self.config.get('openai_api_key', '')
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
    
    def setup_gui(self):
        """Setup the GUI"""
        self.root = tk.Tk()
        self.root.title("🌍 Real-time Voice Translator")
        self.root.geometry("600x700")
        
        # Colors
        self.colors = {
            'bg': '#1a1a1a',
            'secondary': '#2d2d2d', 
            'accent': '#4a9eff',
            'success': '#00d4aa',
            'error': '#ff6b6b',
            'text': '#ffffff',
            'text_secondary': '#b0b0b0'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(header_frame, text="🌍 Real-time Voice Translator", 
                              font=('Arial', 16, 'bold'),
                              fg=self.colors['text'], bg=self.colors['secondary'])
        title_label.pack(pady=15)
        
        # Status
        self.status_label = tk.Label(header_frame, text="● Ready", 
                                   font=('Arial', 10),
                                   fg=self.colors['success'], bg=self.colors['secondary'])
        self.status_label.pack(pady=(0, 15))
        
        # Configuration frame
        config_frame = tk.LabelFrame(main_frame, text="Configuration", 
                                   fg=self.colors['text'], bg=self.colors['bg'],
                                   font=('Arial', 10, 'bold'))
        config_frame.pack(fill=tk.X, pady=(0, 20))
        
        # API Key
        tk.Label(config_frame, text="OpenAI API Key:", 
                fg=self.colors['text'], bg=self.colors['bg']).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.api_key_entry = tk.Entry(config_frame, show="*", width=50)
        self.api_key_entry.pack(padx=10, pady=(0, 10))
        self.api_key_entry.insert(0, self.config.get('openai_api_key', ''))
        
        # Language settings
        lang_frame = tk.Frame(config_frame, bg=self.colors['bg'])
        lang_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(lang_frame, text="Target Language:", 
                fg=self.colors['text'], bg=self.colors['bg']).pack(side=tk.LEFT)
        
        self.target_lang_var = tk.StringVar(value=self.config.get('target_language', 'English'))
        target_lang_combo = ttk.Combobox(lang_frame, textvariable=self.target_lang_var,
                                       values=['English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese'],
                                       state='readonly', width=15)
        target_lang_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Save config button
        save_btn = tk.Button(config_frame, text="💾 Save Settings", 
                           command=self.save_settings,
                           bg=self.colors['accent'], fg='white',
                           font=('Arial', 9), relief='flat')
        save_btn.pack(pady=10)
        
        # Control buttons
        control_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.start_btn = tk.Button(control_frame, text="🎤 Start Translation", 
                                 command=self.start_translation,
                                 bg=self.colors['success'], fg='white',
                                 font=('Arial', 12, 'bold'), relief='flat',
                                 padx=20, pady=10)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = tk.Button(control_frame, text="⏹️ Stop", 
                                command=self.stop_translation,
                                bg=self.colors['error'], fg='white',
                                font=('Arial', 12, 'bold'), relief='flat',
                                padx=20, pady=10, state='disabled')
        self.stop_btn.pack(side=tk.LEFT)
        
        # Audio level indicator
        self.audio_level_var = tk.DoubleVar()
        audio_level_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        audio_level_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(audio_level_frame, text="Audio Level:", 
                fg=self.colors['text'], bg=self.colors['bg']).pack(side=tk.LEFT)
        
        self.audio_level_bar = ttk.Progressbar(audio_level_frame, variable=self.audio_level_var,
                                             maximum=100, length=200)
        self.audio_level_bar.pack(side=tk.LEFT, padx=(10, 0))
        
        # Translation display
        translation_frame = tk.LabelFrame(main_frame, text="Live Translation", 
                                        fg=self.colors['text'], bg=self.colors['bg'],
                                        font=('Arial', 12, 'bold'))
        translation_frame.pack(fill=tk.BOTH, expand=True)
        
        self.translation_text = scrolledtext.ScrolledText(
            translation_frame, 
            wrap=tk.WORD, 
            height=15,
            bg=self.colors['secondary'],
            fg=self.colors['text'],
            font=('Arial', 11),
            insertbackground=self.colors['text']
        )
        self.translation_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Always on top
        self.root.attributes('-topmost', True)
    
    def save_settings(self):
        """Save current settings"""
        self.config['openai_api_key'] = self.api_key_entry.get()
        self.config['target_language'] = self.target_lang_var.get()
        self.save_config()
        self.setup_openai()
        messagebox.showinfo("Settings", "Settings saved successfully!")
    
    def start_translation(self):
        """Start real-time translation"""
        if not self.client:
            messagebox.showerror("Error", "Please configure your OpenAI API key first!")
            return
        
        self.is_recording = True
        self.is_translating = True
        
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_label.config(text="● Recording & Translating", fg=self.colors['success'])
        
        # Start audio recording thread
        self.audio_thread = threading.Thread(target=self.record_audio_continuously, daemon=True)
        self.audio_thread.start()
    
    def stop_translation(self):
        """Stop real-time translation"""
        self.is_recording = False
        self.is_translating = False
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_label.config(text="● Stopped", fg=self.colors['error'])
        self.audio_level_var.set(0)
    
    def record_audio_continuously(self):
        """Continuously record and process audio"""
        try:
            stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            while self.is_recording:
                # Record for specified duration
                frames = []
                for _ in range(0, int(self.sample_rate / self.chunk_size * self.record_seconds)):
                    if not self.is_recording:
                        break
                    
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Update audio level indicator
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    audio_level = np.abs(audio_data).mean()
                    level_percent = min(100, (audio_level / 1000) * 100)
                    self.root.after(0, lambda: self.audio_level_var.set(level_percent))
                
                if frames and self.is_recording:
                    # Convert to audio data
                    audio_data = b''.join(frames)
                    
                    # Check if audio level is above threshold
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    if np.abs(audio_array).mean() > self.config.get('audio_threshold', 500):
                        # Add to processing queue
                        self.audio_queue.put(audio_data)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Audio Error", f"Error recording audio: {str(e)}"))
    
    def start_background_threads(self):
        """Start background processing threads"""
        # Audio processing thread
        self.processing_thread = threading.Thread(target=self.process_audio_queue, daemon=True)
        self.processing_thread.start()
        
        # Translation display thread
        self.display_thread = threading.Thread(target=self.update_translation_display, daemon=True)
        self.display_thread.start()
    
    def process_audio_queue(self):
        """Process audio from queue"""
        while True:
            try:
                if not self.audio_queue.empty() and self.is_translating:
                    audio_data = self.audio_queue.get()
                    
                    # Update status
                    self.root.after(0, lambda: self.status_label.config(text="● Processing...", fg=self.colors['accent']))
                    
                    # Process with OpenAI
                    translation = self.translate_audio(audio_data)
                    
                    if translation:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        self.translation_queue.put(f"[{timestamp}] {translation}")
                    
                    # Reset status
                    if self.is_translating:
                        self.root.after(0, lambda: self.status_label.config(text="● Recording & Translating", fg=self.colors['success']))
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing audio: {e}")
                time.sleep(1)
    
    def translate_audio(self, audio_data):
        """Translate audio using OpenAI"""
        try:
            # Convert audio to WAV format
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.audio.get_sample_size(self.audio_format))
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            wav_buffer.seek(0)
            wav_data = wav_buffer.read()
            
            # Encode to base64
            encoded_audio = base64.b64encode(wav_data).decode('utf-8')
            
            # Create prompt for translation
            target_lang = self.config.get('target_language', 'English')
            prompt = f"Listen to this audio and translate any speech you hear to {target_lang}. If you detect Thai, Indonesian, or any other language, provide a clear translation. If there's no clear speech or just noise, respond with 'No speech detected'."
            
            # Call OpenAI API
            completion = self.client.chat.completions.create(
                model=self.config.get('translation_model', 'gpt-4o-audio-preview'),
                modalities=["text"],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": encoded_audio,
                                    "format": "wav"
                                }
                            }
                        ]
                    }
                ]
            )
            
            response = completion.choices[0].message.content
            
            # Filter out "No speech detected" responses
            if "no speech detected" in response.lower() or "no clear speech" in response.lower():
                return None
                
            return response
            
        except Exception as e:
            print(f"Translation error: {e}")
            return f"Translation error: {str(e)}"
    
    def update_translation_display(self):
        """Update translation display"""
        while True:
            try:
                if not self.translation_queue.empty():
                    translation = self.translation_queue.get()
                    
                    # Update GUI in main thread
                    self.root.after(0, lambda t=translation: self.add_translation_to_display(t))
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Display update error: {e}")
                time.sleep(1)
    
    def add_translation_to_display(self, translation):
        """Add translation to display"""
        self.translation_text.insert(tk.END, translation + "\n\n")
        self.translation_text.see(tk.END)
        
        # Keep only last 50 translations to prevent memory issues
        lines = self.translation_text.get("1.0", tk.END).split("\n")
        if len(lines) > 100:  # 50 translations * 2 lines each
            # Remove oldest translations
            self.translation_text.delete("1.0", f"{len(lines)-100}.0")
    
    def run(self):
        """Run the application"""
        try:
            self.root.mainloop()
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        self.is_recording = False
        self.is_translating = False
        
        if hasattr(self, 'audio'):
            self.audio.terminate()

if __name__ == "__main__":
    app = RealtimeVoiceTranslator()
    app.run()