"""
RetryPolicy 和 RetryState 的单元测试。
"""

from datetime import datetime, timedelta
import unittest

from workflow_engine.models.retry import RetryPolicy, RetryState


class TestRetryPolicy(unittest.TestCase):
    """测试 RetryPolicy。"""

    def test_default_policy(self):
        """测试默认策略。"""
        policy = RetryPolicy()
        self.assertEqual(policy.max_retries, 3)
        self.assertEqual(policy.delay_seconds, 1.0)

    def test_should_retry_within_limit(self):
        """测试在限制内应该重试。"""
        policy = RetryPolicy(max_retries=3)
        exception = Exception("test")
        self.assertTrue(policy.should_retry(exception, 0))
        self.assertTrue(policy.should_retry(exception, 1))
        self.assertTrue(policy.should_retry(exception, 2))

    def test_should_not_retry_exceed_limit(self):
        """测试超过限制不应该重试。"""
        policy = RetryPolicy(max_retries=3)
        exception = Exception("test")
        self.assertFalse(policy.should_retry(exception, 3))

    def test_should_not_retry_wrong_exception_type(self):
        """测试非重试异常类型不应该重试。"""

        class MyException(Exception):
            pass

        class OtherException(Exception):
            pass

        policy = RetryPolicy(retryable_exceptions=(MyException,))
        self.assertTrue(policy.should_retry(MyException(), 0))
        self.assertFalse(policy.should_retry(OtherException(), 0))

    def test_custom_retry_condition(self):
        """测试自定义重试条件。"""

        def custom_condition(exception, retry_count):
            return retry_count < 2

        policy = RetryPolicy(
            max_retries=5,
            retry_condition=custom_condition
        )
        exception = Exception("test")
        self.assertTrue(policy.should_retry(exception, 0))
        self.assertTrue(policy.should_retry(exception, 1))
        self.assertFalse(policy.should_retry(exception, 2))

    def test_get_delay(self):
        """测试获取延迟时间。"""
        policy = RetryPolicy(delay_seconds=2.5)
        self.assertEqual(policy.get_delay(0), 2.5)
        self.assertEqual(policy.get_delay(1), 2.5)


class TestRetryState(unittest.TestCase):
    """测试 RetryState。"""

    def test_initial_state(self):
        """测试初始状态。"""
        state = RetryState(node_id="test")
        self.assertEqual(state.node_id, "test")
        self.assertEqual(state.retry_count, 0)
        self.assertIsNone(state.last_exception)
        self.assertIsNone(state.scheduled_retry_time)
        self.assertFalse(state.is_retrying)

    def test_can_retry(self):
        """测试是否可以重试。"""
        policy = RetryPolicy(max_retries=2)
        state = RetryState(node_id="test")
        state.last_exception = Exception("test")

        state.retry_count = 0
        self.assertTrue(state.can_retry(policy))

        state.retry_count = 1
        self.assertTrue(state.can_retry(policy))

        state.retry_count = 2
        self.assertFalse(state.can_retry(policy))

    def test_mark_for_retry(self):
        """测试标记为重试。"""
        policy = RetryPolicy(max_retries=2, delay_seconds=0.1)
        state = RetryState(node_id="test")
        exception = Exception("test")
        state.mark_for_retry(exception, policy)

        self.assertTrue(state.is_retrying)
        self.assertEqual(state.last_exception, exception)
        self.assertIsNotNone(state.scheduled_retry_time)
        # 检查 scheduled_retry_time 在未来 0.1 秒左右
        expected_time = datetime.now() + timedelta(seconds=0.1)
        self.assertAlmostEqual(
            (state.scheduled_retry_time - expected_time).total_seconds(),
            0,
            delta=0.01
        )

    def test_should_execute_now(self):
        """测试是否现在应该执行。"""
        state = RetryState(node_id="test")

        # 未标记重试
        self.assertFalse(state.should_execute_now())

        # 标记重试，没有延迟
        state.is_retrying = True
        self.assertTrue(state.should_execute_now())

        # 标记重试，有延迟，但时间未到
        future_time = datetime.now() + timedelta(seconds=10)
        state.scheduled_retry_time = future_time
        self.assertFalse(state.should_execute_now())

        # 标记重试，有延迟，时间已到
        past_time = datetime.now() - timedelta(seconds=1)
        state.scheduled_retry_time = past_time
        self.assertTrue(state.should_execute_now())

    def test_increment_retry(self):
        """测试增加重试计数。"""
        state = RetryState(node_id="test")
        state.retry_count = 1
        state.is_retrying = True
        state.scheduled_retry_time = datetime.now()
        state.last_exception = Exception("test")

        state.increment_retry()

        self.assertEqual(state.retry_count, 2)
        self.assertFalse(state.is_retrying)
        self.assertIsNone(state.scheduled_retry_time)

    def test_reset(self):
        """测试重置。"""
        state = RetryState(node_id="test")
        state.retry_count = 3
        state.is_retrying = True
        state.last_exception = Exception("test")
        state.scheduled_retry_time = datetime.now()

        state.reset()

        self.assertEqual(state.retry_count, 0)
        self.assertFalse(state.is_retrying)
        self.assertIsNone(state.last_exception)
        self.assertIsNone(state.scheduled_retry_time)


if __name__ == "__main__":
    unittest.main()
