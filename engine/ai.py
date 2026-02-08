import os
import json
import pandas as pd
from pydantic import BaseModel, field_validator
from typing import List, Any
from openai import AzureOpenAI
from dotenv import load_dotenv
from state_manager import state

load_dotenv()

class ExperimentSchema(BaseModel):
    summary: str
    anomalies: List[str]
    next_steps: str
    is_reproducible: bool
    ai_generated: bool = True

    @field_validator('next_steps', mode='before')
    @classmethod
    def flatten_list_to_string(cls, v: Any) -> str:
        if isinstance(v, list):
            return " ".join(str(x) for x in v)
        return str(v) if v is not None else ""

class ScienceAI:
    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        # Default fallback
        self.default_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-nano")
        
        if not self.api_key: print("DEBUG: AI Key Missing")
        if not self.endpoint: print("DEBUG: AI Endpoint Missing")

        self.client = None
        if self.api_key and self.endpoint:
            try:
                self.client = AzureOpenAI(
                    api_key=self.api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint
                )
            except Exception as e:
                print(f"AI Connection Failed: {e}")
                self.client = None

    def get_placeholder_analysis(self, csv_path: str) -> ExperimentSchema:
        """Fast, local analysis for immediate UI feedback without AI lag."""
        try:
            df = pd.read_csv(csv_path)
            cols = len(df.columns)
            rows = len(df)
            summary = f"File imported successfully. Contains {rows} rows and {cols} columns. Click 'ANALYZE' to run AI diagnostics."
        except:
            summary = "File imported. Pending analysis."
            
        return ExperimentSchema(
            summary=summary,
            anomalies=[],
            next_steps="Select this node and click ANALYZE to generate insights.",
            is_reproducible=True,
            ai_generated=False
        )

    def analyze_csv_data(self, csv_path: str, model: str = "gpt-5-mini") -> ExperimentSchema:
        df = pd.read_csv(csv_path)
        if df.empty or len(df.columns) < 2 or len(df) < 3:
            return ExperimentSchema(
                summary="Insufficient data for analysis.",
                anomalies=["INSUFFICIENT_DATA"],
                next_steps="Upload a more comprehensive dataset.",
                is_reproducible=False
            )
        
        if state.stop_ai_requested:
            state.stop_ai_requested = False
            return self._local_analysis(df)
        
        if self.client:
            try:
                csv_snippet = df.head(15).to_csv()
                prompt = f"Analyze this experimental data and return JSON:\n{csv_snippet}"
                response = self.client.chat.completions.create(
                    model=model, # Use Mini for single files
                    messages=[
                        {"role": "system", "content": "You are a scientific data analyzer. Return strictly valid JSON with keys: summary, anomalies (list of strings), next_steps (single string), is_reproducible (bool)."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                data = json.loads(response.choices[0].message.content)
                data["ai_generated"] = True
                return ExperimentSchema(**data)
            except Exception as e:
                print(f"AI Error: {e}")
        
        return self._local_analysis(df)

    def compare_experiments(self, df1: pd.DataFrame, df2: pd.DataFrame) -> dict:
        numeric_cols = df1.select_dtypes(include=['number']).columns.intersection(df2.select_dtypes(include=['number']).columns)
        if len(numeric_cols) == 0: return {"summary": "NO COMMON DATA", "anomalies": []}

        stats1 = df1[numeric_cols].describe().to_json()
        stats2 = df2[numeric_cols].describe().to_json()

        if self.client:
            try:
                prompt = f"Compare Parent (A) vs Child (B) stats:\nA: {stats1}\nB: {stats2}\nIdentify drift. Return JSON: {{summary, anomalies}}."
                response = self.client.chat.completions.create(
                    model="gpt-5-mini", # Use Mini for comparison too
                    messages=[{"role": "system", "content": "Concise delta analysis."}, {"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception: pass
        return self._local_comparison(df1, df2, numeric_cols)

    def analyze_branch_history(self, history_text: str) -> str:
        """Generates a narrative change log for a branch using NANO."""
        if not self.client: return "AI OFFLINE: Cannot generate branch report."
        
        try:
            prompt = f"Here is the commit history of a scientific experiment branch:\n{history_text}\n\nWrite a concise 'Evolutionary Report' summarizing how the experiment changed over time."
            response = self.client.chat.completions.create(
                model="gpt-5-nano", # Keep Nano for broad project analysis
                messages=[{"role": "system", "content": "You are a research historian."}, {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating report: {e}"

    def _local_analysis(self, df):
        cols = df.select_dtypes(include=['number']).columns
        return ExperimentSchema(
            summary=f"Local Analysis: {len(cols)} numeric columns detected. AI unavailable.", 
            anomalies=[], 
            next_steps="Check AI connection or API Key.", 
            is_reproducible=True, 
            ai_generated=False
        )

    def _local_comparison(self, df1, df2, cols):
        return {"summary": "AI Offline. Manual comparison required.", "anomalies": []}