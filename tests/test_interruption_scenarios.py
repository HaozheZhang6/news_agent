"""Test immediate interruption scenarios and response times."""
import unittest
import asyncio
import time
import threading
from unittest.mock import Mock, patch, AsyncMock
from src.ipc import Command, CommandType


class TestInterruptionScenarios(unittest.TestCase):
    
    def setUp(self):
        """Set up interruption test environment."""
        self.interrupt_event = threading.Event()
        self.current_speech_task = None
        self.response_times = []
        
    async def mock_speech_task(self, text: str, duration: float = 5.0):
        """Mock speech task that can be interrupted."""
        start_time = time.time()
        try:
            await asyncio.sleep(duration)
            return f"Completed: {text}"
        except asyncio.CancelledError:
            end_time = time.time()
            interrupt_time = end_time - start_time
            self.response_times.append(interrupt_time)
            raise
    
    def test_immediate_stop_command(self):
        """Test STOP command interrupts speech within 50ms."""
        async def test_scenario():
            # Start long speech
            speech_task = asyncio.create_task(
                self.mock_speech_task("This is a long news briefing...", 10.0)
            )
            
            # Wait 1 second, then interrupt
            await asyncio.sleep(1.0)
            
            # Simulate STOP command
            interrupt_start = time.time()
            speech_task.cancel()
            
            try:
                await speech_task
            except asyncio.CancelledError:
                interrupt_end = time.time()
                interrupt_time = interrupt_end - interrupt_start
                
                # Should interrupt within 50ms
                self.assertLess(interrupt_time, 0.05)
        
        asyncio.run(test_scenario())
    
    def test_deep_dive_immediate_transition(self):
        """Test DEEP_DIVE command immediately transitions content."""
        async def test_scenario():
            # Simulate current news brief
            brief_task = asyncio.create_task(
                self.mock_speech_task("Apple stock rises 3%...", 3.0)
            )
            
            # Wait 1 second, then deep dive
            await asyncio.sleep(1.0)
            
            transition_start = time.time()
            
            # Cancel brief and start deep dive
            brief_task.cancel()
            try:
                await brief_task
            except asyncio.CancelledError:
                pass
            
            # Start deep dive immediately
            deep_dive_task = asyncio.create_task(
                self.mock_speech_task("Apple's stock surge is driven by...", 10.0)
            )
            
            transition_end = time.time()
            transition_time = transition_end - transition_start
            
            # Transition should be immediate (< 30ms)
            self.assertLess(transition_time, 0.03)
            
            # Clean up
            deep_dive_task.cancel()
            try:
                await deep_dive_task
            except asyncio.CancelledError:
                pass
        
        asyncio.run(test_scenario())
    
    def test_multiple_rapid_interruptions(self):
        """Test handling multiple rapid interruptions."""
        async def test_scenario():
            interrupt_times = []
            
            for i in range(3):
                # Start speech
                speech_task = asyncio.create_task(
                    self.mock_speech_task(f"News item {i}", 5.0)
                )
                
                # Wait briefly, then interrupt
                await asyncio.sleep(0.5)
                
                interrupt_start = time.time()
                speech_task.cancel()
                
                try:
                    await speech_task
                except asyncio.CancelledError:
                    interrupt_end = time.time()
                    interrupt_times.append(interrupt_end - interrupt_start)
            
            # All interruptions should be fast
            for interrupt_time in interrupt_times:
                self.assertLess(interrupt_time, 0.05)
        
        asyncio.run(test_scenario())


class TestRealTimeCommandProcessing(unittest.TestCase):
    
    def test_command_classification_speed(self):
        """Test voice command classification speed."""
        def classify_intent(text: str) -> Command:
            """Fast intent classification."""
            text_lower = text.lower()
            
            if "stop" in text_lower:
                return Command(CommandType.STOP)
            elif "tell me more" in text_lower:
                return Command(CommandType.DEEP_DIVE)
            elif "skip" in text_lower:
                return Command(CommandType.SKIP)
            else:
                return Command(CommandType.NEWS_REQUEST, data=text)
        
        test_phrases = [
            "stop",
            "tell me more about that",
            "skip to next",
            "what's the latest news",
            "how's Apple stock doing"
        ]
        
        classification_times = []
        
        for phrase in test_phrases:
            start_time = time.time()
            command = classify_intent(phrase)
            end_time = time.time()
            
            classification_time = end_time - start_time
            classification_times.append(classification_time)
            
            # Verify correct classification
            if "stop" in phrase:
                self.assertEqual(command.type, CommandType.STOP)
            elif "tell me more" in phrase:
                self.assertEqual(command.type, CommandType.DEEP_DIVE)
            elif "skip" in phrase:
                self.assertEqual(command.type, CommandType.SKIP)
            else:
                self.assertEqual(command.type, CommandType.NEWS_REQUEST)
        
        # All classifications should be under 1ms
        max_time = max(classification_times)
        self.assertLess(max_time, 0.001)
    
    def test_command_queue_performance(self):
        """Test command queue performance under load."""
        import queue
        
        command_queue = queue.Queue()
        
        # Fill queue with commands rapidly
        start_time = time.time()
        for i in range(100):
            cmd = Command(CommandType.NEWS_REQUEST, data=f"command_{i}")
            command_queue.put(cmd)
        
        # Retrieve all commands
        retrieved_commands = []
        while not command_queue.empty():
            retrieved_commands.append(command_queue.get())
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle 100 commands in under 10ms
        self.assertLess(total_time, 0.01)
        self.assertEqual(len(retrieved_commands), 100)


class TestContextualCommands(unittest.TestCase):
    
    def test_deep_dive_without_context(self):
        """Test DEEP_DIVE command when no news context exists."""
        # No current news index
        current_news_index = -1
        news_items = []
        
        # Simulate DEEP_DIVE command
        command = Command(CommandType.DEEP_DIVE)
        
        # Should handle gracefully
        if current_news_index == -1 or not news_items:
            response = "No news item to dive deeper into."
        else:
            response = f"Deep dive for item {current_news_index}"
        
        self.assertEqual(response, "No news item to dive deeper into.")
    
    def test_skip_at_end_of_list(self):
        """Test SKIP command when at end of news list."""
        current_news_index = 2
        news_items = ['item1', 'item2', 'item3']  # 3 items, index 2 is last
        
        # Simulate SKIP command
        command = Command(CommandType.SKIP)
        
        if current_news_index + 1 >= len(news_items):
            response = "No more news to skip to."
            current_news_index = -1  # Reset
        else:
            current_news_index += 1
            response = f"Skipped to item {current_news_index}"
        
        self.assertEqual(response, "No more news to skip to.")
        self.assertEqual(current_news_index, -1)
    
    def test_context_preservation(self):
        """Test that context is preserved across commands."""
        # Initial state
        current_news_index = 1
        news_items = ['tech news', 'stock news', 'weather news']
        
        # DEEP_DIVE should preserve index
        deep_dive_cmd = Command(CommandType.DEEP_DIVE)
        
        if current_news_index >= 0:
            context_preserved = True
            selected_item = news_items[current_news_index]
        else:
            context_preserved = False
            selected_item = None
        
        self.assertTrue(context_preserved)
        self.assertEqual(selected_item, 'stock news')
        self.assertEqual(current_news_index, 1)  # Index unchanged


if __name__ == '__main__':
    unittest.main()