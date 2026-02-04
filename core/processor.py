from fpdf import FPDF
import json

def export_to_report(filename, analysis_dict, branch_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", "B", 16)
    pdf.cell(40, 10, f"SCI-GIT RESEARCH REPORT: {branch_name}")
    pdf.ln(20)
    
    pdf.set_font("Courier", "", 12)
    pdf.multi_cell(0, 10, f"SUMMARY:\n{analysis_dict.get('summary', 'N/A')}")
    pdf.ln(10)
    
    pdf.cell(40, 10, "ANOMALIES DETECTED:")
    pdf.ln(10)
    for item in analysis_dict.get('anomalies', []):
        pdf.cell(0, 10, f"- {item}")
        pdf.ln(8)
        
    pdf.output(filename)
    return True