#!/usr/bin/env python3
"""
Canary Deployment Validation Script for Hybrid Model Strategy
Validates that GLM-4.5 configuration is properly deployed and functional.
"""

import json
import subprocess
import sys
from pathlib import Path
import yaml

class CanaryValidator:
    def __init__(self):
        self.claude_dir = Path.cwd() / ".claude"
        self.project_root = Path.cwd()
        self.issues = []
        self.passed = 0
        self.failed = 0
    
    def validate_custom_modes_config(self) -> bool:
        """Validate that custom_modes.yml has GLM-4.5 configured for all roles."""
        custom_modes_file = self.claude_dir / "custom_modes.yml"
        
        if not custom_modes_file.exists():
            self.issues.append("❌ custom_modes.yml not found")
            return False
        
        try:
            with open(custom_modes_file, 'r') as f:
                config = yaml.safe_load(f)
            
            expected_roles = ["architect", "orchestrator", "implementer", "critic", "integrator"]
            all_configured = True
            
            for mode in config.get('customModes', []):
                slug = mode.get('slug')
                model = mode.get('model')
                
                if slug in expected_roles:
                    if model == "glm-4.5":
                        print(f"✅ {slug}: correctly configured with glm-4.5")
                        self.passed += 1
                    else:
                        print(f"❌ {slug}: has model '{model}' instead of 'glm-4.5'")
                        self.issues.append(f"Role {slug} has wrong model: {model}")
                        all_configured = False
                        self.failed += 1
            
            if all_configured:
                print("✅ All roles configured with GLM-4.5")
                return True
            else:
                return False
                
        except Exception as e:
            self.issues.append(f"Error reading custom_modes.yml: {e}")
            return False
    
    def validate_model_config(self) -> bool:
        """Validate global model configuration exists and has correct settings."""
        model_config_file = self.project_root / ".claude" / "model-config.json"
        
        if not model_config_file.exists():
            self.issues.append("❌ model-config.json not found")
            return False
        
        try:
            with open(model_config_file, 'r') as f:
                config = json.load(f)
            
            # Check global defaults
            global_defaults = config.get('globalDefaults', {})
            if global_defaults.get('model') == 'glm-4.5':
                print("✅ Global default model set to glm-4.5")
                self.passed += 1
            else:
                print(f"❌ Global default model is '{global_defaults.get('model')}' instead of 'glm-4.5'")
                self.issues.append("Global default model not set to glm-4.5")
                self.failed += 1
                return False
            
            # Check hybrid config
            hybrid_config = config.get('hybridModelConfig', {})
            if hybrid_config.get('primaryModel') == 'glm-4.5':
                print("✅ Hybrid primary model set to glm-4.5")
                self.passed += 1
            else:
                print(f"❌ Hybrid primary model is '{hybrid_config.get('primaryModel')}'")
                self.issues.append("Hybrid primary model not set to glm-4.5")
                self.failed += 1
                return False
            
            if hybrid_config.get('premiumModel') == 'claude-4.1-opus':
                print("✅ Hybrid premium model set to claude-4.1-opus")
                self.passed += 1
            else:
                print(f"❌ Hybrid premium model is '{hybrid_config.get('premiumModel')}'")
                self.issues.append("Hybrid premium model not set to claude-4.1-opus")
                self.failed += 1
                return False
            
            return True
            
        except Exception as e:
            self.issues.append(f"Error reading model-config.json: {e}")
            return False
    
    def validate_monitoring_system(self) -> bool:
        """Validate that monitoring script exists and can run."""
        monitor_script = self.project_root / "scripts" / "model-usage-monitor.py"
        
        if not monitor_script.exists():
            self.issues.append("❌ model-usage-monitor.py not found")
            return False
        
        try:
            # Test if script can run
            result = subprocess.run([
                sys.executable, str(monitor_script), "report"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Monitoring script runs successfully")
                self.passed += 1
                return True
            else:
                print(f"❌ Monitoring script failed: {result.stderr}")
                self.issues.append(f"Monitoring script error: {result.stderr}")
                self.failed += 1
                return False
                
        except Exception as e:
            self.issues.append(f"Error running monitoring script: {e}")
            return False
    
    def validate_cost_savings_target(self) -> bool:
        """Check if we're meeting cost savings targets."""
        monitor_script = self.project_root / "scripts" / "model-usage-monitor.py"
        
        try:
            result = subprocess.run([
                sys.executable, str(monitor_script)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Log a test event and then check savings
                result = subprocess.run([
                    sys.executable, str(monitor_script), "report"
                ], capture_output=True, text=True, timeout=30)
                
                if "✅ Meeting savings target!" in result.stdout:
                    print("✅ Cost savings target being met")
                    self.passed += 1
                    return True
                else:
                    print("❌ Not meeting cost savings target")
                    self.issues.append("Cost savings target not met")
                    self.failed += 1
                    return False
            else:
                return False
                
        except Exception as e:
            self.issues.append(f"Error validating cost savings: {e}")
            return False
    
    def run_validation(self) -> bool:
        """Run all validation checks."""
        print("🚀 Starting Canary Deployment Validation")
        print("=" * 50)
        
        checks = [
            ("Custom Modes Configuration", self.validate_custom_modes_config),
            ("Model Configuration", self.validate_model_config),
            ("Monitoring System", self.validate_monitoring_system),
            ("Cost Savings Target", self.validate_cost_savings_target)
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            print(f"\n📋 {check_name}:")
            if not check_func():
                all_passed = False
        
        print("\n📊 Validation Summary:")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Total Checks: {self.passed + self.failed}")
        
        if self.issues:
            print("\n🚨 Issues Found:")
            for issue in self.issues:
                print(f"  • {issue}")
        
        if all_passed:
            print("\n🎉 Canary deployment validation PASSED!")
            print("✅ Hybrid model strategy is ready for production")
            return True
        else:
            print("\n⚠️  Canary deployment validation FAILED")
            print("❌ Issues must be resolved before proceeding")
            return False

def main():
    """Main execution function."""
    validator = CanaryValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()