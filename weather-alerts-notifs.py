import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkinter
import threading




class WeatherAlertsManager:
    """Manage weather alerts and notifications."""
    
    def __init__(self, app):
        self.app = app
        self.alert_thresholds = {
            'high_temperature': 35.0,
            'low_temperature': -10.0,
            'high_wind_speed': 15.0,
            'low_pressure': 980.0,
            'high_severity': 70.0
        }
        self.active_alerts = []
    
    def check_weather_alerts(self, weather_data):
        """Check for weather conditions that warrant alerts."""
        new_alerts = []
        
        # Temperature alerts
        temp = weather_data.get('temperature', 0)
        if temp > self.alert_thresholds['high_temperature']:
            new_alerts.append({
                'type': 'temperature',
                'severity': 'warning',
                'title': 'High Temperature Alert',
                'message': f'Temperature is very high: {temp:.1f}°C',
                'icon': '🔥'
            })
        elif temp < self.alert_thresholds['low_temperature']:
            new_alerts.append({
                'type': 'temperature',
                'severity': 'warning',
                'title': 'Low Temperature Alert',
                'message': f'Temperature is very low: {temp:.1f}°C',
                'icon': '🥶'
            })
        
        # Wind speed alerts
        wind_speed = weather_data.get('wind_speed', 0)
        if wind_speed > self.alert_thresholds['high_wind_speed']:
            new_alerts.append({
                'type': 'wind',
                'severity': 'caution',
                'title': 'High Wind Alert',
                'message': f'Strong winds detected: {wind_speed:.1f} m/s',
                'icon': '💨'
            })
        
        # Pressure alerts (potential storms)
        pressure = weather_data.get('pressure', 1013)
        if pressure < self.alert_thresholds['low_pressure']:
            new_alerts.append({
                'type': 'pressure',
                'severity': 'watch',
                'title': 'Low Pressure Alert',
                'message': f'Low pressure system detected: {pressure:.1f} hPa',
                'icon': '⛈️'
            })
        
        # Weather severity alerts
        severity = weather_data.get('weather_severity', 0)
        if severity > self.alert_thresholds['high_severity']:
            new_alerts.append({
                'type': 'severity',
                'severity': 'warning',
                'title': 'Severe Weather Alert',
                'message': f'High weather severity index: {severity:.0f}/100',
                'icon': '⚠️'
            })
        
        # Update active alerts
        self.active_alerts = new_alerts
        
        # Display alerts in UI
        if new_alerts:
            self.display_alerts()
        
        return new_alerts
    
    def display_alerts(self):
        """Display active alerts in the UI."""
        if not self.active_alerts:
            return
        
        # Create alerts window
        alerts_window = tk.Toplevel(self.app.root)
        alerts_window.title("Weather Alerts")
        alerts_window.geometry("400x300")
        alerts_window.transient(self.app.root)
        
        # Create alerts list
        main_frame = ttk.Frame(alerts_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Active Weather Alerts", style='Title.TLabel').pack(pady=(0, 10))
        
        # Scrollable alerts frame
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for i, alert in enumerate(self.active_alerts):
            alert_frame = ttk.LabelFrame(scrollable_frame, text=f"{alert['icon']} {alert['title']}", padding="5")
            alert_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(alert_frame, text=alert['message']).pack(anchor=tk.W)
            
            severity_colors = {
                'warning': 'red',
                'caution': 'orange',
                'watch': 'yellow'
            }
            
            severity_label = ttk.Label(alert_frame, text=f"Severity: {alert['severity'].upper()}")
            severity_label.pack(anchor=tk.W)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        ttk.Button(main_frame, text="Close", command=alerts_window.destroy).pack(pady=10)

class DataExportManager:
    """Handle data export functionality."""
    
    def __init__(self, app):
        self.app = app
    
    def export_current_data(self, filename=None):
        """Export current weather data to CSV."""
        if not filename:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Weather Data"
            )
        
        if not filename:
            return False
        
        try:
            # Get data for current city
            city_parts = self.app.current_city.split(', ')
            city, country = city_parts[0], city_parts[1] if len(city_parts) > 1 else ''
            
            # Export last 30 days of data
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)
            
            conn = sqlite3.connect(self.app.database_path)
            df = pd.read_sql_query("""
                SELECT * FROM processed_weather_data
                WHERE city = ? AND country = ?
                AND datetime(timestamp) > datetime(?)
                ORDER BY timestamp
            """, conn, params=(city, country, start_time.isoformat()))
            conn.close()
            
            df.to_csv(filename, index=False)
            
            messagebox.showinfo("Export Complete", f"Data exported to {filename}")
            return True
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {e}")
            return False

# Integration with main app
def enhance_main_app(self):
    """Add enhanced features to the main application."""
    
    # Add alerts manager
    self.alerts_manager = WeatherAlertsManager(self)
    
    # Add export manager
    self.export_manager = DataExportManager(self)
    
    # Add alerts check to data update process
    original_update = self._update_ui_with_data
    
    def enhanced_update(data):
        original_update(data)
        # Check for alerts after updating UI
        alerts = self.alerts_manager.check_weather_alerts(data)
        if alerts:
            self.update_status(f"⚠️ {len(alerts)} weather alert(s) active")
    
    self._update_ui_with_data = enhanced_update
    
    # Add export option to menu
    self.create_enhanced_menu()

def create_enhanced_menu(self):
    """Create enhanced menu with additional options."""
    # Get existing menubar
    menubar = self.root.nametowidget(self.root['menu'])
    
    # Add Data menu
    data_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Data", menu=data_menu)
    data_menu.add_command(label="Export Current Data", command=self.export_manager.export_current_data)
    data_menu.add_separator()
    data_menu.add_command(label="View Alerts", command=self.alerts_manager.display_alerts)
    
    # Add Help menu
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="About", command=self.show_about_dialog)

def show_about_dialog(self):
    """Show about dialog."""
    about_text = """
    Weather Dashboard v1.0
    
    A comprehensive weather monitoring application
    built with Python and Tkinter.
    
    Features:
    • Real-time weather data collection
    • Advanced data processing and analysis
    • Interactive visualizations
    • Weather alerts and notifications
    • Data export capabilities
    
    Developed as part of the Python Development Program.
    """
    
    messagebox.showinfo("About Weather Dashboard", about_text)

# Integration Testing Framework:
def run_integration_tests(self):
    """Run comprehensive integration tests for the UI."""
    
    test_results = []
    
    # Test 1: Data loading
    try:
        cities = self.get_available_cities()
        if cities:
            test_results.append(("Data Loading", "PASS", f"Found {len(cities)} cities"))
        else:
            test_results.append(("Data Loading", "FAIL", "No cities found"))
    except Exception as e:
        test_results.append(("Data Loading", "ERROR", str(e)))
    
    # Test 2: UI component updates
    try:
        if self.current_city:
            self.refresh_data()
            test_results.append(("UI Updates", "PASS", "UI components updated"))
        else:
            test_results.append(("UI Updates", "SKIP", "No city selected"))
    except Exception as e:
        test_results.append(("UI Updates", "ERROR", str(e)))
    
    # Test 3: Chart rendering
    try:
        self.update_trends_chart()
        self.update_historical_chart()
        test_results.append(("Chart Rendering", "PASS", "Charts rendered successfully"))
    except Exception as e:
        test_results.append(("Chart Rendering", "ERROR", str(e)))
    
    # Display test results
    self.show_test_results(test_results)

def show_test_results(self, results):
    """Display integration test results."""
    results_window = tk.Toplevel(self.root)
    results_window.title("Integration Test Results")
    results_window.geometry("500x400")
    
    # Create results display
    tree = ttk.Treeview(results_window, columns=('status', 'details'), show='tree headings')
    tree.heading('#0', text='Test')
    tree.heading('status', text='Status')
    tree.heading('details', text='Details')
    
    for test_name, status, details in results:
        tree.insert('', 'end', text=test_name, values=(status, details))
    
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    ttk.Button(results_window, text="Close", command=results_window.destroy).pack(pady=10)
