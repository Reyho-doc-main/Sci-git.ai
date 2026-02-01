# Sci-git.ai

## Overview
**sci-git.ai** is a prototype desktop application designed to help student researchers track, compare, and understand their experiments in a structured, version-controlled way.

Instead of treating experiments as isolated files or notebook entries, sci-git.ai organises them into a meaningful experiment history. By combining structured experiment logging with lightweight AI assistance, the system reduces confusion, highlights inconsistencies, and encourages better documentation and reproducibility in research work.

---

## Problem Statement
In research labs, experiments are often repeated multiple times with small changes in parameters, conditions, or setup. However, tracking these experiment histories is challenging:
- Records are scattered across notebooks or files.
- Version control tools exist but are not designed for experimental data.
- Students and researchers struggle to compare results, identify inconsistencies, or understand changes over time.

This often leads to:
- Repeated work  
- Confusion when results differ  
- Difficulty sharing experiment history within a team  

---

## Proposed Solution
sci-git.ai provides a **version-controlled experiment database** with AI-powered assistance.

### Key Features
- **Experiment Logging**: Assists in recording the experiment name, purpose, parameters, results, and notes, with a consistent format
- **Version Control**: Each experiment is treated as a version, enabling structured history tracking.  
- **Comparison Engine**: Highlights differences in parameters/results when similar experiments are detected.  
- **Visual Insights**: Generate plots and comparisons to identify trends or anomalies.

---

## AI Assistance
AI in sci-git.ai can:
- Suggest similar past experiments  
- Generate short summaries  
- Assist in creating structured experiment logs  

⚠️ **Note**: The AI does not make scientific conclusions, it only helps users understand experiment history and the purpose behind experiments, and will only assist in the discovery and research of science.

---

## Target Users
- **Primary Users**: Undergraduate research students, Final Year Project students  
- **Secondary Users**: Supervisors and researchers

By focusing on students, sci-git.ai helps them:
- Track experiments more effectively  
- Develop better reasoning and documentation habits  
- Learn real-world skills in experiment management  

---

## Feasibility
sci-git.ai will be developed as a simple desktop prototype application. The initial implementation will focus on saving experiment records, listing experiment versions, comparing experiments, and generating basic AI summaries. Functionality will be prioritised over advanced interface design to keep the scope realistic. 

---

## Summary
sci-git.ai proposes a practical tool for recording and comparing experiment histories. By keeping the system simple and focused, it provides an accessible way for student researchers to manage experiments and reduce confusion when results differ.

---

## Project Status
This project is currently under active development as a prototype for academic and educational use.

---

## Getting Started
1. Clone the repository:
    ```bash
    git clone https://github.com/Reyho-doc-main/Sci-git.ai.git

2. Navigate into the repository:
    ```bash
    cd Sci-git.ai

3. Install dependencies (to be updated):
    ```bash
    pip install -r requirements.txt

4. Run the application:
    ```bash
    python main.py