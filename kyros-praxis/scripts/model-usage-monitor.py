#!/usr/bin/env python3
"""
Model Usage Monitoring Script for Hybrid Model Strategy
Tracks GLM-4.5 and Claude 4.1 Opus usage patterns, costs, and performance metrics.
"""

import json
import time
import datetime
from pathlib import Path
from typing import Dict, List, Any
import subprocess
import sys
from zoneinfo import ZoneInfo

class ModelUsageMonitor:
    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or Path.home() / ".claude" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.usage_log = self.log_dir / "model_usage.jsonl"
        self.metrics_file = self.log_dir / "model_metrics.json"
        
    def log_model_usage(self, 
                       model: str, 
                       role: str, 
                       task_type: str, 
                       tokens_estimated: int = None,
                       duration_seconds: float = None,
                       cost_usd: float = None):
        """Log a model usage event for cost tracking and analysis."""
        
        usage_event = {
            "timestamp": datetime.datetime.now(ZoneInfo("UTC")).isoformat(),
            "model": model,
            "role": role,
            "task_type": task_type,
            "tokens_estimated": tokens_estimated,
            "duration_seconds": duration_seconds,
            "cost_usd": cost_usd or self._estimate_cost(model, tokens_estimated or 1000)
        }
        
        with open(self.usage_log, "a") as f:
            f.write(json.dumps(usage_event) + "\n")
    
    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estimate cost in USD based on model and token count."""
        # Current pricing estimates (update as needed)
        pricing = {
            "glm-4.5": 0.002,  # $0.002 per 1K tokens
            "claude-4.1-opus": 0.015,  # $0.015 per 1K tokens
            "openrouter/sonoma-sky-alpha": 0.001
        }
        return (pricing.get(model, 0.005) * tokens) / 1000
    
    def get_usage_summary(self, days: int = 30) -> Dict[str, Any]:
        """Generate usage summary for the last N days."""
        cutoff_date = datetime.datetime.now(ZoneInfo("UTC")) - datetime.timedelta(days=days)
        summary = {
            "total_cost_usd": 0.0,
            "total_tokens": 0,
            "model_usage": {},
            "role_usage": {},
            "daily_usage": {}
        }
        
        if not self.usage_log.exists():
            return summary
        
        with open(self.usage_log, "r") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    event_date = datetime.datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                    
                    if event_date < cutoff_date:
                        continue
                    
                    # Update totals
                    summary["total_cost_usd"] += event["cost_usd"]
                    summary["total_tokens"] += event["tokens_estimated"] or 0
                    
                    # Model usage
                    model = event["model"]
                    summary["model_usage"][model] = summary["model_usage"].get(model, 0) + event["cost_usd"]
                    
                    # Role usage
                    role = event["role"]
                    summary["role_usage"][role] = summary["role_usage"].get(role, 0) + event["cost_usd"]
                    
                    # Daily usage
                    day_key = event_date.strftime("%Y-%m-%d")
                    summary["daily_usage"][day_key] = summary["daily_usage"].get(day_key, 0) + event["cost_usd"]
                    
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        
        return summary
    
    def get_cost_savings_analysis(self) -> Dict[str, Any]:
        """Analyze cost savings compared to all-Claude 4.1 Opus scenario."""
        summary = self.get_usage_summary(30)
        
        # Calculate what this would cost with all Claude 4.1 Opus
        claude_cost = summary["total_tokens"] * 0.015 / 1000
        actual_cost = summary["total_cost_usd"]
        savings = claude_cost - actual_cost
        savings_percentage = (savings / claude_cost * 100) if claude_cost > 0 else 0
        
        return {
            "actual_cost_usd": actual_cost,
            "all_claude_cost_usd": claude_cost,
            "savings_usd": savings,
            "savings_percentage": savings_percentage,
            "glm_usage_percentage": summary["model_usage"].get("glm-4.5", 0) / actual_cost * 100 if actual_cost > 0 else 0,
            "target_savings_percentage": 35.0
        }
    
    def print_daily_report(self):
        """Print a daily usage report."""
        savings_analysis = self.get_cost_savings_analysis()
        summary = self.get_usage_summary(1)
        
        print(f"\n📊 Daily Model Usage Report")
        print(f"=" * 50)
        print(f"Date: {datetime.datetime.now(ZoneInfo('UTC')).strftime('%Y-%m-%d')}")
        print(f"Total Cost Today: ${summary['total_cost_usd']:.4f}")
        print(f"Total Tokens: {summary['total_tokens']:,}")
        
        print(f"\n📈 Model Distribution:")
        for model, cost in summary["model_usage"].items():
            percentage = (cost / summary["total_cost_usd"] * 100) if summary["total_cost_usd"] > 0 else 0
            print(f"  {model}: ${cost:.4f} ({percentage:.1f}%)")
        
        print(f"\n💰 Cost Savings Analysis (30-day):")
        print(f"  Actual Cost: ${savings_analysis['actual_cost_usd']:.2f}")
        print(f"  All-Claude Cost: ${savings_analysis['all_claude_cost_usd']:.2f}")
        print(f"  Savings: ${savings_analysis['savings_usd']:.2f} ({savings_analysis['savings_percentage']:.1f}%)")
        print(f"  GLM Usage: {savings_analysis['glm_usage_percentage']:.1f}%")
        print(f"  Target Savings: {savings_analysis['target_savings_percentage']:.1f}%")
        
        # Check if meeting targets
        if savings_analysis['savings_percentage'] >= savings_analysis['target_savings_percentage']:
            print(f"  ✅ Meeting savings target!")
        else:
            print(f"  ⚠️  Below savings target")

def main():
    """Main execution function."""
    monitor = ModelUsageMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        monitor.print_daily_report()
    else:
        # Log a sample usage event for testing
        monitor.log_model_usage(
            model="glm-4.5",
            role="implementer",
            task_type="code_review",
            tokens_estimated=2500,
            duration_seconds=45.2
        )
        print("✅ Logged sample model usage event")

if __name__ == "__main__":
    main()