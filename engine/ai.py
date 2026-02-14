# --- FILE: engine/ai.py ---
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

class InconsistencyReport(BaseModel):
    summary: str
    inconsistent_node_ids: List[int]
    anomalies: List[str]
    next_steps: str

class ScienceAI:
    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        self.default_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-nano")
        
        self.client = None
        self._init_client()

    def _init_client(self):
        """Internal method to initialize client from current attributes."""
        if self.api_key and self.endpoint:
            try:
                self.client = AzureOpenAI(
                    api_key=self.api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint
                )
                print("AI Client Initialized.")
            except Exception as e:
                print(f"AI Connection Failed: {e}")
                self.client = None
        else:
            self.client = None

    def configure_client(self, key, endpoint):
        """Allows runtime configuration of credentials."""
        self.api_key = key
        self.endpoint = endpoint
        self._init_client()
        return self.client is not None

    def get_placeholder_analysis(self, csv_path: str) -> ExperimentSchema:
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
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            return ExperimentSchema(summary="Error reading file.", anomalies=["FILE_ERROR"], next_steps="Check file format.", is_reproducible=False, ai_generated=False)

        if df.empty or len(df.columns) < 2 or len(df) < 3:
            return ExperimentSchema(
                summary="Insufficient data for analysis.",
                anomalies=["INSUFFICIENT_DATA"],
                next_steps="Upload a more comprehensive dataset.",
                is_reproducible=False,
                ai_generated=False
            )
        
        if state.stop_ai_requested:
            state.stop_ai_requested = False
            return self._local_analysis(df)
        
        if self.client:
            try:
                csv_snippet = df.head(15).to_csv()
                prompt = f"Analyze this experimental data and return JSON:\n{csv_snippet}"
                response = self.client.chat.completions.create(
                    model=model,
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
                print(f"AI Error (Falling back to local): {e}")
                # Fall through to local analysis
        
        return self._local_analysis(df)

    def generate_simplified_summary(self, csv_path: str) -> ExperimentSchema:
        """Generates a non-technical summary for a SINGLE NODE."""
        try:
            df = pd.read_csv(csv_path)
            csv_snippet = df.head(10).to_csv()
        except Exception:
            return ExperimentSchema(summary="Error reading file.", anomalies=[], next_steps="", is_reproducible=False, ai_generated=False)

        if not self.client:
            return ExperimentSchema(summary="AI Offline. Cannot generate simplified report.", anomalies=[], next_steps="", is_reproducible=False, ai_generated=False)

        try:
            prompt = (
                f"Here is a snippet of scientific data:\n{csv_snippet}\n\n"
                "Explain the significance of this experiment to a 6th grader or non-scientist. "
                "Avoid jargon. Focus on what is being measured and why it might matter. "
                "Return JSON: {summary, anomalies: [], next_steps: '', is_reproducible: true}"
            )
            response = self.client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": "You are a science communicator explaining complex data simply."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            data["ai_generated"] = True
            return ExperimentSchema(**data)
        except Exception as e:
            return ExperimentSchema(summary=f"AI Error: {e}", anomalies=[], next_steps="", is_reproducible=False, ai_generated=False)

    def generate_project_simplified_summary(self, tree_data_text: str) -> ExperimentSchema:
        """Generates a non-technical summary for the WHOLE PROJECT."""
        if not self.client:
            return ExperimentSchema(summary="AI Offline. Cannot generate project report.", anomalies=[], next_steps="", is_reproducible=False, ai_generated=False)

        try:
            prompt = (
                f"Here is the history of a scientific project (list of file versions and branches):\n{tree_data_text}\n\n"
                "Tell the 'story' of this research project to a non-scientist (6th grader level). "
                "Explain how the project started, how it branched out, and what the overall goal (and impact) seems to be based on the file names and experiments done. "
                "Return JSON: {summary, anomalies: [], next_steps: '', is_reproducible: true}"
            )
            response = self.client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": "You are a scientist explaining the history of a science project to some teens interested in what you do. Explain the goals clearly, and the significance of the work."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            data["ai_generated"] = True
            return ExperimentSchema(**data)
        except Exception as e:
            return ExperimentSchema(summary=f"AI Error: {e}", anomalies=[], next_steps="", is_reproducible=False, ai_generated=False)

    def find_inconsistencies(self, tree_data_text: str) -> InconsistencyReport:
        if not self.client:
            return InconsistencyReport(
                summary="AI Offline. Please configure API Key in settings or dropdown.",
                inconsistent_node_ids=[],
                anomalies=["AI_OFFLINE"],
                next_steps="Click AI -> Analyze to configure credentials."
            )
            
        try:
            prompt = (
                f"Analyze this experiment tree history for logical inconsistencies:\n{tree_data_text}\n"
                "Return JSON: {summary, inconsistent_node_ids: [int], anomalies: [str], next_steps: str}"
            )
            response = self.client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": "You are a research auditor. Find logic gaps."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return InconsistencyReport(**data)
        except Exception as e:
            return InconsistencyReport(
                summary=f"Error: {e}",
                inconsistent_node_ids=[],
                anomalies=["API_ERROR"],
                next_steps="Retry later."
            )

    def compare_experiments(self, df1: pd.DataFrame, df2: pd.DataFrame) -> dict:
        numeric_cols = df1.select_dtypes(include=['number']).columns.intersection(df2.select_dtypes(include=['number']).columns)
        if len(numeric_cols) == 0: return {"summary": "NO COMMON DATA", "anomalies": []}

        stats1 = df1[numeric_cols].describe().to_json()
        stats2 = df2[numeric_cols].describe().to_json()

        if self.client:
            try:
                prompt = f"Compare Parent (A) vs Child (B) stats:\nA: {stats1}\nB: {stats2}\nIdentify drift. Return JSON: {{summary, anomalies}}."
                response = self.client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=[{"role": "system", "content": "Concise delta analysis."}, {"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception: pass
        return self._local_comparison(df1, df2, numeric_cols)

    def analyze_branch_history(self, history_text: str) -> str:
        if not self.client: return "AI OFFLINE: Cannot generate branch report."
        try:
            prompt = f"Here is the commit history:\n{history_text}\n\nWrite a concise 'Evolutionary Report'."
            response = self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[{"role": "system", "content": "You are a research historian."}, {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating report: {e}"

    def _local_analysis(self, df):
        """Fallback when AI is offline."""
        cols = df.select_dtypes(include=['number']).columns
        row_count = len(df)
        return ExperimentSchema(
            summary=f"LOCAL MODE: Dataset contains {row_count} rows and {len(cols)} numeric columns. Basic statistical profiling available in plot view.", 
            anomalies=[], 
            next_steps="Connect Azure OpenAI to enable advanced insights.", 
            is_reproducible=True, 
            ai_generated=False
        )

    def _local_comparison(self, df1, df2, cols):
        return {"summary": "AI Offline. Visual comparison only.", "anomalies": []}