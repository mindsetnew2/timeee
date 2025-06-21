import time
import random
import json
import logging
import os
import socket
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
import subprocess
import sys

class TorSeleniumBot:
    def __init__(self):
        self.driver = None
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Generate timestamp for log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"logs/bot_log_{timestamp}.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)  # Real-time terminal output
            ]
        )
        
        print(f"🔧 Logging initialized. Log file: {log_filename}")
        
    def load_urls_config(self, config_file="urls_config.json"):
        """Load URLs from configuration file"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"📁 Loaded URL configuration from {config_file}")
                return config
            else:
                self.logger.warning(f"⚠️  URL config file {config_file} not found. Creating default config.")
                self.create_default_config(config_file)
                return self.load_urls_config(config_file)
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Invalid JSON in {config_file}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error loading URL config: {e}")
            return None
    
    def create_default_config(self, config_file="urls_config.json"):
        """Create a default URL configuration file"""
        default_config = {
            "urls": [
                {
                    "url": "https://httpbin.org/ip",
                    "name": "IP Check Test",
                    "enabled": True
                },
                {
                    "url": "https://httpbin.org/user-agent",
                    "name": "User Agent Test",
                    "enabled": True
                }
            ],
            "settings": {
                "cycles_per_url": 20,
                "min_delay_between_cycles": 5,
                "max_delay_between_cycles": 15,
                "min_reading_time": 2,
                "max_reading_time": 5
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📝 Created default URL configuration file: {config_file}")
    
    def check_tor_running(self, port=9050):
        """Check if Tor is already running on the specified port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def start_tor(self):
        """Start Tor service or check if already running"""
        try:
            # Check if Tor is already running (e.g., in GitHub Actions)
            if os.environ.get('TOR_ALREADY_RUNNING') == 'true':
                self.logger.info("🌐 Tor is already running (detected from environment)")
                if self.check_tor_running():
                    self.logger.info("✅ Tor SOCKS proxy confirmed running on port 9050")
                    return True
                else:
                    self.logger.error("❌ Environment says Tor is running but port 9050 is not accessible")
                    return False
            
            # Check if Tor is already running on port 9050
            if self.check_tor_running():
                self.logger.info("🌐 Tor is already running on port 9050")
                return True
            
            # Try to start Tor service
            self.logger.info("🌐 Starting Tor service...")
            subprocess.run(['sudo', 'service', 'tor', 'start'], check=True, capture_output=True)
            time.sleep(5)  # Wait for Tor to start
            
            # Verify Tor is running
            result = subprocess.run(['sudo', 'service', 'tor', 'status'], capture_output=True, text=True)
            if "active (running)" in result.stdout:
                self.logger.info("✅ Tor service started successfully")
                return True
            else:
                self.logger.error("❌ Tor service failed to start properly")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Failed to start Tor: {e}")
            # Try to check if Tor is running anyway
            if self.check_tor_running():
                self.logger.info("✅ Tor appears to be running despite service command failure")
                return True
            return False
        except Exception as e:
            self.logger.error(f"❌ Error checking/starting Tor: {e}")
            # Try to check if Tor is running anyway
            if self.check_tor_running():
                self.logger.info("✅ Tor appears to be running despite error")
                return True
            return False
    
    def setup_firefox_with_tor(self):
        """Setup Firefox browser with Tor proxy"""
        try:
            self.logger.info("🔧 Setting up Firefox browser with Tor proxy...")
            
            firefox_options = Options()
            firefox_options.add_argument('--headless')  # Run in headless mode for GitHub Actions
            
            # Configure proxy settings for Tor
            firefox_options.set_preference('network.proxy.type', 1)
            firefox_options.set_preference('network.proxy.socks', '127.0.0.1')
            firefox_options.set_preference('network.proxy.socks_port', 9050)
            firefox_options.set_preference('network.proxy.socks_version', 5)
            
            # Additional privacy settings
            firefox_options.set_preference('privacy.trackingprotection.enabled', True)
            firefox_options.set_preference('dom.webdriver.enabled', False)
            firefox_options.set_preference('useAutomationExtension', False)
            
            # User agent randomization
            user_agents = [
                'Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0',
                'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
                'Mozilla/5.0 (X11; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0',
                'Mozilla/5.0 (X11; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0'
            ]
            selected_agent = random.choice(user_agents)
            firefox_options.set_preference('general.useragent.override', selected_agent)
            
            self.driver = webdriver.Firefox(options=firefox_options)
            self.driver.set_page_load_timeout(30)
            
            self.logger.info(f"✅ Firefox browser setup completed with User-Agent: {selected_agent}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup Firefox with Tor: {e}")
            return False
    
    def simulate_human_behavior(self):
        """Simulate human-like behavior on the page"""
        try:
            self.logger.info("🤖 Starting human behavior simulation...")
            actions = ActionChains(self.driver)
            
            # Get page dimensions
            window_width = self.driver.execute_script("return window.innerWidth;")
            window_height = self.driver.execute_script("return window.innerHeight;")
            self.logger.info(f"📐 Page dimensions: {window_width}x{window_height}")
            
            # Get current page title and URL
            try:
                page_title = self.driver.title
                current_url = self.driver.current_url
                self.logger.info(f"📄 Page loaded: '{page_title}' at {current_url}")
            except:
                self.logger.warning("⚠️  Could not retrieve page title/URL")
            
            # Random scrolling
            scroll_actions = random.randint(2, 5)
            self.logger.info(f"📜 Performing {scroll_actions} scroll actions...")
            
            for i in range(scroll_actions):
                scroll_amount = random.randint(100, 500)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                self.logger.info(f"📜 Scroll {i+1}/{scroll_actions}: {scroll_amount}px down")
                time.sleep(random.uniform(0.5, 1.5))
            
            # Random mouse movements
            movement_count = random.randint(3, 7)
            self.logger.info(f"🖱️  Performing {movement_count} mouse movements...")
            
            for i in range(movement_count):
                x = random.randint(50, window_width - 50)
                y = random.randint(50, window_height - 50)
                actions.move_by_offset(x - window_width//2, y - window_height//2)
                actions.perform()
                self.logger.info(f"🖱️  Mouse movement {i+1}/{movement_count}: ({x}, {y})")
                time.sleep(random.uniform(0.2, 0.8))
                actions.reset_actions()
            
            # Random clicks on safe areas (avoiding buttons/links)
            self.logger.info("👆 Attempting safe random clicks...")
            try:
                safe_elements = self.driver.find_elements(By.TAG_NAME, "div")[:5]
                if safe_elements:
                    element = random.choice(safe_elements)
                    actions.move_to_element(element).click().perform()
                    self.logger.info("👆 Performed safe random click on div element")
                    time.sleep(random.uniform(0.5, 1.0))
                else:
                    self.logger.info("👆 No safe elements found for clicking")
            except Exception as e:
                self.logger.warning(f"⚠️  Could not perform random click: {e}")
            
            # Pause to simulate reading
            reading_time = random.uniform(2, 5)
            self.logger.info(f"📖 Simulating reading for {reading_time:.1f} seconds...")
            time.sleep(reading_time)
            
            # Final scroll to bottom
            self.logger.info("📜 Scrolling to bottom of page...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 2))
            
            # Get final scroll position
            scroll_position = self.driver.execute_script("return window.pageYOffset;")
            self.logger.info(f"📍 Final scroll position: {scroll_position}px")
            
            self.logger.info("✅ Human behavior simulation completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error during human behavior simulation: {e}")
    
    def visit_url(self, url, url_name="Unknown"):
        """Visit the specified URL and simulate human behavior"""
        try:
            self.logger.info(f"🌐 Visiting: {url_name} - {url}")
            start_time = time.time()
            
            self.driver.get(url)
            
            # Wait for page to load
            load_wait = random.uniform(2, 4)
            self.logger.info(f"⏳ Waiting {load_wait:.1f}s for page to load...")
            time.sleep(load_wait)
            
            load_time = time.time() - start_time
            self.logger.info(f"⏱️  Page loaded in {load_time:.2f} seconds")
            
            # Simulate human behavior
            self.simulate_human_behavior()
            
            return True
            
        except TimeoutException:
            self.logger.warning(f"⏰ Page load timeout for {url} - continuing with behavior simulation")
            self.simulate_human_behavior()
            return True
        except WebDriverException as e:
            self.logger.error(f"❌ WebDriver error while visiting {url}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Unexpected error while visiting {url}: {e}")
            return False
    
    def close_browser(self):
        """Close the browser and clean up"""
        if self.driver:
            try:
                self.logger.info("🔒 Closing browser...")
                self.driver.quit()
                self.logger.info("✅ Browser closed successfully")
            except Exception as e:
                self.logger.error(f"❌ Error closing browser: {e}")
    
    def run_bot_cycle(self, url_config, cycle_number):
        """Run a single bot cycle"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"🚀 Starting Cycle {cycle_number} for {url_config['name']}")
        self.logger.info(f"{'='*60}")
        
        cycle_start_time = time.time()
        
        # Setup browser with Tor
        if not self.setup_firefox_with_tor():
            self.logger.error(f"❌ Failed to setup browser for cycle {cycle_number}")
            return False
        
        try:
            # Visit the URL
            success = self.visit_url(url_config['url'], url_config['name'])
            
            # Additional random delay
            final_delay = random.uniform(1, 3)
            self.logger.info(f"⏳ Final delay: {final_delay:.1f}s before closing...")
            time.sleep(final_delay)
            
            cycle_duration = time.time() - cycle_start_time
            if success:
                self.logger.info(f"✅ Cycle {cycle_number} completed successfully in {cycle_duration:.2f}s")
            else:
                self.logger.error(f"❌ Cycle {cycle_number} failed after {cycle_duration:.2f}s")
            
            return success
            
        finally:
            # Always close browser after each cycle
            self.close_browser()
            
            # Random delay between cycles
            if cycle_number > 0:  # Don't delay after the last cycle
                inter_cycle_delay = random.uniform(2, 5)
                self.logger.info(f"💤 Inter-cycle delay: {inter_cycle_delay:.1f}s")
                time.sleep(inter_cycle_delay)

def main():
    print("🤖 Tor Selenium Bot Starting...")
    print("="*60)
    
    bot = TorSeleniumBot()
    
    # Load URL configuration
    config = bot.load_urls_config()
    if not config:
        bot.logger.error("❌ Failed to load URL configuration. Exiting...")
        sys.exit(1)
    
    # Filter enabled URLs
    enabled_urls = [url for url in config['urls'] if url.get('enabled', True)]
    if not enabled_urls:
        bot.logger.error("❌ No enabled URLs found in configuration. Exiting...")
        sys.exit(1)
    
    bot.logger.info(f"📋 Found {len(enabled_urls)} enabled URLs to process")
    
    # Get settings
    settings = config.get('settings', {})
    cycles_per_url = settings.get('cycles_per_url', 20)
    min_delay = settings.get('min_delay_between_cycles', 5)
    max_delay = settings.get('max_delay_between_cycles', 15)
    
    bot.logger.info(f"⚙️  Configuration: {cycles_per_url} cycles per URL, {min_delay}-{max_delay}s delays")
    
    # Start/check Tor service
    if not bot.start_tor():
        bot.logger.error("❌ Failed to start or verify Tor service. Exiting...")
        sys.exit(1)
    
    total_successful_cycles = 0
    total_failed_cycles = 0
    
    try:
        for url_index, url_config in enumerate(enabled_urls):
            bot.logger.info(f"\n🎯 Processing URL {url_index + 1}/{len(enabled_urls)}: {url_config['name']}")
            
            url_successful_cycles = 0
            url_failed_cycles = 0
            
            for cycle in range(1, cycles_per_url + 1):
                try:
                    if bot.run_bot_cycle(url_config, cycle):
                        url_successful_cycles += 1
                        total_successful_cycles += 1
                    else:
                        url_failed_cycles += 1
                        total_failed_cycles += 1
                    
                    # Delay between cycles (except for the last cycle of the last URL)
                    if not (url_index == len(enabled_urls) - 1 and cycle == cycles_per_url):
                        delay = random.uniform(min_delay, max_delay)
                        bot.logger.info(f"⏳ Waiting {delay:.1f}s before next cycle...")
                        time.sleep(delay)
                        
                except KeyboardInterrupt:
                    bot.logger.info("\n⚠️  Bot stopped by user (Ctrl+C)")
                    raise
                except Exception as e:
                    bot.logger.error(f"❌ Error in cycle {cycle} for {url_config['name']}: {e}")
                    url_failed_cycles += 1
                    total_failed_cycles += 1
                    continue
            
            bot.logger.info(f"📊 URL '{url_config['name']}' completed: {url_successful_cycles} successful, {url_failed_cycles} failed")
    
    except KeyboardInterrupt:
        bot.logger.info("\n🛑 Bot execution interrupted by user")
    
    finally:
        bot.logger.info(f"\n{'='*60}")
        bot.logger.info("📈 FINAL STATISTICS")
        bot.logger.info(f"{'='*60}")
        bot.logger.info(f"✅ Total successful cycles: {total_successful_cycles}")
        bot.logger.info(f"❌ Total failed cycles: {total_failed_cycles}")
        bot.logger.info(f"📊 Success rate: {(total_successful_cycles/(total_successful_cycles + total_failed_cycles)*100):.1f}%" if (total_successful_cycles + total_failed_cycles) > 0 else "N/A")
        
        # Only try to stop Tor if we started it ourselves
        if not os.environ.get('TOR_ALREADY_RUNNING') == 'true':
            try:
                bot.logger.info("🌐 Stopping Tor service...")
                subprocess.run(['sudo', 'service', 'tor', 'stop'], check=True, capture_output=True)
                bot.logger.info("✅ Tor service stopped successfully")
            except Exception as e:
                bot.logger.error(f"❌ Could not stop Tor service: {e}")
        else:
            bot.logger.info("🌐 Leaving Tor running (was started externally)")
        
        bot.logger.info("🏁 Bot execution completed")

if __name__ == "__main__":
    main()
