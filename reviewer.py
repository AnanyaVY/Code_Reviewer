"""
Code review logic combining static analysis and AI analysis.
Handles pylint, bandit, ESLint, and Hugging Face CodeT5 integration.
"""
import subprocess
import tempfile
import os
import json
import logging
from typing import Dict, List, Any
import streamlit as st
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_code_review_prompt(code: str, language: str) -> str:
    prompt = f"""Review this {language} code and provide:
1. Brief summary of what the code does
2. Readability suggestions 
3. Potential bugs
4. Security concerns
5. Refactoring suggestions

Code:
{code}

REVIEW:"""
    return prompt

def call_huggingface_model(prompt: str) -> str:
    try:
        from transformers import pipeline
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        generator = pipeline(
            "text2text-generation",
            model="Salesforce/codet5-base",
            device=0 if torch.cuda.is_available() else -1
        )
        
        short_prompt = prompt[:1000] + "\nREVIEW:"
        result = generator(
            short_prompt,
            max_length=512,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True
        )
        
        feedback = result[0]['generated_text']
        if "REVIEW:" in feedback:
            feedback = feedback.split("REVIEW:")[-1].strip()
        
        return feedback if feedback else "AI model generated no specific feedback."
        
    except ImportError:
        return "PyTorch/Transformers not available. Install with: pip install torch transformers"
    except Exception as e:
        return f"AI analysis failed: {str(e)}"

class CodeReviewer:
    def __init__(self):
        self.supported_languages = ["Python", "JavaScript"]

    def run_pylint_analysis(self, code: str) -> Dict[str, Any]:
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['pylint', temp_file, '--output-format=json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            pylint_results = []
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            pylint_results.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            
            return {
                "success": True,
                "results": pylint_results,
                "raw_output": result.stdout,
                "errors": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Pylint timed out", "results": []}
        except FileNotFoundError:
            return {"success": False, "error": "pylint not found. Run: pip install pylint", "results": []}
        except Exception as e:
            return {"success": False, "error": str(e), "results": []}
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)

    def run_bandit_analysis(self, code: str) -> Dict[str, Any]:
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['bandit', '-f', 'json', '-r', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            bandit_results = {}
            if result.stdout.strip():
                try:
                    bandit_results = json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass
            
            return {
                "success": True,
                "results": bandit_results,
                "raw_output": result.stdout,
                "errors": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Bandit timed out", "results": {}}
        except FileNotFoundError:
            return {"success": False, "error": "bandit not found. Run: pip install bandit", "results": {}}
        except Exception as e:
            return {"success": False, "error": str(e), "results": {}}
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)

    def run_eslint_analysis(self, code: str) -> Dict[str, Any]:
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['npx', 'eslint', temp_file, '--format=json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            eslint_results = []
            if result.stdout.strip():
                try:
                    eslint_results = json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass
            
            return {
                "success": True,
                "results": eslint_results,
                "raw_output": result.stdout,
                "errors": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "ESLint timed out", "results": []}
        except FileNotFoundError:
            return {"success": False, "error": "ESLint/Node not found. Install Node.js + npm install -g eslint", "results": []}
        except Exception as e:
            return {"success": False, "error": str(e), "results": []}
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)

    def run_static_analysis(self, code: str, language: str) -> Dict[str, Any]:
        results = {
            "language": language,
            "pylint": None,
            "bandit": None,
            "eslint": None
        }
        
        if language == "Python":
            st.info("🔍 Running Pylint + Bandit...")
            results["pylint"] = self.run_pylint_analysis(code)
            results["bandit"] = self.run_bandit_analysis(code)
        elif language == "JavaScript":
            st.info("🔍 Running ESLint...")
            results["eslint"] = self.run_eslint_analysis(code)
        
        return results

    def run_ai_analysis(self, code: str, language: str) -> Dict[str, Any]:
        try:
            st.info("🤖 Running CodeT5 AI analysis...")
            prompt = create_code_review_prompt(code, language)
            ai_feedback = call_huggingface_model(prompt)
            
            return {
                "success": True,
                "feedback": ai_feedback,
                "model_used": "Salesforce/codet5-base"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "feedback": "AI analysis unavailable"
            }

    def review_code(self, code: str, language: str) -> Dict[str, Any]:
        if not code.strip():
            return {"error": "No code provided", "static_analysis": {}, "ai_analysis": {}}
        
        if language not in self.supported_languages:
            return {
                "error": f"Unsupported language: {language}",
                "static_analysis": {},
                "ai_analysis": {}
            }
        
        static_results = self.run_static_analysis(code, language)
        ai_results = self.run_ai_analysis(code, language)
        
        return {
            "language": language,
            "static_analysis": static_results,
            "ai_analysis": ai_results,
            "timestamp": str(pd.Timestamp.now())
        }
