from fpdf import FPDF
import json
import os

def export_to_report(filename, analysis_dict, branch_name, plot_image_path=None):
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Courier", "B", 16)
    pdf.cell(0, 10, f"SCI-GIT REPORT: {branch_name}", ln=True, align='C')
    pdf.ln(10)
    
    # Image (Chart)
    if plot_image_path and os.path.exists(plot_image_path):
        # Keep aspect ratio, width=150mm
        pdf.image(plot_image_path, x=30, w=150)
        pdf.ln(5)
    
    # Summary
    pdf.set_font("Courier", "", 12)
    pdf.multi_cell(0, 10, f"SUMMARY:\n{analysis_dict.get('summary', 'N/A')}")
    pdf.ln(10)
    
    # Anomalies
    pdf.set_font("Courier", "B", 12)
    pdf.cell(0, 10, "ANOMALIES DETECTED:", ln=True)
    pdf.set_font("Courier", "", 12)
    for item in analysis_dict.get('anomalies', []):
        pdf.cell(0, 10, f"- {item}", ln=True)
        
    pdf.output(filename)
    return True