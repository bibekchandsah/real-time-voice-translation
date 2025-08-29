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
        
        # Minimized window
        self.minimized_window = None
        self.is_minimized = False
        
        # Audio settings
        self.chunk_size = 1024
        self.sample_rate = 16000
        self.channels = 1
        self.audio_format = pyaudio.paInt16
        self.record_seconds = 5  # Process audio every 5 seconds
        
        # Start background processing
        self.start_background_threads()
        
        # Auto-open mini translator if enabled in config
        if self.config.get('enable_minimized', False):
            self.create_minimized_window()
    
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
                'selected_audio_model': 'gpt-4o-audio-preview',
                'enable_minimized': False,
                'always_on_top': True
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
    
    def get_language_flag_and_name(self, language_code):
        """Get country flag and language name from language code"""
        language_map = {
            'en': ('🇺🇸', 'English'),
            'es': ('🇪🇸', 'Spanish'),
            'fr': ('🇫🇷', 'French'),
            'de': ('🇩🇪', 'German'),
            'zh': ('🇨🇳', 'Chinese'),
            'ja': ('🇯🇵', 'Japanese'),
            'ko': ('🇰🇷', 'Korean'),
            'hi': ('🇮🇳', 'Hindi'),
            'th': ('🇹🇭', 'Thai'),
            'id': ('🇮🇩', 'Indonesian'),
            'vi': ('🇻🇳', 'Vietnamese'),
            'ar': ('🇸🇦', 'Arabic'),
            'ru': ('🇷🇺', 'Russian'),
            'pt': ('🇧🇷', 'Portuguese'),
            'it': ('🇮🇹', 'Italian'),
            'nl': ('🇳🇱', 'Dutch'),
            'pl': ('🇵🇱', 'Polish'),
            'tr': ('🇹🇷', 'Turkish'),
            'sv': ('🇸🇪', 'Swedish'),
            'da': ('🇩🇰', 'Danish'),
            'no': ('🇳🇴', 'Norwegian'),
            'fi': ('🇫🇮', 'Finnish'),
            'he': ('🇮🇱', 'Hebrew'),
            'cs': ('🇨🇿', 'Czech'),
            'hu': ('🇭🇺', 'Hungarian'),
            'ro': ('🇷🇴', 'Romanian'),
            'bg': ('🇧🇬', 'Bulgarian'),
            'hr': ('🇭🇷', 'Croatian'),
            'sk': ('🇸🇰', 'Slovak'),
            'sl': ('🇸🇮', 'Slovenian'),
            'et': ('🇪🇪', 'Estonian'),
            'lv': ('🇱🇻', 'Latvian'),
            'lt': ('🇱🇹', 'Lithuanian'),
            'uk': ('🇺🇦', 'Ukrainian'),
            'be': ('🇧🇾', 'Belarusian'),
            'mk': ('🇲🇰', 'Macedonian'),
            'sq': ('🇦🇱', 'Albanian'),
            'sr': ('🇷🇸', 'Serbian'),
            'bs': ('🇧🇦', 'Bosnian'),
            'me': ('🇲🇪', 'Montenegrin'),
            'is': ('🇮🇸', 'Icelandic'),
            'ga': ('🇮🇪', 'Irish'),
            'cy': ('🏴󠁧󠁢󠁷󠁬󠁳󠁿', 'Welsh'),
            'mt': ('🇲🇹', 'Maltese'),
            'eu': ('🏴󠁥󠁳󠁰󠁶󠁿', 'Basque'),
            'ca': ('🏴󠁥󠁳󠁣󠁴󠁿', 'Catalan'),
            'gl': ('🏴󠁥󠁳󠁧󠁡󠁿', 'Galician'),
        }
        
        # Try to match by language code
        if language_code.lower() in language_map:
            return language_map[language_code.lower()]
        
        # Try to match by language name
        for code, (flag, name) in language_map.items():
            if name.lower() == language_code.lower():
                return flag, name
        
        # Default fallback
        return '🌐', language_code.title()
    
    def detect_language_from_text(self, text):
        """Detect language from text using OpenAI"""
        try:
            if not self.client:
                return 'unknown', 0
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": f"Detect the language of this text and return only the language code (like 'en', 'es', 'th', 'id', etc.) and confidence percentage (0-100). Format: 'language_code,confidence'. Text: '{text}'"
                    }
                ]
            )
            
            result = response.choices[0].message.content.strip()
            if ',' in result:
                lang_code, confidence = result.split(',')
                return lang_code.strip(), int(confidence.strip().replace('%', ''))
            else:
                return result.strip(), 85  # Default confidence
                
        except Exception as e:
            print(f"Language detection error: {e}")
            return 'unknown', 0
    
    def setup_gui(self):
        """Setup the GUI"""
        self.root = tk.Tk()
        self.root.title("🌍 Real-time Voice Translator")
        self.root.geometry("680x870")
        
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
        
        # Two-column layout for Target Language and Audio Model
        two_column_frame = tk.Frame(settings_frame, bg=self.colors['bg'])
        two_column_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Left column - Target Language
        left_column = tk.Frame(two_column_frame, bg=self.colors['bg'])
        left_column.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(left_column, text="Target Language:", 
                fg=self.colors['text'], bg=self.colors['bg']).pack(side=tk.LEFT)
        
        self.target_lang_var = tk.StringVar(value=self.config.get('target_language', 'English'))
        target_lang_combo = ttk.Combobox(left_column, textvariable=self.target_lang_var,
                                       values=['English', 'Nepali', 'Hindi', 'Spanish', 'French', 'German', 'Chinese', 'Japanese'],
                                       state='readonly', width=15)
        target_lang_combo.pack(side=tk.LEFT, padx=(10, 20))
        
        # Right column - Audio Model
        right_column = tk.Frame(two_column_frame, bg=self.colors['bg'])
        right_column.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(right_column, text="Audio Model:", 
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
        
        audio_model_combo = ttk.Combobox(right_column, textvariable=self.audio_model_var,
                                       values=list(self.audio_models.keys()),
                                       state='readonly', width=25)
        audio_model_combo.pack(side=tk.LEFT, padx=(10, 0))
        audio_model_combo.bind('<<ComboboxSelected>>', self.on_audio_model_change)
        
        # Additional options checkboxes
        options_frame = tk.Frame(settings_frame, bg=self.colors['bg'])
        options_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Left side - Enable minimized translator
        self.minimized_var = tk.BooleanVar(value=self.config.get('enable_minimized', False))
        self.minimized_cb = tk.Checkbutton(
            options_frame,
            text="📱 Enable Minimized Translator",
            variable=self.minimized_var,
            command=self.toggle_minimized_mode,
            bg=self.colors['bg'],
            fg=self.colors['text'],
            selectcolor=self.colors['secondary'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['accent'],
            font=('Arial', 10),
            relief='flat'
        )
        self.minimized_cb.pack(side=tk.LEFT, anchor=tk.W)
        
        # Right side - Always on top toggle
        self.always_on_top_var = tk.BooleanVar(value=self.config.get('always_on_top', True))
        self.always_on_top_cb = tk.Checkbutton(
            options_frame,
            text="📌 Always on Top",
            variable=self.always_on_top_var,
            command=self.toggle_always_on_top,
            bg=self.colors['bg'],
            fg=self.colors['text'],
            selectcolor=self.colors['secondary'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['accent'],
            font=('Arial', 10),
            relief='flat'
        )
        self.always_on_top_cb.pack(side=tk.LEFT, anchor=tk.W, padx=(30, 0))
        
        # Save config button
        save_btn = tk.Button(config_frame, text="💾 Save Settings", 
                           command=self.save_settings,
                           bg=self.colors['accent'], fg='white',
                           font=('Arial', 9), relief='flat')
        save_btn.pack(pady=10)
        
        # Control buttons with audio level
        control_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Audio level indicator (moved to left side)
        self.audio_level_var = tk.DoubleVar()
        
        # Audio level label with info icon
        audio_label_frame = tk.Frame(control_frame, bg=self.colors['bg'])
        audio_label_frame.pack(side=tk.LEFT)
        
        tk.Label(audio_label_frame, text="Audio Level:", 
                fg=self.colors['text'], bg=self.colors['bg']).pack(side=tk.LEFT)
        
        # Info icon with tooltip
        info_label = tk.Label(audio_label_frame, text="ℹ️", 
                             fg=self.colors['accent'], bg=self.colors['bg'],
                             font=('Arial', 10), cursor='hand2')
        info_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Create tooltip for info icon
        self.create_tooltip(info_label, "If voice is not being detected:\n• Open Settings → System → Sound\n• Increase microphone volume\n• Check microphone permissions")
        
        self.audio_level_bar = ttk.Progressbar(control_frame, variable=self.audio_level_var,
                                             maximum=100, length=150)
        self.audio_level_bar.pack(side=tk.LEFT, padx=(10, 20))
        
        # Start/Stop translation button
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
        
        # Set always on top based on config
        always_on_top = self.config.get('always_on_top', True)
        self.root.attributes('-topmost', always_on_top)
        
        # Set up proper window close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_main_window_close)
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.configure(bg='#2d2d2d')
            
            # Make tooltip always on top if main window is always on top
            always_on_top = self.config.get('always_on_top', True)
            tooltip.attributes('-topmost', always_on_top)
            
            # Position tooltip near the widget
            x = widget.winfo_rootx() + 25
            y = widget.winfo_rooty() + 25
            tooltip.geometry(f"+{x}+{y}")
            
            label = tk.Label(tooltip, text=text, 
                           bg='#2d2d2d', fg='white',
                           font=('Arial', 9), 
                           justify=tk.LEFT,
                           padx=8, pady=6)
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def on_main_window_close(self):
        """Handle main window close event"""
        self.cleanup()
        self.root.destroy()
    
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
        if self.minimized_window and hasattr(self.minimized_window, 'translation_text'):
            self.minimized_window.translation_text.delete('1.0', tk.END)
    
    def toggle_minimized_mode(self):
        """Toggle minimized translator mode"""
        self.config['enable_minimized'] = self.minimized_var.get()
        self.save_config()
        
        if self.minimized_var.get():
            self.create_minimized_window()
        else:
            self.close_minimized_window()
    
    def toggle_always_on_top(self):
        """Toggle always on top mode"""
        self.config['always_on_top'] = self.always_on_top_var.get()
        self.save_config()
        
        # Apply to main window only
        self.root.attributes('-topmost', self.always_on_top_var.get())
        
        # Mini translator window should always stay on top (independent of main window setting)
        if self.minimized_window:
            self.minimized_window.attributes('-topmost', True)
    
    def create_minimized_window(self):
        """Create minimized translator window"""
        if self.minimized_window:
            return
        
        self.minimized_window = tk.Toplevel(self.root)
        self.minimized_window.title("🌍 Mini Translator")
        
        # Position at top-right corner
        screen_width = self.minimized_window.winfo_screenwidth()
        window_width = 400
        window_height = 300
        x_pos = screen_width - window_width - 20
        y_pos = 20
        
        self.minimized_window.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
        self.minimized_window.configure(bg=self.colors['bg'])
        self.minimized_window.attributes('-topmost', True)  # Mini translator always stays on top
        self.minimized_window.attributes('-alpha', 0.95)
        
        # Prevent window from being closed directly
        self.minimized_window.protocol("WM_DELETE_WINDOW", self.on_minimized_close)
        
        # Header
        header_frame = tk.Frame(self.minimized_window, bg=self.colors['secondary'])
        header_frame.pack(fill=tk.X, padx=2, pady=2)
        
        title_label = tk.Label(header_frame, text="🌍 Live Translation", 
                              font=('Arial', 10, 'bold'),
                              fg=self.colors['text'], bg=self.colors['secondary'])
        title_label.pack(side=tk.LEFT, padx=5, pady=3)
        
        # Close button
        close_btn = tk.Button(header_frame, text="✕", 
                             command=self.close_minimized_window,
                             bg=self.colors['error'], fg='white',
                             font=('Arial', 8, 'bold'), relief='flat',
                             padx=5, pady=1)
        close_btn.pack(side=tk.RIGHT, padx=2)
        
        # Translation display
        self.minimized_window.translation_text = scrolledtext.ScrolledText(
            self.minimized_window,
            wrap=tk.WORD,
            height=15,
            bg=self.colors['secondary'],
            fg=self.colors['text'],
            font=('Arial', 9),
            insertbackground=self.colors['text'],
            relief='flat',
            bd=0
        )
        self.minimized_window.translation_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        self.is_minimized = True
    
    def close_minimized_window(self):
        """Close minimized translator window"""
        if self.minimized_window:
            self.minimized_window.destroy()
            self.minimized_window = None
        
        self.is_minimized = False
        self.minimized_var.set(False)
        self.config['enable_minimized'] = False
        self.save_config()
    
    def on_minimized_close(self):
        """Handle minimized window close event"""
        self.close_minimized_window()
    
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
            
            # Create enhanced prompt for translation with language detection
            prompt = f"""Listen to this audio and:
1. Detect the source language with confidence level
2. Transcribe what you hear
3. Translate it to {target_lang}

Respond in this exact format:
SOURCE_LANGUAGE: [detected language code like 'en', 'th', 'id', etc.]
CONFIDENCE: [confidence percentage 0-100]
ORIGINAL: [transcribed text]
TRANSLATED: [translation to {target_lang}]

If there's no clear speech, respond with 'No speech detected'."""
            
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
            
            # Parse the structured response
            return self.parse_openai_audio_response(response, target_lang)
            
        except Exception as e:
            if "does not exist" in str(e) or "model_not_found" in str(e):
                return f"Model '{model}' not available. Try GPT-4o Audio Preview or Whisper-1."
            raise e
    
    def parse_openai_audio_response(self, response, target_lang):
        """Parse OpenAI audio response and format it"""
        try:
            lines = response.strip().split('\n')
            source_lang = 'unknown'
            confidence = 85  # Default fallback
            original_text = ''
            translated_text = ''
            
            for line in lines:
                if line.startswith('SOURCE_LANGUAGE:'):
                    source_lang = line.replace('SOURCE_LANGUAGE:', '').strip()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = int(line.replace('CONFIDENCE:', '').strip().replace('%', ''))
                    except ValueError:
                        confidence = 85  # Fallback if parsing fails
                elif line.startswith('ORIGINAL:'):
                    original_text = line.replace('ORIGINAL:', '').strip()
                elif line.startswith('TRANSLATED:'):
                    translated_text = line.replace('TRANSLATED:', '').strip()
            
            if original_text and translated_text:
                return self.format_translation_with_detection(original_text, translated_text, source_lang, target_lang, confidence)
            else:
                # Fallback: treat entire response as translation
                return f"🌐 (Auto-detected): {response}\n-------------------------"
                
        except Exception as e:
            print(f"Parsing error: {e}")
            return f"🌐 Translation: {response}\n-------------------------"
    
    def translate_with_whisper(self, wav_data, target_lang):
        """Translate using Whisper transcription + GPT translation"""
        try:
            # Use Whisper for transcription
            transcription = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=("audio.wav", wav_data, "audio/wav"),
                response_format="verbose_json"
            )
            
            if transcription.text.strip():
                original_text = transcription.text.strip()
                
                # Detect source language
                detected_lang = getattr(transcription, 'language', 'unknown')
                
                # Translate the transcribed text
                translation_response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user", 
                            "content": f"Translate this text to {target_lang}. If it's already in {target_lang}, just return the original text: {original_text}"
                        }
                    ]
                )
                translated_text = translation_response.choices[0].message.content
                
                # Format with language detection
                return self.format_translation_with_detection(original_text, translated_text, detected_lang, target_lang)
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
                    file=("audio.wav", wav_data, "audio/wav"),
                    response_format="verbose_json"
                )
                
                if transcription.text.strip():
                    original_text = transcription.text.strip()
                    detected_lang = getattr(transcription, 'language', 'unknown')
                    
                    # Translate with Gemini
                    prompt = f"Translate this text to {target_lang}. If it's already in {target_lang}, just return the original text: {original_text}"
                    response = self.gemini_client.generate_content(prompt)
                    translated_text = response.text
                    
                    # Format with language detection
                    return self.format_translation_with_detection(original_text, translated_text, detected_lang, target_lang)
                else:
                    return None
            else:
                return "OpenAI API key needed for audio transcription with Gemini models"
                
        except Exception as e:
            if "API_KEY_INVALID" in str(e):
                return "Invalid Gemini API key. Please check your configuration."
            raise e
    
    def format_translation_with_detection(self, original_text, translated_text, detected_lang, target_lang, confidence=None):
        """Format translation with language detection info"""
        try:
            # Get source language info
            source_flag, source_name = self.get_language_flag_and_name(detected_lang)
            
            # Get target language info
            target_flag, target_name = self.get_language_flag_and_name(target_lang)
            
            # Use provided confidence or detect it
            if confidence is None:
                _, confidence = self.detect_language_from_text(original_text)
            
            # Format the translation
            formatted = f"{source_flag} ({source_name} - {confidence}%): {original_text}\n"
            formatted += f"{target_flag} ({target_name}): {translated_text}\n"
            formatted += "-------------------------"
            
            return formatted
            
        except Exception as e:
            print(f"Formatting error: {e}")
            return f"Original: {original_text}\nTranslated: {translated_text}\n-------------------------"
    
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
        # Add to main window
        self.translation_text.insert(tk.END, translation + "\n\n")
        self.translation_text.see(tk.END)
        
        # Add to minimized window if enabled
        if self.is_minimized and self.minimized_window and hasattr(self.minimized_window, 'translation_text'):
            self.minimized_window.translation_text.insert(tk.END, translation + "\n\n")
            self.minimized_window.translation_text.see(tk.END)
            
            # Keep minimized window content limited
            mini_lines = self.minimized_window.translation_text.get("1.0", tk.END).split("\n")
            if len(mini_lines) > 30:  # Keep only last 10 translations in mini window
                self.minimized_window.translation_text.delete("1.0", f"{len(mini_lines)-30}.0")
        
        # Keep only last 50 translations to prevent memory issues in main window
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
        
        # Close minimized window safely
        if self.minimized_window:
            try:
                self.minimized_window.destroy()
            except tk.TclError:
                # Window already destroyed, ignore the error
                pass
            self.minimized_window = None
        
        if hasattr(self, 'audio'):
            self.audio.terminate()

if __name__ == "__main__":
    app = RealtimeVoiceTranslator()
    app.run()