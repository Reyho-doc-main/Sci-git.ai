import matplotlib
matplotlib.use('Agg')  # <--- CRITICAL: Must be at the very top
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import seaborn as sns
import io
import pygame
import pandas as pd
from settings import UITheme

def create_seaborn_surface(df, width=400, height=300):
    """Generates a Seaborn plot safely in a background thread."""
    try:
        # 1. Create Figure without using pyplot (thread-safe)
        fig = Figure(figsize=(width/80, height/80), dpi=80, facecolor='#16161a')
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        ax.set_facecolor('#0d0d0f')

        # 2. Logic: Plot first two numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) >= 2:
            sns.lineplot(data=df, x=numeric_cols[0], y=numeric_cols[1], 
                         ax=ax, color='#ff7800', linewidth=2)
            ax.set_title(f"ANALYSIS: {numeric_cols[0]} vs {numeric_cols[1]}", 
                         color='#ff7800', fontsize=10, family='monospace')
        else:
            ax.text(0.5, 0.5, "INSUFFICIENT DATA", color='gray', ha='center', va='center')

        # 3. Style the axes
        ax.tick_params(colors='#888888', labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor('#333333')

        # 4. Render to a buffer
        canvas.draw()
        rgba_buffer = canvas.buffer_rgba()
        
        # 5. Convert to Pygame Surface
        return pygame.image.frombuffer(rgba_buffer, canvas.get_width_height(), "RGBA")
    except Exception as e:
        print(f"Plotting Error: {e}")
        # Return a fallback empty surface so the app doesn't crash
        surf = pygame.Surface((width, height))
        surf.fill((30, 30, 35))
        return surf