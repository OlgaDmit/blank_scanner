# dark_mode.py
import tkinter as tk
import json
import os
from config import save_settings, load_config


class ThemeManager:
    
    def __init__(self, app):

        # Initialize theme manager with reference to the main app.

        self.app = app
        self.config_file = ".blank_scanner_theme.json"
        
        # Light theme colors
        self.light_colors = {
            'bg': '#f0f0f0',
            'fg': '#000000',
            'btn_bg': '#2196F3',
            'folder_btn_bg': '#4CAF50',
            'theme_emoji': '☀️',
            'theme_text': 'Светлая тема'
        }
        
        # Dark theme colors
        self.dark_colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'btn_bg': '#3c3c3c',
            'folder_btn_bg': '#2e7d32',
            'theme_emoji': '🌙',
            'theme_text': 'Тёмная тема'
        }
        
        # Load saved theme preference
        _, _, _, saved_dark_mode = load_config()
        if saved_dark_mode:
            self.app.dark_mode = False
            self.toggle()
    
    def _load_theme(self):
        """Load saved theme from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    saved_dark_mode = data.get('dark_mode', False)
                    
                    # If saved theme is dark, apply it
                    if saved_dark_mode:
                        # Set app to dark mode
                        self.app.dark_mode = False  # toggle() will flip to True
                        self.toggle()
        except Exception as e:
            print(f"[DEBUG] Could not load theme: {e}")
    
    def _save_theme(self):
        """Save current theme to config file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'dark_mode': self.app.dark_mode}, f)
        except Exception as e:
            print(f"[DEBUG] Could not save theme: {e}")
    
    def toggle(self):
        """Toggle between light and dark mode"""
        app = self.app
        app.dark_mode = not app.dark_mode
        
        if app.dark_mode:
            app.bg_color = self.dark_colors['bg']
            app.fg_color = self.dark_colors['fg']
            app.btn_bg = self.dark_colors['btn_bg']
            app.folder_btn_bg = self.dark_colors['folder_btn_bg']
            app.theme_label.config(text=self.dark_colors['theme_emoji'])
            app.theme_text.config(text=self.dark_colors['theme_text'])
        else:
            app.bg_color = self.light_colors['bg']
            app.fg_color = self.light_colors['fg']
            app.btn_bg = self.light_colors['btn_bg']
            app.folder_btn_bg = self.light_colors['folder_btn_bg']
            app.theme_label.config(text=self.light_colors['theme_emoji'])
            app.theme_text.config(text=self.light_colors['theme_text'])
        
        # Apply theme to root
        app.root.configure(bg=app.bg_color)
        
        # Update all widgets
        self._apply_theme_to_widgets()
        
        path_arr = getattr(self.app, 'path_arr', [])
        x = getattr(self.app, 'x', 0)
        y = getattr(self.app, 'y', 0)
        w = getattr(self.app, 'w', 640)
        h = getattr(self.app, 'h', 320)
        sharpness = getattr(self.app, 'sharpness', 1.0)
        
        save_settings(path_arr, [x, y, w, h], sharpness, self.app.dark_mode)
        
    
    def _apply_theme_to_widgets(self):
        """Apply current theme to all widgets"""
        app = self.app
        
        for widget in app.root.winfo_children():
            self._update_widget_theme(widget)
    
    def _update_widget_theme(self, widget):
        """Recursively update a widget's theme"""
        app = self.app
        
        try:
            widget_type = widget.winfo_class()
            
            if widget_type in ('Frame', 'LabelFrame'):
                widget.configure(bg=app.bg_color)
            
            elif widget_type == 'Label':
                if widget == app.folder_label and app.current_folder is None:
                    widget.configure(bg=app.bg_color, fg="gray" if not app.dark_mode else "#aaaaaa")
                elif widget != app.theme_label and widget != app.theme_text:
                    widget.configure(bg=app.bg_color, fg=app.fg_color)
            
            elif widget_type == 'Button':
                if (widget == app.scan_btn or widget == app.load_btn or 
                    widget == app.train_btn or widget == app.template_btn or
                    widget == app.tutorial_btn or widget == app.credits_btn):
                    widget.configure(bg=app.btn_bg)
                else:
                    widget.configure(bg=app.folder_btn_bg)
            
            for child in widget.winfo_children():
                self._update_widget_theme(child)
        except:
            pass