import matplotlib
matplotlib.use('Agg') # Non-interactive backend (Thread-safe)
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import seaborn as sns
import pandas as pd
import re

# --- HEADER SCANNER ---
class HeaderScanner:
    @staticmethod
    def detect_temp_unit(df):
        for col in df.columns:
            if re.search(r'(_|\()C(\)|$)|Celsius', col, re.IGNORECASE):
                return 'C', col
            if re.search(r'(_|\()F(\)|$)|Fahrenheit', col, re.IGNORECASE):
                return 'F', col
        return None, None

    @staticmethod
    def convert_column(df, col_name, to_unit):
        if to_unit == 'C':
            df[col_name] = (df[col_name] - 32) * 5.0/9.0
            new_col = re.sub(r'F(ahrenheit)?', 'C', col_name, flags=re.IGNORECASE)
            df.rename(columns={col_name: new_col}, inplace=True)
        elif to_unit == 'F':
            df[col_name] = (df[col_name] * 9.0/5.0) + 32
            new_col = re.sub(r'C(elsius)?', 'F', col_name, flags=re.IGNORECASE)
            df.rename(columns={col_name: new_col}, inplace=True)
        return df

def create_seaborn_surface(df1, df2=None, width=400, height=300, x_col=None, y_col=None):
    """
    Generates a Seaborn plot as RAW BYTES (Thread-safe).
    Returns: (raw_buffer, size_tuple, context_dict)
    """
    fig = Figure(figsize=(width/80, height/80), dpi=80, facecolor='#16161a')
    try:
        # DPI=80 matches the previous sizing logic
        canvas = FigureCanvasAgg(fig)
        
        context = {
            "type": "single",
            "df": df1, # Note: Passing DF back in context is okay for read-only
            "x_col": x_col,
            "y_col": y_col,
            "overlay": False
        }

        line_colors = ['#ff7800', '#00d4ff']
        
        if df2 is None:
            # --- SINGLE MODE ---
            ax = fig.add_subplot(111)
            ax.set_facecolor('#0d0d0f')
            
            # Auto-select columns
            numeric_cols = df1.select_dtypes(include=['number']).columns
            final_x = x_col if x_col and x_col in numeric_cols else (numeric_cols[0] if len(numeric_cols) > 0 else None)
            final_y = y_col if y_col and y_col in numeric_cols else (numeric_cols[1] if len(numeric_cols) > 1 else None)
            
            context["x_col"] = final_x
            context["y_col"] = final_y

            if final_x and final_y:
                sns.lineplot(data=df1, x=final_x, y=final_y, ax=ax, color=line_colors[0], linewidth=2)
                ax.set_title(f"{final_x} vs {final_y}", color=line_colors[0], fontsize=10, family='monospace')
            else:
                ax.text(0.5, 0.5, "INSUFFICIENT DATA", color='gray', ha='center', va='center')
                
        else:
            # --- DUAL MODE ---
            context["type"] = "dual"
            cols1 = df1.select_dtypes(include=['number']).columns
            cols2 = df2.select_dtypes(include=['number']).columns
            common_cols = [c for c in cols1 if c in cols2]
            
            use_x = x_col if x_col in common_cols else (common_cols[0] if len(common_cols)>0 else None)
            use_y = y_col if y_col in common_cols else (common_cols[1] if len(common_cols)>1 else None)
            
            if use_x and use_y:
                # OVERLAY
                context["overlay"] = True
                context["x_col"] = use_x
                context["y_col"] = use_y
                
                ax = fig.add_subplot(111)
                ax.set_facecolor('#0d0d0f')
                sns.lineplot(data=df1, x=use_x, y=use_y, ax=ax, color=line_colors[0], linewidth=2, label="Primary")
                sns.lineplot(data=df2, x=use_x, y=use_y, ax=ax, color=line_colors[1], linewidth=2, label="Secondary")
                ax.set_title("COMPARATIVE OVERLAY", color='#ffffff', fontsize=10, family='monospace')
                ax.legend(facecolor='#16161a', edgecolor='#333333', labelcolor='white')
            else:
                # SIDE BY SIDE
                context["overlay"] = False
                ax1 = fig.add_subplot(211)
                ax1.set_facecolor('#0d0d0f')
                if len(cols1) >= 2:
                    sns.lineplot(data=df1, x=cols1[0], y=cols1[1], ax=ax1, color=line_colors[0])
                
                ax2 = fig.add_subplot(212)
                ax2.set_facecolor('#0d0d0f')
                if len(cols2) >= 2:
                    sns.lineplot(data=df2, x=cols2[0], y=cols2[1], ax=ax2, color=line_colors[1])
                
                fig.tight_layout()

        # Styling
        for ax in fig.axes:
            ax.tick_params(colors='#888888', labelsize=8)
            for spine in ax.spines.values():
                spine.set_edgecolor('#333333')

        # RENDER TO BYTES (Crucial Step)
        canvas.draw()
        raw_string = canvas.buffer_rgba()
        size = canvas.get_width_height()
        
        return raw_string, size, context

    except Exception as e:
        print(f"Plotting Error: {e}")
        return None, (width, height), None