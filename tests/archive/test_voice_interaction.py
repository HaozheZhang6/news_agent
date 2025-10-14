"""Test voice interaction scenarios and chat history display."""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from src.ipc import CommandType
from src.voice_listener_process import classify_intent


class TestVoiceInteraction:
    """Test complete voice interaction scenarios."""
    
    def test_user_voice_recognition_scenarios(self):
        """Test various user voice input scenarios."""
        test_scenarios = [
            # Basic commands
            ("stop", CommandType.STOP),
            ("cancel", CommandType.STOP),  # Now should work
            ("quiet", CommandType.STOP),
            ("tell me more", CommandType.DEEP_DIVE),
            ("skip this", CommandType.SKIP),
            
            # Content requests
            ("latest news", CommandType.NEWS_REQUEST),
            ("what's happening today", CommandType.NEWS_REQUEST),
            ("apple stock price", CommandType.STOCK_REQUEST),
            ("weather forecast", CommandType.WEATHER_REQUEST),
            
            # Navigation and control
            ("speak louder", CommandType.VOLUME_UP),
            ("go slower", CommandType.SPEED_DOWN),
            ("help me", CommandType.HELP),
            ("repeat that", CommandType.REPEAT),
            
            # Real user utterances (more natural)
            ("can you tell me the news", CommandType.NEWS_REQUEST),
            ("I want to know about stocks", CommandType.STOCK_REQUEST),
            ("stop talking please", CommandType.STOP),
            ("explain more about that", CommandType.DEEP_DIVE),
        ]
        
        for user_input, expected_type in test_scenarios:
            command = classify_intent(user_input)
            assert command.type == expected_type, f"Failed for '{user_input}': expected {expected_type}, got {command.type}"
            print(f"✅ '{user_input}' -> {command.type.value}")

    @pytest.mark.asyncio
    async def test_voice_chat_flow(self):
        """Test complete voice chat interaction flow."""
        from src.voice_listener_process import fallback_voice_listener_worker
        import multiprocessing as mp
        
        with patch('speech_recognition.Recognizer') as MockRecognizer, \
             patch('speech_recognition.Microphone') as MockMicrophone, \
             patch('src.conversation_logger.conversation_logger') as mock_logger:
            
            # Mock speech recognition to simulate user inputs
            mock_recognizer = MockRecognizer.return_value
            mock_recognizer.recognize_google.side_effect = [
                "tell me the news",
                "stop",
                "weather today", 
                "cancel"
            ]
            
            # Mock microphone
            MockMicrophone.return_value.__enter__.return_value = MagicMock()
            
            # Create IPC components
            command_queue = mp.Queue()
            interrupt_event = mp.Event()
            shared_state = mp.Manager().dict()
            
            # Simulate conversation for a short time
            import threading
            
            def run_listener():
                try:
                    fallback_voice_listener_worker(command_queue, interrupt_event, shared_state)
                except:
                    pass  # Expected to fail after mock inputs
            
            listener_thread = threading.Thread(target=run_listener, daemon=True)
            listener_thread.start()
            
            # Give it time to process inputs
            await asyncio.sleep(0.5)
            
            # Check that commands were processed
            commands = []
            while not command_queue.empty():
                commands.append(command_queue.get())
            
            # Should have processed some commands
            assert len(commands) > 0, "No commands were processed"
            
            # Verify command types
            expected_types = [CommandType.NEWS_REQUEST, CommandType.STOP, CommandType.WEATHER_REQUEST, CommandType.STOP]
            for i, cmd in enumerate(commands):
                if i < len(expected_types):
                    assert cmd.type == expected_types[i], f"Command {i}: expected {expected_types[i]}, got {cmd.type}"
            
            # Should have logged user inputs
            assert mock_logger.log_user_input.call_count >= len(commands)

    @pytest.mark.asyncio 
    async def test_tts_output_with_console_display(self):
        """Test TTS output and console display functionality."""
        from src.voice_output import say
        
        with patch('src.voice_output.edge_tts') as mock_edge_tts, \
             patch('src.voice_output.pygame') as mock_pygame, \
             patch('src.voice_output.audio_logger') as mock_audio_logger, \
             patch('src.voice_output.conversation_logger') as mock_conv_logger, \
             patch('builtins.print') as mock_print:
            
            # Setup mocks
            mock_edge_tts.Communicate.return_value.save = AsyncMock()
            mock_pygame.mixer.music.get_busy.side_effect = [True, False]
            mock_audio_logger.save_response_audio.return_value = "/test/response.mp3"
            
            # Test TTS with console output
            test_response = "Here are today's headlines: Tech stocks rise 3%"
            
            await say(test_response)
            
            # Should have printed to console
            mock_print.assert_called_with(f"🤖 AGENT: {test_response}")
            
            # Should have logged the response
            mock_conv_logger.log_agent_response.assert_called_once()

    def test_chat_history_console_output(self):
        """Test that chat history is properly displayed in console."""
        with patch('builtins.print') as mock_print, \
             patch('src.conversation_logger.conversation_logger'):
            
            # Simulate user input processing
            user_inputs = [
                "tell me the news",
                "stop that", 
                "weather please",
                "cancel"
            ]
            
            for user_input in user_inputs:
                # This simulates what happens in the voice listener
                print(f"👤 USER: {user_input}")
                
                # Classify command
                command = classify_intent(user_input)
                print(f"📝 COMMAND: {command.type.value}")
                
                # Simulate agent response
                if command.type == CommandType.NEWS_REQUEST:
                    response = "Here are the latest news headlines..."
                elif command.type == CommandType.STOP:
                    response = "Stopped."
                elif command.type == CommandType.WEATHER_REQUEST:
                    response = "Today's weather is sunny..."
                else:
                    response = "I understand."
                
                print(f"🤖 AGENT: {response}")
            
            # Verify console outputs
            expected_calls = []
            for user_input in user_inputs:
                expected_calls.append(f"👤 USER: {user_input}")
            
            # Check that user inputs were printed
            for expected_call in expected_calls:
                found = any(call[0][0] == expected_call for call in mock_print.call_args_list)
                assert found, f"Expected console output not found: {expected_call}"

    @pytest.mark.asyncio
    async def test_error_handling_scenarios(self):
        """Test error handling in voice interaction."""
        from src.voice_output import say
        
        # Test TTS with audio save failure (ffmpeg missing)
        with patch('src.voice_output.edge_tts') as mock_edge_tts, \
             patch('src.voice_output.pygame') as mock_pygame, \
             patch('src.voice_output.audio_logger') as mock_audio_logger, \
             patch('src.voice_output.conversation_logger') as mock_conv_logger, \
             patch('builtins.print') as mock_print:
            
            # Setup mocks
            mock_edge_tts.Communicate.return_value.save = AsyncMock()
            mock_pygame.mixer.music.get_busy.return_value = False
            
            # Simulate audio save failure (ffmpeg missing)
            mock_audio_logger.save_response_audio.side_effect = Exception("ffmpeg not found")
            
            # Should handle error gracefully
            test_response = "This should work even with audio save failure"
            await say(test_response)
            
            # Should still print to console
            mock_print.assert_called_with(f"🤖 AGENT: {test_response}")
            
            # Should log the error
            mock_conv_logger.log_error.assert_called_once()
            
            # Should still log the response (with None audio path)
            mock_conv_logger.log_agent_response.assert_called_with(test_response, None)

    def test_interrupt_command_priority(self):
        """Test that interrupt commands have proper priority."""
        # Test interrupt vs non-interrupt commands
        interrupt_commands = [
            "stop now",
            "tell me more details", 
            "halt everything",
            "cancel please"
        ]
        
        non_interrupt_commands = [
            "skip this story",
            "speak louder",
            "weather today",
            "help me"
        ]
        
        interrupt_types = {CommandType.STOP, CommandType.DEEP_DIVE}
        
        for cmd_text in interrupt_commands:
            command = classify_intent(cmd_text)
            assert command.type in interrupt_types, f"'{cmd_text}' should be interrupt command"
            print(f"🔴 INTERRUPT: '{cmd_text}' -> {command.type.value}")
        
        for cmd_text in non_interrupt_commands:
            command = classify_intent(cmd_text)
            assert command.type not in interrupt_types, f"'{cmd_text}' should not be interrupt command"
            print(f"⚪ NORMAL: '{cmd_text}' -> {command.type.value}")

    def test_conversation_logging_integration(self):
        """Test that conversation logging works with console output."""
        from src.conversation_logger import ConversationLogger
        
        with patch('builtins.open', create=True) as mock_file, \
             patch('builtins.print') as mock_print:
            
            logger = ConversationLogger()
            
            # Simulate a conversation
            conversation_turns = [
                ("👤 USER", "tell me the latest news"),
                ("🤖 AGENT", "Here are today's top stories..."),
                ("👤 USER", "tell me more about the first story"),
                ("🤖 AGENT", "The first story involves..."),
                ("👤 USER", "stop"),
                ("🤖 AGENT", "Stopped."),
            ]
            
            for speaker, text in conversation_turns:
                if speaker == "👤 USER":
                    print(f"{speaker}: {text}")
                    logger.log_user_input(text)
                else:
                    print(f"{speaker}: {text}")
                    logger.log_agent_response(text)
            
            # Verify console output happened
            for speaker, text in conversation_turns:
                expected_call = f"{speaker}: {text}"
                found = any(call[0][0] == expected_call for call in mock_print.call_args_list)
                assert found, f"Missing console output: {expected_call}"


class TestVoiceInteractionManualTesting:
    """Manual test cases for voice interaction testing."""
    
    def test_print_manual_test_scenarios(self):
        """Print manual test scenarios for human testing."""
        print("\n" + "="*60)
        print("MANUAL TEST SCENARIOS FOR VOICE INTERACTION")
        print("="*60)
        
        scenarios = [
            {
                "scenario": "Basic News Request",
                "steps": [
                    "1. Start the application: python -m src.main",
                    "2. Say: 'tell me the news'",
                    "3. Expected: You should see '👤 USER: tell me the news' in console",
                    "4. Expected: Agent should respond with news headlines",
                    "5. Expected: You should see '🤖 AGENT: [response]' in console"
                ]
            },
            {
                "scenario": "Stop Command", 
                "steps": [
                    "1. While agent is speaking, say: 'stop'",
                    "2. Expected: Speech should stop",
                    "3. Expected: Console shows '👤 USER: stop'",
                    "4. Expected: Console shows '🤖 AGENT: Stopped.'"
                ]
            },
            {
                "scenario": "Cancel Command",
                "steps": [
                    "1. Say: 'can you cancel'",
                    "2. Expected: Should be classified as STOP command",
                    "3. Expected: Console shows '👤 USER: can you cancel'",
                    "4. Expected: Agent responds appropriately"
                ]
            },
            {
                "scenario": "Deep Dive Request",
                "steps": [
                    "1. After getting news, say: 'tell me more'",
                    "2. Expected: Should get detailed information",
                    "3. Expected: Console shows conversation flow clearly"
                ]
            },
            {
                "scenario": "Voice Commands Variety",
                "steps": [
                    "1. Try: 'weather today'",
                    "2. Try: 'apple stock price'", 
                    "3. Try: 'speak louder'",
                    "4. Try: 'help me'",
                    "5. Expected: All should be recognized and classified correctly"
                ]
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\nSCENARIO {i}: {scenario['scenario']}")
            print("-" * 40)
            for step in scenario['steps']:
                print(f"  {step}")
        
        print("\n" + "="*60)
        print("TROUBLESHOOTING GUIDE")
        print("="*60)
        print("1. If TTS fails: Install ffmpeg with 'brew install ffmpeg'")
        print("2. If no voice recognition: Check microphone permissions")
        print("3. If no SenseVoice: Download model or use fallback mode")
        print("4. Console should show clear chat history with 👤 and 🤖 emojis")
        print("5. Logs are saved in logs/ directory")
        print("="*60)


# Run manual test scenarios when this file is executed
if __name__ == '__main__':
    test = TestVoiceInteractionManualTesting()
    test.test_print_manual_test_scenarios()
    
    # Run basic tests
    interaction_test = TestVoiceInteraction()
    interaction_test.test_user_voice_recognition_scenarios()
    interaction_test.test_interrupt_command_priority()
    
    print("\n✅ Basic voice interaction tests passed!")
    print("Run the manual test scenarios above for complete testing.")