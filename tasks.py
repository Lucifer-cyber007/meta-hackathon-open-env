from typing import Dict, Any, List

TASKS: Dict[str, Dict[str, Any]] = {
    "easy": {
        "id": "easy",
        "name": "Basic Bug Detection",
        "description": (
            "Review a simple Python utility module. Find edge case bugs and "
            "performance issues. The code looks functional at first glance but "
            "has several critical and minor issues."
        ),
        "difficulty": "easy",
        "max_steps": 3,
        "pr_title": "Add calculate_statistics utility module",
        "pr_description": (
            "Adding utility functions for calculating statistics on lists of numbers. "
            "Used by the analytics dashboard."
        ),
        "file_name": "utils/statistics.py",
        "diff": """\
--- a/utils/statistics.py
++ b/utils/statistics.py
@@ -0,0 +1,30 @@
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

def calculate_max(numbers):
    max_val = numbers[0]
    for num in numbers:
        if num > max_val:
            max_val = num
    return max_val

def get_percentage(value, total):
    return (value / total) * 100

def find_duplicates(items):
    seen = []
    duplicates = []
    for item in items:
        if item in seen:
            duplicates.append(item)
        seen.append(item)
    return duplicates

def safe_divide(a, b):
    if b != 0:
        return a / b
    else:
        return 0
""",
        "known_issues": [
            {
                "line_number": 5,
                "issue_type": "bug",
                "severity": "critical",
                "description": "ZeroDivisionError when numbers list is empty — len(numbers) returns 0",
                "keywords": ["zero", "division", "empty", "len", "zerodivision", "divide by zero"],
            },
            {
                "line_number": 8,
                "issue_type": "bug",
                "severity": "critical",
                "description": "IndexError when numbers list is empty — numbers[0] raises IndexError",
                "keywords": ["index", "indexerror", "empty", "list", "numbers[0]", "first element"],
            },
            {
                "line_number": 14,
                "issue_type": "bug",
                "severity": "critical",
                "description": "ZeroDivisionError in get_percentage when total is 0",
                "keywords": ["zero", "division", "total", "percentage", "zerodivision"],
            },
            {
                "line_number": 17,
                "issue_type": "performance",
                "severity": "minor",
                "description": "Using list for 'seen' causes O(n^2) complexity — use a set for O(1) lookups",
                "keywords": ["set", "performance", "o(n)", "o(n^2)", "lookup", "efficiency", "complexity"],
            },
        ],
        "required_verdict": "request_changes",
        "success_threshold": 0.6,
    },

    "medium": {
        "id": "medium",
        "name": "Security Vulnerability Review",
        "description": (
            "Review a user authentication module. Identify security vulnerabilities "
            "including SQL injection, hardcoded credentials, weak cryptography, and "
            "logic errors in permission checking."
        ),
        "difficulty": "medium",
        "max_steps": 5,
        "pr_title": "Add user authentication and database access layer",
        "pr_description": (
            "Implements user login, password reset, and role-based permission checks. "
            "Connects to PostgreSQL for user data."
        ),
        "file_name": "auth/user_manager.py",
        "diff": """\
--- a/auth/user_manager.py
++ b/auth/user_manager.py
@@ -0,0 +1,52 @@
import hashlib

DB_PASSWORD = "admin123"
API_SECRET = "supersecret_key_do_not_share"

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_query(query)

def login(username, password):
    hashed = hashlib.md5(password.encode()).hexdigest()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{hashed}'"
    user = execute_query(query)
    if user:
        return {"status": "success", "user": user}
    return {"status": "failed"}

def reset_password(email, new_password):
    if len(new_password) > 6:
        query = f"UPDATE users SET password = '{new_password}' WHERE email = '{email}'"
        execute_query(query)
        return True
    return False

def delete_user(user_id):
    execute_query(f"DELETE FROM users WHERE id = {user_id}")
    return True

def serialize_user(user_data):
    import pickle
    return pickle.dumps(user_data)

def deserialize_user(data):
    import pickle
    return pickle.loads(data)

def log_action(user, action):
    log_entry = f"[{action}] User: {user}"
    print(log_entry)

def check_permission(user_role, required_role):
    roles = ["user", "moderator", "admin"]
    return roles.index(user_role) == roles.index(required_role)
""",
        "known_issues": [
            {
                "line_number": 3,
                "issue_type": "security",
                "severity": "critical",
                "description": "Hardcoded database password in source code — use environment variables",
                "keywords": ["hardcoded", "password", "credential", "environment variable", "env", "secret"],
            },
            {
                "line_number": 4,
                "issue_type": "security",
                "severity": "critical",
                "description": "Hardcoded API secret key in source code — use environment variables",
                "keywords": ["hardcoded", "secret", "api key", "credential", "environment variable", "env"],
            },
            {
                "line_number": 7,
                "issue_type": "security",
                "severity": "critical",
                "description": "SQL injection — user_id interpolated directly into query, use parameterized queries",
                "keywords": ["sql injection", "parameterized", "sanitize", "f-string", "interpolat", "injection"],
            },
            {
                "line_number": 11,
                "issue_type": "security",
                "severity": "critical",
                "description": "MD5 is cryptographically broken for password hashing — use bcrypt or argon2",
                "keywords": ["md5", "bcrypt", "argon2", "hash", "cryptograph", "broken", "weak"],
            },
            {
                "line_number": 12,
                "issue_type": "security",
                "severity": "critical",
                "description": "SQL injection in login — username interpolated into query string",
                "keywords": ["sql injection", "parameterized", "username", "injection", "interpolat"],
            },
            {
                "line_number": 20,
                "issue_type": "security",
                "severity": "critical",
                "description": "Password stored in plaintext — must be hashed before storage",
                "keywords": ["plaintext", "hash", "password", "bcrypt", "plain text", "unhashed"],
            },
            {
                "line_number": 33,
                "issue_type": "security",
                "severity": "critical",
                "description": "pickle.loads() on untrusted data allows arbitrary code execution — use JSON instead",
                "keywords": ["pickle", "arbitrary code", "unsafe", "deserialization", "json", "remote code"],
            },
            {
                "line_number": 41,
                "issue_type": "bug",
                "severity": "major",
                "description": "Permission check uses == instead of >= — admin cannot access user-level resources",
                "keywords": ["permission", ">=", "role", "hierarchy", "comparison", "greater", "equal"],
            },
        ],
        "required_verdict": "request_changes",
        "success_threshold": 0.45,
    },

    "hard": {
        "id": "hard",
        "name": "Concurrency & Architecture Bug Hunt",
        "description": (
            "Review a distributed rate limiter and async task queue. Find subtle "
            "concurrency bugs, race conditions, silent exception swallowing, "
            "mutation bugs, and architectural issues that only manifest under load."
        ),
        "difficulty": "hard",
        "max_steps": 8,
        "pr_title": "Implement distributed rate limiter and async task queue",
        "pr_description": (
            "Adds a rate limiter and background task queue for handling "
            "high-throughput job processing with retry logic."
        ),
        "file_name": "core/rate_limiter.py",
        "diff": """\
--- a/core/rate_limiter.py
++ b/core/rate_limiter.py
@@ -0,0 +1,82 @@
import time
import threading
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests, window_seconds):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, user_id):
        now = time.time()
        window_start = now - self.window_seconds
        with self.lock:
            self.requests[user_id] = [
                t for t in self.requests[user_id] if t > window_start
            ]
            if len(self.requests[user_id]) < self.max_requests:
                self.requests[user_id].append(now)
                return True
            return False

class TaskQueue:
    def __init__(self, max_workers=4):
        self.queue = []
        self.max_workers = max_workers
        self.workers = []
        self.running = False

    def add_task(self, task_fn, *args):
        self.queue.append((task_fn, args))

    def _worker(self):
        while self.running:
            if self.queue:
                task_fn, args = self.queue.pop(0)
                try:
                    task_fn(*args)
                except Exception:
                    pass
            time.sleep(0.01)

    def start(self):
        self.running = True
        for _ in range(self.max_workers):
            t = threading.Thread(target=self._worker)
            t.start()
            self.workers.append(t)

    def stop(self):
        self.running = False

class RetryQueue:
    def __init__(self, max_retries=3):
        self.max_retries = max_retries
        self.failed_tasks = {}
        self.retry_counts = defaultdict(int)

    def add_failed(self, task_id, task_fn):
        self.failed_tasks[task_id] = task_fn

    def retry_all(self):
        for task_id, task_fn in self.failed_tasks.items():
            if self.retry_counts[task_id] < self.max_retries:
                try:
                    task_fn()
                    del self.failed_tasks[task_id]
                except Exception:
                    self.retry_counts[task_id] += 1

    def get_stats(self):
        return {
            "pending": len(self.failed_tasks),
            "total_retries": sum(self.retry_counts.values())
        }

def process_batch(items, batch_size=100):
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        result = process_items(batch)
        results.append(result)
    return results

def merge_configs(base_config, override_config):
    merged = base_config
    for key, value in override_config.items():
        merged[key] = value
    return merged
""",
        "known_issues": [
            {
                "line_number": 9,
                "issue_type": "bug",
                "severity": "critical",
                "description": "RateLimiter uses in-memory storage — not actually distributed, state not shared across processes or instances",
                "keywords": ["distributed", "in-memory", "shared", "redis", "instance", "process", "not distributed"],
            },
            {
                "line_number": 25,
                "issue_type": "bug",
                "severity": "critical",
                "description": "TaskQueue.queue is a plain list with no lock — race condition when multiple workers call queue.pop(0) simultaneously",
                "keywords": ["race condition", "thread", "lock", "synchronization", "queue", "concurrent", "list", "pop"],
            },
            {
                "line_number": 39,
                "issue_type": "bug",
                "severity": "major",
                "description": "Exceptions silently swallowed with bare except pass — failed tasks are lost with no logging or retry",
                "keywords": ["exception", "silent", "swallow", "pass", "log", "lost", "bare except", "suppress"],
            },
            {
                "line_number": 49,
                "issue_type": "bug",
                "severity": "major",
                "description": "stop() sets running=False but never calls thread.join() — threads may still execute after stop() returns",
                "keywords": ["join", "thread", "stop", "shutdown", "daemon", "join()", "running"],
            },
            {
                "line_number": 63,
                "issue_type": "bug",
                "severity": "critical",
                "description": "retry_all() deletes from failed_tasks while iterating over it — RuntimeError: dictionary changed size during iteration",
                "keywords": ["dictionary", "iteration", "modify", "runtimeerror", "list()", "copy", "iterate", "delete"],
            },
            {
                "line_number": 73,
                "issue_type": "bug",
                "severity": "major",
                "description": "process_batch uses append instead of extend — returns list of batch-results not individual results, wrong data shape",
                "keywords": ["extend", "append", "batch", "result", "granularity", "list", "shape"],
            },
            {
                "line_number": 79,
                "issue_type": "bug",
                "severity": "major",
                "description": "merge_configs mutates base_config in-place — merged = base_config is a reference, not a copy; use base_config.copy()",
                "keywords": ["copy", "reference", "mutate", "shallow copy", "dict", "base_config", "in-place"],
            },
            {
                "line_number": 25,
                "issue_type": "performance",
                "severity": "minor",
                "description": "Use collections.deque instead of list for O(1) popleft() vs O(n) pop(0)",
                "keywords": ["deque", "o(1)", "performance", "popleft", "list", "collections"],
            },
        ],
        "required_verdict": "request_changes",
        "success_threshold": 0.35,
    },

    "js-async": {
        "id": "js-async",
        "name": "JavaScript Async Flow Review",
        "description": "Review a JavaScript module handling data fetching and state updates. Find async/await pitfalls and race conditions.",
        "difficulty": "easy-medium",
        "max_steps": 4,
        "pr_title": "Fix data loading and caching logic",
        "pr_description": "Implements an async data Fetcher with internal cache.",
        "file_name": "api/fetcher.js",
        "diff": """\
--- a/api/fetcher.js
+++ b/api/fetcher.js
@@ -0,0 +1,35 @@
+class DataFetcher {
+  constructor() {
+    this.cache = {};
+    this.loading = false;
+  }
+
+  async fetchData(url) {
+    if (this.cache[url]) return this.cache[url];
+
+    this.loading = true;
+    try {
+      const response = fetch(url);
+      const data = await response.json();
+      this.cache[url] = data;
+      return data;
+    } catch (err) {
+      console.error("Fetch failed");
+    } finally {
+      this.loading = false;
+    }
+  }
+
+  updateUI(data) {
+    this.fetchData('/api/user').then(user => {
+      document.getElementById('user').innerText = user.name;
+    });
+  }
+
+  async loadItems(urls) {
+    urls.forEach(async (url) => {
+      await this.fetchData(url);
+    });
+  }
+}
""",
        "known_issues": [
            {
                "line_number": 11,
                "issue_type": "bug",
                "severity": "critical",
                "description": "Missing await on fetch(url) — response will be a Promise, not the result",
                "keywords": ["await", "fetch", "promise"],
            },
            {
                "line_number": 16,
                "issue_type": "bug",
                "severity": "major",
                "description": "Silent error swallowing in catch block without rethrowing or user notification",
                "keywords": ["catch", "swallow", "error", "rethrow"],
            },
            {
                "line_number": 30,
                "issue_type": "performance",
                "severity": "major",
                "description": "forEach with async callback doesn't await the loop — use Promise.all or for...of",
                "keywords": ["forEach", "async", "Promise.all", "loop"],
            },
        ],
        "required_verdict": "request_changes",
        "success_threshold": 0.5,
    },

    "sql-injection": {
        "id": "sql-injection",
        "name": "Advanced SQL Injection Hunt",
        "description": "Review a Node.js database service. Identify multiple sophisticated SQL injection patterns.",
        "difficulty": "medium",
        "max_steps": 5,
        "pr_title": "Enhance reporting queries with dynamic sorting",
        "pr_description": "Adds support for custom sort orders and limits in reports.",
        "file_name": "db/reports.js",
        "diff": """\
--- a/db/reports.js
+++ b/db/reports.js
@@ -0,0 +1,28 @@
+const db = require('./connection');
+
+async function getReport(type, sortBy = 'created_at', limit = 10) {
+  const query = `
+    SELECT * FROM reports 
+    WHERE type = '${type}' 
+    ORDER BY ${sortBy} 
+    LIMIT ${limit}
+  `;
+  return db.query(query);
+}
+
+async function getUserSummary(userId) {
+  const sql = "SELECT * FROM summaries WHERE user_id = " + userId;
+  return db.query(sql);
+}
+
+async function searchLogs(term) {
+  const sql = `SELECT * FROM logs WHERE message LIKE '%${term}%'`;
+  return db.query(sql);
+}
""",
        "known_issues": [
            {
                "line_number": 6,
                "issue_type": "security",
                "severity": "critical",
                "description": "Classic SQL Injection in WHERE clause via template literal",
                "keywords": ["sql injection", "injection", "template literal"],
            },
            {
                "line_number": 7,
                "issue_type": "security",
                "severity": "critical",
                "description": "SQL Injection in ORDER BY clause — cannot be parameterized, must use whitelist",
                "keywords": ["order by", "injection", "whitelist"],
            },
            {
                "line_number": 8,
                "issue_type": "security",
                "severity": "critical",
                "description": "SQL Injection in LIMIT clause — ensure limit is a number",
                "keywords": ["limit", "injection", "number"],
            },
            {
                "line_number": 14,
                "issue_type": "security",
                "severity": "critical",
                "description": "Simple string concatenation SQL Injection",
                "keywords": ["concatenation", "injection", "sql"],
            },
        ],
        "required_verdict": "request_changes",
        "success_threshold": 0.6,
    },

    "react-security": {
        "id": "react-security",
        "name": "React Component Security",
        "description": "Review a React component for XSS risks and sensitive data leaks.",
        "difficulty": "medium",
        "max_steps": 4,
        "pr_title": "Implement UserProfile component with markdown support",
        "pr_description": "Adds a profile page that renders user-provided bio content.",
        "file_name": "components/UserProfile.jsx",
        "diff": """\
--- a/components/UserProfile.jsx
+++ b/components/UserProfile.jsx
@@ -0,0 +1,25 @@
+import React from 'react';
+
+export const UserProfile = ({ user, authToken }) => {
+  console.log("Loading profile for user:", user.id, "Token:", authToken);
+
+  const renderBio = (bio) => {
+    return <div dangerouslySetInnerHTML={{ __html: bio }} />;
+  };
+
+  return (
+    <div className="profile-card">
+      <h1>{user.name}</h1>
+      <div className="bio">
+        {renderBio(user.bio)}
+      </div>
+      <button onClick={() => window.location.href = `/edit?token=${authToken}`}>
+        Edit Profile
+      </button>
+    </div>
+  );
+};
""",
        "known_issues": [
            {
                "line_number": 4,
                "issue_type": "security",
                "severity": "major",
                "description": "Sensitive data (authToken) leaked to browser console",
                "keywords": ["console", "leak", "token", "sensitive"],
            },
            {
                "line_number": 7,
                "issue_type": "security",
                "severity": "critical",
                "description": "XSS vulnerability via dangerouslySetInnerHTML without sanitization",
                "keywords": ["dangerouslySetInnerHTML", "xss", "sanitize", "cross-site scripting"],
            },
            {
                "line_number": 16,
                "issue_type": "security",
                "severity": "major",
                "description": "Sensitive token leaked in URL query parameters",
                "keywords": ["url", "query parameter", "token", "leak"],
            },
        ],
        "required_verdict": "request_changes",
        "success_threshold": 0.5,
    },

    "django-auth": {
        "id": "django-auth",
        "name": "Django Auth Logic Review",
        "description": "Review Django middleware and auth backends for bypasses and timing attacks.",
        "difficulty": "hard",
        "max_steps": 7,
        "pr_title": "Custom Authentication and Security Middleware",
        "pr_description": "Customizes Django auth to support legacy hash formats and IP-based restrictions.",
        "file_name": "auth/middleware.py",
        "diff": """\
--- a/auth/middleware.py
+++ b/auth/middleware.py
@@ -0,0 +1,40 @@
+from django.shortcuts import redirect
+from django.conf import settings
+
+class IPBlockMiddleware:
+    def __init__(self, get_response):
+        self.get_response = get_response
+
+    def __call__(self, request):
+        ip = request.META.get('REMOTE_ADDR')
+        if ip in settings.BLOCKED_IPS:
+            return redirect('/blocked/')
+        return self.get_response(request)
+
+class LegacyBackend:
+    def authenticate(self, request, username=None, password=None):
+        user = User.objects.get(username=username)
+        if user.legacy_password == password:
+            return user
+        return None
+
+def validate_token(token):
+    if token == settings.SUPER_SECRET_TOKEN:
+        return True
+    return False
+
+def secure_view(request):
+    if not request.user.is_authenticated:
+        return redirect('/login/')
+    # Sensitive data processing here
+    pass
""",
        "known_issues": [
            {
                "line_number": 17,
                "issue_type": "security",
                "severity": "critical",
                "description": "Plaintext password comparison for legacy accounts",
                "keywords": ["plaintext", "password", "comparison"],
            },
            {
                "line_number": 21,
                "issue_type": "security",
                "severity": "critical",
                "description": "Timing attack vulnerability in string comparison for secret token",
                "keywords": ["timing attack", "comparison", "constant time"],
            },
            {
                "line_number": 16,
                "issue_type": "bug",
                "severity": "major",
                "description": "User.objects.get() raises DoesNotExist if user not found; should use filter().first() or try/except",
                "keywords": ["DoesNotExist", "exception", "crash"],
            },
        ],
        "required_verdict": "request_changes",
        "success_threshold": 0.4,
    },

    "node-race": {
        "id": "node-race",
        "name": "Node.js Concurrency Issues",
        "description": "Identify race conditions in a Node.js singleton service responsible for inventory tracking.",
        "difficulty": "hard",
        "max_steps": 6,
        "pr_title": "Inventory Management Singleton",
        "pr_description": "Initial implementation of in-memory inventory tracking for fast access.",
        "file_name": "services/inventory.js",
        "diff": """\
--- a/services/inventory.js
+++ b/services/inventory.js
@@ -0,0 +1,30 @@
+let inventory = {
+  'item_1': 100,
+  'item_2': 50
+};
+
+async function purchaseItem(itemId, quantity) {
+  const currentStock = inventory[itemId];
+  
+  if (currentStock >= quantity) {
+    // Simulate DB delay
+    await new Promise(resolve => setTimeout(resolve, 100));
+    
+    inventory[itemId] = currentStock - quantity;
+    return true;
+  }
+  return false;
+}
+
+async function restockItem(itemId, amount) {
+  inventory[itemId] += amount;
+}
+
+module.exports = { purchaseItem, restockItem };
""",
        "known_issues": [
            {
                "line_number": 7,
                "issue_type": "bug",
                "severity": "critical",
                "description": "Race condition: stock checked at line 7 but updated at line 12 after await. Parallel calls can lead to over-selling.",
                "keywords": ["race condition", "atomic", "oversell"],
            },
            {
                "line_number": 12,
                "issue_type": "bug",
                "severity": "major",
                "description": "Inventory update uses stale 'currentStock' variable instead of incrementing current value.",
                "keywords": ["stale", "atomic", "increment"],
            },
        ],
        "required_verdict": "request_changes",
        "success_threshold": 0.3,
    },

    "js_async": {
        "id": "js_async",
        "name": "JavaScript Async Bug Review",
        "description": "Review a JavaScript async handler with 5 bugs: unhandled promise rejection, missing await, callback hell, no error boundary, and memory leak from uncleaned event listener.",
        "difficulty": "medium",
        "max_steps": 5,
        "file_name": "api/async_handler.js",
        "pr_title": "Add async API handler for user data fetching",
        "pr_description": "Implements async handler to fetch and process user data from external API. Adds caching and retry logic.",
        "diff": """\
--- a/api/async_handler.js
+++ b/api/async_handler.js
@@ -1,40 +1,60 @@
+const EventEmitter = require('events');
+const emitter = new EventEmitter();
+
+async function fetchUserData(userId) {
+    const response = fetch(`/api/users/${userId}`);  // line 5: missing await
+    return response.json();
+}
+
+function processData(data, callback) {
+    getData(data, function(err, result) {             // line 9: callback hell starts
+        parseResult(result, function(err, parsed) {
+            saveToDb(parsed, function(err, saved) {  // line 11: deeply nested callbacks
+                callback(saved);
+            });
+        });
+    });
+}
+
+async function handleRequest(req, res) {
+    const userData = await fetchUserData(req.userId);
+    
+    emitter.on('data', (chunk) => {                  // line 21: listener never removed = memory leak
+        processChunk(chunk);
+    });
+
+    Promise.all([                                    // line 25: unhandled promise rejection
+        fetchProfile(req.userId),
+        fetchPermissions(req.userId)
+    ]);
+
+    try {
+        const result = processUserData(userData);
+        res.send(result);
+    } catch(e) {
+        console.log(e);                              // line 34: swallows error, no response sent
+    }
+
+    const timer = setInterval(() => {               // line 37: interval never cleared
+        checkStatus();
+    }, 1000);
+}
+
+module.exports = { handleRequest };
""",
        "required_verdict": "request_changes",
        "known_issues": [
            {
                "line_number": 5,
                "issue_type": "bug",
                "severity": "major",
                "description": "Missing await on fetch() call — returns Promise instead of response",
                "keywords": ["await", "fetch", "promise", "missing"]
            },
            {
                "line_number": 11,
                "issue_type": "style",
                "severity": "minor",
                "description": "Callback hell — deeply nested callbacks should be replaced with async/await",
                "keywords": ["callback", "nested", "hell", "async"]
            },
            {
                "line_number": 21,
                "issue_type": "bug",
                "severity": "major",
                "description": "Event listener added on every request but never removed — causes memory leak",
                "keywords": ["memory leak", "listener", "emitter", "removed"]
            },
            {
                "line_number": 25,
                "issue_type": "bug",
                "severity": "critical",
                "description": "Promise.all() result not awaited — unhandled promise rejection if either promise fails",
                "keywords": ["unhandled", "promise", "await", "rejection"]
            },
            {
                "line_number": 34,
                "issue_type": "bug",
                "severity": "major",
                "description": "Error caught but no error response sent to client — request hangs forever",
                "keywords": ["error", "response", "catch", "hang"]
            }
        ]
    },

    "api_security": {
        "id": "api_security",
        "name": "API Security Review",
        "description": "Review a Python FastAPI endpoints file with 6 security bugs: JWT bypass, CORS wildcard, missing rate limiting, exposed stack trace, insecure direct object reference, and debug mode enabled.",
        "difficulty": "hard",
        "max_steps": 6,
        "file_name": "api/endpoints.py",
        "pr_title": "Refactor API endpoints with JWT authentication",
        "pr_description": "Adds JWT-based auth to all endpoints. Enables CORS for frontend. Adds error handling.",
        "diff": """\
--- a/api/endpoints.py
+++ b/api/endpoints.py
@@ -1,50 +1,70 @@
+from fastapi import FastAPI, Request
+from jose import jwt
+import traceback
+
+app = FastAPI(debug=True)                            # line 4: debug mode exposes internals
+
+app.add_middleware(
+    CORSMiddleware,
+    allow_origins=["*"],                             # line 9: wildcard CORS
+    allow_methods=["*"],
+    allow_credentials=True,
+)
+
+SECRET_KEY = "secret"                                # line 14: weak JWT secret
+
+def verify_token(token: str):
+    try:
+        payload = jwt.decode(token, SECRET_KEY, algorithms=["none"])  # line 18: algorithm=none bypass
+        return payload
+    except:
+        return None                                  # line 21: returns None instead of raising
+
+@app.get("/users/{user_id}")
+def get_user(user_id: int, token: str):
+    user = db.query(f"SELECT * FROM users WHERE id={user_id}")  # line 25: IDOR - no ownership check
+    return user
+
+@app.exception_handler(Exception)
+def handle_error(request: Request, exc: Exception):
+    return JSONResponse(
+        status_code=500,
+        content={"error": traceback.format_exc()}   # line 32: full stack trace exposed to client
+    )
+
+@app.post("/login")
+def login(username: str, password: str):
+    user = authenticate(username, password)
+    token = jwt.encode({"sub": username}, SECRET_KEY)
+    return {"token": token}                          # line 39: no rate limiting on login endpoint
""",
        "required_verdict": "request_changes",
        "known_issues": [
            {
                "line_number": 4,
                "issue_type": "security",
                "severity": "major",
                "description": "debug=True exposes internal routes, error details and auto-reload in production",
                "keywords": ["debug", "production", "exposed"]
            },
            {
                "line_number": 9,
                "issue_type": "security",
                "severity": "major",
                "description": "Wildcard CORS with allow_credentials=True is dangerous — allows any origin to make credentialed requests",
                "keywords": ["CORS", "wildcard", "credentials", "origin"]
            },
            {
                "line_number": 18,
                "issue_type": "security",
                "severity": "critical",
                "description": "JWT decoded with algorithm='none' — allows unsigned tokens, complete auth bypass",
                "keywords": ["JWT", "none", "algorithm", "bypass", "unsigned"]
            },
            {
                "line_number": 25,
                "issue_type": "security",
                "severity": "critical",
                "description": "No ownership check — any authenticated user can fetch any other user's data (IDOR)",
                "keywords": ["IDOR", "ownership", "authorization", "access control"]
            },
            {
                "line_number": 32,
                "issue_type": "security",
                "severity": "major",
                "description": "Full stack trace returned in API response — leaks internal code structure to attackers",
                "keywords": ["stack trace", "traceback", "exposed", "leak"]
            },
            {
                "line_number": 39,
                "issue_type": "security",
                "severity": "major",
                "description": "No rate limiting on /login endpoint — vulnerable to brute force attacks",
                "keywords": ["rate limit", "brute force", "login", "throttle"]
            }
        ]
    },

    "orm_bugs": {
        "id": "orm_bugs",
        "name": "Database ORM Bug Review",
        "description": "Review a SQLAlchemy ORM models file with 5 bugs: N+1 query, missing index on foreign key, transaction not committed, mutable default argument, and missing relationship cascade.",
        "difficulty": "medium",
        "max_steps": 5,
        "file_name": "models/database.py",
        "pr_title": "Add ORM models for orders and products",
        "pr_description": "Implements SQLAlchemy models for the e-commerce order system. Adds relationships between User, Order, and Product.",
        "diff": """\
--- a/models/database.py
+++ b/models/database.py
@@ -1,45 +1,65 @@
+from sqlalchemy import Column, Integer, String, ForeignKey
+from sqlalchemy.orm import relationship, Session
+
+class User(Base):
+    __tablename__ = "users"
+    id = Column(Integer, primary_key=True)
+    name = Column(String)
+    orders = relationship("Order")                   # line 8: missing cascade="all, delete-orphan"
+
+class Order(Base):
+    __tablename__ = "orders"
+    id = Column(Integer, primary_key=True)
+    user_id = Column(Integer, ForeignKey("users.id")) # line 13: missing index=True on FK
+    items = Column(String)
+
+def get_user_orders(session: Session, user_ids: list):
+    users = session.query(User).all()
+    for user in users:
+        print(user.orders)                           # line 19: N+1 query — lazy loads orders per user
+    return users
+
+def create_order(session: Session, user_id: int, items: list = []):  # line 22: mutable default arg
+    order = Order(user_id=user_id, items=str(items))
+    session.add(order)
+                                                     # line 25: missing session.commit()
+    return order
+
+def bulk_update_prices(session: Session, updates: dict):
+    for product_id, price in updates.items():
+        session.execute(
+            f"UPDATE products SET price={price} WHERE id={product_id}"  # line 31: raw SQL = SQL injection
+        )
+    session.commit()
""",
        "required_verdict": "request_changes",
        "known_issues": [
            {
                "line_number": 8,
                "issue_type": "bug",
                "severity": "major",
                "description": "relationship() missing cascade='all, delete-orphan' — orphaned Order rows left in DB when User deleted",
                "keywords": ["cascade", "orphan", "delete", "relationship"]
            },
            {
                "line_number": 13,
                "issue_type": "performance",
                "severity": "major",
                "description": "Foreign key column user_id has no index — causes full table scan on every join",
                "keywords": ["index", "foreign key", "scan", "performance"]
            },
            {
                "line_number": 19,
                "issue_type": "performance",
                "severity": "critical",
                "description": "N+1 query problem — accessing user.orders inside loop fires one SQL query per user",
                "keywords": ["N+1", "lazy load", "query", "loop", "joinedload"]
            },
            {
                "line_number": 22,
                "issue_type": "bug",
                "severity": "major",
                "description": "Mutable default argument [] is shared across all calls — list persists between function calls",
                "keywords": ["mutable", "default", "list", "shared", "argument"]
            },
            {
                "line_number": 25,
                "issue_type": "bug",
                "severity": "critical",
                "description": "session.commit() never called — order is added to session but never persisted to database",
                "keywords": ["commit", "persist", "transaction", "session"]
            }
        ]
    },

    "auth_system": {
        "id": "auth_system",
        "name": "JWT Auth System Review",
        "description": "Review a JWT authentication handler with 7 bugs: no expiry on tokens, weak secret key, session fixation, token not invalidated on logout, missing signature verification, timing attack on comparison, and tokens stored in localStorage.",
        "difficulty": "hard",
        "max_steps": 7,
        "file_name": "auth/jwt_handler.py",
        "pr_title": "Implement JWT authentication system",
        "pr_description": "Full JWT-based authentication with login, logout, and token refresh. Stores tokens client-side.",
        "diff": """\
--- a/auth/jwt_handler.py
+++ b/auth/jwt_handler.py
@@ -1,55 +1,75 @@
+import jwt
+import time
+
+SECRET = "abc123"                                    # line 4: weak, hardcoded secret key
+
+def create_token(user_id: int) -> str:
+    payload = {
+        "user_id": user_id,
+                                                     # line 9: no exp (expiry) field in payload
+    }
+    return jwt.encode(payload, SECRET, algorithm="HS256")
+
+def verify_token(token: str) -> dict:
+    try:
+        payload = jwt.decode(token, options={"verify_signature": False})  # line 15: skips signature check
+        return payload
+    except jwt.ExpiredSignatureError:
+        return {}
+
+def login(username: str, password: str, session: dict):
+    if authenticate(username, password):
+        session["user"] = username                   # line 22: session fixation — old session not regenerated
+        token = create_token(username)
+        return token
+
+def logout(token: str, session: dict):
+    session.clear()
+                                                     # line 28: token not added to blacklist/revoked
+
+def check_admin(user_token: str, required_role: str) -> bool:
+    user = get_user(user_token)
+    if user.role == required_role:                   # line 32: string comparison vulnerable to timing attack
+        return True
+    return False
+
+def reset_password(user_id: int, old_password: str, new_password: str):
+    if verify_password(old_password, stored_hash):
+        update_password(user_id, new_password)
+                                                     # line 39: old sessions not invalidated after password reset
""",
        "required_verdict": "request_changes",
        "known_issues": [
            {
                "line_number": 4,
                "issue_type": "security",
                "severity": "critical",
                "description": "Hardcoded weak secret key 'abc123' — trivially guessable, must use env var with strong random value",
                "keywords": ["secret", "hardcoded", "weak", "env var"]
            },
            {
                "line_number": 9,
                "issue_type": "security",
                "severity": "critical",
                "description": "JWT token has no expiry (exp claim missing) — tokens are valid forever",
                "keywords": ["expiry", "exp", "token", "forever", "expire"]
            },
            {
                "line_number": 15,
                "issue_type": "security",
                "severity": "critical",
                "description": "verify_signature=False disables JWT signature verification — any token accepted as valid",
                "keywords": ["signature", "verify", "disabled", "bypass"]
            },
            {
                "line_number": 22,
                "issue_type": "security",
                "severity": "major",
                "description": "Session fixation — existing session ID not regenerated on login, allows session hijacking",
                "keywords": ["session", "fixation", "regenerate", "hijack"]
            },
            {
                "line_number": 28,
                "issue_type": "security",
                "severity": "major",
                "description": "Logout does not invalidate the JWT token — token remains usable until expiry",
                "keywords": ["logout", "blacklist", "revoke", "invalidate", "token"]
            },
            {
                "line_number": 32,
                "issue_type": "security",
                "severity": "minor",
                "description": "String equality check vulnerable to timing attack — use hmac.compare_digest() instead",
                "keywords": ["timing attack", "compare_digest", "hmac", "equality"]
            },
            {
                "line_number": 39,
                "issue_type": "security",
                "severity": "major",
                "description": "Password reset does not invalidate existing sessions — attacker with old session stays logged in",
                "keywords": ["password reset", "session", "invalidate", "old session"]
            }
        ]
    },

    "data_pipeline": {
        "id": "data_pipeline",
        "name": "Data Pipeline Bug Review",
        "description": "Review a data processing pipeline with 6 bugs: memory leak from accumulating list, unchecked None input, wrong dtype causing silent overflow, file handle never closed, bare except swallowing errors, and off-by-one in batch slicing.",
        "difficulty": "medium",
        "max_steps": 6,
        "file_name": "pipeline/processor.py",
        "pr_title": "Add batch data processing pipeline",
        "pr_description": "Implements chunked batch processor for large CSV datasets. Adds transformation and validation steps.",
        "diff": """\
--- a/pipeline/processor.py
+++ b/pipeline/processor.py
@@ -1,50 +1,70 @@
+import numpy as np
+import csv
+
+results_cache = []                                   # line 4: module-level list grows forever = memory leak
+
+def process_record(record: dict) -> dict:
+    value = record["amount"] * 1.1                   # line 7: no None check — KeyError if "amount" missing
+    return {"processed": value}
+
+def convert_to_array(data: list) -> np.ndarray:
+    arr = np.array(data, dtype=np.int8)              # line 11: int8 overflows silently for values > 127
+    return arr
+
+def process_batch(records: list, batch_size: int = 100):
+    results_cache.append(records)                    # line 15: appends entire batch to module-level list
+    
+    for i in range(0, len(records), batch_size):
+        batch = records[i : i + batch_size + 1]     # line 18: off-by-one — includes extra record at boundary
+        yield batch
+
+def load_csv(filepath: str) -> list:
+    f = open(filepath, 'r')                          # line 22: file handle never closed
+    reader = csv.reader(f)
+    return list(reader)
+
+def run_pipeline(filepath: str):
+    try:
+        data = load_csv(filepath)
+        processed = [process_record(r) for r in data]
+        return processed
+    except:                                          # line 31: bare except swallows ALL errors silently
+        return []
""",
        "required_verdict": "request_changes",
        "known_issues": [
            {
                "line_number": 4,
                "issue_type": "bug",
                "severity": "major",
                "description": "Module-level results_cache list grows unboundedly — each call appends data, never cleared = memory leak",
                "keywords": ["memory leak", "cache", "unbounded", "module-level", "accumulate"]
            },
            {
                "line_number": 7,
                "issue_type": "bug",
                "severity": "major",
                "description": "No None/missing key check before accessing record['amount'] — raises KeyError on incomplete records",
                "keywords": ["None", "KeyError", "missing", "check", "amount"]
            },
            {
                "line_number": 11,
                "issue_type": "bug",
                "severity": "critical",
                "description": "dtype=int8 silently overflows for values > 127 — data corruption with no error raised",
                "keywords": ["overflow", "int8", "dtype", "silent", "numpy"]
            },
            {
                "line_number": 18,
                "issue_type": "bug",
                "severity": "minor",
                "description": "Slice uses i+batch_size+1 instead of i+batch_size — off-by-one includes an extra record in each batch",
                "keywords": ["off-by-one", "slice", "batch", "boundary", "index"]
            },
            {
                "line_number": 22,
                "issue_type": "bug",
                "severity": "major",
                "description": "File opened with open() but never closed — file handle leak, especially bad in loops",
                "keywords": ["file", "close", "handle", "leak", "open", "context manager"]
            },
            {
                "line_number": 31,
                "issue_type": "bug",
                "severity": "major",
                "description": "Bare except: catches all exceptions including KeyboardInterrupt and SystemExit — errors silently swallowed",
                "keywords": ["bare except", "swallow", "silent", "exception", "broad"]
            }
        ]
    },
}

def get_task(task_id: str) -> Dict[str, Any]:
    return TASKS.get(task_id, {})

def get_all_tasks() -> List[Dict[str, Any]]:
    return list(TASKS.values())
