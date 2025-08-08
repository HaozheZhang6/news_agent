"""Test user preference learning from interaction patterns."""
import unittest
import time
import json
from unittest.mock import Mock, patch
from src.ipc import Command, CommandType


class PreferenceLearner:
    """Mock preference learning system for testing."""
    
    def __init__(self):
        self.interactions = []
        self.topic_scores = {}
        self.skip_patterns = {}
        self.engagement_times = {}
    
    def record_interaction(self, command_type: CommandType, context: dict, duration: float = 0):
        """Record user interaction for learning."""
        interaction = {
            'command': command_type,
            'context': context,
            'duration': duration,
            'timestamp': time.time()
        }
        self.interactions.append(interaction)
        self._update_preferences(interaction)
    
    def _update_preferences(self, interaction):
        """Update preference scores based on interaction."""
        topic = interaction['context'].get('topic', 'unknown')
        command = interaction['command']
        duration = interaction['duration']
        
        # Initialize topic if new
        if topic not in self.topic_scores:
            self.topic_scores[topic] = 0
            self.skip_patterns[topic] = {'skips': 0, 'total': 0}
            self.engagement_times[topic] = []
        
        # Update scores based on command
        if command == CommandType.SKIP:
            self.topic_scores[topic] -= 1
            self.skip_patterns[topic]['skips'] += 1
        elif command == CommandType.DEEP_DIVE:
            self.topic_scores[topic] += 2
        elif command == CommandType.STOP and duration < 3.0:
            self.topic_scores[topic] -= 0.5  # Early stop = slight disinterest
        
        # Track engagement time
        if duration > 0:
            self.engagement_times[topic].append(duration)
        
        self.skip_patterns[topic]['total'] += 1
    
    def get_topic_preference(self, topic: str) -> float:
        """Get preference score for topic."""
        return self.topic_scores.get(topic, 0)
    
    def get_skip_rate(self, topic: str) -> float:
        """Get skip rate for topic."""
        if topic not in self.skip_patterns or self.skip_patterns[topic]['total'] == 0:
            return 0.0
        pattern = self.skip_patterns[topic]
        return pattern['skips'] / pattern['total']
    
    def get_avg_engagement_time(self, topic: str) -> float:
        """Get average engagement time for topic."""
        if topic not in self.engagement_times or not self.engagement_times[topic]:
            return 0.0
        times = self.engagement_times[topic]
        return sum(times) / len(times)


class TestPreferenceLearning(unittest.TestCase):
    
    def setUp(self):
        """Set up preference learning test environment."""
        self.learner = PreferenceLearner()
    
    def test_skip_pattern_detection(self):
        """Test detection of skip patterns by topic."""
        # Simulate user consistently skipping sports news
        sports_interactions = [
            {'command': CommandType.SKIP, 'context': {'topic': 'sports'}},
            {'command': CommandType.SKIP, 'context': {'topic': 'sports'}},
            {'command': CommandType.SKIP, 'context': {'topic': 'sports'}},
        ]
        
        # User engages with tech news
        tech_interactions = [
            {'command': CommandType.DEEP_DIVE, 'context': {'topic': 'technology'}},
            {'command': CommandType.NEWS_REQUEST, 'context': {'topic': 'technology'}},
        ]
        
        # Record interactions
        for interaction in sports_interactions:
            self.learner.record_interaction(
                interaction['command'], 
                interaction['context']
            )
        
        for interaction in tech_interactions:
            self.learner.record_interaction(
                interaction['command'],
                interaction['context']
            )
        
        # Check skip rates
        sports_skip_rate = self.learner.get_skip_rate('sports')
        tech_skip_rate = self.learner.get_skip_rate('technology')
        
        self.assertEqual(sports_skip_rate, 1.0)  # 100% skip rate
        self.assertEqual(tech_skip_rate, 0.0)    # 0% skip rate
        
        # Check preference scores
        self.assertLess(self.learner.get_topic_preference('sports'), 0)
        self.assertGreater(self.learner.get_topic_preference('technology'), 0)
    
    def test_engagement_time_tracking(self):
        """Test tracking of engagement time patterns."""
        # User listens longer to tech news
        tech_durations = [8.5, 12.3, 6.7, 15.2]
        for duration in tech_durations:
            self.learner.record_interaction(
                CommandType.NEWS_REQUEST,
                {'topic': 'technology'},
                duration
            )
        
        # User stops early on politics
        politics_durations = [2.1, 1.8, 3.2]
        for duration in politics_durations:
            self.learner.record_interaction(
                CommandType.STOP,
                {'topic': 'politics'},
                duration
            )
        
        tech_avg = self.learner.get_avg_engagement_time('technology')
        politics_avg = self.learner.get_avg_engagement_time('politics')
        
        self.assertGreater(tech_avg, 8.0)
        self.assertLess(politics_avg, 4.0)
        self.assertGreater(tech_avg, politics_avg)
    
    def test_deep_dive_interest_scoring(self):
        """Test that deep dive requests increase interest scores."""
        # Base score
        initial_score = self.learner.get_topic_preference('ai')
        self.assertEqual(initial_score, 0)
        
        # User requests deep dive on AI news
        self.learner.record_interaction(
            CommandType.DEEP_DIVE,
            {'topic': 'ai', 'news_title': 'ChatGPT updates'},
            10.5  # Long engagement
        )
        
        # Score should increase significantly
        after_deep_dive = self.learner.get_topic_preference('ai')
        self.assertGreater(after_deep_dive, initial_score + 1)
        
        # Another deep dive should increase further
        self.learner.record_interaction(
            CommandType.DEEP_DIVE,
            {'topic': 'ai', 'news_title': 'Google Bard news'},
            8.2
        )
        
        final_score = self.learner.get_topic_preference('ai')
        self.assertGreater(final_score, after_deep_dive)
    
    def test_mixed_behavior_patterns(self):
        """Test learning from mixed user behavior patterns."""
        # User has mixed behavior on financial news
        financial_interactions = [
            (CommandType.NEWS_REQUEST, 7.5),    # Good engagement
            (CommandType.SKIP, 0),              # Skip one item
            (CommandType.DEEP_DIVE, 12.0),      # Deep dive on another
            (CommandType.STOP, 2.1),            # Early stop
            (CommandType.NEWS_REQUEST, 9.3),    # Good engagement
        ]
        
        for command, duration in financial_interactions:
            self.learner.record_interaction(
                command,
                {'topic': 'finance'},
                duration
            )
        
        # Should show moderate interest (some positives, some negatives)
        finance_score = self.learner.get_topic_preference('finance')
        finance_skip_rate = self.learner.get_skip_rate('finance')
        
        # Moderate score (not strongly positive or negative)
        self.assertGreater(finance_score, -1)
        self.assertLess(finance_score, 3)
        
        # 20% skip rate (1 out of 5)
        self.assertAlmostEqual(finance_skip_rate, 0.2, places=1)
    
    def test_temporal_preference_changes(self):
        """Test tracking preference changes over time."""
        # User initially dislikes crypto news
        early_crypto_interactions = [
            (CommandType.SKIP, {'topic': 'crypto'}, 0),
            (CommandType.STOP, {'topic': 'crypto'}, 1.5),
            (CommandType.SKIP, {'topic': 'crypto'}, 0),
        ]
        
        for command, context, duration in early_crypto_interactions:
            self.learner.record_interaction(command, context, duration)
        
        early_score = self.learner.get_topic_preference('crypto')
        
        # Later, user becomes interested (market changes, etc.)
        later_crypto_interactions = [
            (CommandType.NEWS_REQUEST, {'topic': 'crypto'}, 6.8),
            (CommandType.DEEP_DIVE, {'topic': 'crypto'}, 11.2),
            (CommandType.NEWS_REQUEST, {'topic': 'crypto'}, 8.5),
        ]
        
        for command, context, duration in later_crypto_interactions:
            self.learner.record_interaction(command, context, duration)
        
        later_score = self.learner.get_topic_preference('crypto')
        
        # Score should improve over time
        self.assertLess(early_score, 0)      # Initially negative
        self.assertGreater(later_score, 0)   # Later positive
        self.assertGreater(later_score, early_score)
    
    def test_interruption_context_learning(self):
        """Test learning from interruption context."""
        # User interrupts during certain types of content
        interruption_contexts = [
            # Interrupts political news quickly
            (CommandType.STOP, {'topic': 'politics', 'subtopic': 'election'}, 2.1),
            (CommandType.SKIP, {'topic': 'politics', 'subtopic': 'congress'}, 0),
            
            # But engages with political economic news
            (CommandType.DEEP_DIVE, {'topic': 'politics', 'subtopic': 'economy'}, 9.5),
            (CommandType.NEWS_REQUEST, {'topic': 'politics', 'subtopic': 'trade'}, 7.2),
        ]
        
        for command, context, duration in interruption_contexts:
            self.learner.record_interaction(command, context, duration)
        
        # Should learn nuanced preferences within topics
        politics_score = self.learner.get_topic_preference('politics')
        
        # Mixed signals should result in moderate score
        self.assertGreater(politics_score, -1)
        self.assertLess(politics_score, 2)


class TestPreferenceBasedRanking(unittest.TestCase):
    
    def setUp(self):
        """Set up ranking test environment."""
        self.learner = PreferenceLearner()
        
        # Set up some learned preferences
        preferences = {
            'technology': 5,
            'finance': 2, 
            'sports': -3,
            'politics': -1,
            'health': 1
        }
        
        for topic, score in preferences.items():
            self.learner.topic_scores[topic] = score
    
    def test_news_ranking_by_preference(self):
        """Test ranking news items by learned preferences."""
        mock_news_items = [
            {'title': 'Sports Update', 'topic': 'sports'},
            {'title': 'Tech Innovation', 'topic': 'technology'},
            {'title': 'Market Update', 'topic': 'finance'},
            {'title': 'Health Study', 'topic': 'health'},
            {'title': 'Political News', 'topic': 'politics'},
        ]
        
        # Rank by preference scores
        ranked_items = sorted(
            mock_news_items,
            key=lambda item: self.learner.get_topic_preference(item['topic']),
            reverse=True
        )
        
        # Should be ordered: tech, finance, health, politics, sports
        expected_order = ['technology', 'finance', 'health', 'politics', 'sports']
        actual_order = [item['topic'] for item in ranked_items]
        
        self.assertEqual(actual_order, expected_order)
    
    def test_filtering_disliked_content(self):
        """Test filtering out strongly disliked content."""
        mock_news_items = [
            {'title': 'Tech News', 'topic': 'technology'},
            {'title': 'Sports News', 'topic': 'sports'},      # Negative score
            {'title': 'Finance News', 'topic': 'finance'},
            {'title': 'More Sports', 'topic': 'sports'},      # Negative score
        ]
        
        # Filter out topics with scores below threshold (-2)
        threshold = -2
        filtered_items = [
            item for item in mock_news_items
            if self.learner.get_topic_preference(item['topic']) > threshold
        ]
        
        # Should exclude sports items (score = -3)
        topics_remaining = [item['topic'] for item in filtered_items]
        self.assertNotIn('sports', topics_remaining)
        self.assertIn('technology', topics_remaining)
        self.assertIn('finance', topics_remaining)


if __name__ == '__main__':
    unittest.main()