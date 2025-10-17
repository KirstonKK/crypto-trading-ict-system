"""
Trading System Application Launcher
Coordinates ICT Monitor and Bybit Demo Trading
"""

import asyncio
import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class TradingSystemLauncher:
    """Coordinates the launch of all trading system components"""
    
    def __init__(self, config):
        self.config = config
        self.ict_process: Optional[subprocess.Popen] = None
        self.demo_process: Optional[subprocess.Popen] = None
        
    def start(self):
        """Start the complete trading system"""
        logger.info("🚀 Launching Kirston's Trading Algorithm")
        logger.info("=" * 50)
        
        try:
            # Start ICT Enhanced Monitor
            self._start_ict_monitor()
            
            # Wait for ICT Monitor to be ready
            self._wait_for_ict_monitor()
            
            # Start Bybit Demo Trading
            self._start_demo_trading()
            
            # Keep running
            self._monitor_processes()
            
        except Exception as e:
            logger.error(f"💥 Failed to start trading system: {e}")
            self.stop()
            raise
    
    def _start_ict_monitor(self):
        """Start ICT Enhanced Monitor"""
        logger.info("🔄 Starting ICT Enhanced Monitor...")
        
        ict_script = Path(__file__).parent.parent / 'monitors' / 'ict_enhanced_monitor.py'
        
        self.ict_process = subprocess.Popen([
            'python3', str(ict_script)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info(f"✅ ICT Monitor started (PID: {self.ict_process.pid})")
    
    def _wait_for_ict_monitor(self):
        """Wait for ICT Monitor to be ready"""
        import requests
        
        logger.info("⏳ Waiting for ICT Monitor to be ready...")
        
        for attempt in range(30):  # 30 seconds timeout
            try:
                response = requests.get(f'http://localhost:{self.config.ICT_MONITOR_PORT}/health', timeout=2)
                if response.status_code == 200:
                    logger.info("✅ ICT Monitor is ready!")
                    return
            except:
                pass
            
            time.sleep(1)
        
        raise Exception("ICT Monitor failed to start within 30 seconds")
    
    def _start_demo_trading(self):
        """Start Bybit Demo Trading System"""
        logger.info("🔄 Starting Bybit Demo Trading...")
        
        demo_script = Path(__file__).parent.parent / 'trading' / 'demo_trading_system.py'
        
        self.demo_process = subprocess.Popen([
            'python3', str(demo_script)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info(f"✅ Demo Trading started (PID: {self.demo_process.pid})")
    
    def _monitor_processes(self):
        """Monitor running processes"""
        logger.info("👀 Monitoring trading system processes...")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                # Check if processes are still running
                if self.ict_process and self.ict_process.poll() is not None:
                    logger.error("💥 ICT Monitor process died!")
                    break
                    
                if self.demo_process and self.demo_process.poll() is not None:
                    logger.error("💥 Demo Trading process died!")
                    break
                
                time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("👋 Shutdown requested")
    
    def stop(self):
        """Stop all processes"""
        logger.info("🛑 Stopping trading system...")
        
        if self.demo_process:
            self.demo_process.terminate()
            logger.info("✅ Demo Trading stopped")
            
        if self.ict_process:
            self.ict_process.terminate() 
            logger.info("✅ ICT Monitor stopped")
        
        logger.info("👋 Trading system stopped")