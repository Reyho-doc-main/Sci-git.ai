from fpdf import FPDF
import os
import pandas as pd
from settings import UITheme

class PDFReport(FPDF):
    def __init__(self):
        super().__init__()

        self.add_font(
            "DejaVu", "",
            os.path.join("pdfFonts", "DejaVuSans.ttf"),
            uni=True
        )
        self.add_font(
            "DejaVu", "B",
            os.path.join("pdfFonts", "DejaVuSans-Bold.ttf"),
            uni=True
        )

    def header(self):
        self.set_font('DejaVu', 'B', 12)
        self.cell(0, 10, 'SCI-GIT // AUTOMATED RESEARCH LOG', 0, 1, 'R')
        self.line(10, 20, 200, 20)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVu', '', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def export_to_report(filename, analysis_dict, branch_name, plot_image_path=None):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, f"EXPERIMENTAL REPORT: {branch_name}", ln=True, align='L')
    pdf.ln(5)
    
    if plot_image_path and os.path.exists(plot_image_path):
        pdf.image(plot_image_path, x=10, w=190)
        pdf.ln(5)
    
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "AI ANALYSIS SUMMARY:", ln=True)
    pdf.set_font("DejaVu", "", 11)
    summary_text = analysis_dict.get('summary', 'No summary available.')
    pdf.multi_cell(0, 6, summary_text)
    pdf.ln(5)
    
    anomalies = analysis_dict.get('anomalies', [])
    if anomalies:
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, "DETECTED ANOMALIES:", ln=True)
        pdf.set_font("DejaVu", "", 11)

        for i, item in enumerate(anomalies, start=1):
            pdf.multi_cell(0, 6, f"{i}. {item}")  # wraps
            pdf.ln(1)

    next_steps = analysis_dict.get("next_steps", "")
    if next_steps:
        pdf.ln(2)
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, "NEXT STEPS:", ln=True)
        pdf.set_font("DejaVu", "", 11)
        pdf.multi_cell(0, 6, next_steps)  # wraps

    try:
        pdf.output(filename)
        return True
    except Exception as e:
        print(f"PDF Generation Error: {e}")
        return False

class DiffEngine:
    @staticmethod
    def compute_diff(file_path_a, file_path_b):
        """
        Compares two CSV files and returns a list of styled lines for Pygame.
        Returns: List of (text, color) tuples.
        """
        try:
            df_a = pd.read_csv(file_path_a)
            df_b = pd.read_csv(file_path_b)
        except Exception as e:
            return [("Error reading files for diff.", (255, 0, 0))]

        lines = []
        
        # 1. Header Comparison
        cols_a = set(df_a.columns)
        cols_b = set(df_b.columns)
        
        added_cols = cols_b - cols_a
        removed_cols = cols_a - cols_b
        
        if added_cols:
            lines.append((f"++ ADDED COLUMNS: {', '.join(added_cols)}", (0, 255, 0)))
        if removed_cols:
            lines.append((f"-- REMOVED COLUMNS: {', '.join(removed_cols)}", (255, 50, 50)))
        
        # 2. Row Comparison (Key-based if 'id' exists, else Index-based)
        max_rows = max(len(df_a), len(df_b))
        
        # Limit diff to 50 rows to prevent UI lag
        limit = min(max_rows, 50) 
        
        lines.append(("--- ROW COMPARISON (First 50) ---", UITheme.TEXT_DIM))
        
        for i in range(limit):
            # Case 1: Row exists in both
            if i < len(df_a) and i < len(df_b):
                row_a = df_a.iloc[i]
                row_b = df_b.iloc[i]
                
                # Check for differences
                diffs = []
                for col in df_a.columns:
                    if col in df_b.columns:
                        val_a = str(row_a[col])
                        val_b = str(row_b[col])
                        if val_a != val_b:
                            diffs.append(f"{col}: {val_a}->{val_b}")
                
                if diffs:
                    lines.append((f"MOD ROW {i}: " + ", ".join(diffs), (255, 200, 0)))
                # Else: Row is identical, don't show (cleaner)

            # Case 2: Row added in B
            elif i >= len(df_a):
                row_str = ", ".join([str(x) for x in df_b.iloc[i].values])
                lines.append((f"++ NEW ROW {i}: {row_str[:50]}...", (0, 255, 0)))

            # Case 3: Row removed in B (exists in A)
            elif i >= len(df_b):
                row_str = ", ".join([str(x) for x in df_a.iloc[i].values])
                lines.append((f"-- DEL ROW {i}: {row_str[:50]}...", (255, 50, 50)))

        if max_rows > 50:
            lines.append((f"... ({max_rows - 50} more rows hidden)", UITheme.TEXT_DIM))
            
        return lines