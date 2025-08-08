"""Test the simple parallel agent implementation."""
import unittest
import asyncio
import queue
import time
from unittest.mock import Mock, patch, AsyncMock
from src.simple_parallel_agent import (
    Command, CommandType, VoiceListener, NewsSpeaker, ParallelNewsAgent
)


class TestSimpleParallelAgent(unittest.TestCase):
    
    def test_command_classification_speed(self):
        """Test command classification is under 1ms."""
        command_queue = queue.Queue()
        listener = VoiceListener(command_queue)
        
        test_phrases = [
            ("stop", CommandType.STOP),
            ("tell me more", CommandType.DEEP_DIVE), 
            ("skip to next", CommandType.SKIP),
            ("what's the news", CommandType.NEWS_REQUEST),
            ("exit", CommandType.EXIT)
        ]
        
        total_time = 0
        for phrase, expected_type in test_phrases:
            start_time = time.time()
            command = listener.classify_command(phrase)
            end_time = time.time()
            
            classification_time = end_time - start_time
            total_time += classification_time
            
            self.assertEqual(command.type, expected_type)
            self.assertLess(classification_time, 0.001)  # < 1ms
        
        avg_time = total_time / len(test_phrases)
        self.assertLess(avg_time, 0.001)
    
    def test_immediate_interruption(self):
        """Test immediate speech interruption."""
        async def test_interruption():
            speaker = NewsSpeaker()
            
            # Mock the voice output to track interruption
            with patch('src.simple_parallel_agent.voice_output.say') as mock_say:
                mock_say.return_value = asyncio.sleep(5)  # Long speech
                
                # Start speaking
                speech_task = asyncio.create_task(
                    speaker.say_interruptible("This is a long message that should be interrupted")
                )
                
                # Wait briefly, then interrupt
                await asyncio.sleep(0.01)
                interrupt_time = time.time()
                speaker.interrupt_speech()
                
                # Speech should be cancelled
                try:
                    result = await speech_task
                    self.assertFalse(result)  # Should return False for interrupted
                except asyncio.CancelledError:
                    pass  # Expected
                
                end_time = time.time()
                interrupt_duration = end_time - interrupt_time
                
                # Interruption should be immediate (< 50ms)
                self.assertLess(interrupt_duration, 0.05)
        
        asyncio.run(test_interruption())
    
    def test_command_queue_performance(self):
        """Test command queue handles rapid commands."""
        command_queue = queue.Queue()
        
        # Add commands rapidly
        start_time = time.time()
        commands = []
        for i in range(50):
            cmd = Command(CommandType.NEWS_REQUEST, f"command {i}")
            command_queue.put(cmd)
            commands.append(cmd)
        
        # Retrieve all commands
        retrieved = []
        while not command_queue.empty():
            retrieved.append(command_queue.get())
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle 50 commands quickly
        self.assertLess(total_time, 0.01)  # < 10ms
        self.assertEqual(len(retrieved), 50)
    
    def test_context_preservation(self):
        """Test news context is preserved across commands."""
        async def test_context():
            speaker = NewsSpeaker()
            
            # Mock agent with news items
            speaker.agent.current_news_items = [
                {'title': 'Tech News', 'summary': 'AI breakthrough'},
                {'title': 'Market News', 'summary': 'Stocks rise'},
                {'title': 'Sports News', 'summary': 'Championship game'}
            ]
            speaker.agent.get_deep_dive = lambda idx: f"Deep dive for item {idx}"
            
            # Set current news index
            speaker.current_news_index = 1
            
            # Deep dive should use current context
            with patch('src.simple_parallel_agent.voice_output.say') as mock_say:
                mock_say.return_value = None
                
                deep_dive_cmd = Command(CommandType.DEEP_DIVE, "tell me more")
                await speaker.handle_deep_dive(deep_dive_cmd)
                
                # Should preserve index
                self.assertEqual(speaker.current_news_index, 1)
                
                # Skip should advance index
                skip_cmd = Command(CommandType.SKIP, "skip")
                await speaker.handle_skip(skip_cmd)
                
                self.assertEqual(speaker.current_news_index, 2)
        
        asyncio.run(test_context())
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        async def test_edges():
            speaker = NewsSpeaker()
            
            # Test deep dive without news context
            speaker.current_news_index = -1
            speaker.agent.current_news_items = []
            
            with patch('src.simple_parallel_agent.voice_output.say') as mock_say:
                mock_say.return_value = None
                
                # Should handle gracefully
                await speaker.handle_deep_dive(Command(CommandType.DEEP_DIVE))
                mock_say.assert_called()
                
                # Test skip at end of list
                speaker.agent.current_news_items = ['item1', 'item2']
                speaker.current_news_index = 1  # Last item
                
                await speaker.handle_skip(Command(CommandType.SKIP))
                
                # Should reset index
                self.assertEqual(speaker.current_news_index, -1)
        
        asyncio.run(test_edges())


class TestIntegrationScenarios(unittest.TestCase):
    
    def test_stop_then_deep_dive_scenario(self):
        """Test realistic user interaction: stop, then deep dive."""
        async def test_scenario():
            agent = ParallelNewsAgent()
            
            # Mock components
            agent.speaker.agent.current_news_items = [
                {'title': 'Breaking News', 'summary': 'Important update'}
            ]
            agent.speaker.current_news_index = 0
            agent.speaker.agent.get_deep_dive = lambda idx: "Detailed explanation..."
            
            with patch('src.simple_parallel_agent.voice_output.say') as mock_say:
                mock_say.return_value = None
                
                # User says "stop"
                stop_cmd = Command(CommandType.STOP, "stop")
                agent.command_queue.put(stop_cmd)
                
                # Then immediately says "tell me more"
                deep_dive_cmd = Command(CommandType.DEEP_DIVE, "tell me more")
                agent.command_queue.put(deep_dive_cmd)
                
                # Process commands
                agent.running = True
                
                # Process first command (stop)
                cmd1 = agent.command_queue.get(timeout=0.01)
                await agent.speaker.handle_stop(cmd1)
                
                # Process second command (deep dive)
                cmd2 = agent.command_queue.get(timeout=0.01) 
                await agent.speaker.handle_deep_dive(cmd2)
                
                # Both should execute without issues
                self.assertEqual(mock_say.call_count, 2)
        
        asyncio.run(test_scenario())


if __name__ == '__main__':
    unittest.main()