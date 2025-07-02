import tkinter as tk 
from tkinter import ttk, messagebox 
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkinter
import threading

"""
tkinter/ttk: GUI elements and themed widgets
sqlite3: Database connection to fetch weather data
pandas: Could be used later for data processing (though not shown in this snippet)
datetime: Time-based formatting and calculations
matplotlib: For charts (trends and historical visualizations)
threading: Used to avoid freezing the GUI during data refresh
"""

class WeatherApp:
    """
    Main weather application with modular UI components.
    """
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.root = tk.Tk()
        self.root.title("Weather Dashboard")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Application state
        self.current_city = None
        self.current_data = None
        self.refresh_interval = 30000  # 30 seconds
        
        # Initialize UI components
        self.setup_styles()
        self.create_main_layout()
        self.create_menu_bar()
        self.load_initial_data()
        self.start_auto_refresh()
    
    def setup_styles(self):
        """Configure application-wide styles and themes."""
        style = ttk.Style()
        style.theme_use('clam')  # Modern looking theme
        
        # Define custom styles
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Data.TLabel', font=('Arial', 11))
        style.configure('Large.TLabel', font=('Arial', 24, 'bold'))
        
        # Custom colors for weather conditions
        style.configure('Hot.TLabel', foreground='red')
        style.configure('Cold.TLabel', foreground='blue')
        style.configure('Normal.TLabel', foreground='green')
    
    def create_main_layout(self):
        """Create the main application layout structure.
        Set up our grid and high-level layout."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for responsiveness
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Create main sections
        self.create_header_section(main_frame)
        self.create_current_weather_section(main_frame)
        self.create_details_section(main_frame)
        self.create_status_section(main_frame)
    
    def create_header_section(self, parent):
        """Create the application header with title and city selection."""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        # Application title
        title_label = ttk.Label(header_frame, text="Weather Dashboard", style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # City selection frame
        city_frame = ttk.Frame(header_frame)
        city_frame.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Label(city_frame, text="City:").grid(row=0, column=0, padx=(0, 5))
        
        self.city_var = tk.StringVar()
        self.city_combo = ttk.Combobox(city_frame, textvariable=self.city_var, 
                                      state="readonly", width=20)
        self.city_combo.grid(row=0, column=1, padx=(0, 10))
        self.city_combo.bind('<<ComboboxSelected>>', self.on_city_changed)
        
        # Refresh button
        refresh_btn = ttk.Button(city_frame, text="Refresh", command=self.refresh_data)
        refresh_btn.grid(row=0, column=2)
    
    def create_current_weather_section(self, parent):
        """Create the main current weather display section."""
        current_frame = ttk.LabelFrame(parent, text="Current Weather", padding="10")
        current_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        current_frame.columnconfigure(0, weight=1)
        
        # Current temperature (large display)
        self.temp_label = ttk.Label(current_frame, text="--°C", style='Large.TLabel')
        self.temp_label.grid(row=0, column=0, pady=(0, 10))
        
        # Weather description
        self.desc_label = ttk.Label(current_frame, text="Loading...", style='Heading.TLabel')
        self.desc_label.grid(row=1, column=0, pady=(0, 15))
        
        # Key metrics in a grid
        metrics_frame = ttk.Frame(current_frame)
        metrics_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # Create metric display widgets
        self.create_metric_display(metrics_frame, "Feels Like", "feels_like", 0, 0, "°C")
        self.create_metric_display(metrics_frame, "Humidity", "humidity", 0, 1, "%")
        self.create_metric_display(metrics_frame, "Pressure", "pressure", 1, 0, "hPa")
        self.create_metric_display(metrics_frame, "Wind", "wind_speed", 1, 1, "m/s")
        # create_metric_display() is a reusable method for rendering metric name, value label, and units
        
        # Comfort index
        comfort_frame = ttk.Frame(current_frame)
        comfort_frame.grid(row=3, column=0, pady=(15, 0), sticky=(tk.W, tk.E))
        
        ttk.Label(comfort_frame, text="Comfort Index:", style='Heading.TLabel').grid(row=0, column=0)
        self.comfort_label = ttk.Label(comfort_frame, text="--", style='Data.TLabel')
        self.comfort_label.grid(row=0, column=1, padx=(10, 0))
        
        self.comfort_bar = ttk.Progressbar(comfort_frame, length=200, mode='determinate')
        self.comfort_bar.grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky=(tk.W, tk.E))
    
    def create_metric_display(self, parent, label_text, data_key, row, col, unit):
        """Create a standardized metric display widget."""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=col, padx=10, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(frame, text=f"{label_text}:", style='Data.TLabel').grid(row=0, column=0, sticky=tk.W)
        
        value_label = ttk.Label(frame, text=f"-- {unit}", style='Data.TLabel')
        value_label.grid(row=1, column=0, sticky=tk.W)
        
        # Store reference for updates
        setattr(self, f"{data_key}_label", value_label)
    
    def create_details_section(self, parent):
        """Create the detailed information and visualization section."""
        details_frame = ttk.LabelFrame(parent, text="Details & Trends", padding="10")
        details_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(1, weight=1)
        
        # Create notebook for tabbed content
        self.notebook = ttk.Notebook(details_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Recent trends tab
        self.create_trends_tab()
        
        # Historical data tab
        self.create_historical_tab()
        
        # Detailed metrics tab
        self.create_detailed_metrics_tab()
    
    def create_trends_tab(self):
        """Create the trends visualization tab."""
        trends_frame = ttk.Frame(self.notebook)
        self.notebook.add(trends_frame, text="Recent Trends")
        
        # Matplotlib figure for trends
        self.trends_fig, self.trends_ax = plt.subplots(figsize=(6, 4))
        self.trends_canvas = FigureCanvasTkinter(self.trends_fig, trends_frame)
        self.trends_canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        trends_frame.columnconfigure(0, weight=1)
        trends_frame.rowconfigure(0, weight=1)
    
    def create_historical_tab(self):
        """Create the historical data tab."""
        historical_frame = ttk.Frame(self.notebook)
        self.notebook.add(historical_frame, text="Historical")
        
        # Time period selection
        period_frame = ttk.Frame(historical_frame)
        period_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(period_frame, text="Period:").grid(row=0, column=0, padx=(0, 5))
        
        self.period_var = tk.StringVar(value="7 days")
        period_combo = ttk.Combobox(period_frame, textvariable=self.period_var, 
                                   values=["24 hours", "3 days", "7 days", "30 days"],
                                   state="readonly", width=15)
        period_combo.grid(row=0, column=1)
        period_combo.bind('<<ComboboxSelected>>', self.on_period_changed)
        
        # Historical chart
        self.hist_fig, self.hist_ax = plt.subplots(figsize=(6, 4))
        self.hist_canvas = FigureCanvasTkinter(self.hist_fig, historical_frame)
        self.hist_canvas.get_tk_widget().grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        historical_frame.columnconfigure(0, weight=1)
        historical_frame.rowconfigure(1, weight=1)
    
    def create_detailed_metrics_tab(self):
        """Create the detailed metrics tab."""
        metrics_frame = ttk.Frame(self.notebook)
        self.notebook.add(metrics_frame, text="Detailed Metrics")
        
        # Create scrollable frame for metrics
        canvas = tk.Canvas(metrics_frame)
        scrollbar = ttk.Scrollbar(metrics_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        metrics_frame.columnconfigure(0, weight=1)
        metrics_frame.rowconfigure(0, weight=1)
        
        # Add detailed metrics
        self.create_detailed_metrics_content(scrollable_frame)
    
    def create_detailed_metrics_content(self, parent):
        """Create the content for detailed metrics."""
        # Derived features section
        derived_frame = ttk.LabelFrame(parent, text="Derived Metrics", padding="10")
        derived_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.heat_index_label = ttk.Label(derived_frame, text="Heat Index: --°C")
        self.heat_index_label.grid(row=0, column=0, sticky=tk.W)
        
        self.wind_chill_label = ttk.Label(derived_frame, text="Wind Chill: --°C")
        self.wind_chill_label.grid(row=1, column=0, sticky=tk.W)
        
        self.severity_label = ttk.Label(derived_frame, text="Weather Severity: --")
        self.severity_label.grid(row=2, column=0, sticky=tk.W)
        
        # Time-based information
        time_frame = ttk.LabelFrame(parent, text="Time Information", padding="10")
        time_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.last_update_label = ttk.Label(time_frame, text="Last Update: --")
        self.last_update_label.grid(row=0, column=0, sticky=tk.W)
        
        self.local_time_label = ttk.Label(time_frame, text="Local Time: --")
        self.local_time_label.grid(row=1, column=0, sticky=tk.W)
    
    def create_status_section(self, parent):
        """Create the status bar at the bottom."""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Data quality indicator
        self.quality_label = ttk.Label(status_frame, text="Data Quality: Unknown")
        self.quality_label.grid(row=0, column=1, sticky=tk.E)
    
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh Data", command=self.refresh_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Full Screen", command=self.toggle_fullscreen)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences", command=self.open_preferences)

# --------------------------------------------------



# Data Integration and Updates:
def load_initial_data(self):
    """Load initial data and populate the interface."""
    try:
        # Load available cities
        cities = self.get_available_cities()
        self.city_combo['values'] = cities
        if cities:
            self.city_combo.set(cities[0])
            self.current_city = cities[0]
            self.refresh_data()
        
    except Exception as e:
        self.show_error(f"Failed to load initial data: {e}")

def get_available_cities(self):
    """Get list of cities with available data."""
    try:
        conn = sqlite3.connect(self.database_path)
        cursor = conn.execute("""
            SELECT DISTINCT city || ', ' || country as city_country
            FROM weather_readings 
            ORDER BY city
        """)
        cities = [row[0] for row in cursor.fetchall()]
        conn.close()
        return cities
    except sqlite3.Error as e:
        self.show_error(f"Database error: {e}")
        return []

def refresh_data(self):
    """Refresh all data displays."""
    if not self.current_city:
        return
    
    self.update_status("Refreshing data...")
    
    # Run data loading in background thread to prevent UI freezing
    threading.Thread(target=self._load_data_background, daemon=True).start()

def _load_data_background(self):
    """Load data in background thread."""
    try:
        # Parse city and country
        city_parts = self.current_city.split(', ')
        city, country = city_parts[0], city_parts[1] if len(city_parts) > 1 else ''
        
        # Load current weather data
        current_data = self.get_current_weather_data(city, country)
        
        if current_data:
            # Update UI in main thread
            self.root.after(0, self._update_ui_with_data, current_data)
        else:
            self.root.after(0, self.update_status, "No data available for selected city")
            
    except Exception as e:
        self.root.after(0, self.show_error, f"Error loading data: {e}")

def _update_ui_with_data(self, data):
    """Update UI components with new data."""
    self.current_data = data
    
    # Update current weather display
    self.temp_label.config(text=f"{data['temperature']:.1f}°C")
    self.desc_label.config(text=data['weather_description'].title())
    
    # Update metric displays
    self.feels_like_label.config(text=f"{data['feels_like']:.1f}°C")
    self.humidity_label.config(text=f"{data['humidity']}%")
    self.pressure_label.config(text=f"{data['pressure']:.1f} hPa")
    self.wind_speed_label.config(text=f"{data['wind_speed']:.1f} m/s")
    
    # Update comfort index
    comfort = data.get('comfort_index', 0)
    self.comfort_label.config(text=f"{comfort:.0f}/100")
    self.comfort_bar['value'] = comfort
    
    # Update detailed metrics
    self.heat_index_label.config(text=f"Heat Index: {data.get('heat_index_c', 0):.1f}°C")
    self.wind_chill_label.config(text=f"Wind Chill: {data.get('wind_chill_c', 0):.1f}°C")
    self.severity_label.config(text=f"Weather Severity: {data.get('weather_severity', 0):.0f}/100")
    
    # Update time information
    self.last_update_label.config(text=f"Last Update: {data['timestamp']}")
    self.local_time_label.config(text=f"Local Time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Update temperature color based on value
    temp = data['temperature']
    if temp > 30:
        self.temp_label.config(style='Hot.TLabel')
    elif temp < 10:
        self.temp_label.config(style='Cold.TLabel')
    else:
        self.temp_label.config(style='Normal.TLabel')
    
    # Update visualizations
    self.update_trends_chart()
    self.update_historical_chart()
    
    self.update_status("Data updated successfully")

def get_current_weather_data(self, city, country):
    """Get the most recent weather data for a city."""
    try:
        conn = sqlite3.connect(self.database_path)
        cursor = conn.execute("""
            SELECT * FROM processed_weather_data
            WHERE city = ? AND country = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (city, country))
        
        row = cursor.fetchone()
        if row:
            # Convert to dictionary (assuming processed_weather_data has all columns)
            columns = [description[0] for description in cursor.description]
            data = dict(zip(columns, row))
            conn.close()
            return data
        
        conn.close()
        return None
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
