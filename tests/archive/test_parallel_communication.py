"""Unit tests for parallel listener-speaker communication."""
import unittest
import asyncio
import time
import threading
import queue
from unittest.mock import Mock, patch, MagicMock
from src.ipc import Command, CommandType, IPCManager

class TestIPCCommunication(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.ipc = IPCManager()
        
    def test_command_creation(self):
        """Test command object creation and serialization."""
        cmd = Command(CommandType.STOP)
        self.assertEqual(cmd.type, CommandType.STOP)
        self.assertIsNotNone(cmd.timestamp)
        
        cmd_with_data = Command(CommandType.NEWS_REQUEST, data="latest tech news")
        self.assertEqual(cmd_with_data.data, "latest tech news")
        
    def test_high_priority_commands(self):
        """Test immediate interrupt commands are flagged correctly."""
        # Test STOP command sets interrupt
        stop_cmd = Command(CommandType.STOP)
        self.ipc.send_command(stop_cmd)
        
        self.assertTrue(self.ipc.is_interrupted())
        self.assertTrue(self.ipc.shared_state['interrupt_requested'])
        
        # Test DEEP_DIVE command sets interrupt  
        self.ipc.clear_interrupt()
        deep_dive_cmd = Command(CommandType.DEEP_DIVE)
        self.ipc.send_command(deep_dive_cmd)
        
        self.assertTrue(self.ipc.is_interrupted())
        
    def test_command_queue_responsiveness(self):
        """Test 10ms command retrieval responsiveness."""
        # Send command
        cmd = Command(CommandType.NEWS_REQUEST, data="test")
        self.ipc.send_command(cmd)
        
        # Measure retrieval time
        start_time = time.time()
        retrieved_cmd = self.ipc.get_command(timeout=0.01)
        end_time = time.time()
        
        self.assertIsNotNone(retrieved_cmd)
        self.assertEqual(retrieved_cmd.type, CommandType.NEWS_REQUEST)
        self.assertLess(end_time - start_time, 0.02)  # Should be < 20ms
        
    def test_no_command_timeout(self):
        """Test timeout behavior when no commands are available."""
        start_time = time.time()
        cmd = self.ipc.get_command(timeout=0.01)
        end_time = time.time()
        
        self.assertIsNone(cmd)
        self.assertLess(end_time - start_time, 0.02)


class TestListenerSpeakerIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up mock listener and speaker."""
        self.command_queue = queue.Queue()
        self.interrupt_event = threading.Event()
        self.shared_state = {'current_news_index': -1, 'is_speaking': False}
        
    def simulate_voice_command(self, text: str) -> Command:
        """Simulate voice recognition and intent classification."""
        text_lower = text.lower()
        
        if "stop" in text_lower:
            return Command(CommandType.STOP)
        elif "tell me more" in text_lower or "dive deeper" in text_lower:
            return Command(CommandType.DEEP_DIVE)
        elif "skip" in text_lower:
            return Command(CommandType.SKIP)
        elif "news" in text_lower:
            return Command(CommandType.NEWS_REQUEST, data=text)
        else:
            return Command(CommandType.NEWS_REQUEST, data=text)
    
    def test_stop_command_immediate_response(self):
        """Test that STOP command interrupts speech immediately."""
        # Simulate speaker is currently speaking
        self.shared_state['is_speaking'] = True
        
        # Send STOP command
        stop_cmd = self.simulate_voice_command("stop")
        self.command_queue.put(stop_cmd)
        
        # Verify command is processed immediately
        self.assertFalse(self.command_queue.empty())
        
        # Simulate interrupt handling
        if stop_cmd.type == CommandType.STOP:
            self.interrupt_event.set()
            self.shared_state['is_speaking'] = False
            
        self.assertTrue(self.interrupt_event.is_set())
        self.assertFalse(self.shared_state['is_speaking'])
        
    def test_deep_dive_command(self):
        """Test DEEP_DIVE command with context."""
        # Set up context - user is listening to news item 0
        self.shared_state['current_news_index'] = 0
        
        # Send DEEP_DIVE command
        deep_dive_cmd = self.simulate_voice_command("tell me more")
        self.command_queue.put(deep_dive_cmd)
        
        # Verify command classification
        self.assertEqual(deep_dive_cmd.type, CommandType.DEEP_DIVE)
        
        # Simulate processing
        retrieved_cmd = self.command_queue.get()
        self.assertEqual(retrieved_cmd.type, CommandType.DEEP_DIVE)
        
        # Should have context to dive deeper
        self.assertGreaterEqual(self.shared_state['current_news_index'], 0)
        
    def test_skip_command_navigation(self):
        """Test SKIP command advances to next news item."""
        # Set up context - user is on news item 0, with more items available
        self.shared_state['current_news_index'] = 0
        mock_news_items = ['item1', 'item2', 'item3']
        
        # Send SKIP command
        skip_cmd = self.simulate_voice_command("skip")
        self.command_queue.put(skip_cmd)
        
        # Verify command
        self.assertEqual(skip_cmd.type, CommandType.SKIP)
        
        # Simulate skip processing
        if self.shared_state['current_news_index'] + 1 < len(mock_news_items):
            self.shared_state['current_news_index'] += 1
            
        self.assertEqual(self.shared_state['current_news_index'], 1)
        
    def test_news_request_command(self):
        """Test news request command processing."""
        news_cmd = self.simulate_voice_command("what's the latest tech news?")
        self.command_queue.put(news_cmd)
        
        self.assertEqual(news_cmd.type, CommandType.NEWS_REQUEST)
        self.assertEqual(news_cmd.data, "what's the latest tech news?")
        
    def test_command_frequency_simulation(self):
        """Test high-frequency command processing simulation."""
        commands = []
        
        # Simulate rapid commands (within 50ms)
        start_time = time.time()
        for i in range(5):
            cmd = Command(CommandType.NEWS_REQUEST, data=f"command_{i}")
            self.command_queue.put(cmd)
            commands.append(cmd)
            time.sleep(0.01)  # 10ms between commands
            
        end_time = time.time()
        
        # Should complete within 100ms
        self.assertLess(end_time - start_time, 0.1)
        
        # All commands should be retrievable
        retrieved_count = 0
        while not self.command_queue.empty():
            self.command_queue.get()
            retrieved_count += 1
            
        self.assertEqual(retrieved_count, 5)


class TestUserPreferenceLearning(unittest.TestCase):
    
    def setUp(self):
        """Set up preference learning test fixtures."""
        self.user_interactions = []
        
    def record_interaction(self, command_type: CommandType, context: dict):
        """Simulate recording user interactions for preference learning."""
        interaction = {
            'command': command_type,
            'timestamp': time.time(),
            'context': context
        }
        self.user_interactions.append(interaction)
        
    def test_skip_pattern_learning(self):
        """Test learning from skip patterns."""
        # Simulate user skipping sports news consistently
        sports_context = {'topic': 'sports', 'news_index': 0}
        tech_context = {'topic': 'technology', 'news_index': 1}
        
        # User skips sports but listens to tech
        self.record_interaction(CommandType.SKIP, sports_context)
        self.record_interaction(CommandType.DEEP_DIVE, tech_context)
        self.record_interaction(CommandType.SKIP, sports_context)
        
        # Analyze patterns
        sports_skips = sum(1 for i in self.user_interactions 
                          if i['command'] == CommandType.SKIP and 
                          i['context'].get('topic') == 'sports')
        
        tech_deep_dives = sum(1 for i in self.user_interactions 
                             if i['command'] == CommandType.DEEP_DIVE and 
                             i['context'].get('topic') == 'technology')
        
        self.assertEqual(sports_skips, 2)
        self.assertEqual(tech_deep_dives, 1)
        
        # Should learn: user prefers tech over sports
        preference_score = {'sports': -sports_skips, 'technology': tech_deep_dives}
        self.assertLess(preference_score['sports'], preference_score['technology'])
        
    def test_interruption_timing_learning(self):
        """Test learning from interruption timing."""
        # Simulate user interrupting at different points
        interactions = [
            {'command': CommandType.STOP, 'timing': 2.5, 'topic': 'politics'},  # Early stop
            {'command': CommandType.DEEP_DIVE, 'timing': 8.0, 'topic': 'tech'},  # Full listen + more
            {'command': CommandType.STOP, 'timing': 1.8, 'topic': 'sports'},     # Very early stop
        ]
        
        # Calculate average listening time by topic
        topic_times = {}
        for interaction in interactions:
            topic = interaction['topic']
            if topic not in topic_times:
                topic_times[topic] = []
            topic_times[topic].append(interaction['timing'])
        
        # Average listening times
        avg_times = {topic: sum(times)/len(times) for topic, times in topic_times.items()}
        
        self.assertGreater(avg_times['tech'], avg_times['politics'])
        self.assertGreater(avg_times['politics'], avg_times['sports'])


if __name__ == '__main__':
    unittest.main()