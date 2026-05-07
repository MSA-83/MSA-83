"""Load testing scripts for Titanium API endpoints."""

import asyncio
import time
from dataclasses import dataclass, field

import httpx


@dataclass
class LoadTestResult:
    """Results from a load test run."""

    endpoint: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    min_response_time: float = float("inf")
    max_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    errors: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    def summary(self) -> str:
        return (
            f"\n=== Load Test Results: {self.endpoint} ===\n"
            f"Total Requests: {self.total_requests}\n"
            f"Successful: {self.successful_requests}\n"
            f"Failed: {self.failed_requests}\n"
            f"Success Rate: {self.success_rate:.1f}%\n"
            f"Avg Response Time: {self.avg_response_time:.2f}ms\n"
            f"Min Response Time: {self.min_response_time:.2f}ms\n"
            f"Max Response Time: {self.max_response_time:.2f}ms\n"
            f"P95 Response Time: {self.p95_response_time:.2f}ms\n"
            f"P99 Response Time: {self.p99_response_time:.2f}ms\n"
            f"Errors: {len(self.errors)}\n"
        )


class LoadTester:
    """Run load tests against Titanium API endpoints."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: dict[str, LoadTestResult] = {}

    async def _make_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        json_data: dict | None = None,
    ) -> tuple[float, bool, str | None]:
        """Make a single request and return (response_time_ms, success, error)."""
        start = time.monotonic()
        try:
            if method.upper() == "GET":
                response = await client.get(url, timeout=30.0)
            else:
                response = await client.post(url, json=json_data, timeout=30.0)

            elapsed = (time.monotonic() - start) * 1000
            return elapsed, response.status_code < 500, None
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            return elapsed, False, str(e)

    async def run_load_test(
        self,
        endpoint: str,
        method: str = "GET",
        json_data: dict | None = None,
        concurrent_users: int = 10,
        requests_per_user: int = 10,
    ) -> LoadTestResult:
        """Run a load test against an endpoint."""
        result = LoadTestResult(endpoint=endpoint)
        response_times = []

        async def user_task():
            async with httpx.AsyncClient(base_url=self.base_url) as client:
                for _ in range(requests_per_user):
                    elapsed, success, error = await self._make_request(client, method, endpoint, json_data)
                    response_times.append(elapsed)
                    result.total_requests += 1
                    if success:
                        result.successful_requests += 1
                    else:
                        result.failed_requests += 1
                        if error:
                            result.errors.append(error)

        tasks = [user_task() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks)

        if response_times:
            response_times.sort()
            result.avg_response_time = sum(response_times) / len(response_times)
            result.min_response_time = min(response_times)
            result.max_response_time = max(response_times)
            result.p95_response_time = response_times[int(len(response_times) * 0.95)]
            result.p99_response_time = response_times[int(len(response_times) * 0.99)]

        self.results[endpoint] = result
        return result

    async def test_health_endpoint(self, concurrent_users: int = 50, requests_per_user: int = 20) -> LoadTestResult:
        """Test health endpoint under load."""
        return await self.run_load_test(
            "/api/health",
            concurrent_users=concurrent_users,
            requests_per_user=requests_per_user,
        )

    async def test_chat_endpoint(self, concurrent_users: int = 10, requests_per_user: int = 5) -> LoadTestResult:
        """Test chat endpoint under load."""
        return await self.run_load_test(
            "/api/chat/",
            method="POST",
            json_data={"message": "Hello, how are you?", "use_rag": False},
            concurrent_users=concurrent_users,
            requests_per_user=requests_per_user,
        )

    async def test_memory_search(self, concurrent_users: int = 20, requests_per_user: int = 10) -> LoadTestResult:
        """Test memory search endpoint under load."""
        return await self.run_load_test(
            "/api/memory/search",
            method="POST",
            json_data={"query": "test query", "top_k": 5},
            concurrent_users=concurrent_users,
            requests_per_user=requests_per_user,
        )

    def print_summary(self):
        """Print summary of all test results."""
        print("\n" + "=" * 60)
        print("LOAD TEST SUMMARY")
        print("=" * 60)
        for result in self.results.values():
            print(result.summary())


async def main():
    """Run load tests."""
    tester = LoadTester(base_url="http://localhost:8000")

    print("Starting load tests...")

    await tester.test_health_endpoint(concurrent_users=50, requests_per_user=20)
    await tester.test_memory_search(concurrent_users=20, requests_per_user=10)

    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
