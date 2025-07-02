import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkinter
import threading

def update_trends_chart(self):
    """Update the trends chart with recent data."""
    if not self.current_city:
        return
    
    try:
        # Get recent data for trends
        city_parts = self.current_city.split(', ')
        city, country = city_parts[0], city_parts[1] if len(city_parts) > 1 else ''
        
        # Load last 24 hours of data
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        conn = sqlite3.connect(self.database_path)
        df = pd.read_sql_query("""
            SELECT timestamp, temperature, humidity, comfort_index
            FROM processed_weather_data
            WHERE city = ? AND country = ?
            AND datetime(timestamp) > datetime(?)
            ORDER BY timestamp
        """, conn, params=(city, country, start_time.isoformat()))
        conn.close()
        
        if df.empty:
            return
        
        # Clear previous plot
        self.trends_ax.clear()
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create subplots for multiple metrics
        ax1 = self.trends_ax
        ax2 = ax1.twinx()
        
        # Plot temperature
        line1 = ax1.plot(df['timestamp'], df['temperature'], 'r-', label='Temperature (°C)', linewidth=2)
        ax1.set_ylabel('Temperature (°C)', color='r')
        ax1.tick_params(axis='y', labelcolor='r')
        
        # Plot humidity on secondary axis
        line2 = ax2.plot(df['timestamp'], df['humidity'], 'b-', label='Humidity (%)', linewidth=2)
        ax2.set_ylabel('Humidity (%)', color='b')
        ax2.tick_params(axis='y', labelcolor='b')
        
        # Format x-axis
        ax1.set_xlabel('Time')
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Add title
        ax1.set_title(f'24-Hour Trends for {self.current_city}')
        
        # Add legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Improve layout
        self.trends_fig.tight_layout()
        self.trends_canvas.draw()
        
    except Exception as e:
        print(f"Error updating trends chart: {e}")

def update_historical_chart(self):
    """Update the historical chart based on selected period."""
    period = self.period_var.get()
    
    # Convert period to timedelta
    period_map = {
        "24 hours": timedelta(hours=24),
        "3 days": timedelta(days=3),
        "7 days": timedelta(days=7),
        "30 days": timedelta(days=30)
    }
    
    time_delta = period_map.get(period, timedelta(days=7))
    
    try:
        city_parts = self.current_city.split(', ')
        city, country = city_parts[0], city_parts[1] if len(city_parts) > 1 else ''
        
        end_time = datetime.now()
        start_time = end_time - time_delta
        
        conn = sqlite3.connect(self.database_path)
        df = pd.read_sql_query("""
            SELECT timestamp, temperature, temp_24h_max, temp_24h_min
            FROM processed_weather_data
            WHERE city = ? AND country = ?
            AND datetime(timestamp) > datetime(?)
            ORDER BY timestamp
        """, conn, params=(city, country, start_time.isoformat()))
        conn.close()
        
        if df.empty:
            return
        
        self.hist_ax.clear()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Plot temperature with min/max band
        self.hist_ax.plot(df['timestamp'], df['temperature'], 'g-', label='Current Temperature', linewidth=2)
        
        if 'temp_24h_max' in df.columns and 'temp_24h_min' in df.columns:
            self.hist_ax.fill_between(df['timestamp'], df['temp_24h_min'], df['temp_24h_max'], 
                                    alpha=0.3, color='green', label='24h Range')
        
        self.hist_ax.set_xlabel('Date/Time')
        self.hist_ax.set_ylabel('Temperature (°C)')
        self.hist_ax.set_title(f'Historical Data - {period}')
        self.hist_ax.legend()
        self.hist_ax.grid(True, alpha=0.3)
        
        plt.setp(self.hist_ax.xaxis.get_majorticklabels(), rotation=45)
        self.hist_fig.tight_layout()
        self.hist_canvas.draw()
        
    except Exception as e:
        print(f"Error updating historical chart: {e}")

# Event Handlers
def on_city_changed(self, event):
    """Handle city selection change."""
    self.current_city = self.city_var.get()
    self.refresh_data()

def on_period_changed(self, event):
    """Handle period selection change for historical chart."""
    self.update_historical_chart()

def toggle_fullscreen(self):
    """Toggle fullscreen mode."""
    current_state = self.root.attributes('-fullscreen')
    self.root.attributes('-fullscreen', not current_state)

def open_preferences(self):
    """Open preferences dialog."""
    PreferencesDialog(self.root, self)

def start_auto_refresh(self):
    """Start automatic data refresh."""
    self.refresh_data()
    self.root.after(self.refresh_interval, self.start_auto_refresh)

def update_status(self, message):
    """Update the status bar message."""
    self.status_label.config(text=message)

def show_error(self, message):
    """Show error message to user."""
    messagebox.showerror("Error", message)
    self.update_status("Error occurred")

def run(self):
    """Start the application main loop."""
    self.root.mainloop()

# ----------------------------------------------------------------------------------

# Creating Preferences Dialog:

class PreferencesDialog:
    """Preferences dialog for application settings."""
    
    def __init__(self, parent, app):
        self.app = app
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Preferences")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_preferences_ui()
    
    def create_preferences_ui(self):
        """Create the preferences interface."""
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # General settings tab
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        
        # Refresh interval setting
        ttk.Label(general_frame, text="Auto-refresh interval (seconds):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        self.refresh_var = tk.StringVar(value=str(self.app.refresh_interval // 1000))
        refresh_entry = ttk.Entry(general_frame, textvariable=self.refresh_var, width=10)
        refresh_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # Temperature units
        ttk.Label(general_frame, text="Temperature units:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        
        self.temp_units_var = tk.StringVar(value="Celsius")
        temp_combo = ttk.Combobox(general_frame, textvariable=self.temp_units_var, 
                                values=["Celsius", "Fahrenheit"], state="readonly")
        temp_combo.grid(row=1, column=1, padx=10, pady=10)
        
        # Display settings tab
        display_frame = ttk.Frame(notebook)
        notebook.add(display_frame, text="Display")
        
        # Theme selection
        ttk.Label(display_frame, text="Theme:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        self.theme_var = tk.StringVar(value="clam")
        theme_combo = ttk.Combobox(display_frame, textvariable=self.theme_var,
                                 values=["clam", "alt", "default", "classic"], state="readonly")
        theme_combo.grid(row=0, column=1, padx=10, pady=10)
        
        # Buttons frame
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Apply", command=self.apply_preferences).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT)
    
    def apply_preferences(self):
        """Apply the selected preferences."""
        try:
            # Update refresh interval
            new_interval = int(self.refresh_var.get()) * 1000
            self.app.refresh_interval = new_interval
            
            # Update theme
            style = ttk.Style()
            style.theme_use(self.theme_var.get())
            
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid refresh interval")
