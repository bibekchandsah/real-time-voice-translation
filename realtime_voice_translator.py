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
        self.setup_gemini()
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
        self.record_seconds = 5  # Process audio every 5 seconds
        
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
                'gemini_api_key': '',
                'source_language': 'auto',  # auto-detect
                'target_language': 'English',
                'audio_threshold': 500,  # Minimum audio level to process
                'translation_model': 'gpt-4o-audio-preview',
                'selected_audio_model': 'gpt-4o-audio-preview'
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
    
    def setup_gemini(self):
        """Initialize Gemini client"""
        try:
            import google.generativeai as genai
            api_key = self.config.get('gemini_api_key', '')
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
            else:
                self.gemini_client = None
        except ImportError:
            self.gemini_client = None
            print("Gemini not available. Install google-generativeai: pip install google-generativeai")
    
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
        
        # API Keys
        api_keys_frame = tk.Frame(config_frame, bg=self.colors['bg'])
        api_keys_frame.pack(fill=tk.X, padx=10, pady=(10, 10))
        
        # OpenAI API Key
        openai_frame = tk.Frame(api_keys_frame, bg=self.colors['bg'])
        openai_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(openai_frame, text="OpenAI API Key:", 
                fg=self.colors['text'], bg=self.colors['bg']).pack(anchor=tk.W)
        
        self.api_key_entry = tk.Entry(openai_frame, show="*", width=50)
        self.api_key_entry.pack(fill=tk.X, pady=(2, 0))
        self.api_key_entry.insert(0, self.config.get('openai_api_key', ''))
        
        # Gemini API Key
        gemini_frame = tk.Frame(api_keys_frame, bg=self.colors['bg'])
        gemini_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(gemini_frame, text="Gemini API Key (Optional):", 
                fg=self.colors['text'], bg=self.colors['bg']).pack(anchor=tk.W)
        
        self.gemini_key_entry = tk.Entry(gemini_frame, show="*", width=50)
        self.gemini_key_entry.pack(fill=tk.X, pady=(2, 0))
        self.gemini_key_entry.insert(0, self.config.get('gemini_api_key', ''))
        
        # Language and model settings
        settings_frame = tk.Frame(config_frame, bg=self.colors['bg'])
        settings_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Target language
        lang_frame = tk.Frame(settings_frame, bg=self.colors['bg'])
        lang_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(lang_frame, text="Target Language:", 
                fg=self.colors['text'], bg=self.colors['bg']).pack(side=tk.LEFT)
        
        self.target_lang_var = tk.StringVar(value=self.config.get('target_language', 'English'))
        target_lang_combo = ttk.Combobox(lang_frame, textvariable=self.target_lang_var,
                                       values=['English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese'],
                                       state='readonly', width=15)
        target_lang_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Audio model selection
        model_frame = tk.Frame(settings_frame, bg=self.colors['bg'])
        model_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(model_frame, text="Audio Model:", 
                fg=self.colors['text'], bg=self.colors['bg']).pack(side=tk.LEFT)
        
        # Find current model display name
        current_model = self.config.get('selected_audio_model', 'gpt-4o-audio-preview')
        self.audio_models = {
            'Whisper-1 (Transcribe + Translate)': 'whisper-1',
            'GPT-4o Audio Preview': 'gpt-4o-audio-preview',
            'OpenAI GPT-4o-transcribe': 'openai_gpt4o_transcribe',
            'OpenAI GPT-4o-mini-transcribe': 'openai_gpt4o_mini_transcribe',
            'Gemini 1.5 Flash (Audio)': 'gemini-1.5-flash',
            'Gemini 1.5 Pro (Audio)': 'gemini-1.5-pro',
            'Gemini 2.5 Flash': 'gemini_2_5_flash',
            'Gemini 2.5 Pro': 'gemini_2_5_pro',
        }
        
        # Find display name for current model
        current_display_name = 'GPT-4o Audio Preview'  # default
        for display_name, model_id in self.audio_models.items():
            if model_id == current_model:
                current_display_name = display_name
                break
        
        self.audio_model_var = tk.StringVar(value=current_display_name)
        
        audio_model_combo = ttk.Combobox(model_frame, textvariable=self.audio_model_var,
                                       values=list(self.audio_models.keys()),
                                       state='readonly', width=25)
        audio_model_combo.pack(side=tk.LEFT, padx=(10, 0))
        audio_model_combo.bind('<<ComboboxSelected>>', self.on_audio_model_change)
        
        # Save config button
        save_btn = tk.Button(config_frame, text="💾 Save Settings", 
                           command=self.save_settings,
                           bg=self.colors['accent'], fg='white',
                           font=('Arial', 9), relief='flat')
        save_btn.pack(pady=10)
        
        # Control buttons
        control_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.toggle_btn = tk.Button(control_frame, text="🎤 Start Translation", 
                                  command=self.toggle_translation,
                                  bg=self.colors['success'], fg='white',
                                  font=('Arial', 12, 'bold'), relief='flat',
                                  padx=30, pady=12)
        self.toggle_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        # Clear translations button
        self.clear_btn = tk.Button(control_frame, text="🗑️ Clear", 
                                 command=self.clear_translations,
                                 bg=self.colors['secondary'], fg=self.colors['text'],
                                 font=('Arial', 10), relief='flat',
                                 padx=15, pady=8)
        self.clear_btn.pack(side=tk.LEFT)
        
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
        self.config['gemini_api_key'] = self.gemini_key_entry.get()
        self.config['target_language'] = self.target_lang_var.get()
        
        # Save selected audio model
        selected_model_name = self.audio_model_var.get()
        if selected_model_name in self.audio_models:
            self.config['selected_audio_model'] = self.audio_models[selected_model_name]
        
        self.save_config()
        self.setup_openai()
        self.setup_gemini()
        messagebox.showinfo("Settings", "Settings saved successfully!")
    
    def on_audio_model_change(self, event=None):
        """Handle audio model selection change"""
        selected_model_name = self.audio_model_var.get()
        if selected_model_name in self.audio_models:
            self.config['selected_audio_model'] = self.audio_models[selected_model_name]
            self.save_config()
    
    def toggle_translation(self):
        """Toggle translation on/off"""
        if not self.is_recording:
            self.start_translation()
        else:
            self.stop_translation()
    
    def clear_translations(self):
        """Clear all translations from display"""
        self.translation_text.delete('1.0', tk.END)
    
    def start_translation(self):
        """Start real-time translation"""
        selected_model = self.config.get('selected_audio_model', 'gpt-4o-audio-preview')
        
        # Check if we have the required API key for the selected model
        if selected_model.startswith('gemini'):
            if not self.gemini_client:
                messagebox.showerror("Error", "Please configure your Gemini API key first!")
                return
        else:
            if not self.client:
                messagebox.showerror("Error", "Please configure your OpenAI API key first!")
                return
        
        self.is_recording = True
        self.is_translating = True
        
        # Update button appearance
        self.toggle_btn.config(
            text="⏹️ Stop Translation",
            bg=self.colors['error'],
            activebackground='#ff8a8a'
        )
        self.status_label.config(text="● Recording & Translating (5s intervals)", fg=self.colors['success'])
        
        # Start audio recording thread
        self.audio_thread = threading.Thread(target=self.record_audio_continuously, daemon=True)
        self.audio_thread.start()
    
    def stop_translation(self):
        """Stop real-time translation"""
        self.is_recording = False
        self.is_translating = False
        
        # Update button appearance
        self.toggle_btn.config(
            text="🎤 Start Translation",
            bg=self.colors['success'],
            activebackground='#45a049'
        )
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
        """Translate audio using selected AI model"""
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
            
            # Get selected model and target language
            selected_model = self.config.get('selected_audio_model', 'gpt-4o-audio-preview')
            target_lang = self.config.get('target_language', 'English')
            
            # Handle different model types
            if selected_model.startswith('gemini'):
                return self.translate_with_gemini(wav_data, target_lang, selected_model)
            elif selected_model == 'whisper-1':
                return self.translate_with_whisper(wav_data, target_lang)
            else:
                return self.translate_with_openai_audio(wav_data, target_lang, selected_model)
            
        except Exception as e:
            print(f"Translation error: {e}")
            return f"Translation error: {str(e)}"
    
    def translate_with_openai_audio(self, wav_data, target_lang, model):
        """Translate using OpenAI audio models"""
        try:
            # Encode to base64
            encoded_audio = base64.b64encode(wav_data).decode('utf-8')
            
            # Create prompt for translation
            prompt = f"Listen to this audio and translate any speech you hear to {target_lang}. If you detect Thai, Indonesian, or any other language, provide a clear translation. If there's no clear speech or just noise, respond with 'No speech detected'."
            
            # Call OpenAI API
            completion = self.client.chat.completions.create(
                model=model,
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
            if "does not exist" in str(e) or "model_not_found" in str(e):
                return f"Model '{model}' not available. Try GPT-4o Audio Preview or Whisper-1."
            raise e
    
    def translate_with_whisper(self, wav_data, target_lang):
        """Translate using Whisper transcription + GPT translation"""
        try:
            # Use Whisper for transcription
            transcription = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=("audio.wav", wav_data, "audio/wav")
            )
            
            if transcription.text.strip():
                # Translate the transcribed text
                translation_response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user", 
                            "content": f"Translate this text to {target_lang}. If it's already in {target_lang}, just return the original text: {transcription.text}"
                        }
                    ]
                )
                return translation_response.choices[0].message.content
            else:
                return None
                
        except Exception as e:
            raise e
    
    def translate_with_gemini(self, wav_data, target_lang, model):
        """Translate using Gemini models"""
        try:
            if not self.gemini_client:
                return "Gemini API key not configured"
            
            # First transcribe with Whisper (if available), then translate with Gemini
            if self.client:
                # Use Whisper for transcription
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=("audio.wav", wav_data, "audio/wav")
                )
                
                if transcription.text.strip():
                    # Translate with Gemini
                    prompt = f"Translate this text to {target_lang}. If it's already in {target_lang}, just return the original text: {transcription.text}"
                    response = self.gemini_client.generate_content(prompt)
                    return response.text
                else:
                    return None
            else:
                return "OpenAI API key needed for audio transcription with Gemini models"
                
        except Exception as e:
            if "API_KEY_INVALID" in str(e):
                return "Invalid Gemini API key. Please check your configuration."
            raise e
    
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