import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import os
from datetime import datetime
import numpy as np
import sqlite3
from io import BytesIO

# Optional imports with fallbacks
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    import xlrd
    HAS_XLRD = True
except ImportError:
    HAS_XLRD = False

class SalesAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sales Analysis Dashboard")
        self.root.geometry("1400x900")
        self.root.configure(bg='#9ECAD6')
        
        # Data storage
        self.df = None
        self.db_path = "sales_data.db"
        self.init_database()
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.setup_styles()
        
        # Create main interface
        self.create_widgets()
        
    def setup_styles(self):
        """Configure custom styles for the application"""
        self.style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background='#f0f0f0')
        self.style.configure('Heading.TLabel', font=('Arial', 12, 'bold'), background='#f0f0f0')
        self.style.configure('Custom.TButton',font=('Arial', 10, 'bold'),foreground='white',background="#F6640A",borderwidth=1,focusthickness=3,focuscolor='none',padding=6)
        self.style.map('Custom.TButton',background=[('active', '#e07e27'), ('pressed', "#c36717")],foreground=[('disabled', 'gray')])
        self.style.configure('Custom.TFrame', background="#143E41",font=("Arial", 12, "bold"))
        self.style.configure("CustomNotebook.TNotebook.Tab", font=("Arial", 12, "bold"))
        
    def init_database(self):
        """Initialize SQLite database for storing sales data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT,
                sales_amount REAL,
                quantity INTEGER,
                profit REAL,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        
    def create_widgets(self):
        """Create the main GUI components"""
        # Main container with notebook for tabs
        self.notebook = ttk.Notebook(self.root,style="CustomNotebook.TNotebook")
        self.notebook.pack(expand=1,fill='both')
        
        # Tab 1: Data Upload and Processing
        self.upload_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.upload_frame, text="📁 Data Upload")
        self.create_upload_tab()
        
        # Tab 2: Analytics Dashboard
        self.analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analytics_frame, text="📊 Analytics")
        self.create_analytics_tab()
        
        # Tab 3: Product Images
        self.images_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.images_frame, text="🖼️ Product Images")
        self.create_images_tab()
    
    def create_upload_tab(self):
        """Create the data upload interface"""
        # File upload section
        upload_section = ttk.LabelFrame(self.upload_frame, padding=20,style='Custom.TFrame',height=130,text="Upload File")
        upload_section.pack(fill='x', padx=20, pady=10)
        upload_section.pack_propagate(False)
        
        # File selection
        file_frame = ttk.Frame(upload_section,style='Custom.TFrame')
        file_frame.pack(fill='x', pady=10)

        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=60)
        file_entry.pack(side='left', padx=(0, 10))
        
        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file,style='Custom.TButton')
        browse_btn.pack(side='left',pady=10)
        
        # Load data button
        load_btn = ttk.Button(upload_section, text="Load Data", command=self.load_data,style='Custom.TButton')
        load_btn.pack(pady=10,padx=10)
        
        # Data preview section
        preview_section = ttk.LabelFrame(self.upload_frame, text="Data Preview", padding=10)
        preview_section.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Treeview for data display
        columns = ('Product', 'Sales', 'Quantity', 'Profit')
        self.tree = ttk.Treeview(preview_section, columns=columns, show='headings', height=15,style='Custom.TFrame')
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(preview_section, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(preview_section, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        
    def create_analytics_tab(self):
        """Create the analytics dashboard"""
        # Control panel
        control_panel = ttk.LabelFrame(self.analytics_frame, text="Analysis Controls", padding=10)
        control_panel.pack(fill='x', padx=20, pady=10)
        
        controls_frame = ttk.Frame(control_panel)
        controls_frame.pack(fill='x')
        
        # Top N products selector
        ttk.Label(controls_frame, text="Show Top:").pack(side='left', padx=(0, 5))
        self.top_n_var = tk.StringVar(value="10")
        top_n_spin = ttk.Spinbox(controls_frame, from_=1, to=50, textvariable=self.top_n_var, width=5)
        top_n_spin.pack(side='left', padx=(0, 20))
        
        # Metric selector
        ttk.Label(controls_frame, text="Metric:").pack(side='left', padx=(0, 5))
        self.metric_var = tk.StringVar(value="sales_amount")
        metric_combo = ttk.Combobox(controls_frame, textvariable=self.metric_var, 
                                   values=["sales_amount", "quantity", "profit"], width=15)
        metric_combo.pack(side='left', padx=(0, 20))
        
        # Update button
        update_btn = ttk.Button(controls_frame, text="Update Charts", command=self.update_charts)
        update_btn.pack(side='left', padx=20)
        
        # Export button
        export_btn = ttk.Button(controls_frame, text="Export Charts", command=self.export_charts)
        export_btn.pack(side='left', padx=10)
        
        # Statistics display
        stats_frame = ttk.LabelFrame(self.analytics_frame, text="Key Statistics", padding=10)
        stats_frame.pack(fill='x', padx=20, pady=10)
        
        self.stats_text = tk.Text(stats_frame, height=4, font=('Arial', 10))
        self.stats_text.pack(fill='x')
        
        # Charts frame
        charts_frame = ttk.Frame(self.analytics_frame)
        charts_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Create matplotlib figure
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(14, 6))
        self.fig.patch.set_facecolor('#f0f0f0')
        
        self.canvas = FigureCanvasTkAgg(self.fig, charts_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
    def create_images_tab(self):
        """Create the product images interface"""
        if not (HAS_PIL and HAS_REQUESTS and HAS_DDGS):
            # Show message about missing libraries
            missing_libs = []
            if not HAS_PIL:
                missing_libs.append("Pillow (PIL)")
            if not HAS_REQUESTS:
                missing_libs.append("requests")
            if not HAS_DDGS:
                missing_libs.append("duckduckgo-search")
            
            info_label = ttk.Label(self.images_frame, 
                                  text=f"Image functionality requires: {', '.join(missing_libs)}\n"
                                       f"Install with: pip install {' '.join(missing_libs).lower().replace('pillow (pil)', 'pillow')}")
            info_label.pack(expand=True)
            return
        
        # Controls
        image_controls = ttk.LabelFrame(self.images_frame, text="Image Controls", padding=10)
        image_controls.pack(fill='x', padx=20, pady=10)
        
        controls_frame = ttk.Frame(image_controls)
        controls_frame.pack(fill='x')
        
        ttk.Label(controls_frame, text="Select Product:").pack(side='left', padx=(0, 5))
        self.product_var = tk.StringVar()
        self.product_combo = ttk.Combobox(controls_frame, textvariable=self.product_var, width=30)
        self.product_combo.pack(side='left', padx=(0, 20))
        
        download_btn = ttk.Button(controls_frame, text="Download Image", 
                                 command=self.download_product_image)
        download_btn.pack(side='left', padx=10)
        
        # Image display area
        image_display = ttk.LabelFrame(self.images_frame, text="Product Image", padding=10)
        image_display.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.image_label = ttk.Label(image_display, text="No image loaded")
        self.image_label.pack(expand=True)
        
    def browse_file(self):
        """Open file dialog to select Excel file"""
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            
    def load_data(self):
        """Load and process Excel data with multiple engine fallbacks"""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showerror("Error", "Please select an Excel file first!")
            return
        
        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            # Try different methods to read Excel file
            self.df = None
            error_messages = []
            
            # Method 1: Try openpyxl for .xlsx files
            if file_ext == '.xlsx' and HAS_OPENPYXL:
                try:
                    self.df = pd.read_excel(file_path, engine='openpyxl')
                except Exception as e:
                    error_messages.append(f"openpyxl: {str(e)}")
            
            # Method 2: Try xlrd for .xls files or as fallback
            if self.df is None and HAS_XLRD:
                try:
                    self.df = pd.read_excel(file_path, engine='xlrd')
                except Exception as e:
                    error_messages.append(f"xlrd: {str(e)}")
            
            # Method 3: Try default pandas excel reader
            if self.df is None:
                try:
                    self.df = pd.read_excel(file_path)
                except Exception as e:
                    error_messages.append(f"default: {str(e)}")
            
            # Method 4: Try reading as CSV if all Excel methods fail
            if self.df is None:
                try:
                    # Ask user if they want to try CSV format
                    result = messagebox.askyesno("Excel Read Failed", 
                                               "Failed to read as Excel file. Try reading as CSV?")
                    if result:
                        self.df = pd.read_csv(file_path)
                except Exception as e:
                    error_messages.append(f"CSV: {str(e)}")
            
            # If still no data loaded, show error
            if self.df is None:
                error_msg = "Failed to load file with all available methods:\n" + "\n".join(error_messages)
                error_msg += "\n\nTry installing missing libraries:\npip install openpyxl xlrd"
                messagebox.showerror("Error", error_msg)
                return
            
            # Check if dataframe is empty
            if self.df.empty:
                messagebox.showerror("Error", "The file appears to be empty!")
                return
            
            # Clean and standardize column names
            self.df.columns = self.df.columns.str.lower().str.strip()
            
            # Try to identify common column patterns
            column_mapping = {}
            for col in self.df.columns:
                if any(keyword in col for keyword in ['product', 'item', 'name']):
                    column_mapping['product_name'] = col
                elif any(keyword in col for keyword in ['sales', 'amount', 'revenue', 'total']):
                    column_mapping['sales_amount'] = col
                elif any(keyword in col for keyword in ['quantity', 'qty', 'units']):
                    column_mapping['quantity'] = col
                elif any(keyword in col for keyword in ['profit', 'margin']):
                    column_mapping['profit'] = col
            
            # If no columns found, let user select manually
            if not column_mapping:
                self.manual_column_mapping()
                return
            
            # Rename columns
            self.df.rename(columns=column_mapping, inplace=True)
            
            # Ensure required columns exist
            required_cols = ['product_name', 'sales_amount', 'quantity', 'profit']
            for col in required_cols:
                if col not in self.df.columns:
                    if col == 'product_name':
                        # Use first column as product name if none found
                        if len(self.df.columns) > 0:
                            self.df['product_name'] = self.df.iloc[:, 0].astype(str)
                        else:
                            self.df['product_name'] = [f"Product_{i+1}" for i in range(len(self.df))]
                    else:
                        self.df[col] = 0 if col != 'quantity' else 1
            
            # Data cleaning
            self.df['sales_amount'] = pd.to_numeric(self.df['sales_amount'], errors='coerce').fillna(0)
            self.df['quantity'] = pd.to_numeric(self.df['quantity'], errors='coerce').fillna(1).astype('Int64')
            self.df['profit'] = pd.to_numeric(self.df['profit'], errors='coerce').fillna(0)
            
            # Remove rows with empty product names
            self.df = self.df[self.df['product_name'].str.strip() != '']
            self.df = self.df[self.df['product_name'] != 'nan']
            
            # Group by product name and sum values
            self.df = self.df.groupby('product_name').agg({
                'sales_amount': 'sum',
                'quantity': 'sum',
                'profit': 'sum'
            }).reset_index()
            
            # Save to database
            self.save_to_database()
            
            # Update display
            self.update_treeview()
            if HAS_PIL and HAS_REQUESTS and HAS_DDGS:
                self.update_product_list()
            self.update_charts()
            
            messagebox.showinfo("Success", f"Loaded {len(self.df)} products successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
        print(self.df.isnull().sum())

    def manual_column_mapping(self):
        """Allow user to manually map columns"""
        if self.df is None or self.df.empty:
            return
            
        # Create a new window for column mapping
        mapping_window = tk.Toplevel(self.root)
        mapping_window.title("Column Mapping")
        mapping_window.geometry("500x400")
        
        ttk.Label(mapping_window, text="Please map your columns to the required fields:", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Available columns
        available_columns = [''] + list(self.df.columns)
        
        # Mapping variables
        self.column_vars = {
            'product_name': tk.StringVar(),
            'sales_amount': tk.StringVar(),
            'quantity': tk.StringVar(),
            'profit': tk.StringVar()
        }
        
        # Create mapping interface
        mapping_frame = ttk.Frame(mapping_window)
        mapping_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        labels = {
            'product_name': 'Product Name *',
            'sales_amount': 'Sales Amount *',
            'quantity': 'Quantity',
            'profit': 'Profit'
        }
        
        for i, (field, var) in enumerate(self.column_vars.items()):
            ttk.Label(mapping_frame, text=labels[field]).grid(row=i, column=0, sticky='w', pady=5)
            combo = ttk.Combobox(mapping_frame, textvariable=var, values=available_columns, width=30)
            combo.grid(row=i, column=1, padx=10, pady=5)
            
            # Try to auto-select based on column names
            for col in available_columns[1:]:  # Skip empty string
                if any(keyword in col.lower() for keyword in field.split('_')):
                    var.set(col)
                    break
        
        # Buttons
        button_frame = ttk.Frame(mapping_window)
        button_frame.pack(pady=20)
        
        def apply_mapping():
            # Get selected columns
            mapping = {field: var.get() for field, var in self.column_vars.items()}
            
            # Check required fields
            if not mapping['product_name'] or not mapping['sales_amount']:
                messagebox.showerror("Error", "Product Name and Sales Amount are required!")
                return
            
            # Apply mapping
            rename_dict = {v: k for k, v in mapping.items() if v}
            self.df.rename(columns=rename_dict, inplace=True)
            
            # Add missing optional columns
            if 'quantity' not in self.df.columns:
                self.df['quantity'] = 1
            if 'profit' not in self.df.columns:
                self.df['profit'] = 0
            
            mapping_window.destroy()
            
            # Continue with data processing
            try:
                # Data cleaning
                # Correct way (don't chain with inplace)
                self.df['sales_amount'] = pd.to_numeric(self.df['sales_amount'], errors='coerce').fillna(0)
                
                self.df['quantity'] = pd.to_numeric(self.df['quantity'], errors='coerce').fillna(1).astype(int)
                
                self.df['profit'] = pd.to_numeric(self.df['profit'], errors='coerce').fillna(0)

                
                # Remove rows with empty product names
                self.df = self.df[self.df['product_name'].str.strip() != '']
                
                # Group by product name and sum values
                self.df = self.df.groupby('product_name').agg({
                    'sales_amount': 'sum',
                    'quantity': 'sum',
                    'profit': 'sum'
                }).reset_index()
                
                # Save to database
                self.save_to_database()
                
                # Update display
                self.update_treeview()
                if HAS_PIL and HAS_REQUESTS and HAS_DDGS:
                    self.update_product_list()
                self.update_charts()
                
                messagebox.showinfo("Success", f"Loaded {len(self.df)} products successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process data: {str(e)}")
        
        ttk.Button(button_frame, text="Apply Mapping", command=apply_mapping).pack(side='left', padx=10)
        ttk.Button(button_frame, text="Cancel", command=mapping_window.destroy).pack(side='left')
            
    def save_to_database(self):
        """Save data to SQLite database"""
        if self.df is not None:
            conn = sqlite3.connect(self.db_path)
            # Clear existing data
            conn.execute("DELETE FROM sales_data")
            # Insert new data
            self.df.to_sql('sales_data', conn, if_exists='append', index=False)
            conn.close()
            
    def update_treeview(self):
        """Update the data preview treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add new items
        if self.df is not None:
            for _, row in self.df.head(100).iterrows():  # Show top 100 rows
                self.tree.insert('', 'end', values=(
                    row['product_name'],
                    f"${row['sales_amount']:.2f}",
                    int(row['quantity']),
                    f"${row['profit']:.2f}"
                ))
                
    def update_product_list(self):
        """Update product list in images tab"""
        if self.df is not None:
            products = self.df['product_name'].tolist()
            self.product_combo['values'] = products
            if products:
                self.product_combo.set(products[0])
                
    def update_charts(self):
        """Update the analytics charts"""
        if self.df is None:
            return
            
        try:
            top_n = int(self.top_n_var.get())
            metric = self.metric_var.get()
            
            if self.df[metric].sum() == 0:
                print("Nothing to plot: all values are zero.")
                return

            
            # Get top N products
            top_products = self.df.nlargest(top_n, metric)
            self.df[metric] = pd.to_numeric(self.df[metric], errors='coerce').fillna(0)
            print(self.df[metric].dtype)
            
            # Clear previous plots
            self.ax1.clear()
            self.ax2.clear()
            
            # Bar chart
            bars = self.ax1.bar(range(len(top_products)), top_products[metric], 
                               color=plt.cm.viridis(np.linspace(0, 1, len(top_products))))
            self.ax1.set_xlabel('Products')
            self.ax1.set_ylabel(metric.replace('_', ' ').title())
            self.ax1.set_title(f'Top {top_n} Products by {metric.replace("_", " ").title()}')
            self.ax1.set_xticks(range(len(top_products)))
            self.ax1.set_xticklabels([name[:10] + '...' if len(name) > 10 else name 
                                    for name in top_products['product_name']], rotation=45)
            
            # Add value labels on bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                self.ax1.text(bar.get_x() + bar.get_width()/2., height,
                             f'{height:.0f}', ha='center', va='bottom', fontsize=8)
            
            # Pie chart
            colors = plt.cm.Set3(np.linspace(0, 1, len(top_products)))
            wedges, texts, autotexts = self.ax2.pie(top_products[metric], 
                                                   labels=[name[:15] + '...' if len(name) > 15 else name 
                                                          for name in top_products['product_name']],
                                                   autopct='%1.1f%%', colors=colors)
            self.ax2.set_title(f'{metric.replace("_", " ").title()} Distribution')
            
            # Adjust layout
            self.fig.tight_layout()
            self.canvas.draw()
            
            # Update statistics
            self.update_statistics()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update charts: {str(e)}")
            
    def update_statistics(self):
        """Update key statistics display"""
        if self.df is None:
            return
            
        total_sales = self.df['sales_amount'].sum()
        total_quantity = self.df['quantity'].sum()
        total_profit = self.df['profit'].sum()
        avg_sales = self.df['sales_amount'].mean()
        top_product = self.df.loc[self.df['sales_amount'].idxmax(), 'product_name']
        
        stats_text = f"""Total Sales: ${total_sales:,.2f} | Total Quantity: {total_quantity:,} | Total Profit: ${total_profit:,.2f}
Average Sales per Product: ${avg_sales:,.2f} | Total Products: {len(self.df)}
Top Selling Product: {top_product}"""
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
        
    def download_product_image(self):
        """Download product image from DuckDuckGo"""
        if not (HAS_PIL and HAS_REQUESTS and HAS_DDGS):
            messagebox.showwarning("Warning", "Image functionality requires PIL, requests, and duckduckgo-search libraries!")
            return
            
        product_name = self.product_var.get()
        if not product_name:
            messagebox.showwarning("Warning", "Please select a product first!")
            return
            
        def download_image():
            try:
                # Search for images using DuckDuckGo
                with DDGS() as ddgs:
                    results = list(ddgs.images(f"{product_name} product", max_results=1))
                    
                if results:
                    image_url = results[0]['image']
                    
                    # Download image
                    response = requests.get(image_url, timeout=10)
                    response.raise_for_status()
                    
                    # Open image from bytes
                    image = Image.open(BytesIO(response.content))
                    
                    # Resize image to fit display
                    image.thumbnail((400, 400), Image.Resampling.LANCZOS)
                    
                    # Convert to PhotoImage
                    photo = ImageTk.PhotoImage(image)
                    
                    # Update image label
                    self.image_label.configure(image=photo, text="")
                    self.image_label.image = photo  # Keep a reference
                    
                    # Save image locally
                    os.makedirs("product_images", exist_ok=True)
                    image_path = f"product_images/{product_name.replace(' ', '_')}.jpg"
                    image.save(image_path)
                    
                    messagebox.showinfo("Success", f"Image downloaded and saved to {image_path}")
                else:
                    messagebox.showwarning("Warning", "No images found for this product.")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to download image: {str(e)}")
        
        # Run download in separate thread to prevent GUI freezing
        thread = threading.Thread(target=download_image)
        thread.daemon = True
        thread.start()
        
    def export_charts(self):
        """Export charts as image files"""
        if self.df is None:
            messagebox.showwarning("Warning", "No data loaded!")
            return
            
        try:
            # Create exports directory
            os.makedirs("exports", exist_ok=True)
            
            # Save current figure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exports/sales_analysis_{timestamp}.png"
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            
            # Also export data as Excel
            excel_filename = f"exports/sales_data_{timestamp}.xlsx"
            top_n = int(self.top_n_var.get())
            metric = self.metric_var.get()
            self.df[metric] = pd.to_numeric(self.df[metric], errors='coerce').fillna(0)
            top_products = self.df.nlargest(top_n, metric)
            top_products.to_excel(excel_filename, index=False)
            
            messagebox.showinfo("Success", f"Charts exported to {filename}\nData exported to {excel_filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")

def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = SalesAnalysisApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()