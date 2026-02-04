import os
import json
import pandas as pd
from pydantic import BaseModel, Field
from typing import List, Optional
from openai import AzureOpenAI

class ExperimentSchema(BaseModel):
    summary: str
    anomalies: List[str]
    next_steps: str
    is_reproducible: bool
    ai_generated: bool = True

class ScienceAI:
    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        
        self.client = None
        if self.api_key and self.endpoint:
            try:
                self.client = AzureOpenAI(
                    api_key=self.api_key,
                    api_version="2023-12-01-preview",
                    azure_endpoint=self.endpoint
                )
            except Exception:
                self.client = None

    def analyze_csv_data(self, csv_path: str) -> ExperimentSchema:
        df = pd.read_csv(csv_path)
        
        # If AI is available, attempt smart analysis
        if self.client:
            try:
                csv_snippet = df.head(15).to_csv()
                prompt = f"Analyze this experimental data and return JSON:\n{csv_snippet}"
                
                response = self.client.chat.completions.create(
                    model=self.deployment,
                    messages=[
                        {"role": "system", "content": "You are a scientific data analyzer. Return strictly valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                raw_json = response.choices[0].message.content
                data = json.loads(raw_json)
                data["ai_generated"] = True
                return ExperimentSchema(**data)
            except Exception as e:
                print(f"AI Error: {e}. Falling back to local engine.")
        
        # Fallback Engine: Manual Statistical Analysis
        return self._local_analysis(df)

    def _local_analysis(self, df: pd.DataFrame) -> ExperimentSchema:
        """Standard math-based summary if AI is offline."""
        summary_parts = []
        for col in df.select_dtypes(include=['number']).columns:
            avg = df[col].mean()
            summary_parts.append(f"{col}: mean={avg:.2f}")
            
        return ExperimentSchema(
            summary="LOCAL STATS: " + " | ".join(summary_parts),
            anomalies=["Manual check required: AI offline."],
            next_steps="Repeat experiment to verify variance.",
            is_reproducible=True,
            ai_generated=False
        )